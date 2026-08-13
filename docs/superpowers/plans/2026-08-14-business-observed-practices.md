# Armenian Business Correspondence Practices Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Complete four reproducible current-usage studies for `CAND-BIZ-002`, `CAND-BIZ-003`, `CAND-BIZ-004`, and `CAND-BIZ-006`, then prepare evidence-bounded rule proposals for Arman's approval.

**Architecture:** Each study has one JSONL observation file and one deterministic JSON aggregate paired by an ASCII kebab-case stem. A shared research note fixes eligibility, taxonomy, exclusions, and conclusions; the source registry links every aggregate. Normative rules remain unchanged until explicit approval.

**Tech Stack:** Markdown, JSONL, JSON, Python standard library, repository `tools/aggregate_usage.py` and `tools/validate.py`.

## Global Constraints

- Only modern Eastern Armenian and reformed orthography used in the Republic of Armenia are eligible.
- Each study requires at least 100 manually verified observations, 20 independent domains, and three corpus layers.
- Open every retained public source; search snippets and result counts are leads, not evidence.
- Exclude mirrors, duplicate or parameter-only URLs, spam, machine translation, invented examples, inaccessible private mail, and ordinary prose that does not expose the studied email element.
- Store only the public URL, conservative organizational domain, layer, predefined variant, date, and a verification example of at most 240 characters.
- Do not publish copied messages, personal data, addresses, entered values, or complete correspondence.
- Frequency supports only a current-practice recommendation. It cannot establish comprehension, politeness, trust, or task-success effects.
- Do not modify normative references before Arman's explicit approval of the resulting proposals.

---

### Task 1: Freeze the four-study protocol and regression contract

**Files:**
- Create: `research/notes/business-observed-practices.md`
- Modify: `tests/test_rule_candidates.py`
- Test: `tests/test_rule_candidates.py`

**Interfaces:**
- Consumes: the four `usage-study-required` business candidates in `research/rule-candidates.json`.
- Produces: exact study IDs `USAGE-BIZ-002`, `USAGE-BIZ-003`, `USAGE-BIZ-004`, and `USAGE-BIZ-006`, with fixed variant taxonomies.

- [ ] **Step 1: Add a failing contract test**

Assert that the research note contains all four study IDs, the 100/20/3 thresholds, eligibility boundaries, protected-data exclusions, and the exact variant families defined in Tasks 2 through 5.

- [ ] **Step 2: Run the focused test and verify RED**

Run: `python -m unittest tests.test_rule_candidates -v`

Expected: failure because `research/notes/business-observed-practices.md` does not exist.

- [ ] **Step 3: Write the protocol**

Document shared sampling rules and the four task-specific eligibility and taxonomy sections before collecting observations.

- [ ] **Step 4: Run the focused test and verify GREEN**

Run: `python -m unittest tests.test_rule_candidates -v`

Expected: all focused tests pass.

### Task 2: Study greeting punctuation and line breaks

**Files:**
- Create: `research/observations/biz-002.jsonl`
- Create: `research/aggregates/biz-002.json`
- Modify: `research/notes/business-observed-practices.md`

**Interfaces:**
- Consumes: public Armenian business-email messages, verbatim public email templates, and product-maintained correspondence examples.
- Produces: `USAGE-BIZ-002` with variants `<punctuation>/<layout>/<addressee>`, where punctuation is `comma`, `exclamation`, `none`, or `other`; layout is `same-line` or `new-line`; addressee is `person`, `role`, `organization`, or `collective`.

- [ ] **Step 1: Collect and manually verify 100 eligible observations**

Retain `Հարգելի`-based greetings only when the source explicitly presents an email or email template. Record the punctuation following the complete greeting and whether body text starts on the same or next visible line.

- [ ] **Step 2: Build the deterministic aggregate**

Run: `python tools/aggregate_usage.py research/observations/biz-002.jsonl research/aggregates/biz-002.json --id USAGE-BIZ-002 --query "Armenian business-email greeting punctuation and line breaks, segmented by addressee type"`

- [ ] **Step 3: Validate and summarize without causal claims**

Run: `python tools/validate.py`

Record distribution, layer concentration, exclusions, and whether any broadly distributed variant reaches the methodology threshold.

### Task 3: Study subject-line punctuation

**Files:**
- Create: `research/observations/biz-003.jsonl`
- Create: `research/aggregates/biz-003.json`
- Modify: `research/notes/business-observed-practices.md`

**Interfaces:**
- Consumes: publicly visible verbatim Armenian email subject lines and explicit Armenian email-subject templates.
- Produces: `USAGE-BIZ-003` with variants `none/phrase`, `none/statement`, `question-mark/question`, `terminal-mark/statement`, and `other`.

- [ ] **Step 1: Collect and manually verify 100 eligible observations**

Exclude article titles, web-form headings, notification titles, and prose suggestions that are not presented as a subject line. For questions, record the Armenian question mark even though it is placed inside the final word rather than at line end.

- [ ] **Step 2: Build the deterministic aggregate**

Run: `python tools/aggregate_usage.py research/observations/biz-003.jsonl research/aggregates/biz-003.json --id USAGE-BIZ-003 --query "Armenian business-email subject-line punctuation, segmented by phrase, statement, and question"`

- [ ] **Step 3: Validate and summarize without causal claims**

Run: `python tools/validate.py`

Record distribution, layer concentration, exclusions, and the separate result for full questions.

### Task 4: Study reply and forward prefixes

**Files:**
- Create: `research/observations/biz-004.jsonl`
- Create: `research/aggregates/biz-004.json`
- Modify: `research/notes/business-observed-practices.md`

**Interfaces:**
- Consumes: public Armenian email-client interfaces, public mailing-list or correspondence archives, and documentation showing an actual generated reply or forward subject.
- Produces: `USAGE-BIZ-004` with variants `re/reply`, `fwd/forward`, `fw/forward`, `localized/reply`, `localized/forward`, and `other`.

- [ ] **Step 1: Collect and manually verify 100 eligible observations**

Retain only prefixes shown as part of a reply or forward subject. Exclude prose merely mentioning `Re:` or `Fwd:`, duplicate thread copies, and non-email uses of `Re`.

- [ ] **Step 2: Build the deterministic aggregate**

Run: `python tools/aggregate_usage.py research/observations/biz-004.jsonl research/aggregates/biz-004.json --id USAGE-BIZ-004 --query "Reply and forward prefixes in Armenian email contexts, segmented by operation and prefix form"`

- [ ] **Step 3: Validate and summarize without causal claims**

Run: `python tools/validate.py`

Report reply and forward results separately and disclose client, archive, or layer concentration.

### Task 5: Study closing formulas by relationship context

**Files:**
- Create: `research/observations/biz-006.jsonl`
- Create: `research/aggregates/biz-006.json`
- Modify: `research/notes/business-observed-practices.md`

**Interfaces:**
- Consumes: public Armenian business email, verbatim public templates, and correspondence examples with an explicit relationship context.
- Produces: `USAGE-BIZ-006` with variants `<formula>/<relationship>`, where formula is `respectfully`, `best-wishes`, `thanks`, `sincerely`, `none`, or `other`; relationship is `formal`, `neutral`, or `established-colleague`.

- [ ] **Step 1: Collect and manually verify 100 eligible observations**

Retain the formula immediately preceding the sender signature. Exclude ordinary letters not identified as email, automatic legal footers, signatures without a closing formula, and examples whose relationship context cannot be classified.

- [ ] **Step 2: Build the deterministic aggregate**

Run: `python tools/aggregate_usage.py research/observations/biz-006.jsonl research/aggregates/biz-006.json --id USAGE-BIZ-006 --query "Armenian business-email closing formulas, segmented by relationship context"`

- [ ] **Step 3: Validate and summarize without causal claims**

Run: `python tools/validate.py`

Record distribution and recommend only context combinations supported by the sample.

### Task 6: Register evidence and prepare approval proposals

**Files:**
- Modify: `skills/hy-text/references/sources.md`
- Modify: `research/rule-candidates.json`
- Modify: `research/notes/business-observed-practices.md`
- Modify: `tests/test_rule_candidates.py`

**Interfaces:**
- Consumes: the four validated aggregates from Tasks 2 through 5.
- Produces: registered `USAGE-BIZ-*` sources, `source-ready` candidates only where the evidence gate is met, and four evidence-bounded decisions for Arman.

- [ ] **Step 1: Add failing registry and candidate-sync tests**

Assert exact source IDs, paths, candidate statuses, and source arrays. Require every proposed rule to state its sample limitations and avoid causal language.

- [ ] **Step 2: Run focused tests and verify RED**

Run: `python -m unittest tests.test_rule_candidates tests.test_usage_research -v`

- [ ] **Step 3: Register aggregates and write proposals**

Add the four rows to `sources.md`, update the candidate records, and write conclusions in the research note. Do not edit `business-writing.md`.

- [ ] **Step 4: Run focused tests and verify GREEN**

Run: `python -m unittest tests.test_rule_candidates tests.test_usage_research -v`

### Task 7: Complete verification and publish the research branch

**Files:**
- Modify only if a verification failure reveals an in-scope defect.

**Interfaces:**
- Consumes: all study artifacts and repository contracts.
- Produces: a clean pushed `research/business-observed-practices` branch; no merge, tag, release, or normative rule.

- [ ] **Step 1: Run all repository gates**

Run the repository validator, complete unittest suite, all three skill validators, plugin validator, `py_compile`, JSON parsing, deterministic aggregate rebuilds, `git diff --check`, and an explicit unchanged check for `skills/hy-text/references/business-writing.md`.

- [ ] **Step 2: Commit intentional changes**

Use content-based commit messages. Do not use a branch or commit name beginning with `codex`.

- [ ] **Step 3: Push and reconcile remote state**

Push `research/business-observed-practices`, fetch it, and require local HEAD to equal `origin/research/business-observed-practices` with a clean worktree.
