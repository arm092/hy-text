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

    def test_global_rank_status_reference_and_evidence_are_exact(self):
        expected = [
            ("CAND-INF-001", "info-style.md", "insufficient", []),
            ("CAND-INF-002", "info-style.md", "insufficient", []),
            ("CAND-INF-003", "info-style.md", "insufficient", []),
            ("CAND-INF-004", "info-style.md", "insufficient", []),
            ("CAND-INF-005", "info-style.md", "insufficient", []),
            ("CAND-INF-006", "info-style.md", "insufficient", []),
            ("CAND-UX-001", "ux-writing.md", "usage-study-required", []),
            ("CAND-UX-002", "ux-writing.md", "usage-study-required", []),
            ("CAND-UX-003", "ux-writing.md", "usage-study-required", []),
            ("CAND-UX-004", "ux-writing.md", "usage-study-required", []),
            ("CAND-UX-005", "ux-writing.md", "insufficient", []),
            ("CAND-UX-006", "ux-writing.md", "insufficient", []),
            ("CAND-BIZ-001", "business-writing.md", "insufficient", []),
            ("CAND-BIZ-002", "business-writing.md", "usage-study-required", []),
            ("CAND-BIZ-003", "business-writing.md", "usage-study-required", []),
            ("CAND-BIZ-004", "business-writing.md", "usage-study-required", []),
            ("CAND-BIZ-005", "business-writing.md", "insufficient", []),
            ("CAND-BIZ-006", "business-writing.md", "usage-study-required", []),
        ]
        actual = [
            (
                row["candidate_id"],
                row["reference"],
                row["status"],
                row["source_ids"],
            )
            for row in self.rows
        ]
        self.assertEqual(expected, actual)

    def test_information_candidates_are_information_style_research_questions(self):
        expected_topics = (
            "decision or required action",
            "verifiable fact, measure, or example",
            "naming the verified actor",
            "simple finite verbs",
            "one main idea per paragraph",
            "descriptive Armenian link labels",
        )
        information_rows = self.rows[:6]
        self.assertEqual(
            [f"CAND-INF-{index:03d}" for index in range(1, 7)],
            [row["candidate_id"] for row in information_rows],
        )
        for row, topic in zip(information_rows, expected_topics):
            with self.subTest(candidate=row["candidate_id"]):
                self.assertIn(topic, row["question"])
                self.assertIn("frequency", row["required_evidence"].lower())
                self.assertEqual("insufficient", row["status"])
                self.assertEqual([], row["source_ids"])

    def test_causal_questions_cannot_be_promoted_by_frequency(self):
        causal_ids = {
            "CAND-INF-001",
            "CAND-INF-002",
            "CAND-INF-003",
            "CAND-INF-004",
            "CAND-INF-005",
            "CAND-INF-006",
            "CAND-UX-005",
            "CAND-UX-006",
            "CAND-BIZ-005",
        }
        by_id = {row["candidate_id"]: row for row in self.rows}
        self.assertEqual(
            {candidate_id: "insufficient" for candidate_id in causal_ids},
            {candidate_id: by_id[candidate_id]["status"] for candidate_id in causal_ids},
        )

        readme = (ROOT / "research" / "README.md").read_text(encoding="utf-8")
        self.assertIn("stable global rank", readme)
        self.assertIn("cannot be promoted by a frequency aggregate", readme)


if __name__ == "__main__":
    unittest.main()
