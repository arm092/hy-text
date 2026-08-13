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
REGISTRY_COLUMNS = {
    "ID": "id",
    "Evidence type": "evidence_type",
    "Status": "status",
    "Authority": "authority",
    "Title and locator": None,
    "Scope": "scope",
    "Availability": "availability",
    "Provenance": "provenance",
}


def audit_records():
    return json.loads((ROOT / "research" / "source-audit.json").read_text(encoding="utf-8"))


def rule_chunk(path, rule_id):
    text = path.read_text(encoding="utf-8")
    return re.search(rf"^## {rule_id}$.*?(?=^## HY-|\Z)", text, re.MULTILINE | re.DOTALL).group()


def markdown_cells(line):
    return [cell.strip() for cell in line.strip().strip("|").split("|")]


def registry_records():
    lines = (REFERENCES / "sources.md").read_text(encoding="utf-8").splitlines()
    expected_headers = list(REGISTRY_COLUMNS)
    header_index = next(
        index
        for index, line in enumerate(lines)
        if line.startswith("| ID |") and markdown_cells(line) == expected_headers
    )
    headers = markdown_cells(lines[header_index])
    records = {}
    for line in lines[header_index + 2 :]:
        if not line.startswith("| SRC-"):
            break
        cells = markdown_cells(line)
        if len(cells) != len(headers):
            raise ValueError(f"registry row has {len(cells)} cells, expected {len(headers)}: {line}")
        columns = dict(zip(headers, cells))
        title_prefix, separator, locator_suffix = columns["Title and locator"].rpartition("](")
        if not separator or not title_prefix.startswith("[") or not locator_suffix.endswith(")"):
            raise ValueError(f"invalid title and locator cell: {columns['Title and locator']}")
        record = {
            field: columns[header]
            for header, field in REGISTRY_COLUMNS.items()
            if field is not None
        }
        record["title"] = title_prefix[1:]
        record["locator"] = locator_suffix[:-1]
        if record["id"] in records:
            raise ValueError(f"duplicate registry ID: {record['id']}")
        records[record["id"]] = record
    return records


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
        fields = ("id", "evidence_type", "status", "availability", "authority", "title", "locator", "scope", "provenance")
        expected = {
            record["id"]: {field: record[field] for field in fields}
            for record in audit_records()
        }
        actual = registry_records()
        self.assertEqual(set(expected), set(actual))
        for source_id, expected_record in expected.items():
            for field, expected_value in expected_record.items():
                with self.subTest(source_id=source_id, field=field):
                    self.assertEqual(expected_value, actual[source_id][field])

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

    def test_bipm_source_supports_only_regulated_si_spacing(self):
        by_id = {record["id"]: record for record in audit_records()}
        source = by_id["SRC-BIPM-SI-BROCHURE"]
        self.assertEqual("technical standard", source["evidence_type"])
        self.assertEqual("verified", source["status"])
        self.assertEqual("Bureau International des Poids et Mesures (BIPM)", source["authority"])
        self.assertEqual(
            "The International System of Units (SI), 9th edition, Version 4.01",
            source["title"],
        )
        self.assertEqual(
            "https://www.bipm.org/documents/d/guest/si-brochure-9-en-pdf",
            source["locator"],
        )
        for fragment in ("Section 5.4.3", "including °C", "°", "′", "″", "not support for compact Armenian"):
            self.assertIn(fragment, source["scope"])
