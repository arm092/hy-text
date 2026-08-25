# Task 1 fix round 6 report – concrete-referent microcopy rule

## Scope

- `skills/hy-text/references/info-style.md`
- `skills/hy-text/references/scoring.md`
- `skills/hy-score/SKILL.md`
- `tests/test_repository_contract.py`

Base commit: `603593cd942c8f4526b1550dbf0c7aacaff82b96`.

No scoring gold, public weights, caps, evaluator thresholds, labels, or manifest versions changed. No ignored calibration or temporary directory was opened.

## Root cause

The prior generalized UX and business rows used `HY-INF-002`. Its documented application is marketing, product, and reporting text, and its rule is an abstract evaluative claim needing a verifiable fact, measure, or example. Generic status messages, deictic references, urgency-only labels, and certainty-only confirmations do not necessarily meet that scope.

`HY-INF-006` already existed as the unique link-text rule and is referenced by legacy check-gold coverage. Rather than duplicate or renumber that stable ID, its existing link-text prescription and examples were preserved and its rule/application were broadened narrowly to concrete-referent UX and business microcopy.

## TDD evidence

### RED

Added and extended structural contracts before documentation edits. They require one `HY-INF-006` rule with every mandatory field, preserved link-text coverage, the generalized concrete-referent scope, strict fixture-leak protection, local generalized-state bindings, exact existing anchor vectors, and the unchanged release and scoring-gold contracts.

Command:

```powershell
python -m unittest tests.test_repository_contract.RepositoryContractTest.test_score_rubric_classifies_generalized_ux_and_business_states tests.test_repository_contract.RepositoryContractTest.test_hy_inf_006_preserves_link_text_coverage_and_adds_concrete_microcopy_scope tests.test_repository_contract.RepositoryContractTest.test_score_contract_is_present tests.test_golden_contract.GoldenContractTest.test_second_human_adjudication_is_exact_and_preserves_fixture_identity -v
```

Result: exit `1`, as expected. The generalized rows still named `HY-INF-002`, the success, article-opening, and coercive-demand rows were absent, and `HY-INF-006` lacked the new concrete-referent wording.

### GREEN

The focused command passed after the narrow documentation changes. One initial assertion used a lower-case sentence fragment while the scorer instruction began with a capital letter; correcting only that test assertion produced the final focused GREEN run.

## Implementation

- Broadened `HY-INF-006` to require a concrete object, event, value, result, or action in place of generic status, deictic reference, certainty-only, or urgency-only labels, while retaining its link-target/action requirement, examples, exception, severity, and editorial basis.
- Rebound generic attachment, error, placeholder, empty-state, dangerous-confirmation, and success-notification rows from `HY-INF-002` to `HY-INF-006`; anchors are unchanged.
- Added a specific article-opening state under `HY-ADD-001` and a standalone coercive business-demand state under `HY-BIZ-004` plus `HY-BIZ-002`, each bound to its existing stable impact row.
- Directed `hy-score` to apply `HY-INF-006` before broad generic UX-only rows, without allowing a missing UX component alone to reduce language purity.

## Final verification

```powershell
python -m unittest tests.test_repository_contract tests.test_golden_contract -v
python tools\validate.py
python C:\Users\Arman\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\hy-text
python C:\Users\Arman\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\hy-score
python -m py_compile tests\test_repository_contract.py
```

Results:

- `36` repository and golden contract tests passed.
- `hy-text validation passed`.
- Both skill validators reported `Skill is valid!`.
- Python compilation passed.

## Concern

- Git may emit existing LF-to-CRLF warnings for edited tracked files. The scoped whitespace check is clean.
