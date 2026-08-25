import json
import hashlib
import re
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]

def canonical_json_sha256(value):
    payload = json.dumps(
        value, ensure_ascii=False, sort_keys=True, separators=(",", ":")
    ).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def normalized_text_sha256(path):
    text = (
        path.read_text(encoding="utf-8")
        .replace("\r\n", "\n")
        .replace("\r", "\n")
    )
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


class GoldenContractTest(unittest.TestCase):
    def test_check_set_has_release_scale_domain_and_rule_family_coverage(self):
        cases = json.loads((ROOT / "tests" / "golden" / "check.json").read_text(encoding="utf-8"))
        self.assertEqual(50, len(cases))
        self.assertEqual(50, len({case["id"] for case in cases}))

        domains = ("article", "business", "marketing", "mixed", "ux")
        self.assertEqual(
            {domain: 10 for domain in domains},
            {domain: sum(case["domain"] == domain for case in cases) for domain in domains},
        )
        for domain in domains:
            domain_cases = [case for case in cases if case["domain"] == domain]
            self.assertTrue(any(case["expected_rules"] for case in domain_cases))
            self.assertTrue(any(not case["expected_rules"] for case in domain_cases))

        expected_families = {
            rule.split("-")[1]
            for case in cases
            for rule in case["expected_rules"]
        }
        self.assertTrue(
            {"TYP", "PUN", "GRM", "INF", "UX", "BIZ", "ANT", "ADD"}.issubset(
                expected_families
            )
        )

        protected_types = {
            span["type"]
            for case in cases
            for span in case["protected_spans"]
        }
        self.assertTrue(
            {"code", "command", "url", "foreign", "quotation", "filename"}.issubset(
                protected_types
            )
        )
        for case in cases:
            required_fields = {
                "id", "domain", "text", "expected_text", "expected_rules", "protected_spans"
            }
            self.assertTrue(required_fields.issubset(case))
            self.assertTrue(set(case).issubset(required_fields | {"accepted_corrections"}))
            self.assertTrue(case["text"].strip())
            self.assertTrue(case["expected_text"].strip())
            accepted = case.get("accepted_corrections", [case["expected_text"]])
            self.assertIn(case["expected_text"], accepted)
            self.assertEqual(len(accepted), len(set(accepted)))
            if case["expected_rules"]:
                self.assertNotIn(case["text"], accepted)
            else:
                self.assertEqual(case["text"], case["expected_text"])
            for span in case["protected_spans"]:
                self.assertIn(span["text"], case["text"])
                self.assertIn(span["text"], case["expected_text"])

    def test_check_corrections_do_not_invent_missing_operational_facts(self):
        cases = json.loads((ROOT / "tests" / "golden" / "check.json").read_text(encoding="utf-8"))
        by_id = {case["id"]: case for case in cases}

        self.assertEqual(
            "Հանդիպման ամփոփում\nՊետք է որոշել՝ ով և մինչև երբ կպատրաստի ամսական "
            "հաշվետվությունը։ Հաջորդ հանդիպումը երկուշաբթի է։",
            by_id["business-03"]["expected_text"],
        )
        self.assertEqual(
            "Կցել եմ contract.pdf ֆայլը։ Խնդրում եմ ստուգել այն և պատասխանել մինչև "
            "չորեքշաբթի։",
            by_id["business-05"]["expected_text"],
        )
        self.assertEqual(
            "Մեր թիմը պատրաստ է օգնել նոր հաճախորդներին։",
            by_id["marketing-01"]["expected_text"],
        )
        self.assertEqual(
            "Պատվերը հասել է երկուշաբթի՝ սահմանված ժամկետից ուշ։",
            by_id["marketing-05"]["expected_text"],
        )

    def test_check_corrections_do_not_add_unsupported_times_or_payment_instruments(self):
        cases = json.loads((ROOT / "tests" / "golden" / "check.json").read_text(encoding="utf-8"))
        payment_instruments = ("քարտ", "բանկային հաշիվ", "կանխիկ")

        for case in cases:
            corrections = case.get("accepted_corrections", [case["expected_text"]])
            source_times = set(re.findall(r"(?<!\d)\d{1,2}:\d{2}(?!\d)", case["text"]))
            for correction in corrections:
                with self.subTest(case=case["id"], correction=correction):
                    self.assertTrue(
                        set(re.findall(r"(?<!\d)\d{1,2}:\d{2}(?!\d)", correction)).issubset(
                            source_times
                        )
                    )
                    for instrument in payment_instruments:
                        if instrument not in case["text"]:
                            self.assertNotIn(instrument, correction)

    def test_check_release_results_are_complete_and_pass_quality_gates(self):
        module = __import__("importlib.util").util
        spec = module.spec_from_file_location("hy_text_evaluate_for_golden", ROOT / "tools" / "evaluate.py")
        evaluate = module.module_from_spec(spec)
        spec.loader.exec_module(evaluate)
        golden = json.loads((ROOT / "tests" / "golden" / "check.json").read_text(encoding="utf-8"))
        results = json.loads(
            (ROOT / "tests" / "calibration" / "v1.0.0" / "check-results.json").read_text(
                encoding="utf-8"
            )
        )

        metrics = evaluate.detection_metrics(golden, results)

        self.assertEqual(50, metrics["case_count"])
        self.assertGreaterEqual(metrics["recall"], 0.90)
        self.assertLessEqual(metrics["clean_false_positive_rate"], 0.05)
        self.assertEqual(0, metrics["protected_mutations"])
        self.assertEqual(0, metrics["correction_failures"])
        self.assertEqual(1.0, metrics["correction_accuracy"])

    def test_scoring_set_has_fifty_arman_reviewed_cases(self):
        cases = json.loads((ROOT / "tests" / "golden" / "scoring.json").read_text(encoding="utf-8"))
        self.assertEqual(50, len(cases))
        self.assertEqual({"article", "business", "marketing", "mixed", "ux"}, {case["domain"] for case in cases})
        for case in cases:
            self.assertEqual({"typography", "language", "grammar", "structure", "reader"}, set(case["scores"]))
            self.assertTrue(case["reviewed"], "every scoring fixture must carry Arman's explicit review")

        by_id = {case["id"]: case for case in cases}
        self.assertEqual(
            "Բացեք config/app.php ֆայլը և փոխեք locale-ի արժեքը։",
            by_id["mixed-05"]["text"],
        )
        self.assertEqual(
            "API-ի պատասխանը պարունակում է `{\"status\":\"ok\"}` տողը։",
            by_id["mixed-06"]["text"],
        )
        self.assertEqual(
            {
                "typography": 4,
                "language": 9,
                "grammar": 4,
                "structure": 9,
                "reader": 9,
            },
            by_id["article-03"]["scores"],
        )
        readme = (ROOT / "tests" / "golden" / "README.md").read_text(encoding="utf-8")
        self.assertIn("article-03", readme)
        self.assertIn("human re-review on 2026-08-15", readme)

    def test_second_human_adjudication_is_exact_and_preserves_fixture_identity(self):
        cases = json.loads((ROOT / "tests" / "golden" / "scoring.json").read_text(encoding="utf-8"))
        self.assertEqual(50, len(cases))
        self.assertEqual(
            [
                f"{domain}-{number:02d}"
                for domain in ("article", "business", "marketing", "mixed", "ux")
                for number in range(1, 11)
            ],
            [case["id"] for case in cases],
        )
        self.assertTrue(all(case["reviewed"] for case in cases))

        identity = hashlib.sha256(
            "".join(f'{case["id"]}\0{case["text"]}\n' for case in cases).encode()
        ).hexdigest()
        self.assertEqual(
            "07386b8a8135abc5065d624b4063950304e3ec528ffb3d40a1141dcf274b4219",
            identity,
        )

        by_id = {case["id"]: case for case in cases}
        expected = {
            "article-05": {"typography": 9, "language": 4, "grammar": 9, "structure": 6, "reader": 2},
            "marketing-04": {"typography": 9, "language": 3, "grammar": 9, "structure": 5, "reader": 2},
            "ux-02": {"typography": 9, "language": 7, "grammar": 9, "structure": 6, "reader": 3},
        }
        for case_id, scores in expected.items():
            self.assertEqual(scores, by_id[case_id]["scores"])

        unchanged = hashlib.sha256(
            "".join(
                f'{case["id"]}\0{json.dumps(case["scores"], sort_keys=True, separators=(",", ":"))}\n'
                for case in cases
                if case["id"] not in expected
            ).encode()
        ).hexdigest()
        self.assertEqual(
            "198c414c4f711999f3099d5bc8f704ebdf7fc54c24ca0ecfe3b0c4abcbe7b704",
            unchanged,
        )

    def test_score_release_evidence_is_exact_complete_and_passing(self):
        module = __import__("importlib.util").util
        spec = module.spec_from_file_location(
            "hy_text_evaluate_for_score_evidence", ROOT / "tools" / "evaluate.py"
        )
        evaluate = module.module_from_spec(spec)
        spec.loader.exec_module(evaluate)

        calibration = ROOT / "tests" / "calibration" / "v1.0.0"
        golden_path = ROOT / "tests" / "golden" / "scoring.json"
        golden = json.loads(golden_path.read_text(encoding="utf-8"))
        canonical_ids = [case["id"] for case in golden]
        dimensions = ("typography", "language", "grammar", "structure", "reader")
        all_runs = []
        pass_records = {}
        summary = json.loads((calibration / "summary.json").read_text(encoding="utf-8"))

        for run in range(1, 4):
            path = calibration / f"pass-{run}.json"
            records = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(50, len(records))
            self.assertEqual(canonical_ids, [record["id"] for record in records])
            self.assertEqual(50, len({record["id"] for record in records}))
            for record in records:
                self.assertEqual({"id", "run", "scores"}, set(record))
                self.assertEqual(run, record["run"])
                self.assertNotIsInstance(record["run"], bool)
                self.assertEqual(dimensions, tuple(record["scores"]))
                for score in record["scores"].values():
                    self.assertIsInstance(score, (int, float))
                    self.assertNotIsInstance(score, bool)
                    self.assertGreaterEqual(score, 0)
                    self.assertLessEqual(score, 10)
            pass_records[run] = records
            all_runs.extend(records)

        self.assertEqual(150, len(all_runs))
        self.assertEqual(150, len({(record["run"], record["id"]) for record in all_runs}))

        metrics = evaluate.score_calibration(golden, all_runs)
        self.assertTrue(metrics["passed"])
        self.assertEqual([], metrics["failing_cases"])
        self.assertEqual(150, metrics["run_completeness"]["actual_results"])
        self.assertTrue(metrics["run_completeness"]["complete"])
        self.assertLessEqual(metrics["max_total_deviation"], 0.7)
        self.assertLessEqual(metrics["max_dimension_deviation"], 1.0)

        self.assertEqual(
            "176dd8f459da89a6ed20ead17cba0ea8466c9abe",
            summary["provenance"]["source_head"],
        )
        self.assertEqual(
            canonical_json_sha256(golden),
            summary["provenance"]["golden"]["sha256"],
        )
        for relative, digest in summary["provenance"]["rubric"]["files"].items():
            self.assertEqual(normalized_text_sha256(ROOT / relative), digest)
        integrity = summary["provenance"]["integrity_statement"]
        for word in ("edited", "filtered", "discarded", "substituted", "averaged"):
            self.assertIn(word, integrity)

        self.assertIn("hash_algorithms", summary["provenance"])
        algorithms = summary["provenance"]["hash_algorithms"]
        self.assertEqual(
            "original blind scorer JSON file bytes",
            algorithms["source_raw_sha256"]["input"],
        )
        self.assertFalse(
            algorithms["source_raw_sha256"]["reproducible_from_tracked_records"]
        )
        self.assertEqual(
            {
                "ensure_ascii": False,
                "sort_keys": True,
                "separators": [",", ":"],
                "trailing_newline": False,
            },
            algorithms["canonical_records_sha256"]["serialization"],
        )
        self.assertEqual("UTF-8", algorithms["canonical_records_sha256"]["encoding"])
        self.assertEqual("preserved", algorithms["canonical_records_sha256"]["array_order"])
        raw_hashes = []
        for run in range(1, 4):
            for chunk in range(1, 11):
                evidence = summary["chunk_hashes"][f"pass-{run}"][f"chunk-{chunk:02d}"]
                self.assertEqual(
                    {
                        "source_file",
                        "source_raw_sha256",
                        "canonical_records_sha256",
                        "records",
                    },
                    set(evidence),
                )
                self.assertEqual(
                    f"pass-{run}-chunk-{chunk:02d}.json",
                    evidence["source_file"],
                )
                self.assertRegex(evidence["source_raw_sha256"], r"^[0-9a-f]{64}$")
                raw_hashes.append(evidence["source_raw_sha256"])
                records = pass_records[run][(chunk - 1) * 5 : chunk * 5]
                self.assertEqual(5, evidence["records"])
                self.assertEqual(
                    canonical_json_sha256(records),
                    evidence["canonical_records_sha256"],
                )

        self.assertEqual(30, len(raw_hashes))
        self.assertEqual(30, len(set(raw_hashes)))
        for run in range(1, 4):
            evidence = summary["assembled_hashes"][f"pass-{run}"]
            self.assertEqual(50, evidence["records"])
            self.assertEqual(canonical_json_sha256(pass_records[run]), evidence["sha256"])
        self.assertEqual(150, summary["assembled_hashes"]["all-runs"]["records"])
        self.assertEqual(
            canonical_json_sha256(all_runs),
            summary["assembled_hashes"]["all-runs"]["sha256"],
        )
        self.assertEqual(0, summary["evaluator"]["exit_code"])
        self.assertEqual(
            {"max_total_deviation": 0.7, "max_dimension_deviation": 1.0},
            summary["evaluator"]["thresholds"],
        )
        self.assertEqual(metrics, summary["evaluator"]["result"])

    def test_protected_content_cases_cover_all_types(self):
        cases = json.loads((ROOT / "tests" / "golden" / "protected.json").read_text(encoding="utf-8"))
        self.assertEqual({"code", "command", "foreign", "quote", "url"}, {case["type"] for case in cases})
        for case in cases:
            self.assertIn(case["protected"], case["input"])

    def test_score_skill_requires_independent_dimension_evidence(self):
        skill = (ROOT / "skills" / "hy-score" / "SKILL.md").read_text(encoding="utf-8")
        for fragment in ("50 բառից կարճ", "9.0", "10.0", "separate observable effect"):
            self.assertIn(fragment, skill)
        self.assertIn("One issue does not automatically lower every dimension", skill)
        self.assertIn("exclude the complete span from deductions", skill)

    def test_grammar_008_golden_cases_preserve_every_protected_class(self):
        cases = json.loads(
            (ROOT / "tests" / "golden" / "hy-grm-008-protected.json").read_text(
                encoding="utf-8"
            )
        )
        self.assertEqual(
            {
                "code",
                "command",
                "url",
                "email",
                "identifier",
                "filename",
                "foreign-quotation",
                "protected-official-spelling",
            },
            {case["type"] for case in cases},
        )
        for case in cases:
            with self.subTest(case=case["id"]):
                self.assertEqual(case["input"], case["expected"])
                self.assertIn("Apricodeում", case["protected"])
                self.assertIn(case["protected"], case["input"])
                self.assertEqual([], case["expected_findings"])

    def test_ci_covers_three_operating_systems(self):
        workflow = (ROOT / ".github" / "workflows" / "validate.yml").read_text(encoding="utf-8")
        for runner in ("windows-latest", "macos-latest", "ubuntu-latest"):
            self.assertIn(runner, workflow)


if __name__ == "__main__":
    unittest.main()
