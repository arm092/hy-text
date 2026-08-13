# Normative research before corpus expansion

## Status

Approved in principle by Arman Khachatryan on 2026-08-13. This specification defines the research stage that precedes the next rule-writing stage.

## Scope

The research covers only modern Eastern Armenian and the reformed orthography used in the Republic of Armenia. Western Armenian and traditional orthography remain outside the project.

This stage has two outcomes:

1. strengthen the normative source registry for the existing and planned rule families;
2. determine the correct treatment of Armenian inflection attached to foreign-script words and names.

It does not add a large batch of editorial rules. New prescriptions follow only after the evidence is recorded and reviewed.

## Evidence hierarchy

Evidence is considered in this order:

1. decisions and guidance of the Language Committee of the Republic of Armenia;
2. normative dictionaries and academic grammar or orthography publications;
3. Armenian legislation and technical standards when the domain is regulated;
4. Unicode and CLDR for characters, encoding, normalization, and locale data;
5. qualified modern-usage aggregates;
6. an explicitly labelled editorial decision when higher-level sources do not settle the issue.

An editorial preference must not be described as an official rule. A single search result, search-engine count, or copied passage is not a usage corpus.

## Source audit

The source registry will be expanded with records for:

- orthography and grammar;
- Armenian punctuation and hyphen-like characters;
- inflection of abbreviations, titles, product names, and foreign-script units;
- terminology and preferred Armenian equivalents;
- regulated scientific and technical notation.

Each record must contain a stable source ID, evidence type, direct link or full bibliographic description, and a narrow statement of what the source supports.

Placeholder sources cannot support a new official rule.

## Modern-usage studies

Usage research is required when authoritative sources conflict, do not cover digital writing, or leave multiple forms open. Each disputed form must satisfy the project thresholds:

- at least 100 relevant uses;
- at least 20 independent domains;
- at least three of the five corpus layers;
- mirrors, duplicates, spam, obvious machine translation, and irrelevant matches excluded.

The repository stores only reproducible aggregates: queries, variants, counts, layer distribution, domains, collection date, exclusions, and short verification examples. It does not store copied corpora or personal user text.

## Proposed foreign-script inflection rule

The candidate rule ID is `HY-GRM-008`.

Candidate prescription: when an Armenian case ending or article must be attached to a word or name retained in foreign script, separate the unchanged foreign form from the Armenian ending with a hyphen.

Candidate examples:

- correct: `Մենք աշխատում ենք Apricode-ում։`
- correct: `Apricode-ի թիմը պատասխանեց։`
- incorrect: `Մենք աշխատում ենք Apricodeում։`
- incorrect for the intended locative meaning: `Մենք աշխատում ենք Apricode։`

The last form is not globally incorrect. A bare foreign name may be valid when its syntactic role does not require an attached Armenian ending, for example `Մենք ընտրեցինք Apricode։`. A checker must therefore use grammatical context and must not flag every bare foreign-script token.

The rule does not apply to:

- a foreign fragment quoted as foreign-language text;
- code, commands, URLs, email addresses, identifiers, or file names;
- an Armenian generic word that carries the inflection instead, for example `Apricode ընկերությունում`;
- a context where no Armenian ending is grammatically required;
- a protected official spelling that is being reproduced verbatim.

The Language Committee guidance on quotation marks already provides direct evidence for separating an Armenian ending from a foreign-script title, using the example `«The New York Times»-ի`. Research must still determine whether the public rule should prescribe ASCII `-` (U+002D), Armenian hyphen `֊` (U+058A), or treat one as primary and the other as an accepted variant in digital text.

## Decision rules for `HY-GRM-008`

The candidate becomes an official-norm rule only if the authoritative material supports both its construction and stated scope. If authoritative sources support the construction but do not settle the character choice, the construction and character policy must have separate bases.

If character usage requires a corpus study:

- a variant at 70% or above across multiple layers may become the default;
- variants at 50–69% remain contextual alternatives;
- below 50%, the official character remains preferred;
- a project-specific compatibility choice remains labelled as an editorial decision.

## Review ledger

The repository will gain a review ledger that records reference name, reviewed commit, reviewer, date, and status. Arman's approval covers the current versions of:

- `typography.md`;
- `editorial-punctuation.md`;
- `editorial-grammar.md` through `HY-GRM-007`.

Adding or materially changing a prescription after approval returns the affected rule to pending review. Therefore `HY-GRM-008` will be pending even though the earlier grammar rules are approved.

## Verification

The implementation plan must include checks that:

- every official rule references a non-placeholder authoritative source;
- every modern-usage rule references a schema-valid qualifying aggregate;
- source IDs are unique and resolvable;
- approved rules are tied to an immutable commit;
- `HY-GRM-008` includes valid examples and contextual counterexamples;
- protected fragments remain unchanged;
- all text is UTF-8 and Unicode NFC;
- the repository test suite and three-OS CI remain green.

## Deliverables

The research stage will produce:

1. an expanded normative source registry;
2. bibliographic and web-evidence notes without copied corpora;
3. qualifying usage aggregates where necessary;
4. a review ledger for the three approved references;
5. an evidence-backed draft of `HY-GRM-008`;
6. a ranked queue of the next rules that are ready to draft.

No `v1.0.0` tag or release is created during this stage.
