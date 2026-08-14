# Data handling policy

## Classification and default treatment

| Class | Typical data | Default model exposure | Default action |
|---|---|---|---|
| C0 Public | public docs, published code, approved marketing copy | allowed | normal work |
| C1 Internal | routine internal notes, non-sensitive process text | minimum useful context | proceed quietly |
| C2 Confidential | proprietary source, plans, contracts, financial aggregates | minimized excerpts | reference or redact first |
| C3 Restricted | direct identifiers, customer/employee rows, production samples, security findings | pseudonymized or local aggregate | local compute, minimize, confirm disclosure |
| C4 Secret | tokens, passwords, private keys, cookies, authorization values, recovery codes | never intentionally expose | reference locally; block high-confidence disclosure |

Classification is a handling aid, not a legal determination. Use company policy when it is stricter.

## Required invariants

- A raw C4 value must not appear in model-visible output, commands, patches, logs, test fixtures, evidence, or explanations.
- C3 entity relationships may be preserved with non-reversible labels; no raw-to-label mapping is persisted by V1.
- Detection output contains only rule/category/class/severity/count, never the matched substring.
- A safe placeholder such as `${TOKEN}`, `$DATABASE_URL`, `{{SECRET_REF}}`, `<redacted>`, `example`, `dummy`, or `changeme` is not treated as a real secret by itself.
- A detector miss does not make data public. A detector match does not authorize opening or sending the source.

## Output minimization

Preserve the smallest semantics needed for the task: error type, state transition, ordering, entity relationship, aggregate, schema, or method. Remove unused rows/columns, long bodies, headers containing authentication, document metadata, and identifiers that do not affect the answer.

## Pseudonym labels

The local helper can produce labels such as `{{DLP:EMAIL:1a2b3c4d}}`. Labels are HMAC-derived with an in-memory or caller-supplied local salt. They are non-reversible and stable only within the scope of that salt. They are not encryption and are not a vault.

## Actions and confirmation

Reading a narrowly selected source is different from sending, posting, uploading, inviting, granting, publishing, or updating an external system. Keep high-impact actions draft-only until the user confirms the exact destination and minimized content.
