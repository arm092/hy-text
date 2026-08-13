# Four observed UX practices

## Scope and date

This protocol covers `CAND-UX-001` through `CAND-UX-004` in public Armenian-language interfaces observed from 2026-08-14 onward. It covers only modern Eastern Armenian and reformed orthography used in the Republic of Armenia.

Search engines and site search may locate candidate pages. A result is retained only after the public page, document, or interface is opened and the relevant Armenian string and context are manually verified. Search-result snippets and result counts are not observations.

Product-maintained public localization resources are eligible when the resource maps an Armenian string to an explicit interface state or control. The immutable file URL is opened and verified, forks and copied locale bundles are excluded, and the hosting domain remains the conservative independence key even when several unrelated product owners use the same code host.

## Shared sampling rules

- Retain at least 100 distinct relevant URLs, 20 manually verified organizational independence keys, and three corpus layers for each study.
- A URL contributes one observation to a study. When a page contains several eligible strings, record the string that represents the page's principal or first eligible pattern and note competing patterns in the exclusions log before aggregation.
- Reuse the same independence key for subdomains and separately branded services controlled by one organization.
- Exclude mirrors, duplicate or parameter-only URL variants, navigation text without the studied interaction, machine-translated pages, inaccessible authenticated states, foreign-language strings, screenshots whose text cannot be verified, and ordinary prose that merely describes an interaction.
- Keep only a short verification example of at most 240 characters. Do not retain personal data, entered values, complete articles, or complete documents.
- Record the page's live URL even when a search engine or a documentation index supplied the lead.

## `CAND-UX-001` – destructive-action labels

Eligible strings are labels of controls that delete, remove, revoke, deactivate, reset, or irreversibly discard user-controlled data or access. Confirmation-dialog buttons and documented verbatim interface labels are eligible; instructional prose is not.

Variant labels combine wording form and action type:

- `imperative/<action>` – a second-person command such as `Ջնջեք`;
- `infinitive/<action>` – an infinitive such as `Ջնջել`;
- `noun-phrase/<action>` – a nominal label such as `Հաշվի ջնջում`;
- `other/<action>` – a relevant Armenian label outside the three proposed forms, such as a confirmation `Այո`; this prevents an observed alternative from being forced into the research question's initial taxonomy.

`<action>` is one of `account`, `content`, `access`, `reset`, or `other`. Record cancel and recovery controls only as context, not as separate observations.

## `CAND-UX-002` – punctuation after field labels

Eligible strings are visible Armenian labels associated with an input, select, or textarea. Placeholder-only prompts, table headings, key-value readouts, and prose preceding a form are excluded.

Variant labels combine punctuation and layout:

- `colon/stacked`, `no-colon/stacked`;
- `colon/inline`, `no-colon/inline`.
- `other-punctuation/stacked`, `other-punctuation/inline` – the label ends in visible punctuation other than a colon; this category prevents a full stop or another observed mark from being forced into the binary comparison.

`stacked` means the label is visually above the control; `inline` means the label and control share a row. A required-field marker is ignored when determining whether a colon is present.

## `CAND-UX-003` – register of direct address

Eligible strings are interface instructions, notices, errors, confirmations, or onboarding text directed to a user. Ordinary editorial prose and quotations are excluded.

Variant labels combine register and audience:

- `formal/<audience>` – explicit `Դուք`, `Ձեր`, or corresponding formal verb agreement;
- `informal/<audience>` – explicit `դու`, `քո`, or corresponding informal verb agreement;
- `impersonal/<audience>` – no direct second-person address, including neutral infinitive or passive wording.

`<audience>` is one of `general`, `government-service`, `customer`, `student`, or `professional`. Capitalization at sentence start does not alone establish the formal category.

## `CAND-UX-004` – loading and progress messages

Eligible strings describe an active wait, loading, processing, upload, download, or progress state. Completed-state messages, static instructions to wait, and article prose are excluded.

Variant labels combine grammatical form and state:

- `finite/determinate`, `finite/indeterminate` – a finite verb such as `Բեռնվում է`;
- `verbal-noun/determinate`, `verbal-noun/indeterminate` – a verbal noun or nominal process label;
- `ellipsis-label/determinate`, `ellipsis-label/indeterminate` – a short label whose defining presentation includes an ellipsis.

When an ellipsis-marked label also contains a finite verb, classify it as `finite/*`; the short example preserves the ellipsis for a later secondary count. `determinate` requires visible numeric, percentage, step, or bounded-item progress; otherwise use `indeterminate`.

## Decision and publication

Each study remains `usage-study-required` until its observation file passes repository validation and its deterministic aggregate passes the 100-use, 20-domain, and three-layer thresholds. The aggregate can establish a description of observed practice, not a causal usability benefit. A rule is drafted only after Arman reviews the aggregate and proposed conclusion.

## Results from the 2026-08-14 slice

All four observation sets passed the mechanical sample gates. The registered aggregates are deterministic rebuilds of their paired JSONL files.

| Candidate | Uses | Domains | Layers | Observed distribution | Research conclusion |
|---|---:|---:|---:|---|---|
| `CAND-UX-001` | 100 | 20 | 4 | 99 infinitive labels; 1 other label | The infinitive dominates this slice, but 81 uses come from the community layer and 79 are content deletion. Treat the result as a narrow tendency, not a universal recommendation. |
| `CAND-UX-002` | 100 | 90 | 5 | 94 without a colon; 4 with a colon; 2 with other punctuation | Colon-free labels dominate both stacked and inline layouts across a broadly distributed sample. This supports a current-practice editorial recommendation, not a claim that omission improves usability. |
| `CAND-UX-003` | 100 | 32 | 4 | 80 formal; 12 impersonal; 8 informal | Formal address dominates this slice, but 72 uses come from the community layer. Audience and product voice remain required context. |
| `CAND-UX-004` | 100 | 20 | 5 | 41 finite; 44 verbal-noun; 15 ellipsis-label; 9 determinate | No form reaches 70 percent, and 85 uses come from the community layer. Retain contextual variants; the sample does not justify one universal loading formula. |

### Approved publication decisions

Arman approved all four decisions on 2026-08-14. They are published in the normative UX reference without expanding the claims supported by the aggregates:

1. `CAND-UX-001` became `HY-UX-007`: use an infinitive when a destructive control directly names the action. The rule discloses the sample concentration and makes no safety or clarity claim.
2. `CAND-UX-002` became `HY-UX-008`: omit a colon after a short visible field label in stacked and inline layouts. Full questions and sentences retain required punctuation, and protected fragments remain unchanged.
3. `CAND-UX-003` became `HY-UX-009`: formal address is the default for direct address in a general public interface. A deliberately informal product voice and an impersonal construction remain contextual alternatives.
4. `CAND-UX-004` became `HY-UX-010`: choose a finite form for an active state and a verbal noun for a compact status label, retaining a numeric or bounded indicator for determinate progress. The rule explicitly rejects one universal loading formula and treats ellipsis only as presentation.

## Exclusion log

The following candidate families were rejected during the 2026-08-14 collection pass:

- Armenian OpenAI Help Center pages explicitly labelled as machine-translated;
- mass-localized how-to sites whose Armenian text showed obvious machine-translation patterns;
- the live Microsoft Office 2010 language-pack page because its documented interface is obsolete and cannot represent a current interface practice;
- Aladin Express, Harmare, and Mira Trans contact fields from the field-label study because the visible prompt was placeholder-only rather than a persistent field label;
- static prose telling a reader to wait, including the Active Citizen FAQ, from the loading-message study because it is not an active interface state;
- `OK` and `Cancel` confirmation controls in Armenian documentation from the destructive-label study because the labels themselves are foreign-language fragments.

## Search log

- 2026-08-14 – GitHub code searches for `Բեռնվում է`, `Բեռնում...`, `Փաստաթղթի բեռնում`, `Մշակվում է...`, `Ջնջել հաշիվը`, `Ջնջել`, and `Հեռացնել`. Retained resources were opened at immutable commits; upstream repositories were checked for fork and archive state, and copied locale bundles and mismatched source-target pairs were excluded.
- 2026-08-14 – Mozilla Pontoon API searches for active loading, downloading, deletion, and direct-address strings in locale `hy-AM`; Western Armenian `hyw` and traditional-orthography `hye` resources were excluded. Retained entity resources were individually opened.
- 2026-08-14 – TranslateWiki MediaWiki API searches for Eastern Armenian interface messages ending in `/hy`; Western Armenian `/hyw`, fuzzy entries, prose-only messages, errors, and non-control strings were excluded. Retained message resources were individually opened through the revision API.
- 2026-08-14 – Public Armenian government, professional, commercial, community, and media forms were opened to verify a visible label, its associated control, terminal punctuation, and stacked or inline presentation. Placeholder-only prompts and key-value displays were excluded.
