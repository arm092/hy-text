import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class ReviewLedgerTest(unittest.TestCase):
    def test_all_ten_references_are_approved_at_immutable_commits(self):
        rows = json.loads((ROOT / "research" / "reviews.json").read_text(encoding="utf-8"))
        by_name = {row["reference"]: row for row in rows}
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
            "info-style.md": {
                "reviewed_commit": "ee481dd2c9c4313deeb14a50993025a2abdc517e",
                "reviewed_at": "2026-08-14",
                "through_rule": "HY-INF-007",
            },
            "ux-writing.md": {
                "reviewed_commit": "324841d3b731f0c10149af0fa4377ae723fbb257",
                "reviewed_at": "2026-08-14",
                "through_rule": "HY-UX-010",
            },
            "business-writing.md": {
                "reviewed_commit": "f20b16cc6acc64db10ded5f630a1e707b3c50787",
                "reviewed_at": "2026-08-14",
                "through_rule": "HY-BIZ-007",
            },
            "anti-patterns.md": {
                "reviewed_commit": "ee481dd2c9c4313deeb14a50993025a2abdc517e",
                "reviewed_at": "2026-08-14",
                "through_rule": "HY-ANT-005",
            },
            "addenda.md": {
                "reviewed_commit": "ee481dd2c9c4313deeb14a50993025a2abdc517e",
                "reviewed_at": "2026-08-14",
                "through_rule": "HY-ADD-006",
            },
            "scoring.md": {
                "reviewed_commit": "ee481dd2c9c4313deeb14a50993025a2abdc517e",
                "reviewed_at": "2026-08-14",
                "through_rule": None,
            },
            "sources.md": {
                "reviewed_commit": "ee481dd2c9c4313deeb14a50993025a2abdc517e",
                "reviewed_at": "2026-08-14",
                "through_rule": None,
            },
        }
        self.assertEqual(set(expected_reviews), set(by_name))
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
