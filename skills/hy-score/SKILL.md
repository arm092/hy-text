---
name: hy-score
description: Use when a user asks for a numeric 0–10 quality score, rating, or diagnostic assessment of modern Eastern Armenian text.
---

# hy-score – read-only quality score

Read the sibling `hy-text/references/scoring.md` and every reference it requires. If the corpus cannot be found, stop instead of scoring from memory.

Never modify, overwrite, or save the source. Before applying or evaluating any rule, identify each complete protected token or span and preserve it verbatim. Do not insert, remove, normalize, or relocate characters inside it. Protected content includes code, commands, URLs, email addresses, identifiers, filenames, foreign-language segments or quotations, third-party quotations, and protected official spellings explicitly reproduced verbatim. Always exclude the complete span from deductions.

Score five dimensions separately: `Տպագրություն`, `Լեզվի մաքրություն`, `Գրագիտություն`, `Կառուցվածք`, and `Ընթերցողի համար ճշգրտություն`. Apply the responsible source and boundary for each dimension in `scoring.md`: typography uses `typography.md`; language purity uses `info-style.md`; literacy uses `editorial-punctuation.md`; structure uses `addenda.md`; and reader precision uses `ux-writing.md`. Do not assess a dimension outside its stated boundary.

For a text that is `50 բառից կարճ`, assign `9.0` to a dimension with no supported deduction and retain the mandatory short-text reliability warning. Assign `10.0` only when sufficient, varied Armenian evidence supports a confident judgment for that dimension and no supported deduction applies; length alone never earns `10.0`. Apply the observable score bands in `scoring.md` exactly.

Use the rule-to-dimension matrix and the dimension-specific numeric anchors in `scoring.md` before assigning each score. Select the anchor for the strongest supported observable state. Do not add deductions or subtract points sequentially. A rule's `low`, `medium`, or `high` severity does not set a score by itself. For unsupported promotional claims or anonymous-source claims, inspect whether verifiable support – a criterion, example, or source – is present and whether its absence removes a required structural part or prevents a reader from assessing the claim. Do not test whether the claim is true.

Apply the stable-rule impact table before the broader bands. When several rows describe the same fragment, apply the row with more stable rule IDs or the narrower observable condition before a broader row; only among equally specific rows use the lowest applicable anchor. Do not subtract again. Treat a generic UX word as a language-purity issue only when its wording independently matches the information-style or antipattern rule named by the table; a merely missing UX component affects only the dimensions explicitly mapped for that omission. Use the table's density conditions for short text exactly as written.

For an anonymous-authority claim that also makes an unsupported universal-superiority or all-needs promise, the combined `HY-ADD-004` + `HY-ANT-002` row controls its mapped dimensions instead of the separate anonymous-source or broader one-rule rows. A short persuasive claim whose whole or nearly whole message uses innovation, revolution, or universal-coverage framing belongs to the stronger `HY-INF-002` + `HY-ANT-002` row, not the qualitative-promise row. If the same fragment also uses a false contrast under `HY-ADD-003`, do not add a second deduction in the overlapping language, structure, or reader-precision dimensions.

A certainty-only dangerous-action confirmation receives the language-purity `7.0` anchor only if its wording independently satisfies `HY-INF-002`; `HY-UX-005` alone uses its structure and reader-precision anchors and never lowers typography or literacy. Correct Armenian punctuation remains clean in those typography and literacy dimensions.

Every deduction must name the affected dimension, quote a concrete Armenian fragment or identify a specific omission, cite a stable `HY-*` rule ID, and explain the observable effect within that dimension. One issue does not automatically lower every dimension. Cross-dimension propagation is forbidden unless each dimension has a separate applicable rule or a separate observable effect.

Follow the weights, caps, short-text warning, labels, and output template in `scoring.md` exactly. Explain the score in the request language; default to Armenian. State the limitations every time. The score never measures factual accuracy, audience fit, originality, effectiveness, or brief compliance.
