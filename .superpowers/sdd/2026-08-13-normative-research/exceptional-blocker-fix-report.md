# Normative research exceptional blocker fix report

Date: 2026-08-13
Worktree: `C:\Users\Arman\Documents\Codex\2026-08-13\new-chat-2\work\hy-text\.worktrees\normative-evidence`
Branch: `research/normative-evidence`
Starting commit: `e8d52efa7a87fc52dd0b4132362fb8e5d1cc1c50`
Implementation commit: `fbb1e427e68828d0d9364902d53cda55c010754c`

## Scope and constraints

This exceptional fix addresses only the two load-bearing findings left by the final scoped review:

1. A rendered `ժամանակակից գործածություն` basis label could evade `USAGE-*` custody when Markdown or Unicode control, format, or mark characters split either Armenian word.
2. Domain independence could be inflated by IDNA-mapped legacy IPv4 aliases or IPv6 scope IDs.

No research rows, aggregates, schemas, normative rules, approval ledgers, dependencies, branches, tags, releases, pushes, or merges were added or changed. The implementation uses only the Python standard library.

## TDD evidence

At the scoped-review commit, the existing suite passed 73 tests but did not exercise the two bypass classes.

The first focused RED command ran seven new or extended blocker tests. It exited 1 with 7 tests and 13 failures. The failures demonstrated that:

- 100 observations using 20 distinct fullwidth legacy loopback spellings passed aggregation.
- 100 observations using 20 scope IDs on one global IPv6 address passed aggregation.
- Fullwidth global legacy IPv4 was not canonicalized.
- Intra-word Markdown and Unicode controls hid the modern-usage marker.
- Prefix and suffix occurrences falsely triggered the marker.

Independent review supplied further rendered-text probes. Each was added before its correction and observed failing for the expected reason:

- U+0085 and U+001C control-whitespace splits – 1 test, 2 failures.
- Boundary controls, U+FE0F, inline links, and combining-mark false positives – 3 tests, 8 failures.
- Shortcut references and deeply balanced inline destinations – 1 test, 2 failures.
- Quoted-attribute, multiline, and processing-instruction raw HTML – 1 test, 3 failures.

Focused GREEN evidence after the final correction:

- The three adversarial modern-usage marker tests passed.
- `python -m unittest tests.test_usage_research -v` – exit 0; 42 tests; `OK`.
- A mutation probe covered 44 split-word control and Markdown positions with zero misses, plus five unrelated forms with zero false positives.
- Independent bounded re-review reported no remaining Critical or Important finding.

## Implementation

### Modern-usage marker custody

`tools\validate.py` now extracts rendered inline text before exact marker matching. It removes balanced inline-link destinations while keeping visible labels, preserves shortcut and reference-link labels, and uses `html.parser.HTMLParser` for raw HTML, comments, declarations, processing instructions, quoted attributes, and multiline tags. NFKC and case folding remain in place.

Letters and numbers form exact words. Markdown delimiters and Unicode control, format, and mark characters are recorded as soft positions instead of visible word boundaries. The validator accepts the exact two-word marker or the exact concatenated marker only when an invisible position separates the two target words. Prefixes, suffixes, and unrelated intervening words do not trigger custody.

Focused tests cover emphasis, underscores, strikethrough, inline and reference links, deeply nested destinations, HTML tags and comments, control and format characters in both Armenian words and at their boundary, U+FE0F, capitalization, wrapping, indentation, and unrelated prefix, suffix, and intervening-word forms.

### Public domain identity

`tools\usage_common.py` now rejects every parsed IPv6 address with a scope ID before accepting it as a public independence key or URL host. It also reruns legacy IPv4 parsing after IDNA conversion, so fullwidth and other IDNA-mapped historic numeric forms cannot survive as distinct hostname keys.

Non-public aliases such as `１２７.１` and `０１７７.０.０.１` are rejected through the existing public-address policy. A public fullwidth legacy form canonicalizes to its ordinary IPv4 address. Valid global IPv6 and Armenian IDN FQDN behavior remains intact.

## Files changed

- `tools\validate.py`
- `tools\usage_common.py`
- `tests\test_usage_research.py`

This report is the only report-only addition.

## Verification gates

Fresh pre-commit evidence at implementation commit content:

| Command | Result |
| --- | --- |
| `python -m unittest discover -s tests -v` | Exit 0; 79 tests; `OK`. |
| `python tools\validate.py` | Exit 0; `hy-text validation passed`. |
| `python C:\Users\Arman\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\hy-text` | Exit 0; `Skill is valid!`. |
| `python C:\Users\Arman\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\hy-check` | Exit 0; `Skill is valid!`. |
| `python C:\Users\Arman\.codex\skills\.system\skill-creator\scripts\quick_validate.py skills\hy-score` | Exit 0; `Skill is valid!`. |
| `python C:\Users\Arman\.codex\skills\.system\plugin-creator\scripts\validate_plugin.py .` | Exit 0; plugin validation passed. |
| `python -m py_compile tools\aggregate_usage.py tools\usage_common.py tools\validate.py tests\test_usage_research.py` | Exit 0. |
| Parse every repository `*.json` with `json.loads` | Exit 0; 14 JSON files parsed. |
| Scan changed files for U+2014 | Exit 0; none found. |
| `git diff --check` | Exit 0; no whitespace errors; only configured LF-to-CRLF working-copy notices. |

## Residual concerns

No blocker remains within the exceptional scope. Organizational independence keys are still manually supplied and audited by design; this fix prevents syntactic aliases from inflating those keys but does not infer organizational ownership. Standard-library IDNA behavior remains the repository's documented runtime authority.

The implementation was committed as `fbb1e427e68828d0d9364902d53cda55c010754c` with subject `fix: close normative evidence blocker bypasses`. The report-only commit is recorded in the controller handoff because a commit cannot contain its own hash.
