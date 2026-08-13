#!/usr/bin/env python3
"""Evaluate external hy-check and hy-score run results."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


WEIGHTS = {
    "typography": 0.15,
    "language": 0.25,
    "grammar": 0.20,
    "structure": 0.20,
    "reader": 0.20,
}


def detection_metrics(golden: list[dict], reported: list[dict]) -> dict[str, float]:
    by_id = {case["id"]: set(case.get("reported_rules", [])) for case in reported}
    expected_count = found_count = extra_count = reported_count = 0
    for case in golden:
        expected = set(case.get("expected_rules", []))
        actual = by_id.get(case["id"], set())
        expected_count += len(expected)
        found_count += len(expected & actual)
        extra_count += len(actual - expected)
        reported_count += len(actual)
    return {
        "recall": round(found_count / expected_count, 4) if expected_count else 1.0,
        "false_discovery_rate": round(extra_count / reported_count, 4) if reported_count else 0.0,
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
    metrics = detection_metrics(golden, results) if args.mode == "check" else score_drift(golden, results)
    print(json.dumps(metrics, ensure_ascii=False, indent=2))

    if args.mode == "check":
        return 0 if metrics["recall"] >= 0.90 and metrics["false_discovery_rate"] <= 0.05 else 1
    return 0 if metrics["mean_composite_deviation"] <= 0.7 and metrics["max_dimension_deviation"] <= 1.0 else 1


if __name__ == "__main__":
    try:
        sys.exit(main())
    except (KeyError, ValueError, json.JSONDecodeError) as error:
        print(f"ERROR: {error}", file=sys.stderr)
        sys.exit(2)
