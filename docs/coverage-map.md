# Coverage map

This map uses `ru-text` only as a checklist of editorial problem families. No Russian language rule is imported by default.

All ten normative references are expert-reviewed by Arman Khachatryan. The immutable approval hashes are recorded in `research/reviews.json` and checked against the current files by the test suite.

| Area | Armenian evidence required | hy-text destination | Status |
|---|---|---|---|
| Script-specific punctuation | Language Committee, Unicode | `typography.md`, `editorial-punctuation.md` | corpus complete; source registry audited; expert review approved |
| Quotes, spacing, numbers | normative sources plus usage study | `typography.md` | corpus complete; expert review approved; additional usage studies remain future work |
| Orthography and capitalization | normative dictionaries and Language Committee | `editorial-grammar.md` | corpus complete; source registry audited; expert review approved |
| Agreement and syntax | normative grammar | `editorial-grammar.md` | corpus complete; expert review approved |
| Clarity and information order | explicit editorial policy | `info-style.md` | corpus complete; expert review approved |
| Interface copy | Armenian product samples plus editorial policy | `ux-writing.md` | corpus complete; four qualifying web aggregates published; expert review approved |
| Business correspondence | Armenian workplace samples plus editorial policy | `business-writing.md` | corpus complete; two qualifying web aggregates published and two studies documented as insufficient; expert review approved |
| Diagnostic before/after patterns | rules above | `anti-patterns.md` | corpus complete; expert review approved |
| AI-prose tendencies | Armenian examples and counterexamples | `addenda.md` | corpus complete; expert review approved; golden calibration passed |
| Diagnostic scoring | Armenian golden set | `scoring.md` | contract complete; expert review approved; calibration passed on 150/150 results |
