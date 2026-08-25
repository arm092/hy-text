import hashlib
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
                "reviewed_commit": "37898b95568fc90547de9206ab39323ba46d1588",
                "reviewed_at": "2026-08-25",
                "through_rule": "HY-TYP-008",
                "approved_sha256": "ab8b944c4b729abf857adb044f31f5d58f004534282951697d07bf3b3480eaa8",
            },
            "editorial-punctuation.md": {
                "reviewed_commit": "37898b95568fc90547de9206ab39323ba46d1588",
                "reviewed_at": "2026-08-25",
                "through_rule": "HY-PUN-008",
                "approved_sha256": "a6937e438fcbfa59495c9060182b5639488b670ccff80772a92acd56a47f7e0d",
            },
            "editorial-grammar.md": {
                "reviewed_commit": "3771480a6fc7d1106462d8e8aaeacc1e9ad1de64",
                "reviewed_at": "2026-08-14",
                "through_rule": "HY-GRM-008",
                "approved_sha256": "6e31c918451db59cb791a692336e3f3e528c6575c509f63777712dfa15dcfef5",
            },
            "info-style.md": {
                "reviewed_commit": "37898b95568fc90547de9206ab39323ba46d1588",
                "reviewed_at": "2026-08-25",
                "through_rule": "HY-INF-007",
                "approved_sha256": "dd33215830be85aa00b468eb1efa334e243aa0e9fa303270d8c16ad63de18b1c",
            },
            "ux-writing.md": {
                "reviewed_commit": "324841d3b731f0c10149af0fa4377ae723fbb257",
                "reviewed_at": "2026-08-14",
                "through_rule": "HY-UX-010",
                "approved_sha256": "ab7e6d5d75e8402493157efe4cb9c149748c1ad697a164c31a09bb6d2865cb6b",
            },
            "business-writing.md": {
                "reviewed_commit": "f20b16cc6acc64db10ded5f630a1e707b3c50787",
                "reviewed_at": "2026-08-14",
                "through_rule": "HY-BIZ-007",
                "approved_sha256": "fe0f32ac4490e914a59d1a15975bfcd214f02cba487549d19cfec0cb0be0d7d9",
            },
            "anti-patterns.md": {
                "reviewed_commit": "ee481dd2c9c4313deeb14a50993025a2abdc517e",
                "reviewed_at": "2026-08-14",
                "through_rule": "HY-ANT-005",
                "approved_sha256": "8fc8034d2b423467e9f1dc5aac294afac6ce94d10cfd25dd832476204e419356",
            },
            "addenda.md": {
                "reviewed_commit": "ee481dd2c9c4313deeb14a50993025a2abdc517e",
                "reviewed_at": "2026-08-14",
                "through_rule": "HY-ADD-006",
                "approved_sha256": "9b746d065230f92dd9548055778d58cd5ca2e6bfaf16bad516251ccceb53d2a7",
            },
            "scoring.md": {
                "reviewed_commit": "37898b95568fc90547de9206ab39323ba46d1588",
                "reviewed_at": "2026-08-25",
                "through_rule": None,
                "approved_sha256": "84fdcb49b712fc800e0245e3b8ceec45ec3513a8cb9cb94cd29cf8d954f0ff93",
            },
            "sources.md": {
                "reviewed_commit": "37898b95568fc90547de9206ab39323ba46d1588",
                "reviewed_at": "2026-08-25",
                "through_rule": None,
                "approved_sha256": "1bfac7a1a4d16d771a930fa7bb57b6fc35a0a31ec936d4a9da548bc2428a34ca",
            },
        }
        self.assertEqual(set(expected_reviews), set(by_name))
        for row in rows:
            self.assertEqual("Arman Khachatryan", row["reviewer"])
            self.assertEqual("approved", row["status"])
            reference_path = ROOT / "skills" / "hy-text" / "references" / row["reference"]
            current_sha256 = hashlib.sha256(reference_path.read_bytes()).hexdigest()
            self.assertEqual(current_sha256, row.get("approved_sha256"))
        self.assertEqual(
            expected_reviews,
            {
                reference: {
                    "reviewed_commit": row["reviewed_commit"],
                    "reviewed_at": row["reviewed_at"],
                    "through_rule": row["through_rule"],
                    "approved_sha256": row["approved_sha256"],
                }
                for reference, row in by_name.items()
            },
        )
