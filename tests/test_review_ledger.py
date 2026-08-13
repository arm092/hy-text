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
        expected_reviews = {
            "typography.md": {
                "reviewed_commit": "de16c32b402982048f5a20d225a9287c78b1e911",
                "reviewed_at": "2026-08-13",
                "through_rule": "HY-TYP-008",
            },
            "editorial-punctuation.md": {
                "reviewed_commit": "de16c32b402982048f5a20d225a9287c78b1e911",
                "reviewed_at": "2026-08-13",
                "through_rule": "HY-PUN-008",
            },
            "editorial-grammar.md": {
                "reviewed_commit": "3771480a6fc7d1106462d8e8aaeacc1e9ad1de64",
                "reviewed_at": "2026-08-14",
                "through_rule": "HY-GRM-008",
            },
        }
        for row in rows:
            self.assertEqual("Arman Khachatryan", row["reviewer"])
            self.assertEqual("approved", row["status"])
        self.assertEqual(
            expected_reviews,
            {
                reference: {
                    "reviewed_commit": row["reviewed_commit"],
                    "reviewed_at": row["reviewed_at"],
                    "through_rule": row["through_rule"],
                }
                for reference, row in by_name.items()
            },
        )
