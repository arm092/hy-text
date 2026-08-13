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

    def test_candidate_ids_are_stable_and_match_their_reference(self):
        expected_by_reference = {
            "info-style.md": {
                "CAND-INF-001",
                "CAND-INF-002",
                "CAND-INF-003",
                "CAND-INF-004",
                "CAND-INF-005",
                "CAND-INF-006",
            },
            "ux-writing.md": {
                "CAND-UX-001",
                "CAND-UX-002",
                "CAND-UX-003",
                "CAND-UX-004",
                "CAND-UX-005",
                "CAND-UX-006",
            },
            "business-writing.md": {
                "CAND-BIZ-001",
                "CAND-BIZ-002",
                "CAND-BIZ-003",
                "CAND-BIZ-004",
                "CAND-BIZ-005",
                "CAND-BIZ-006",
            },
        }
        expected_ids = set().union(*expected_by_reference.values())
        actual_ids = {row["candidate_id"] for row in self.rows}

        self.assertEqual(expected_ids, actual_ids)
        for reference, expected_reference_ids in expected_by_reference.items():
            with self.subTest(reference=reference):
                self.assertEqual(
                    expected_reference_ids,
                    {
                        row["candidate_id"]
                        for row in self.rows
                        if row["reference"] == reference
                    },
                )

    def test_source_ready_candidates_use_exact_scope_compatible_sources(self):
        expected_source_ids = {
            "CAND-INF-001": ["SRC-LC-QUOTES", "SRC-LC-FOREIGN-INFLECTION"],
            "CAND-INF-002": ["SRC-LC-QUESTION"],
            "CAND-INF-003": ["SRC-LC-QUESTION"],
            "CAND-INF-004": ["SRC-LC-ELLIPSIS"],
            "CAND-INF-005": ["SRC-LC-STRESS"],
            "CAND-INF-006": ["SRC-UNICODE-ARMENIAN"],
        }
        actual_source_ids = {
            row["candidate_id"]: row["source_ids"]
            for row in self.rows
            if row["status"] == "source-ready"
        }
        self.assertEqual(expected_source_ids, actual_source_ids)

        source_records = json.loads(
            (ROOT / "research" / "source-audit.json").read_text(encoding="utf-8")
        )
        verified_ids = {
            record["id"] for record in source_records if record["status"] == "verified"
        }

        for candidate_id, source_ids in actual_source_ids.items():
            with self.subTest(candidate_id=candidate_id):
                self.assertLessEqual(set(source_ids), verified_ids)

        for row in self.rows:
            if row["status"] != "source-ready":
                self.assertEqual([], row["source_ids"])


if __name__ == "__main__":
    unittest.main()
