---
name: hy-text
description: Use when writing, proofreading, editing, or evaluating modern Eastern Armenian text in the reformed orthography of the Republic of Armenia, including typography, editorial quality, UX copy, business correspondence, and AI-prose cleanup.
---

# hy-text – Eastern Armenian text quality

Apply this skill only to modern Eastern Armenian written in the reformed orthography used in the Republic of Armenia. Do not convert Western Armenian or traditional orthography; state that they are unsupported.

User instructions about register, voice, genre, and terminology override editorial defaults. They do not override objective orthography or the requirement to preserve protected content.

## Protected content

Before applying or evaluating any rule, identify each complete protected token or span and preserve it verbatim. Do not insert, remove, normalize, or relocate characters inside it. Protected content includes code, commands, URLs, email addresses, identifiers, filenames, foreign-language segments or quotations, third-party quotations, and protected official spellings explicitly reproduced verbatim.

You may report a consequential problem in a quotation, but never rewrite it.

When checking an existing text, return a proposed corrected version and findings. Never modify the source unless the user explicitly requests an edit. The `hy-check` and `hy-score` skills are always read-only.

## Safe always-on pass

`HY-TYP-008` is contextual because regulated SI notation has a different spacing requirement. Load `references/typography.md` before applying it; it is not part of this safe pass.

Apply only unambiguous fixes silently in Armenian output:

| Issue | Wrong | Correct | Rule |
|---|---|---|---|
| Armenian full stop | `Վերջ.` | `Վերջ։` | HY-TYP-001 |
| Question mark position | `Որտեղ?` | `Որտե՞ղ` | HY-PUN-001 |
| Exclamation mark position | `Ինչ հրաշալի!` | `Ի՜նչ հրաշալի` | HY-PUN-004 |
| Guillemets | `"Անուշ"` | `«Անուշ»` | HY-TYP-003 |
| Ellipsis | `...` | `…` | HY-TYP-005 |

Do not silently apply contextual grammar, style, or vocabulary judgments.

## Load references by task

Reference paths are relative to this file.

| Task | Read |
|---|---|
| Typography, Unicode, numbers | `references/typography.md` |
| Clarity, terminology, translation, stop-words | `references/info-style.md` |
| Armenian punctuation | `references/editorial-punctuation.md` |
| Grammar, spelling, capitalization | `references/editorial-grammar.md` |
| Interfaces and product copy | `references/ux-writing.md` |
| Email and workplace writing | `references/business-writing.md` |
| Diagnostics and rewrites | `references/anti-patterns.md` |
| AI-prose tendencies and editorial addenda | `references/addenda.md` |
| Scoring | `references/scoring.md` |
| Provenance | `references/sources.md` |

An explicit proofreading request requires the whole corpus. A self-initiated check may use only this file plus the obvious lexical entries in `info-style.md`. Call that result a quick check, never a full review. Escalate silently to the full corpus when there is a possible AI-prose tendency, five confirmed findings, or publication-bound text.

## Findings contract

Every finding must quote the affected fragment, name a stable `HY-*` rule ID, check its exception, assign severity, and propose a replacement. A stylistic tendency is evidence for editing, never evidence that AI authored the text.
