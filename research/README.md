# Usage research

This directory stores reproducible aggregates, never copied web corpora. Add one JSON file per disputed form under `aggregates/` after the study satisfies `METHODOLOGY.md`.

An aggregate records the query, alternatives, collection date, counts, at least 20 independent domains, source-layer distribution, exclusions, and short verification examples. It must not contain full articles, private text, or personal data.

No current normative rule claims a **modern usage** basis. That label remains unavailable until a qualifying aggregate is committed and referenced from `sources.md`.

## Observation workflow

Record one observation per line as JSON under `observations/`. Every observation must be manually verified as public, relevant to the disputed form, and independent of every other observation. Reject mirrors, duplicated URLs, spam, obvious machine translation, private material, personal data, and irrelevant matches.

Each object contains `url`, `domain`, `layer`, `variant`, `observed_at`, and `example`. Use one of the five layer identifiers defined by `observation.schema.json`: `government`, `media`, `commercial`, `professional`, or `community`. Strip the evidence to a short verification example of at most 240 characters; never copy a full page or article into the repository.

Automated search-result counts alone are inadmissible. Search may locate candidates, but a human must open and verify every retained observation before aggregation. Repeated observations from the same domain are permitted only when their URLs and relevant uses are genuinely distinct.

After an observation set reaches 100 relevant uses, 20 independent domains, and three positive layers, build its deterministic aggregate with `tools/aggregate_usage.py`. Commit an aggregate under `aggregates/` only when the tool accepts the complete manually verified observation set.
