# Four observed UX practices

## Scope and date

This protocol covers `CAND-UX-001` through `CAND-UX-004` in public Armenian-language interfaces observed from 2026-08-14 onward. It covers only modern Eastern Armenian and reformed orthography used in the Republic of Armenia.

Search engines and site search may locate candidate pages. A result is retained only after the public page, document, or interface is opened and the relevant Armenian string and context are manually verified. Search-result snippets and result counts are not observations.

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

## Exclusion log

The following candidate families were rejected during the 2026-08-14 collection pass:

- Armenian OpenAI Help Center pages explicitly labelled as machine-translated;
- mass-localized how-to sites whose Armenian text showed obvious machine-translation patterns;
- the live Microsoft Office 2010 language-pack page because its documented interface is obsolete and cannot represent a current interface practice;
- Aladin Express, Harmare, and Mira Trans contact fields from the field-label study because the visible prompt was placeholder-only rather than a persistent field label;
- static prose telling a reader to wait, including the Active Citizen FAQ, from the loading-message study because it is not an active interface state;
- `OK` and `Cancel` confirmation controls in Armenian documentation from the destructive-label study because the labels themselves are foreign-language fragments.
