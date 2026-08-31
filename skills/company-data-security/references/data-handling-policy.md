# Data handling policy

## Classification and default treatment

| Class | Typical data | Default model exposure | Default action |
|---|---|---|---|
| C0 Public | public docs, published code, approved marketing copy | allowed | normal work |
| C1 Internal | routine internal notes, non-sensitive process text | minimum useful context | proceed quietly |
| C2 Confidential | proprietary source, plans, contracts, financial aggregates | minimized excerpts | reference or redact first |
| C3 Restricted | direct identifiers, customer/employee rows, production samples, security findings | pseudonymized or local aggregate | local compute, minimize, confirm disclosure |
| C4 Secret | tokens, passwords, private keys, cookies, authorization values, recovery codes | never expose by default; an explicitly declared test credential may use one exact local one-shot confirmation | reference locally; confirm only the bounded test exception; otherwise block high-confidence disclosure |

Classification is a handling aid, not a legal determination. Use company policy when it is stricter.

## Required invariants

- A raw C4 value must not appear in model-visible output, generated commands, patches, logs, test fixtures, evidence, or explanations. The only personal-mode exception is a user-supplied value explicitly declared as test data and confirmed for one exact supported prompt or tool input; production-like private material, credential-store access, encoded/obfuscated values, and reusable approvals remain blocked.
- Approval state contains no prompt, tool input, or credential value. It stores only bounded metadata, an expiring token digest, and a keyed exact-scope fingerprint with private local permissions.
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

Codex personal mode uses an expiring, one-shot confirmation because current `PreToolUse` Hooks do not support a native `ask` decision. A prompt confirmation accompanies the unchanged prompt. A tool request is bound to its complete input and host session, and advances only when its exact marker arrives through a later `UserPromptSubmit`; the local helper has no approve command. Current `UserPromptSubmit` Hooks cannot rewrite the submitted prompt, so a tool-confirmation turn forwards only the random short-lived marker plus value-free context—never the tool secret. The marker's confirmation use is spent before model processing; the exact tool retry consumes the remaining approval once. Strict mode accepts no override. This is a strong accidental-disclosure boundary, not cryptographic isolation from a malicious process running as the same OS user. Every result supplies a value-free storage/reference continuation.
