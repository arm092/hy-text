import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReviewLedgerTest(unittest.TestCase):
    def test_three_references_are_approved_at_an_immutable_commit(self):
        rows = json.loads((ROOT / "research" / "reviews.json").read_text(encoding="utf-8"))
        by_name = {row["reference"]: row for row in rows}
        self.assertEqual(
            {"typography.md", "editorial-punctuation.md", "editorial-grammar.md"},
            set(by_name),
        )
        expected_boundaries = {
            "typography.md": "HY-TYP-008",
            "editorial-punctuation.md": "HY-PUN-008",
            "editorial-grammar.md": "HY-GRM-007",
        }
        for row in rows:
            self.assertEqual("Arman Khachatryan", row["reviewer"])
            self.assertEqual("2026-08-13", row["reviewed_at"])
            self.assertEqual("approved", row["status"])
            self.assertEqual("de16c32b402982048f5a20d225a9287c78b1e911", row["reviewed_commit"])
        self.assertEqual(
            expected_boundaries,
            {reference: row["through_rule"] for reference, row in by_name.items()},
        )
