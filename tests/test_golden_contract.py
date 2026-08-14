import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


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
            self.assertEqual(
                {"id", "domain", "text", "expected_text", "expected_rules", "protected_spans"},
                set(case),
            )
            self.assertTrue(case["text"].strip())
            self.assertTrue(case["expected_text"].strip())
            for span in case["protected_spans"]:
                self.assertIn(span["text"], case["text"])
                self.assertIn(span["text"], case["expected_text"])

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
