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

## Bounded detector contract

- Assignment detection distinguishes unquoted code references and constructor expressions from quoted or structured literal values. Explicit provider-token patterns still inspect literals inside code. Conventional environment names and authorization headers retain their context across string and JSON-object representations. An ambiguous unquoted alphabetic identifier alone is not high-confidence evidence of a credential.
- Placeholder exemptions apply to the complete placeholder, never a word contained within a credential. Safe path exemptions cover exact environment template basenames and SSH public-key counterparts; naming a private file `dummy`, `fixture` or `synthetic` does not exempt it. Shell command fields inspect POSIX quoting/escaping and punctuation while retaining Windows path spelling; this is lexical inspection, not general shell execution or dataflow analysis.
- Overlapping detections cover their full combined span. Normalization cannot displace an existing match or silently leave the rest visible. More than 64 findings in a text or JSON value fails closed instead of returning a partially redacted result. JSON is bounded in bytes, depth and types, including valid Unicode and finite numbers.
- Phone detection uses explicit international prefixes, plausible grouping, or a phone-labelled compact value. Bare numeric counters, epochs and version/date sequences are not sufficient evidence. This trades ambiguous unlabelled-number recall for useful source/log inspection; it is not a complete personal-data classifier.
- Base64 inspection supports a single encoded layer up to 16 KiB decoded content; arbitrary encryption, runtime string construction, fragmented credentials and general encodings are outside the detector contract. PEM marker processing is linear and also recognizes a truncated body after a private-key header.
- Recognized GitHub token families include the documented classic, fine-grained and stateless installation-token prefixes ([official format reference](https://docs.github.com/en/authentication/keeping-your-account-and-data-secure/about-authentication-to-github)). No credential is validated against a provider during local inspection.
- Hook events require their documented fields and accept bounded JSON tool values, including scalars and arrays. Duplicate keys, non-finite numbers and uninspectable payloads receive fixed event-specific failures. Sensitive post-tool results return `decision: block` with redacted feedback: unlike `continue: false` alone, this also rejects the original result at the code-mode nested Promise boundary ([official Hook protocol](https://learn.chatgpt.com/docs/hooks), checked 2026-10-05). Packaged contract tests do not prove a running host has loaded the new Hook.
- Approval mutations serialize within a bounded wait. Corrupt/oversized state or invalid expiry/schema fields cannot become a personal-mode override; one-shot consumption and session/scope checks remain mandatory. The Windows lock branch requires native Windows qualification separately from the macOS subprocess/concurrency tests.
- Repeated redaction recognizes only exact generated DLP labels as placeholders. Whitespace before a wrapper's first string literal cannot disable assignment detection. Structured keys retain NFKC-sensitive context; obfuscated credential keys remain ineligible for one-shot approval. Explicit Chinese phone fields and integer phone values share the string-field contract, while ordinary numeric counters keep their original types.
- A detected private-key body is redacted across reflowed or indented body lines, including a body prefix followed by an indented continuation; this is a confidentiality control, not cryptographic PEM validation.
- Approval issuance reserves space within a 256-record pending-plus-used budget, with at most 128 pending requests; consumption separately caps used records at 256. A failed pending-file deletion can retain duplicate metadata, with the used record still preventing replay. Older oversized directories make bounded expired-record cleanup progress before denying and can recover on retry. Ambiguous JSON fields, non-finite values and unresolvable state paths fail closed; raw prompts, tool inputs and matched credentials are never written into these records.
- Literal/header context survives JSON separator line breaks, and Bearer redaction covers the `~` character in the [RFC 6750 token alphabet](https://www.rfc-editor.org/rfc/rfc6750#section-2.1), including the full suffix after that character.
- Shell path inspection includes static option/environment assignment values and Windows drive-relative spelling. Each shell lexical read span (including consumed whitespace/delimiters) is limited to 65,536 characters before failing closed; the aggregate text/value limits still apply. Long commands consisting of short tokens remain inspectable. This bounds standard-library tokenization cost without executing a shell.
- For canonical `apply_patch` tools, framed patch strings and the `input`, `command` or `patch` field distinguish Add/Update/Delete/Move file targets from source-body path references. Actual credential-file targets remain denied, including names with spaces; the full payload still receives secret-content inspection. Unknown or ambiguous input shapes retain conservative raw path inspection.
- Complete patch targets and parsed shell file arguments use the whole filename for safe-template/public-key exemptions. A filename with an added space suffix cannot inherit the exemption of its shorter prefix. Static assignments inspect their RHS; incomplete non-POSIX quote fragments retain raw-text inspection while the POSIX pass owns the complete quoted value.
- Consumed pending records cannot shadow a fresh confirmation. Under the state lock, cleanup discards only private temporary files with the exact atomic-writer staging name, including partial writes; other unexpected state files remain errors. Prompt retries recheck the current hard-block policy before consuming a historical confirmation. Expiry uses wall-clock timestamps; cancellation text and mode changes do not promise pending-request revocation.
- Raw state reads explicitly select Windows binary mode, preserving arbitrary HMAC key bytes. CRT text mode can translate CRLF and treat Ctrl-Z as EOF ([Microsoft translation-mode contract](https://learn.microsoft.com/en-us/cpp/c-runtime-library/translation-mode-constants?view=msvc-170)); a fixed control-byte key and native text-mode negative control cover this boundary without opening an existing credential store.

## Output minimization

Preserve the smallest semantics needed for the task: error type, state transition, ordering, entity relationship, aggregate, schema, or method. Remove unused rows/columns, long bodies, headers containing authentication, document metadata, and identifiers that do not affect the answer.

## Pseudonym labels

The local helper can produce labels such as `{{DLP:EMAIL:1a2b3c4d}}`. Labels are HMAC-derived with an in-memory or caller-supplied local salt. They are non-reversible and stable only within the scope of that salt. They are not encryption and are not a vault.

## Actions and confirmation

Reading a narrowly selected source is different from sending, posting, uploading, inviting, granting, publishing, or updating an external system. Keep high-impact actions draft-only until the user confirms the exact destination and minimized content.

Codex personal mode uses an expiring, one-shot confirmation because current `PreToolUse` Hooks do not support a native `ask` decision. A prompt confirmation accompanies the unchanged prompt. A tool request is bound to its complete input and host session, and advances only when its exact marker arrives through a later `UserPromptSubmit`; the local helper has no approve command. Current `UserPromptSubmit` Hooks cannot rewrite the submitted prompt, so a tool-confirmation turn forwards only the random short-lived marker plus value-free context—never the tool secret. The marker's confirmation use is spent before model processing; the exact tool retry consumes the remaining approval once. Strict mode accepts no override. This is a strong accidental-disclosure boundary, not cryptographic isolation from a malicious process running as the same OS user. Every result supplies a value-free storage/reference continuation.
