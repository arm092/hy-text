# Normative research final fix report

Date: 2026-08-13
Worktree: `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence`
Branch: `research/normative-evidence`
Starting commit: `3be705f140bac2dbd6f680b258945b562ad2c558`
Implementation commit: `80e3fc89e6d4b14492e8a376072ff06ccd7a0813`

## Scope and constraints

This was one coherent TDD fix wave for every finding in the final branch review. It did not create or invent observation rows, usage aggregates, personal data, tags, releases, pushes, or merges. `HY-GRM-008` remains beyond the approved `HY-GRM-007` ledger boundary and therefore remains pending Arman's review.

The approval ledger itself was not modified. Its immutable commit remains `de16c32b402982048f5a20d225a9287c78b1e911`, with boundaries `HY-TYP-008`, `HY-PUN-008`, and `HY-GRM-007`.

## TDD evidence

Baseline before the fix:

- `python -m unittest discover -s tests -v` – exit 0, 46 tests, `OK`.
- `python tools\validate.py` – exit 0, `hy-text validation passed`.

Focused RED command:

```powershell
python -m unittest tests.test_usage_research tests.test_validator tests.test_golden_contract tests.test_repository_contract tests.test_source_audit tests.test_rule_candidates -v
```

Result before production changes: exit 1; 66 tests ran; 32 failures and 23 errors. The failures were the intended missing behaviors: no custody API or recomputation, IDNA aliases did not match, public-host checks were absent, invalid UTF-8 escaped, JSONL was outside NFC discovery, canonical variants split, empty or control-only evidence passed, the CLI overwrote identical/hard-linked input, atomic writing was absent, protected classes were incomplete, BIPM was unregistered, SI scope was incomplete, `HY-PUN-005` overclaimed its source, and `CAND-INF-*` had the wrong semantics and statuses.

Focused GREEN commands:

- `python -m unittest tests.test_usage_research tests.test_validator -v` – exit 0; 38 tests; `OK`.
- `python -m unittest tests.test_golden_contract tests.test_repository_contract tests.test_source_audit tests.test_rule_candidates tests.test_review_ledger -v` – exit 0; 29 tests; `OK`.

The same regression tests therefore failed against the pre-fix implementation for the expected reasons and passed after the minimal implementation.

Final code review then supplied concrete adversarial probes. They were added as tests before each corresponding correction. Representative review-driven RED results were:

- The five-test public-host, meaningful-example, schema-parity, and multiline-custody probe exited 1 with the expected failures before the fixes; after the fixes, all five passed.
- `python -m unittest tests.test_usage_research.UsageAggregateTest.test_non_public_hosts_and_addresses_are_rejected -v` failed once for an overlong hostname that became short only after removing `www`; after moving the complete-host length check before key normalization, it passed.
- The same focused public-host test then failed six `.arpa` subtests; after rejecting the complete special-use `.arpa` namespace, it passed.
- `python -m unittest tests.test_usage_research -v` – exit 0; 36 tests; `OK` after all review-driven corrections.

## Finding disposition and rationale

1. **Evidence custody.** Added the single convention `<study-slug>.jsonl` ↔ `<study-slug>.json` ↔ `USAGE-<STUDY-SLUG-UPPER>`, documented it in `research\README.md` and `skills\hy-text\references\sources.md`, and enforced registry uniqueness, ID/filename/path agreement, aggregate/observation pairing, threshold rebuilding, and exact comparison of derived fields in `tools\validate.py`. Every `USAGE-*` reference in a rule resolves independently of basis wording. Modern-usage detection normalizes Unicode whitespace, capitalization, Markdown emphasis, wrapping, indentation, block quotes, and list decoration, and requires a registered qualifying aggregate. `exclusions` is explicitly documented as manually audited metadata rather than a recomputed count. Observation-only draft studies remain allowed. No production observation or aggregate was added.
2. **Public domain identity.** Added shared standard-library IDNA and `ipaddress` normalization in `tools\usage_common.py`. Supported Unicode and punycode aliases collapse to one key; unsafe standard-library IDNA deviation mappings are rejected rather than mapped to a different hostname. Localhost, non-public single-label hosts, special-use/local suffixes including `.arpa`, reserved example names, overlong DNS names, legacy numeric spellings of non-public IPs, and non-global, private, reserved, loopback, link-local, multicast, and unspecified IP addresses are rejected. The complete hostname is validated before a leading `www` is removed. The manually supplied parent independence key remains authoritative; the tooling does not infer organizational ownership or registrable domains.
3. **UTF-8 and NFC.** Added `.jsonl` to repository text discovery, converted `UnicodeDecodeError` into validator errors, and normalized variants/examples to NFC before counting and output. Embedded Unicode control/format characters are rejected so visually identical labels cannot split counts. Committed aggregate labels/examples must already be canonical.
4. **Safe output.** `tools\aggregate_usage.py` rejects resolved-identical and hard-linked input/output paths. It serializes to a same-directory temporary file and uses `os.replace`; a failed replace leaves an existing output unchanged and removes the temporary file.
5. **Protected spans.** `skills\hy-text\SKILL.md`, `skills\hy-check\SKILL.md`, and `skills\hy-score\SKILL.md` now preserve each complete protected token/span. `HY-GRM-008` explicitly excludes code, commands, URLs, email addresses, identifiers, filenames, foreign quotations, and protected official spellings. `tests\golden\hy-grm-008-protected.json` locks all eight classes with unchanged output and no findings.
6. **`HY-PUN-005` evidence scope.** The Arman-approved rule, application, examples, exception, and severity remain unchanged. Only the basis is corrected to editorial. `SRC-LC-STRESS` is stated as official support for the repeated-conjunction example, not for every contrast or semantic-emphasis case.
7. **Candidate queue.** Replaced `CAND-INF-001..006` with genuine information-style research questions. The array still contains exactly 18 rows and six per reference. Tests lock exact global order, ID, reference, status, and evidence mapping. All information-style causal questions, `CAND-UX-005`, `CAND-UX-006`, and `CAND-BIZ-005` remain `insufficient` and cannot be promoted by frequency. There are currently zero `source-ready` candidates.
8. **SI/BIPM.** Added verified primary source `SRC-BIPM-SI-BROCHURE` from the official BIPM PDF, `The International System of Units (SI), 9th edition, Version 4.01`, Section 5.4.3: `https://www.bipm.org/documents/d/guest/si-brochure-9-en-pdf`. The official publication page is `https://www.bipm.org/en/publications/si-brochure`. JSON and Markdown registry values are identical. `HY-TYP-008` retains its approved compact reader-facing prescription, labels it editorial, and gives the narrow regulated SI spacing exception, including `20 °C` and the plane-angle exceptions. The contextual rule was removed from the safe always-on table.
9. **Schema/runtime contract.** `research\observation.schema.json` accepts case-insensitive HTTP(S) IRIs, including Unicode hostnames, and names runtime public-host validation as authoritative. `research\aggregate.schema.json` now requires the exact allowed layer vocabulary with positive counts, nonblank query/variant/example strings, positive variant counts, and at least one short example containing a letter or number at runtime. Standard-library tests inspect both schemas and exercise representative values against runtime normalization.
10. **Task 7 report.** Corrected the ignored `.superpowers\sdd\2026-08-13-normative-research\task-7-report.md`: for `HEAD...origin/master`, `12 0` meant 12 commits unique to the left side (`HEAD`) and 0 unique to the right, so the branch was ahead 12 and behind 0.

## Files changed

Production and research contracts:

- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\tools\usage_common.py`
- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\tools\aggregate_usage.py`
- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\tools\validate.py`
- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\research\README.md`
- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\research\aggregate.schema.json`
- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\research\observation.schema.json`
- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\research\rule-candidates.json`
- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\research\source-audit.json`
- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\skills\hy-text\SKILL.md`
- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\skills\hy-check\SKILL.md`
- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\skills\hy-score\SKILL.md`
- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\skills\hy-text\references\editorial-grammar.md`
- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\skills\hy-text\references\editorial-punctuation.md`
- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\skills\hy-text\references\sources.md`
- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\skills\hy-text\references\typography.md`

Regression tests:

- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\tests\golden\hy-grm-008-protected.json`
- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\tests\test_golden_contract.py`
- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\tests\test_repository_contract.py`
- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\tests\test_rule_candidates.py`
- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\tests\test_source_audit.py`
- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\tests\test_usage_research.py`
- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\tests\test_validator.py`

Verification reports:

- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\.superpowers\sdd\2026-08-13-normative-research\task-7-report.md`
- `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence\.superpowers\sdd\2026-08-13-normative-research\final-fix-report.md`

## Final verification

Fresh pre-commit results after all review corrections:

| Command | Result |
| --- | --- |
| `python -m unittest discover -s tests -v` | Exit 0; 73 tests; `OK`. |
| `python tools\validate.py` | Exit 0; `hy-text validation passed`. |
| `python C:\Users\Arman\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\hy-text` | Exit 0; `Skill is valid!`. |
| `python C:\Users\Arman\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\hy-check` | Exit 0; `Skill is valid!`. |
| `python C:\Users\Arman\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\hy-score` | Exit 0; `Skill is valid!`. |
| `python C:\Users\Arman\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py .` | Exit 0; plugin validation passed. |
| `python -m py_compile tools\aggregate_usage.py tools\usage_common.py tools\validate.py tests\test_usage_research.py` | Exit 0. |
| Parse every repository `*.json` with `json.loads` | Exit 0; `all JSON parsed`. |
| Scan changed files for U+2014 | Exit 0; no em dash found. |
| `git diff --check` | Exit 0; no whitespace errors; only configured LF-to-CRLF working-copy notices. |

Two independent final reviewers re-ran the concrete custody and code-review probes against the live worktree. Both reported no remaining Critical, Important, or Minor findings and `Ready: Yes`.

Implementation was committed as `80e3fc89e6d4b14492e8a376072ff06ccd7a0813` (`fix: enforce normative evidence integrity`). A report-only commit records this file and the corrected Task 7 report. Fresh post-commit evidence, final status, divergence, tags, and releases are reported in the controller handoff because a commit cannot include its own hash.
