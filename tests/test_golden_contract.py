import json
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class GoldenContractTest(unittest.TestCase):
    def test_scoring_set_has_fifty_reviewable_cases(self):
        cases = json.loads((ROOT / "tests" / "golden" / "scoring.json").read_text(encoding="utf-8"))
        self.assertEqual(50, len(cases))
        self.assertEqual({"article", "business", "marketing", "mixed", "ux"}, {case["domain"] for case in cases})
        for case in cases:
            self.assertEqual({"typography", "language", "grammar", "structure", "reader"}, set(case["scores"]))
            self.assertFalse(case["reviewed"], "draft fixtures must not impersonate Arman's review")

    def test_protected_content_cases_cover_all_types(self):
        cases = json.loads((ROOT / "tests" / "golden" / "protected.json").read_text(encoding="utf-8"))
        self.assertEqual({"code", "command", "foreign", "quote", "url"}, {case["type"] for case in cases})
        for case in cases:
            self.assertIn(case["protected"], case["input"])

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
