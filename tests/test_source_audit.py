import json
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

class SourceAuditTest(unittest.TestCase):
    def test_audit_records_are_resolvable_and_non_placeholder(self):
        records = json.loads((ROOT / "research" / "source-audit.json").read_text(encoding="utf-8"))
        ids = [record["id"] for record in records]
        self.assertEqual(len(ids), len(set(ids)))
        for record in records:
            self.assertIn(record["evidence_type"], {"official norm", "academic source", "technical standard"})
            self.assertIn(record["status"], {"verified", "limited", "rejected"})
            self.assertTrue(record["locator"].startswith(("https://", "ISBN ")))
            self.assertNotIn("համալրման փուլ", record["locator"])
