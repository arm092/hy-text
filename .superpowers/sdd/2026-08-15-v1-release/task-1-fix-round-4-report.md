# Task 1 fix round 4 report – scoring precedence clarification

## Scope

- `skills/hy-text/references/scoring.md`
- `skills/hy-score/SKILL.md`
- `tests/test_repository_contract.py`

Base commit: `ff9870f76bc494ebaff53ec617fda1c1e467c178`.

No public weights, caps, labels, thresholds, rule IDs, evaluator settings, or scoring fixtures changed. The ignored blind-run raw, evaluation, and report directories were not opened, and no scoring gold case ID or text was read for this clarification.

## TDD evidence

### RED

Added `RepositoryContractTest.test_score_rubric_prioritizes_combined_promotional_and_confirmation_states`. It parses the stable impact table and checks the existing dimension anchors for the combined and one-rule states. It also requires generic observable taxonomy and the corresponding `hy-score` precedence instructions without encoding a fixture.

Command:

```powershell
python -m unittest tests.test_repository_contract.RepositoryContractTest.test_score_rubric_prioritizes_combined_promotional_and_confirmation_states -v
```

Result: exit `1`, as expected. The rubric lacked the required generic innovation, revolution, and universal-coverage taxonomy.

### GREEN

After the minimal rubric and skill clarifications, the same focused test exited `0`.

An initial complete contract run then exposed two existing prose invariants affected by the wording change: the qualitative-promise exclusion phrase and Armenian sentence-stop validation. Restoring the compatible exclusion sequence and replacing two ASCII sentence stops with U+0589 made the three affected scoring-contract tests pass before the final complete run.

## Implementation

- Made the stronger `HY-INF-002` + `HY-ANT-002` state observable for a short persuasive claim whose whole or nearly whole message uses innovation, revolution, universal-coverage, or all-needs framing; the existing `3.0` / `5.0` / `2.0` anchors remain unchanged.
- Clarified that the general qualitative-promise row excludes those stronger observable states and retains its existing `4.0` / `6.0` / `3.0` anchors.
- Explicitly prioritized the combined anonymous-authority plus unsupported universal-superiority state over `HY-ADD-004` alone and broader one-rule rows, retaining the existing language `4.0`, structure `6.0`, and reader-precision `2.0` anchors.
- Clarified that an overlapping `HY-ADD-003` false contrast does not produce a second deduction in those controlled language, structure, and reader-precision dimensions.
- Clarified that a certainty-only `HY-UX-005` confirmation uses only structure `6.0` and reader precision `3.0`; language `7.0` remains conditional on independently satisfying `HY-INF-002`, and correct Armenian punctuation leaves typography and literacy clean.

## Final verification

```powershell
python -m unittest tests.test_repository_contract tests.test_golden_contract -v
python tools\validate.py
python C:\Users\Arman\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\hy-score
git diff --check -- skills/hy-text/references/scoring.md skills/hy-score/SKILL.md tests/test_repository_contract.py
```

Results:

- `34` repository and golden contract tests passed.
- `hy-text validation passed`.
- `Skill is valid!`.
- Scoped `git diff --check` exited `0`.
- The Task 1 diff contained no U+2014 em dash.

## Concerns

- Git reports existing LF-to-CRLF conversion warnings for the edited tracked files; the whitespace check is clean.
- This is a generic precedence clarification only. Fresh blind calibration remains a separate release-evidence task.
