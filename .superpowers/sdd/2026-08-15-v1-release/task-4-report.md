# Task 4 – `hy-check` golden quality gate

## Scope

Task 4 adds a 50-case Armenian check corpus, one immutable blind full-corpus result, strict detection and correction metrics, protected-span integrity checks, and release-gating tests. The corpus contains ten cases in each of `article`, `business`, `marketing`, `mixed`, and `ux`, with clean and faulty material in every domain.

## TDD evidence

The initial RED run failed because `tests/golden/check.json`, release results, clean-case false-positive rate, protected mutation metrics, and strict check-result validation did not exist. The first blind run then failed honestly at recall `0.8889`: five sentence-final ASCII periods were misclassified as `HY-TYP-002`. The output was preserved outside the passing directory and was not edited.

A generic `HY-TYP-001`/`HY-TYP-002` boundary contract was added test-first. It assigns final sentence terminators to `HY-TYP-001` and internal clause separators to `HY-TYP-002`. A new blind pass then reached recall `1.0`, clean-case false-positive rate `0.0`, and zero protected mutations.

Review fix round 1 began with failing tests for protected-span relocation, duplication, mutation plus reinsertion, reordered protected spans, empty and no-op faulty corrections, clean-text rewrites, reviewed correction alternatives, malformed IDs, and unknown IDs. The evaluator now validates exact stable IDs against the normative corpus, gates corrected text against canonical or explicitly reviewed alternatives, and forces clean results to remain byte-identical to the source.

Review fix round 2 added RED controls proving that unsafe canonical or accepted corrections could previously legitimize a moved protected span or mutate one of two identical occurrences and reinsert a replacement elsewhere. The GREEN implementation derives a structural fingerprint from the source for every protected occurrence: line, Armenian-sentence slot, occurrence ordinal, and token slot before the protected placeholder. Every accepted correction and result must preserve multiplicity, order, and this source-derived slot. This permits edits elsewhere in the containing text while rejecting relocation, loss, duplication, replacement, and reordering.

## Corpus correction review

Canonical corrections were revised where the earlier fixture invented facts that the source did not provide:

- `business-03` asks to decide the responsible person and deadline instead of inventing a person and Friday deadline.
- `business-04` uses `հնարավորինս շուտ` instead of inventing `17:00`.
- `business-05` names `contract.pdf` and requests review and response without inventing a section or prices.
- `marketing-01` removes the unsupported service-quality claim instead of inventing a two-hour SLA.
- `marketing-05` states only that the order arrived after the set deadline instead of inventing a supplier and two-day delay.
- `ux-02` asks the reader to check generic data instead of assuming a card payment and card details.

Seven non-canonical blind corrections were individually checked against their rule and stored as explicit context-supported alternatives. Corpus-wide contracts reject newly introduced clock times and payment instruments when they are absent from the source.

## Immutable evidence

The committed blind result remains byte-for-byte unchanged from the fresh successful pass. SHA-256:

`50BEC4A1100F3B27EF482A053DB4E213D552C37FB5B486C8C6CBD7876AF10A6F`

Final check metrics:

- cases evaluated: `50/50`
- expected rule occurrences found: `45/45`
- recall: `1.0`
- clean-case false-positive rate: `0.0`
- protected mutations: `0`
- correction failures: `0`
- correction accuracy: `1.0`

## Validation

Required validation commands completed successfully after the final fixes:

- focused evaluator and golden-contract tests
- complete `unittest` discovery suite
- `python tools/validate.py`
- `quick_validate.py skills/hy-check`
- `quick_validate.py skills/hy-text`
- `git diff --check`
- scoped U+2014 scan

No scoring files, release metadata, Task 5 files, or calibration temporary directories were modified by Task 4.

## Review fix round 3

The scoped re-review supplied two exact moves that the previous line/sentence/token-slot fingerprint accepted: moving `app.php` across a comma and across an ASCII question mark without changing the number of preceding words. RED tests reproduced both as unsafe accepted corrections and unsafe reported outputs. Another RED control captured the regression where the legitimate surrounding edit `Բացեք app.php ֆայլը հիմա։` to `Խնդրում եմ բացել app.php ֆայլը հիմա։` was rejected even though the protected occurrence remained anchored.

The heuristic fingerprint was replaced with a protected-atom edit alignment. Every protected source occurrence receives a unique atom. Non-protected token occurrences whose multiplicity is unchanged become stable alignment anchors. The evaluator requires every protected atom to keep the same partial order relative to all stable anchors. Inserted, deleted, or reworded surrounding tokens do not constrain the atom, so ordinary wording edits remain valid. Moving punctuation or another stable token across the atom, reordering protected atoms, losing or duplicating an atom, or substituting one duplicate occurrence and reinserting a copy changes the alignment and is rejected.

GREEN evidence after this replacement:

- the exact comma and question moves are rejected both in golden accepted corrections and reported results
- the exact legitimate pre-span wording edit is accepted
- the duplicate-occurrence substitution/reinsertion control remains rejected
- focused evaluator and golden tests pass
- the immutable 50-case result remains at recall `1.0`, clean-case false-positive rate `0.0`, protected mutations `0`, correction failures `0`, and correction accuracy `1.0`
- full test discovery, repository validation, both relevant skill validators, diff check, and the U+2014 scan pass

The previously added source-support gates for clock times and payment instruments remain active and passing.

## Review fix round 4

The fresh-eyes implementation targeted the remaining anchorless relocation gap from round 3. RED coverage added one accepted-correction control and one reported-result control for the exact case `Բացեք app.php հիմա.` to `Խնդրում եմ անմիջապես օգտագործեք app.php։`. Before the fix, the accepted correction passed protected-span validation and failed only later with `missing check results`, while the reported result incorrectly produced zero protected mutations. The pre-existing comma/question relocation controls stayed red-free, and the legitimate wording edit `Բացեք app.php ֆայլը հիմա.` to `Խնդրում եմ բացել app.php ֆայլը հիմա։` remained the acceptance target.

The evaluator contract now treats protected-span preservation as evidence-based rather than vacuously true. The protected-atom partial-order check still requires every stable non-protected token whose multiplicity is unchanged to remain on the same side of each protected atom, but it now also requires at least one such stable anchor for every checked protected occurrence. If a correction rewrites all surrounding non-protected material so completely that no stable anchor survives, the evaluator rejects the correction as an unverified relocation instead of silently accepting it. This closes the anchorless rewrite bypass while preserving legitimate edits that still keep source-supported anchors on one side of the protected atom.

GREEN evidence after the change:

- the exact anchorless accepted correction now fails with `accepted correction relocates protected span`
- the exact anchorless reported output now yields one protected mutation and one correction failure
- the comma and ASCII-question relocation controls remain rejected
- the duplicate-occurrence substitution/reinsertion control remains rejected
- the legitimate wording edit before `app.php` remains accepted
- focused evaluator plus golden tests pass, and the immutable release result remains unchanged

## Review fix round 5

The final breaker round supplied two exact follow-up failures in the round-4 anchor contract. First, byte-identical protected-only clean text such as `app.php` was being rejected because the evaluator required an anchor even when the source and target were identical. Second, a lone terminal punctuation mark at the absolute end of the text could still act as a vacuous anchor, so `Բացեք app.php հիմա.` to `Խնդրում եմ անմիջապես app.php.` slipped through while reporting zero protected mutations.

RED coverage added three generic controls. Protected-only identity now runs for `app.php`, `app.php.`, and `app.php։` and must pass cleanly. Terminal-punctuation-only relocation now fails both as an accepted correction and as a reported result for both ASCII `.` and Armenian `։`. The existing anchorless full rewrite, comma/question relocation, duplicate substitution/reinsertion, and legitimate wording-edit controls stayed in scope.

The round-5 evaluator change qualifies anchors rather than broadening heuristics. Exact byte equality now returns immediate preservation evidence before any anchor analysis. For non-identical source and target, the evaluator still enforces the partial-order relation against every stable token, but it only treats a stable token as sufficient positional evidence when it is not a lone terminal punctuation token at the absolute end of the token stream. Final `.` or `։` can still participate in order checks, but they cannot by themselves justify that a protected atom stayed anchored. This keeps fail-closed behavior for true anchorless rewrites while restoring direct identity preservation and removing the terminal-punctuation bypass.

GREEN evidence after the round-5 change:

- exact protected-only identity now passes for `app.php`, `app.php.`, and `app.php։`
- terminal-punctuation-only relocation is rejected for both ASCII and Armenian final punctuation in accepted-correction and reported-result paths
- the anchorless full rewrite remains rejected
- comma and question relocation remain rejected
- duplicate substitution/reinsertion remains rejected
- the legitimate wording edit before `app.php` remains accepted

## Review fix round 6

The exceptional round-6 review found that round 5 still relied on an enumerated terminal-punctuation set, so other punctuation marks at absolute text end could remain vacuous sole anchors. The exact bypass `Բացեք app.php հիմա,` to `Խնդրում եմ անմիջապես app.php,` reproduced both failure modes again: accepted-correction validation fell through to `missing check results`, and reported-result scoring still produced zero protected mutations. A second RED control using terminal ellipsis `…` proved that the gap was generic rather than comma-specific.

The round-6 fix replaces the hard-coded terminal-mark allowlist with a Unicode structural rule from the Python standard library. Anchor qualification now uses `unicodedata.category(token)` and treats any punctuation token in category `P*` as non-meaningful when it appears at the absolute terminal token position. This applies only to anchor qualification, not to the partial-order comparison itself: terminal punctuation can still expose a relocation when other meaningful anchors survive, but it can no longer act alone as the sole preservation evidence. Exact `source == target` still passes immediately, and lexical anchors continue to prove stationary edits around a protected span.

GREEN evidence after the round-6 change:

- terminal comma-only relocation is rejected in both accepted-correction and reported-result paths
- terminal ellipsis-only relocation is rejected in both accepted-correction and reported-result paths
- previously covered final `.` and `։` bypasses remain rejected
- exact protected-only identity remains accepted
- anchorless full rewrites remain rejected
- comma/question boundary relocation, duplicate substitution/reinsertion, and legitimate lexical-anchor edits keep their prior behavior
