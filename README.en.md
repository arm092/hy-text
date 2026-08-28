# hy-text

`hy-text` is an open, source-backed text-quality reference for modern Eastern Armenian in AI agents. It is built for editors and content teams.

`v1.1.0` is the current stable release. It adds the rule that expands `և` to `ԵՎ` in all-caps text.

It supports only modern Eastern Armenian and the reformed orthography used in the Republic of Armenia. Western Armenian and traditional orthography are explicitly unsupported.

The project ships three skills: `hy-text` for safe always-on typography, `hy-check` for full read-only proofreading, and `hy-score` for a diagnostic 0–10 score. Code, URLs, commands, foreign-language segments, and third-party quotations are protected.

The architecture is inspired by [talkstream/ru-text](https://github.com/talkstream/ru-text), while the Armenian corpus is independently formulated from Armenian sources and usage research.

[Installation](INSTALL.en.md) · [Methodology](METHODOLOGY.md) · [Sources](skills/hy-text/references/sources.md)

MIT © 2026 Arman Khachatryan
