# Usage research

This directory stores reproducible aggregates, never copied web corpora. Add one JSON file per disputed form under `aggregates/` after the study satisfies `METHODOLOGY.md`.

An aggregate records the query, alternatives, collection date, counts, at least 20 independent domains, source-layer distribution, exclusions, and short verification examples. It must not contain full articles, private text, or personal data.

No current normative rule claims a **modern usage** basis. That label remains unavailable until a qualifying aggregate is committed and referenced from `sources.md`.

## Rule candidate promotion

`rule-candidates.json` is a ranked research queue, not a substitute for the normative corpus. Only a `source-ready` candidate can proceed to rule drafting, and its rule must remain within the narrow scope of every cited verified source. After explicit approval and normative inclusion, its status becomes `published`, and the reason names the resulting stable rule ID. A `usage-study-required` candidate becomes ready only after its observations produce an aggregate that passes repository validation. An `insufficient` candidate remains unpublished as a rule until the specifically required evidence is obtained and validated.

Array order is the stable global rank. A causal question about comprehension, trust, accountability, task success, or error rates cannot be promoted by a frequency aggregate, regardless of sample size. It remains `insufficient` until the comparative or authoritative evidence named in `required_evidence` is verified.

An editorial policy may transparently support an editorial decision, but it is not external empirical evidence. It cannot be used to claim an official norm, modern usage, or a causal reader outcome.

## Observation workflow

Record one observation per line as JSON under `observations/`. Every observation must be manually verified as public, relevant to the disputed form, and independent of every other observation. Reject mirrors, duplicated URLs, spam, obvious machine translation, private material, personal data, and irrelevant matches.

Each object contains `url`, `domain`, `layer`, `variant`, `observed_at`, and `example`. Set `domain` to the manually verified organizational independence key, not automatically to the URL hostname. The URL hostname must equal that key or be its subdomain; multiple subdomains controlled by the same independent source must reuse one key. The tooling canonicalizes supported Unicode and punycode aliases with the standard-library IDNA codec but never infers registrable domains or organizational ownership. It rejects IDNA deviation characters whose standard-library mapping could change host identity instead of guessing a different public key. It accepts only public multi-label hosts or global IP addresses and rejects localhost, single-label intranet hosts, special-use/local suffixes, reserved example domains, legacy numeric spellings of non-public IP addresses, and non-public IP ranges. Use one of the five layer identifiers defined by `observation.schema.json`: `government`, `media`, `commercial`, `professional`, or `community`. Variant labels and examples are trimmed and normalized to Unicode NFC before counting; Unicode control and format characters are invalid anywhere in those values. Strip the evidence to at least one meaningful short verification example of at most 240 characters containing a letter or number; never copy a full page or article into the repository.

Automated search-result counts alone are inadmissible. Search may locate candidates, but a human must open and verify every retained observation before aggregation. Repeated observations from the same domain are permitted only when their URLs and relevant uses are genuinely distinct.

After an observation set reaches 100 relevant uses, 20 independent domains, and three positive layers, build its deterministic aggregate with `tools/aggregate_usage.py`. The CLI rejects identical input and output files and replaces aggregate output atomically, so a failed write cannot truncate an existing aggregate.

Use one custody convention: lowercase ASCII kebab-case `<study-slug>` maps to `research/observations/<study-slug>.jsonl`, `research/aggregates/<study-slug>.json`, and `USAGE-<STUDY-SLUG-UPPER>`. Register the ID and both paths in the usage-aggregate table in `skills/hy-text/references/sources.md`. A rule with basis `ժամանակակից գործածություն` cites that `USAGE-*` ID directly. Repository validation rejects an unpaired or unregistered aggregate and recomputes every derived field from the paired observations. `exclusions` is manual audit metadata rather than a derived count: the validator checks its shape, while a researcher remains responsible for recording it honestly. Observations may remain unaggregated while a study is incomplete; never create an aggregate or modern-usage claim until the thresholds pass.
