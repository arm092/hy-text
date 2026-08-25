# Golden-set status

Arman Khachatryan reviewed the Armenian text and all five dimension scores in all 50 scoring fixtures on 2026-08-15. Every case therefore has `reviewed: true`.

Arman Khachatryan completed a human re-review on 2026-08-15 for `article-03`. The approved vector is typography 4, language 9, grammar 4, structure 9, and reader 9: the text has two local punctuation-boundary defects and no independent language, structure, or reader defect.

Arman Khachatryan completed the second human expert-score adjudication on 2026-08-25. Exactly three vectors changed: `article-05` is typography 9, language 4, grammar 9, structure 6, reader 2 because the anonymous authority and unsupported superiority claim are not sourced; `marketing-04` is typography 9, language 3, grammar 9, structure 5, reader 2 because its innovative/universal promise is almost wholly unsupported; and `ux-02` is typography 9, language 7, grammar 9, structure 6, reader 3 because Armenian typography and punctuation are correct, but the confirmation wording is vague and omits the action/consequence. `marketing-06` remains unchanged at 9/3/9/5/2. All 50 reviewed records retain their original IDs and text.

Run three independent `hy-score` passes per case and store the outputs outside user-authored source text. Version 1.0 requires total-score deviation within ±0.7 and per-dimension deviation within ±1.0 from the reviewed median.

The v1.0.0 release calibration passed on 2026-08-25. The immutable raw outputs are `tests/calibration/v1.0.0/pass-1.json`, `pass-2.json`, and `pass-3.json`; each contains all 50 cases in canonical order. All 150 results were evaluated without editing, filtering, substitution, discarding, or averaging. The maximum total-score deviation is 0.7 and the maximum per-dimension deviation is 1.0. `tests/calibration/v1.0.0/summary.json` records the source HEAD, rubric and golden-set hashes, all 30 blind-chunk hashes, assembled-output hashes, evaluator command, completeness, thresholds, and passing result.
