# `hy-score` calibration design

**Date:** 2026-08-15
**Status:** approved design, pending written-spec review
**Scope:** modern Eastern Armenian with the reformed orthography used in the Republic of Armenia

## Objective

Calibrate `hy-score` against 50 texts whose Armenian wording and five expert dimension scores were reviewed by Arman Khachatryan. Three blind agent passes must reproduce the expert assessment within the release thresholds without reading the expert scores or one another's results.

The public weights, caps, labels, protected-span policy, and read-only behavior do not change.

## Baseline evidence

The first three blind passes produced 150 results. They failed the current gate:

- mean weighted absolute deviation: `1.1`, limit `0.7`;
- maximum single-dimension deviation: `4.0`, limit `1.0`;
- mean agent scores were higher than the expert means in all five dimensions;
- the largest ambiguity occurred between language purity, structure, and reader precision;
- short clean texts reviewed at `9` were commonly assigned `10` because the existing `9–10` anchor does not distinguish those values.

The failed outputs are diagnostic evidence only. They must not be filtered, rewritten, or presented as a passing calibration.

## Baseline score and short texts

For a text shorter than 50 words, a dimension with no supported deduction receives `9.0`. The short-text reliability warning remains mandatory.

`10.0` is available only when the Armenian evidence is long and varied enough to support a confident judgment for that dimension and no supported deduction applies. Text length alone never earns `10.0`.

This distinction limits false precision. It is not a penalty for brevity.

## Dimension ownership

### `Տպագրություն`

Covers character choice, spaces, quotation marks, dashes, numeric notation, measurement units, and other visible typographic conventions. Its normative source is `typography.md`.

It does not assess grammar, word choice, message completeness, or the content inside a protected span.

### `Լեզվի մաքրություն`

Covers word choice, unnecessary borrowing, bureaucratic constructions, empty intensifiers, unsupported promotional language, stock filler, and machine-like prose. Its normative sources are `info-style.md`, `anti-patterns.md`, and the relevant prose rules in `addenda.md`.

It does not absorb a missing UX action, result, reason, or next step merely because the message is vague.

### `Գրագիտություն`

Covers Armenian grammar and punctuation. Its normative sources are `editorial-grammar.md` and `editorial-punctuation.md`.

It does not deduct for a typographic convention unless a separate grammar or punctuation rule applies to the same visible construction.

### `Կառուցվածք`

Covers ordering, logical connection, grouping, progression, and the presence of structural parts required by the text type. Its normative sources are the structural rules in `info-style.md`, `addenda.md`, and the applicable domain reference.

It does not duplicate a reader-precision deduction unless the issue also breaks an observable structural requirement.

### `Ընթերցողի համար ճշգրտություն`

Covers whether the reader can identify the relevant action, result, object, reason, consequence, deadline, or next step. It uses the applicable domain reference, including `ux-writing.md` and `business-writing.md`.

It does not measure factual truth, audience fit, originality, effectiveness, or compliance with an unstated brief.

## Observable score bands

Each dimension is assigned independently.

| Score band | Observable condition |
|---:|---|
| `9–10` | No supported issue in the dimension. Use `9.0` for a text under 50 words; reserve `10.0` for sufficient and varied evidence. |
| `7–8` | A local issue is present, but the text still performs the dimension's function without substantial repair. |
| `5–6` | An important component is weak, generic, or incomplete and requires a clear editorial correction. |
| `3–4` | The text fails a substantial part of the dimension's function or contains a serious repeated problem. |
| `0–2` | The dimension's function is almost entirely absent or critically broken. |

Within a band, use the upper value for one contained issue and the lower value for repeated or interacting issues. Half-points are allowed only when the evidence genuinely falls between the two adjacent integer anchors; they must not be used to simulate precision.

## Deduction contract

Every deduction must include:

1. the affected dimension;
2. a concrete Armenian fragment or an explicitly identified omission;
3. a stable applicable `HY-*` rule ID;
4. an explanation of the observable effect inside that dimension.

One issue may affect more than one dimension only when each dimension has a separate applicable rule or a separately explained observable effect. The score must not fall merely because another dimension fell.

Complete protected spans remain verbatim and excluded from deductions. Armenian endings attached outside a foreign-script token, such as `locale-ի` and `API-ի`, are evaluated under `HY-GRM-008`; the protected token itself is not edited or penalized.

## Blind calibration protocol

1. Generate a blinded input containing only `id`, `domain`, and `text`.
2. Keep expert scores and review flags inaccessible to scoring agents.
3. Run three independent fresh-context `hy-score` passes.
4. Prevent every pass from reading other pass outputs.
5. Validate 50 unique IDs per pass, all five dimensions, input order, and the `0–10` range.
6. Preserve all 150 raw outputs, including failures.
7. Evaluate results without manually altering scores or excluding difficult cases.

The release gate remains:

- total score deviation within `±0.7` of the expert score;
- each dimension within `±1.0` of the expert score;
- three independent passes over all 50 reviewed texts.

If the repeated blind run fails, report the evidence and return to the dimension wording. Do not change the expert scores, weaken the thresholds, or expose the holdout answers to the scoring agents.

## Testing and release integration

Repository tests must enforce the short-text baseline, dimension boundaries, protected-span handling, the required deduction fields, and the blinded-result schema. `tools/evaluate.py` must implement the documented release interpretation explicitly and report enough detail to identify failing cases and dimensions.

The calibration results become release evidence only after the gate passes. Version manifests, stable-release README wording, the changelog heading, tag `v1.0.0`, and the GitHub Release remain unchanged until all other release gates also pass.
