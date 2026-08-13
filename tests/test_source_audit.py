import json
import re
import unittest
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REFERENCES = ROOT / "skills" / "hy-text" / "references"
REQUIRED_FIELDS = {
    "id",
    "evidence_type",
    "authority",
    "title",
    "locator",
    "scope",
    "accessed_at",
    "status",
    "availability",
    "provenance",
}
EVIDENCE_TYPES = {"official norm", "academic source", "technical standard"}
STATUSES = {"verified", "limited", "rejected"}
AVAILABILITY = {"direct", "legacy host unavailable", "bibliographic only"}
BASIS_TYPES = {"պաշտոնական նորմ", "ժամանակակից գործածություն", "խմբագրական որոշում"}
SCOPE_LIMITERS = (" not ", " only", " until ", " cannot ", "specific", "concrete")


def audit_records():
    return json.loads((ROOT / "research" / "source-audit.json").read_text(encoding="utf-8"))


def rule_chunk(path, rule_id):
    text = path.read_text(encoding="utf-8")
    return re.search(rf"^## {rule_id}$.*?(?=^## HY-|\Z)", text, re.MULTILINE | re.DOTALL).group()


class SourceAuditTest(unittest.TestCase):
    def test_audit_records_have_complete_narrow_evidence_metadata(self):
        records = audit_records()
        ids = [record["id"] for record in records]
        self.assertEqual(len(ids), len(set(ids)))
        for record in records:
            self.assertTrue(REQUIRED_FIELDS.issubset(record), record["id"])
            self.assertIn(record["evidence_type"], EVIDENCE_TYPES)
            self.assertIn(record["status"], STATUSES)
            self.assertIn(record["availability"], AVAILABILITY)
            self.assertTrue(record["locator"].startswith(("https://", "ISBN ")))
            self.assertNotIn("համալրման փուլ", record["locator"])
            self.assertTrue(record["authority"].strip())
            self.assertTrue(record["title"].strip())
            self.assertGreaterEqual(len(record["scope"].split()), 10)
            self.assertTrue(
                any(limiter in record["scope"].lower() for limiter in SCOPE_LIMITERS),
                f"{record['id']} has no explicit scope limiter",
            )
            self.assertTrue(record["provenance"].strip())
            self.assertEqual(record["accessed_at"], date.fromisoformat(record["accessed_at"]).isoformat())

    def test_audit_records_are_synchronized_with_markdown_registry(self):
        registry = (REFERENCES / "sources.md").read_text(encoding="utf-8")
        rows = {
            columns[1].strip(): line
            for line in registry.splitlines()
            if line.startswith("| SRC-")
            for columns in (line.split("|"),)
        }
        for record in audit_records():
            self.assertIn(record["id"], rows)
            for field in ("id", "evidence_type", "status", "authority", "title", "locator", "scope", "availability", "provenance"):
                self.assertIn(record[field], rows[record["id"]], f"{record['id']} missing {field} from sources.md")

    def test_rejected_sources_are_absent_from_active_rules(self):
        active_rules = "\n".join(
            path.read_text(encoding="utf-8")
            for path in REFERENCES.glob("*.md")
            if path.name not in {"scoring.md", "sources.md"}
        )
        for record in audit_records():
            if record["status"] == "rejected":
                self.assertNotIn(record["id"], active_rules)

    def test_active_basis_labels_use_the_three_way_taxonomy(self):
        for path in REFERENCES.glob("*.md"):
            if path.name in {"scoring.md", "sources.md"}:
                continue
            for line in path.read_text(encoding="utf-8").splitlines():
                if line.startswith("**Հիմք։**"):
                    label = line.removeprefix("**Հիմք։** ").partition(" – ")[0]
                    self.assertIn(label, BASIS_TYPES, f"{path.name}: {line}")

    def test_editorial_only_rules_do_not_claim_external_authority(self):
        grammar = REFERENCES / "editorial-grammar.md"
        typography = REFERENCES / "typography.md"
        expected_basis = "**Հիմք։** խմբագրական որոշում – SRC-EDITORIAL-POLICY։"
        self.assertIn(expected_basis, rule_chunk(grammar, "HY-GRM-002"))
        self.assertIn(expected_basis, rule_chunk(typography, "HY-TYP-005"))
        self.assertIn(expected_basis, rule_chunk(typography, "HY-TYP-007"))
