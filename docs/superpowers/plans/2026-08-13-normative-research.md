# Normative Research Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Build a verifiable Armenian normative-research layer, record Arman's completed reviews, and add an evidence-backed rule for Armenian endings attached to foreign-script names.

**Architecture:** Structured JSON files hold immutable review decisions, source-audit records, observations, and derived usage aggregates. Standard-library Python validators enforce the evidence thresholds and connect rules to registered sources. Human-readable Markdown explains evidence and decisions without copying source corpora.

**Tech Stack:** Markdown, JSON, Python 3.12 standard library, `unittest`, GitHub Actions on Windows, macOS, and Linux.

## Global Constraints

- Support only modern Eastern Armenian and reformed orthography used in the Republic of Armenia.
- Exclude Western Armenian and traditional orthography.
- Do not store copied corpora, private text, or personal data.
- A disputed usage aggregate requires at least 100 relevant uses, 20 independent domains, and three corpus layers.
- Mark each basis as official norm, modern usage, or editorial decision.
- Preserve code, commands, URLs, email addresses, identifiers, file names, foreign quotations, and protected official spellings.
- Use stable rule IDs and retain `HY-GRM-008` for foreign-script inflection.
- Use only Python's standard library in repository checks.
- Keep `master` as the primary branch and never create a branch whose name starts with `codex`.
- Do not create a tag or release before all `v1.0.0` gates pass.

---

### Task 1: Immutable review ledger

**Files:**
- Create: `research/reviews.json`
- Create: `tests/test_review_ledger.py`
- Modify: `METHODOLOGY.md`

**Interfaces:**
- Consumes: Git commit `de16c32b402982048f5a20d225a9287c78b1e911`, which contains the reviewed rule text.
- Produces: a JSON array whose records contain `reference`, `reviewed_commit`, `reviewer`, `reviewed_at`, `status`, and `through_rule`.

- [ ] **Step 1: Write the failing ledger contract test**

```python
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
```

- [ ] **Step 2: Run the ledger test and verify the missing-file failure**

Run: `python -m unittest tests.test_review_ledger -v`

Expected: FAIL because `research/reviews.json` does not exist.

- [ ] **Step 3: Add the three approved records**

Use commit `de16c32b402982048f5a20d225a9287c78b1e911` for all three records. Set `through_rule` to `HY-TYP-008`, `HY-PUN-008`, and `HY-GRM-007`, respectively.

- [ ] **Step 4: Document review invalidation**

Add to `METHODOLOGY.md`: approval applies to the recorded commit and rule boundary; a materially changed prescription or a later rule returns only the affected material to `pending`.

- [ ] **Step 5: Run the focused and full tests**

Run: `python -m unittest tests.test_review_ledger -v`

Expected: PASS.

Run: `python -m unittest discover -s tests -v`

Expected: all tests PASS.

- [ ] **Step 6: Commit**

```powershell
git add research/reviews.json tests/test_review_ledger.py METHODOLOGY.md
git commit -m "docs: record approved Armenian references"
```

### Task 2: Structured source audit

**Files:**
- Create: `research/source-audit.json`
- Create: `tests/test_source_audit.py`
- Modify: `skills/hy-text/references/sources.md`

**Interfaces:**
- Consumes: registered `SRC-*` identifiers from `sources.md`.
- Produces: audit records with `id`, `evidence_type`, `authority`, `title`, `locator`, `scope`, `accessed_at`, and `status`.

- [ ] **Step 1: Write the failing source-audit test**

```python
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
```

- [ ] **Step 2: Run the test and verify the missing-file failure**

Run: `python -m unittest tests.test_source_audit -v`

Expected: FAIL because `research/source-audit.json` does not exist.

- [ ] **Step 3: Audit authoritative sources**

Record the Language Committee pages already cited by the corpus, the Unicode Armenian chapter, CLDR Armenian punctuation data, and any normative dictionary or academic publication whose bibliographic identity can be verified. Give every record a narrow `scope`; do not treat the whole publication as support for unrelated rules.

- [ ] **Step 4: Remove placeholder authority from active rules**

Replace `SRC-NORMATIVE-GRAMMAR` as a placeholder with individually identifiable sources. If a current rule lacks a verified source, change its basis to `editorial decision` and cite `SRC-EDITORIAL-POLICY`; do not fabricate a normative citation.

- [ ] **Step 5: Synchronize the human-readable registry**

Add or revise the corresponding `sources.md` rows so each verified source ID has the same title, locator, evidence type, and scope as the structured audit.

- [ ] **Step 6: Run tests and validator**

Run: `python -m unittest tests.test_source_audit -v`

Expected: PASS.

Run: `python tools/validate.py`

Expected: `hy-text validation passed`.

- [ ] **Step 7: Commit**

```powershell
git add research/source-audit.json tests/test_source_audit.py skills/hy-text/references/sources.md skills/hy-text/references/editorial-grammar.md
git commit -m "research: audit Armenian normative sources"
```

### Task 3: Validate observations and usage aggregates

**Files:**
- Create: `research/observation.schema.json`
- Create: `tools/aggregate_usage.py`
- Create: `tests/test_usage_research.py`
- Modify: `tools/validate.py`
- Modify: `research/README.md`

**Interfaces:**
- Consumes: newline-delimited JSON observations with `url`, `domain`, `layer`, `variant`, `observed_at`, and `example`.
- Produces: `build_aggregate(observations: list[dict], aggregate_id: str, query: str) -> dict` and validation errors from `validate_usage_aggregates(paths: list[Path]) -> list[str]`.

- [ ] **Step 1: Write failing tests for thresholds and aggregation**

```python
def test_aggregate_requires_one_hundred_uses_twenty_domains_and_three_layers(self):
    observations = make_observations(total=99, domains=20, layers=3)
    with self.assertRaises(ValueError):
        aggregate_usage.build_aggregate(observations, "USAGE-FOREIGN-SUFFIX", "mixed-script suffix")

def test_aggregate_counts_variants_without_storing_full_pages(self):
    observations = make_observations(total=100, domains=20, layers=3)
    result = aggregate_usage.build_aggregate(observations, "USAGE-FOREIGN-SUFFIX", "mixed-script suffix")
    self.assertEqual(100, result["total"])
    self.assertEqual(100, sum(result["variants"].values()))
    self.assertNotIn("page_text", result)
```

- [ ] **Step 2: Run the focused tests and verify import or missing-function failures**

Run: `python -m unittest tests.test_usage_research -v`

Expected: FAIL because `tools/aggregate_usage.py` or `build_aggregate` is missing.

- [ ] **Step 3: Implement the minimal standard-library aggregator**

Implement JSONL loading, URL-domain normalization with `urllib.parse`, duplicate URL rejection, a 240-character example limit, allowed layers, threshold checks, variant totals, and deterministic sorted output.

- [ ] **Step 4: Add repository validation for committed aggregates**

Implement `validate_usage_aggregates()` in `tools/validate.py`. It must reject totals below 100, fewer than 20 unique domains, fewer than three positive layers, totals inconsistent with variant counts, duplicate domains, malformed dates, and examples over 240 characters.

- [ ] **Step 5: Document the observation workflow**

Document that observations must be manually verified, public, relevant, non-duplicated, and stripped to a short example. State that automated search counts alone are inadmissible.

- [ ] **Step 6: Run focused and full verification**

Run: `python -m unittest tests.test_usage_research tests.test_validator -v`

Expected: PASS.

Run: `python -m unittest discover -s tests -v`

Expected: all tests PASS.

- [ ] **Step 7: Commit**

```powershell
git add research/observation.schema.json tools/aggregate_usage.py tests/test_usage_research.py tools/validate.py research/README.md
git commit -m "feat: validate Armenian usage research"
```

### Task 4: Research foreign-script inflection and character choice

**Files:**
- Create: `research/notes/foreign-script-inflection.md`
- Create when thresholds pass: `research/observations/foreign-script-inflection.jsonl`
- Create when thresholds pass: `research/aggregates/foreign-script-inflection.json`
- Modify: `research/source-audit.json`
- Modify: `skills/hy-text/references/sources.md`

**Interfaces:**
- Consumes: Language Committee guidance containing `«The New York Times»-ի`, Unicode definitions for U+002D and U+058A, and verified modern observations if the character choice remains disputed.
- Produces: a decision note that separately evaluates the grammatical construction and the separator code point.

- [ ] **Step 1: Capture authoritative evidence**

Record the exact page title, publisher, URL, access date, a short compliant excerpt or paraphrase, and the narrow proposition supported. Inspect the HTML or source representation to determine which code point the official example actually uses.

- [ ] **Step 2: Record Unicode semantics**

Document U+002D HYPHEN-MINUS and U+058A ARMENIAN HYPHEN, including their official Unicode names. Do not infer Armenian grammatical preference from character names alone.

- [ ] **Step 3: Decide whether usage sampling is necessary**

If authoritative Armenian guidance settles both construction and separator, explain why a modern-usage aggregate is unnecessary. If it settles only the construction, collect and manually verify at least 100 examples across 20 domains and three layers before making a modern-usage claim about the separator.

- [ ] **Step 4: Build the aggregate only from qualifying observations**

Run:

```powershell
python tools/aggregate_usage.py research/observations/foreign-script-inflection.jsonl research/aggregates/foreign-script-inflection.json --id USAGE-FOREIGN-SCRIPT-INFLECTION --query "foreign-script Armenian suffix separator"
```

Expected when thresholds pass: exit 0 and a schema-valid aggregate. If thresholds do not pass, retain the evidence note with status `insufficient` and do not create an aggregate or modern-usage claim.

- [ ] **Step 5: Register accepted sources**

Add `SRC-LC-FOREIGN-INFLECTION` for the construction and a separate source ID for the character policy. Label a compatibility choice as `editorial decision` when it is not an official norm.

- [ ] **Step 6: Validate and commit the evidence**

Run: `python tools/validate.py`

Expected: `hy-text validation passed`.

Commit only verified evidence and qualifying observations:

```powershell
git add research/notes/foreign-script-inflection.md research/source-audit.json skills/hy-text/references/sources.md
if (Test-Path research/observations/foreign-script-inflection.jsonl) { git add research/observations/foreign-script-inflection.jsonl }
if (Test-Path research/aggregates/foreign-script-inflection.json) { git add research/aggregates/foreign-script-inflection.json }
git commit -m "research: document foreign-script inflection"
```

### Task 5: Add `HY-GRM-008` with contextual counterexamples

**Files:**
- Modify: `skills/hy-text/references/editorial-grammar.md`
- Modify: `tests/test_repository_contract.py`
- Modify: `CHANGELOG.md`

**Interfaces:**
- Consumes: the accepted construction and character decision from `research/notes/foreign-script-inflection.md`.
- Produces: stable rule `HY-GRM-008`, pending review after `HY-GRM-007`.

- [ ] **Step 1: Write the failing rule-contract test**

```python
def test_grammar_008_separates_foreign_script_from_armenian_ending(self):
    text = (ROOT / "skills" / "hy-text" / "references" / "editorial-grammar.md").read_text(encoding="utf-8")
    rule = text.split("## HY-GRM-008", 1)[1]
    self.assertIn("Apricode-ում", rule)
    self.assertIn("Apricodeում", rule)
    self.assertIn("Apricode ընկերությունում", rule)
    self.assertIn("SRC-LC-FOREIGN-INFLECTION", rule)
```

- [ ] **Step 2: Run the focused test and verify failure**

Run: `python -m unittest tests.test_repository_contract.RepositoryContractTest.test_grammar_008_separates_foreign_script_from_armenian_ending -v`

Expected: FAIL because `HY-GRM-008` is absent.

- [ ] **Step 3: Add the minimal rule**

The rule must state that a required Armenian case ending or article is separated from an unchanged foreign-script word or name by the evidence-selected separator. Include:

- correct: `Մենք աշխատում ենք Apricode-ում։`
- correct: `Apricode-ի թիմը պատասխանեց։`
- incorrect: `Մենք աշխատում ենք Apricodeում։`
- contextual counterexample: `Մենք ընտրեցինք Apricode։`
- alternative construction: `Մենք աշխատում ենք Apricode ընկերությունում։`
- exceptions for protected fragments and foreign quotations.

Set severity to `medium`. Cite the construction source and, when distinct, the character-policy source. Do not label modern usage unless a qualifying aggregate exists.

- [ ] **Step 4: Record the pending review boundary**

Add an Unreleased changelog entry. Do not alter the approved grammar ledger boundary `HY-GRM-007`; the new rule remains pending by construction.

- [ ] **Step 5: Run focused and complete verification**

Run: `python -m unittest tests.test_repository_contract.RepositoryContractTest.test_grammar_008_separates_foreign_script_from_armenian_ending -v`

Expected: PASS.

Run: `python -m unittest discover -s tests -v`

Expected: all tests PASS.

Run: `python tools/validate.py`

Expected: `hy-text validation passed`.

- [ ] **Step 6: Commit**

```powershell
git add skills/hy-text/references/editorial-grammar.md tests/test_repository_contract.py CHANGELOG.md
git commit -m "feat: add foreign-script inflection rule"
```

### Task 6: Rank the next evidence-backed rule candidates

**Files:**
- Create: `research/rule-candidates.json`
- Create: `tests/test_rule_candidates.py`
- Modify: `research/README.md`

**Interfaces:**
- Consumes: the audited source registry.
- Produces: candidate records with `candidate_id`, `reference`, `question`, `required_evidence`, `source_ids`, `status`, and `reason`.

- [ ] **Step 1: Write the failing candidate-queue test**

```python
def test_candidate_queue_contains_eighteen_research_questions(self):
    rows = json.loads((ROOT / "research" / "rule-candidates.json").read_text(encoding="utf-8"))
    self.assertEqual(18, len(rows))
    self.assertEqual({"info-style.md", "ux-writing.md", "business-writing.md"}, {row["reference"] for row in rows})
    for row in rows:
        self.assertIn(row["status"], {"source-ready", "usage-study-required", "insufficient"})
        self.assertTrue(row["reason"])
```

- [ ] **Step 2: Run the test and verify the missing-file failure**

Run: `python -m unittest tests.test_rule_candidates -v`

Expected: FAIL because `research/rule-candidates.json` does not exist.

- [ ] **Step 3: Add six candidates per reference**

Create six narrow research questions for information style, six for UX writing, and six for business writing. Every `source-ready` candidate must cite verified source IDs. Use `usage-study-required` where current digital practice must be sampled, and `insufficient` where neither authority nor a qualifying aggregate supports a prescription.

- [ ] **Step 4: Document promotion criteria**

Document that only `source-ready` candidates can proceed to rule drafting. A `usage-study-required` candidate becomes ready only after its aggregate passes validation. An `insufficient` candidate remains unpublished as a rule.

- [ ] **Step 5: Run tests and commit**

Run: `python -m unittest tests.test_rule_candidates -v`

Expected: PASS.

```powershell
git add research/rule-candidates.json tests/test_rule_candidates.py research/README.md
git commit -m "research: rank next Armenian rule candidates"
```

### Task 7: Final verification and publication

**Files:**
- Modify only if verification exposes a defect in an earlier task.

**Interfaces:**
- Consumes: all research, rule, test, and documentation changes.
- Produces: a clean synchronized `master` and a green three-OS CI run, without a release.

- [ ] **Step 1: Run all local gates**

```powershell
python -m unittest discover -s tests -v
python tools/validate.py
python C:\Users\Arman\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/hy-text
python C:\Users\Arman\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/hy-check
python C:\Users\Arman\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills/hy-score
python C:\Users\Arman\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py .
git diff --check
```

Expected: every command exits 0; tests report no failures; validators report success.

- [ ] **Step 2: Verify repository state**

```powershell
git status --short
git branch --show-current
git rev-list --left-right --count HEAD...origin/master
git tag --list
gh release list --repo arm092/hy-text
```

Expected before push: clean tree, branch `master`, no unexpected divergence, and no tag or release.

- [ ] **Step 3: Push `master`**

Run: `git push origin master`

Expected: push succeeds without force.

- [ ] **Step 4: Verify three-OS CI**

Run:

```powershell
$runs = gh run list --workflow validate.yml --limit 1 --json databaseId | ConvertFrom-Json
gh run view $runs[0].databaseId --json status,conclusion,jobs,url
```

Expected: Windows, macOS, and Linux jobs all conclude `success`.

- [ ] **Step 5: Hand off review**

Report the evidence decision, direct links to the research note and `HY-GRM-008`, exact test count, CI URL, and the fact that `HY-GRM-008` remains pending Arman's review. Do not create `v1.0.0`.
