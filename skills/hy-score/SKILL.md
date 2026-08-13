---
name: hy-score
description: Use when a user asks for a numeric 0–10 quality score, rating, or diagnostic assessment of modern Eastern Armenian text.
---

# hy-score – read-only quality score

Read the sibling `hy-text/references/scoring.md` and every reference it requires. If the corpus cannot be found, stop instead of scoring from memory.

Never modify, overwrite, or save the source. Before applying or evaluating any rule, identify each complete protected token or span and preserve it verbatim. Do not insert, remove, normalize, or relocate characters inside it. Protected content includes code, commands, URLs, email addresses, identifiers, filenames, foreign-language segments or quotations, third-party quotations, and protected official spellings explicitly reproduced verbatim. Always exclude the complete span from deductions.

Score five dimensions separately: `Տպագրություն`, `Լեզվի մաքրություն`, `Գրագիտություն`, `Կառուցվածք`, and `Ընթերցողի համար ճշգրտություն`. Quote one to three concrete issues per dimension and attach a stable `HY-*` rule ID to each deduction.

Follow the weights, caps, short-text warning, labels, and output template in `scoring.md` exactly. Explain the score in the request language; default to Armenian. State the limitations every time. The score never measures factual accuracy, audience fit, originality, effectiveness, or brief compliance.
