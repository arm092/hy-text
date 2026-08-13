import json
import re
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
        for row in rows:
            self.assertEqual("Arman Khachatryan", row["reviewer"])
            self.assertEqual("2026-08-13", row["reviewed_at"])
            self.assertEqual("approved", row["status"])
            self.assertRegex(row["reviewed_commit"], re.compile(r"^[0-9a-f]{40}$"))
        self.assertEqual("HY-GRM-007", by_name["editorial-grammar.md"]["through_rule"])
