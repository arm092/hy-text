---
name: hy-check
description: Use when a user asks to proofread, correct, edit, or run a full quality review of modern Eastern Armenian text against the hy-text corpus.
---

# hy-check – full read-only review

Review the supplied text with the complete `hy-text` corpus. Locate the sibling `hy-text/references` directory; if it cannot be found, stop instead of checking from memory.

Never modify, overwrite, or save the source. Return proposed text only. Before applying or evaluating any rule, identify each complete protected token or span and preserve it verbatim. Do not insert, remove, normalize, or relocate characters inside it. Protected content includes code, commands, URLs, email addresses, identifiers, filenames, foreign-language segments or quotations, third-party quotations, and protected official spellings explicitly reproduced verbatim.

## Procedure

1. Confirm that the target is modern Eastern Armenian in reformed RA orthography. Report Western Armenian or traditional orthography as unsupported.
2. Read `typography.md`, `editorial-punctuation.md`, and `editorial-grammar.md`.
3. Read `anti-patterns.md`, `info-style.md`, and `addenda.md`.
4. If the domain is identifiable, also read `ux-writing.md` or `business-writing.md`.
5. Check every candidate against the rule's explicit exception.
6. Keep only findings supported by a stable rule ID.

An explicit request always receives the full procedure. A quick check is allowed only when the agent initiates it itself; it covers unambiguous typography and explicit stop-word entries. Escalate to full when a possible AI-prose tendency appears, five findings are confirmed, or the text is publication-bound.

## Output

Return, in this order:

1. Corrected Armenian text.
2. Findings grouped as typography, grammar, clarity, structure, and domain.
3. For every finding: quoted fragment, `HY-*` rule ID, severity (`critical`, `high`, `medium`, `low`), explanation, replacement.
4. A short list of questions where correction needs missing facts.

Write explanations in the user's request language; default to Armenian when unclear. Never claim that stylistic signals prove AI authorship.
