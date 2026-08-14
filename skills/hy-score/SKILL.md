---
name: hy-score
description: Use when a user asks for a numeric 0–10 quality score, rating, or diagnostic assessment of modern Eastern Armenian text.
---

# hy-score – read-only quality score

Read the sibling `hy-text/references/scoring.md` and every reference it requires. If the corpus cannot be found, stop instead of scoring from memory.

Never modify, overwrite, or save the source. Before applying or evaluating any rule, identify each complete protected token or span and preserve it verbatim. Do not insert, remove, normalize, or relocate characters inside it. Protected content includes code, commands, URLs, email addresses, identifiers, filenames, foreign-language segments or quotations, third-party quotations, and protected official spellings explicitly reproduced verbatim. Always exclude the complete span from deductions.

Score five dimensions separately: `Տպագրություն`, `Լեզվի մաքրություն`, `Գրագիտություն`, `Կառուցվածք`, and `Ընթերցողի համար ճշգրտություն`. Apply the responsible source and boundary for each dimension in `scoring.md`: typography uses `typography.md`; language purity uses `info-style.md`; literacy uses `editorial-punctuation.md`; structure uses `addenda.md`; and reader precision uses `ux-writing.md`. Do not assess a dimension outside its stated boundary.

For a text that is `50 բառից կարճ`, assign `9.0` to a dimension with no supported deduction and retain the mandatory short-text reliability warning. Assign `10.0` only when sufficient, varied Armenian evidence supports a confident judgment for that dimension and no supported deduction applies; length alone never earns `10.0`. Apply the observable score bands in `scoring.md` exactly.

Every deduction must name the affected dimension, quote a concrete Armenian fragment or identify a specific omission, cite a stable `HY-*` rule ID, and explain the observable effect within that dimension. One issue does not automatically lower every dimension. Cross-dimension propagation is forbidden unless each dimension has a separate applicable rule or a separate observable effect.

Follow the weights, caps, short-text warning, labels, and output template in `scoring.md` exactly. Explain the score in the request language; default to Armenian. State the limitations every time. The score never measures factual accuracy, audience fit, originality, effectiveness, or brief compliance.
