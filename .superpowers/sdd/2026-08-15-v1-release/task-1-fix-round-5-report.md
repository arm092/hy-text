# Task 1 fix round 5 report – generalized generic-state classification

## Scope

- `skills/hy-text/references/scoring.md`
- `tests/test_repository_contract.py`

Base commit: `54f6c99b86f18a528a843ded3df3f568b98a5ba1`.

This clarification changes no weights, caps, thresholds, public dimensions, unrelated rules, or scoring gold. No ignored calibration temporary directory was opened.

## TDD evidence

### RED

Added `RepositoryContractTest.test_score_rubric_classifies_generalized_ux_and_business_states`. The test requires a separate generalized-state table. It inspects the specific state row, requires its existing combined stable-rule IDs, and requires the matching existing stable-impact condition to occur exactly once.

Command:

```powershell
python -m unittest tests.test_repository_contract.RepositoryContractTest.test_score_rubric_has_stable_rule_impact_anchors tests.test_repository_contract.RepositoryContractTest.test_score_rubric_classifies_generalized_ux_and_business_states -v
```

Result: exit `1`, as expected. The restored fixture-leak guard rejected an exact scoring-gold text in the first implementation, and the generalized-state heading was absent.

### GREEN

Replaced the leaked fixture table with a generalized semantic-state table before the stable-impact table. The focused contract passed after the table included every required state, its local combined-rule cell, and the precise existing stable-impact condition.

### Review remediation

Review found that the first version copied exact scoring-gold texts and complete vectors into the rubric and weakened the fixture-leak guard. This amendment removes the table and its exception entirely. The guard again forbids every scoring-gold text and ID in `scoring.md` without exception. The replacement gives only semantic boundaries, paraphrased non-golden examples, combined IDs, and references to existing anchor rows. It does not repeat any full five-dimension vector.

## Implementation

- Added an explicit, non-policy generalized table for five observable states: deictic attachment reference with bare urgency, objectless generic error, objectless empty state, deictic input command without an expected value, and certainty-only confirmation without an action or consequence.
- States that each generalized formulation independently satisfies `HY-INF-002` alongside its applicable existing business or UX rule.
- Binds each state to its existing combined-rule row and stable-impact condition, without restating anchors or dimension vectors.
- Did not alter `hy-score/SKILL.md`: it already requires reading `scoring.md` and applying the stable impact table, so the new rubric table is directly consumed without duplicating instructions.

## Final verification

```powershell
python -m unittest tests.test_repository_contract tests.test_golden_contract -v
python tools\validate.py
python C:\Users\Arman\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\hy-score
python -m py_compile tests\test_repository_contract.py
git diff --check -- skills/hy-text/references/scoring.md tests/test_repository_contract.py
```

Results:

- Focused fixture-leak and generalized-state contracts passed after the remediation.
- `35` repository and golden contract tests passed.
- `hy-text validation passed`.
- `Skill is valid!`.
- Python compilation passed.
- Scoped whitespace check passed and the Task 1 diff contained no U+2014 em dash.

## Concern

- Git reports existing LF-to-CRLF conversion warnings for the edited tracked files; the scoped whitespace check is clean.
