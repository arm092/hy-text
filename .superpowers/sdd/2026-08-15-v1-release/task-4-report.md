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
