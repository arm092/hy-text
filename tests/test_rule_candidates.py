import json
import unittest
from collections import Counter
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]


class RuleCandidatesTest(unittest.TestCase):
    def setUp(self):
        self.rows = json.loads(
            (ROOT / "research" / "rule-candidates.json").read_text(encoding="utf-8")
        )

    def test_candidate_queue_contains_six_questions_per_reference(self):
        self.assertEqual(18, len(self.rows))
        self.assertEqual(
            {
                "info-style.md": 6,
                "ux-writing.md": 6,
                "business-writing.md": 6,
            },
            Counter(row["reference"] for row in self.rows),
        )

        required_fields = {
            "candidate_id",
            "reference",
            "question",
            "required_evidence",
            "source_ids",
            "status",
            "reason",
        }
        for row in self.rows:
            self.assertEqual(required_fields, set(row))
            self.assertTrue(row["candidate_id"])
            self.assertTrue(row["question"])
            self.assertTrue(row["required_evidence"])
            self.assertIn(
                row["status"],
                {"source-ready", "usage-study-required", "insufficient"},
            )
            self.assertTrue(row["reason"])

        candidate_ids = [row["candidate_id"] for row in self.rows]
        self.assertEqual(len(candidate_ids), len(set(candidate_ids)))

    def test_source_ready_candidates_use_only_verified_audited_sources(self):
        source_records = json.loads(
            (ROOT / "research" / "source-audit.json").read_text(encoding="utf-8")
        )
        verified_ids = {
            record["id"] for record in source_records if record["status"] == "verified"
        }

        for row in self.rows:
            if row["status"] == "source-ready":
                self.assertTrue(row["source_ids"])
                self.assertLessEqual(set(row["source_ids"]), verified_ids)
            else:
                self.assertEqual([], row["source_ids"])


if __name__ == "__main__":
    unittest.main()
