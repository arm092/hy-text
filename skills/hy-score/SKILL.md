---
name: hy-score
description: Use when a user asks for a numeric 0–10 quality score, rating, or diagnostic assessment of modern Eastern Armenian text.
---

# hy-score – read-only quality score

Read the sibling `hy-text/references/scoring.md` and every reference it requires. If the corpus cannot be found, stop instead of scoring from memory.

Never modify, overwrite, or save the source. Treat code, URLs, commands, filenames, foreign-language segments, and third-party quotations as protected and exclude them from Armenian-language deductions.

Score five dimensions separately: `Տպագրություն`, `Լեզվի մաքրություն`, `Գրագիտություն`, `Կառուցվածք`, and `Ընթերցողի համար ճշգրտություն`. Quote one to three concrete issues per dimension and attach a stable `HY-*` rule ID to each deduction.

Follow the weights, caps, short-text warning, labels, and output template in `scoring.md` exactly. Explain the score in the request language; default to Armenian. State the limitations every time. The score never measures factual accuracy, audience fit, originality, effectiveness, or brief compliance.
