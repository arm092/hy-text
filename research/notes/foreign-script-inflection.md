# Foreign-script inflection and separator code point

**Status:** `sufficient` for the exact quoted foreign-script construction and for the scoped U+002D-versus-U+058A choice. No modern-usage claim is made.

## Decision

When an Armenian ending is attached outside the closing Armenian guillemet of a retained foreign-script title, the Language Committee's official example supports the construction `«The New York Times»-ի`.

For this exact construction, use U+002D HYPHEN-MINUS rather than U+058A ARMENIAN HYPHEN. The official archived HTML encodes U+002D in the example, and the Unicode Standard separately identifies U+002D or U+2010 HYPHEN as Armenian word-joining representations while assigning U+058A the end-of-line word-splitting role.

This decision is deliberately narrow:

- it does not establish every unquoted foreign-script inflection pattern;
- it does not establish a general Language Committee preference between U+002D and U+2010;
- if the project prefers U+002D over U+2010 for keyboard, search, or web compatibility, that preference must be labelled `editorial decision`, not `official norm`;
- it does not derive Armenian grammatical preference from the Unicode character names alone.

## Accepted evidence

### SRC-LC-FOREIGN-INFLECTION – construction and encoded example

- **Page title:** `Չակերտների գործածության մասին`
- **Publisher:** ՀՀ լեզվի կոմիտե
- **Official-origin archive URL:** https://web.archive.org/web/20231128194752id_/https://www.langcom.am/%D5%B9%D5%A1%D5%AF%D5%A5%D6%80%D5%BF%D5%B6%D5%A5%D6%80%D5%AB-%D5%A3%D5%B8%D6%80%D5%AE%D5%A1%D5%AE%D5%B8%D6%82%D5%A9%D5%B5%D5%A1%D5%B6-%D5%B4%D5%A1%D5%BD%D5%AB%D5%B6/
- **Accessed:** 2026-08-13
- **Short excerpt:** `Նա «The New York Times»-ի թղթակից էր`։
- **Narrow proposition:** in Armenian text, an Armenian ending may follow a quoted foreign-script title outside the closing guillemet, separated as shown in the example. The source also says the Armenian-script rendering is preferable, but it still supplies the retained-foreign-script construction.

The current `langcom.am` path returns 404 and the legacy `old.langcom.am` path returns HTTP 500. The cited Internet Archive replay is a direct capture of the official `www.langcom.am` origin and is used instead of a third-party republication or search-result rendering.

### SRC-UNICODE-ARMENIAN – character semantics

- **Title:** `The Unicode Standard, Version 17.0, Chapter 7, Section 7.6.1 Armenian`
- **Publisher:** Unicode Consortium
- **URL:** https://www.unicode.org/versions/Unicode17.0.0/core-spec/chapter-7/#G3407
- **Accessed:** 2026-08-13
- **Paraphrase:** Unicode distinguishes the Armenian word-joining hyphen, representable by U+002D or U+2010, from U+058A used to split a word across lines.
- **Narrow proposition:** U+002D and U+058A have different technical semantics in Armenian text. Unicode does not supply the Armenian grammatical construction and does not prefer U+002D over U+2010 for this project.

The official Unicode 17.0 data file was also inspected at https://www.unicode.org/Public/17.0.0/ucd/UnicodeData.txt. Its records give the official names:

| Code point | Official Unicode name | Relevant technical role |
|---|---|---|
| U+002D | HYPHEN-MINUS | One of the two representations Unicode lists for Armenian word joining; also a generic character with ambiguous semantics outside a specified context. |
| U+058A | ARMENIAN HYPHEN | The Armenian word-splitting character that Unicode says may be used when a word is split across lines. |

The names identify the characters; the role descriptions and the Committee's encoded example, not the names by themselves, support the separator decision.

## Exact code-point inspection

The inspection used the `id_` Internet Archive replay form so archive toolbar markup and URL rewriting were not inserted into the captured official HTML.

1. Fetch the 2023-11-28 19:47:52 UTC replay as text.
2. Locate the literal ASCII needle `The New York Times` in the captured response.
3. Take the following source fragment and decode HTML character references only. No Unicode normalization or punctuation substitution is applied.
4. Enumerate the characters immediately after the title.

Relevant captured source fragment:

```html
&laquo;The New York Times&raquo;-&#1387;
```

Decoded sequence around the boundary:

| Position | Character | Code point |
|---|---|---|
| Closing guillemet | `»` | U+00BB |
| Separator | `-` | U+002D |
| Armenian ending start | `ի` | U+056B |

The same `U+00BB U+002D U+056B` boundary was reproduced from the accessible official-origin captures dated 2021-01-27, 2021-04-15, 2021-05-26, and 2023-11-28. Other indexed captures that could not be replayed reliably during this check were not treated as corroborating evidence.

## Why no usage aggregate was created

The threshold study is unnecessary for the question actually decided here:

- the official Armenian guidance establishes the construction and contains a source-level U+002D;
- Unicode's Armenian section explicitly places U+002D on the word-joining side of the technical distinction and U+058A on the end-of-line word-splitting side;
- therefore U+058A is not an unresolved competing separator for this exact construction.

No `research/observations/foreign-script-inflection.jsonl` or `research/aggregates/foreign-script-inflection.json` was created. The repository must not claim modern usage for this decision. A broader claim about unquoted foreign names, or a preference between U+002D and U+2010, would require separate authoritative evidence or a qualifying study of at least 100 manually verified uses across 20 independent domains and three layers.
