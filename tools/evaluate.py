#!/usr/bin/env python3
"""Evaluate external hy-check and hy-score run results."""

from __future__ import annotations

import argparse
from decimal import Decimal
import json
import math
import sys
from pathlib import Path


DIMENSIONS = ("typography", "language", "grammar", "structure", "reader")

WEIGHTS = {
    "typography": 0.15,
    "language": 0.25,
    "grammar": 0.20,
    "structure": 0.20,
    "reader": 0.20,
}

TOTAL_DEVIATION_LIMIT = 0.7
DIMENSION_DEVIATION_LIMIT = 1.0
REVIEWED_CASE_COUNT = 50


def _validate_scores(scores: object, context: str) -> None:
    if not isinstance(scores, dict) or set(scores) != set(DIMENSIONS):
        raise ValueError(f"{context} scores must contain exactly the required dimensions")

    for dimension in DIMENSIONS:
        value = scores[dimension]
        if isinstance(value, bool) or not isinstance(value, (int, float)):
            raise ValueError(f"{context} score for {dimension} must be numeric")
        if not math.isfinite(value) or not 0 <= value <= 10:
            raise ValueError(f"{context} score for {dimension} must be from 0 to 10")


def total_score(scores: dict[str, float]) -> float:
    """Return the published weighted score after non-compensatory caps."""
    _validate_scores(scores, "score")
    total = round(sum(float(scores[dimension]) * WEIGHTS[dimension] for dimension in DIMENSIONS), 1)
    caps = [10.0]
    if any(float(scores[dimension]) < 3.0 for dimension in DIMENSIONS):
        caps.append(5.0)
    if float(scores["typography"]) < 4.0:
        caps.append(7.0)
    if float(scores["grammar"]) < 4.0:
        caps.append(7.0)
    return min(total, *caps)


def score_calibration(golden: list[dict], runs: list[dict], expected_runs: int = 3) -> dict:
    """Evaluate every reviewed case in every required blind scoring run."""
    if isinstance(expected_runs, bool) or not isinstance(expected_runs, int) or expected_runs < 1:
        raise ValueError("expected_runs must be a positive integer")
    if not isinstance(golden, list) or not isinstance(runs, list):
        raise ValueError("golden and runs must be JSON arrays")

    reviewed: dict[str, dict] = {}
    for case in golden:
        if not isinstance(case, dict):
            raise ValueError("golden cases must be objects")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError("golden cases require a non-empty id")
        if case.get("reviewed") is not True:
            raise ValueError(f"golden case {case_id} is not reviewed")
        if case_id in reviewed:
            raise ValueError(f"duplicate reviewed golden id: {case_id}")
        _validate_scores(case.get("scores"), f"golden case {case_id}")
        reviewed[case_id] = case

    if len(reviewed) != REVIEWED_CASE_COUNT:
        raise ValueError(f"expected exactly {REVIEWED_CASE_COUNT} reviewed golden cases")

    expected_run_numbers = set(range(1, expected_runs + 1))
    observed_runs: set[int] = set()
    seen_pairs: set[tuple[int, str]] = set()
    results_by_pair: dict[tuple[int, str], dict] = {}

    for result in runs:
        if not isinstance(result, dict):
            raise ValueError("run results must be objects")
        run_number = result.get("run")
        case_id = result.get("id")
        if isinstance(run_number, bool) or not isinstance(run_number, int):
            raise ValueError("run must be an integer")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError("run results require a non-empty id")
        pair = (run_number, case_id)
        if pair in seen_pairs:
            raise ValueError(f"duplicate run/id pair: {run_number}/{case_id}")
        seen_pairs.add(pair)
        if run_number not in expected_run_numbers:
            raise ValueError(f"missing or unexpected runs: expected 1 through {expected_runs}")
        if case_id not in reviewed:
            raise ValueError(f"run {run_number} contains unknown reviewed case: {case_id}")
        _validate_scores(result.get("scores"), f"run {run_number} case {case_id}")
        observed_runs.add(run_number)
        results_by_pair[pair] = result

    if observed_runs != expected_run_numbers:
        raise ValueError(f"missing or unexpected runs: expected 1 through {expected_runs}")

    reviewed_ids = set(reviewed)
    for run_number in sorted(expected_run_numbers):
        observed_ids = {case_id for number, case_id in results_by_pair if number == run_number}
        missing_ids = reviewed_ids - observed_ids
        if missing_ids:
            raise ValueError(
                f"missing reviewed cases for run {run_number}: {', '.join(sorted(missing_ids))}"
            )

    expected_result_count = expected_runs * REVIEWED_CASE_COUNT
    if len(results_by_pair) != expected_result_count:
        raise ValueError(f"expected exactly {expected_result_count} run results")

    total_deviation_limit = Decimal(str(TOTAL_DEVIATION_LIMIT))
    dimension_deviation_limit = Decimal(str(DIMENSION_DEVIATION_LIMIT))
    maximum_total_deviation = Decimal("0")
    maximum_dimension_deviation = Decimal("0")
    failing_cases = []
    for run_number in sorted(expected_run_numbers):
        for case_id in sorted(reviewed_ids):
            expert_scores = reviewed[case_id]["scores"]
            result_scores = results_by_pair[(run_number, case_id)]["scores"]
            total_deviation = abs(
                Decimal(str(total_score(result_scores))) - Decimal(str(total_score(expert_scores)))
            )
            dimension_deviations = {
                dimension: abs(
                    Decimal(str(result_scores[dimension]))
                    - Decimal(str(expert_scores[dimension]))
                )
                for dimension in DIMENSIONS
            }
            maximum_total_deviation = max(maximum_total_deviation, total_deviation)
            maximum_dimension_deviation = max(maximum_dimension_deviation, *dimension_deviations.values())
            failing_dimensions = {
                dimension: float(deviation)
                for dimension, deviation in dimension_deviations.items()
                if deviation > dimension_deviation_limit
            }
            total_failure = total_deviation > total_deviation_limit
            if total_failure:
                failing_dimensions = {
                    dimension: float(deviation)
                    for dimension, deviation in dimension_deviations.items()
                    if deviation > 0
                }
            if total_failure or failing_dimensions:
                failing_cases.append(
                    {
                        "run": run_number,
                        "id": case_id,
                        "total_deviation": float(total_deviation),
                        "dimension_deviations": failing_dimensions,
                    }
                )

    run_completeness = {
        "expected_runs": expected_runs,
        "actual_runs": len(observed_runs),
        "reviewed_cases": REVIEWED_CASE_COUNT,
        "expected_results": expected_result_count,
        "actual_results": len(results_by_pair),
        "complete": True,
    }
    return {
        "passed": not failing_cases,
        "run_completeness": run_completeness,
        "max_total_deviation": float(maximum_total_deviation),
        "max_dimension_deviation": float(maximum_dimension_deviation),
        "failing_cases": failing_cases,
    }


def detection_metrics(golden: list[dict], reported: list[dict]) -> dict:
    """Evaluate one complete blind hy-check run against its golden corpus."""
    if not isinstance(golden, list) or not isinstance(reported, list):
        raise ValueError("golden and check results must be JSON arrays")

    golden_by_id: dict[str, dict] = {}
    for case in golden:
        if not isinstance(case, dict):
            raise ValueError("golden check cases must be objects")
        case_id = case.get("id")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError("golden check cases require a non-empty id")
        if case_id in golden_by_id:
            raise ValueError(f"duplicate golden check id: {case_id}")
        expected_rules = case.get("expected_rules", [])
        if not isinstance(expected_rules, list) or any(
            not isinstance(rule, str) or not rule.startswith("HY-") for rule in expected_rules
        ):
            raise ValueError(f"golden check case {case_id} has invalid expected rules")
        if len(expected_rules) != len(set(expected_rules)):
            raise ValueError(f"golden check case {case_id} has duplicate expected rules")
        protected_spans = case.get("protected_spans", [])
        if not isinstance(protected_spans, list) or any(
            not isinstance(span, dict)
            or not isinstance(span.get("type"), str)
            or not isinstance(span.get("text"), str)
            or not span["text"]
            for span in protected_spans
        ):
            raise ValueError(f"golden check case {case_id} has invalid protected spans")
        golden_by_id[case_id] = case

    reported_by_id: dict[str, dict] = {}
    for result in reported:
        if not isinstance(result, dict):
            raise ValueError("check results must be objects")
        case_id = result.get("id")
        if not isinstance(case_id, str) or not case_id:
            raise ValueError("check results require a non-empty id")
        if case_id in reported_by_id:
            raise ValueError(f"duplicate check result id: {case_id}")
        if case_id not in golden_by_id:
            raise ValueError(f"unknown check result id: {case_id}")
        rules = result.get("reported_rules")
        corrected_text = result.get("corrected_text")
        if not isinstance(rules, list) or any(
            not isinstance(rule, str) or not rule.startswith("HY-") for rule in rules
        ):
            raise ValueError(f"check result {case_id} has invalid reported rules")
        if len(rules) != len(set(rules)):
            raise ValueError(f"check result {case_id} has duplicate reported rules")
        if not isinstance(corrected_text, str):
            raise ValueError(f"check result {case_id} requires corrected_text")
        reported_by_id[case_id] = result

    missing_ids = set(golden_by_id) - set(reported_by_id)
    if missing_ids:
        raise ValueError(f"missing check results: {', '.join(sorted(missing_ids))}")

    expected_count = found_count = 0
    clean_count = clean_with_findings = 0
    protected_mutation_count = 0
    diagnostics = []
    for case in golden:
        case_id = case["id"]
        expected = set(case.get("expected_rules", []))
        result = reported_by_id[case_id]
        actual = set(result["reported_rules"])
        expected_count += len(expected)
        found_count += len(expected & actual)
        if not expected:
            clean_count += 1
            if actual:
                clean_with_findings += 1

        mutated_spans = [
            span
            for span in case.get("protected_spans", [])
            if span["text"] not in result["corrected_text"]
        ]
        protected_mutation_count += len(mutated_spans)
        diagnostics.append(
            {
                "id": case_id,
                "missing_rules": sorted(expected - actual),
                "extra_rules": sorted(actual - expected),
                "protected_mutations": mutated_spans,
                "correction_matches": result["corrected_text"] == case.get("expected_text", ""),
            }
        )

    return {
        "recall": round(found_count / expected_count, 4) if expected_count else 1.0,
        "clean_false_positive_rate": (
            round(clean_with_findings / clean_count, 4) if clean_count else 0.0
        ),
        "protected_mutations": protected_mutation_count,
        "case_count": len(golden_by_id),
        "cases": diagnostics,
    }


def score_drift(golden: list[dict], runs: list[dict]) -> dict[str, float]:
    reviewed = {case["id"]: case for case in golden if case.get("reviewed") is True}
    deviations = []
    dimension_deviations = []
    for run in runs:
        case = reviewed.get(run["id"])
        if not case:
            continue
        weighted_absolute = 0.0
        for dimension, weight in WEIGHTS.items():
            deviation = abs(float(run["scores"][dimension]) - float(case["scores"][dimension]))
            dimension_deviations.append(deviation)
            weighted_absolute += deviation * weight
        deviations.append(weighted_absolute)
    if not deviations:
        raise ValueError("no reviewed golden cases matched the supplied runs")
    return {
        "mean_composite_deviation": round(sum(deviations) / len(deviations), 1),
        "max_dimension_deviation": round(max(dimension_deviations), 1),
    }


def read_json(path: Path) -> list[dict]:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--golden", type=Path, required=True)
    parser.add_argument("--results", type=Path, required=True)
    parser.add_argument("--mode", choices=("check", "score"), required=True)
    args = parser.parse_args()

    golden = read_json(args.golden)
    results = read_json(args.results)
    metrics = detection_metrics(golden, results) if args.mode == "check" else score_calibration(golden, results)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))

    if args.mode == "check":
        return 0 if (
            metrics["recall"] >= 0.90
            and metrics["clean_false_positive_rate"] <= 0.05
            and metrics["protected_mutations"] == 0
        ) else 1
    return 0 if metrics["passed"] else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyError, TypeError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(2)
