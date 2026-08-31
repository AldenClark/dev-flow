---
name: company-data-security
description: Protect credentials, personal/customer records, non-public data, and sensitive actions. Use for confidentiality, DLP, redaction, least privilege, or risky tool/data flows; exclude public-only work.
---

# Company Data Security

Reduce unnecessary data exposure while keeping normal work moving. Apply one data-handling policy, then use only the controls that the current product surface actually supports.

## Responsibility contract

- Consumes: the user's task, selected sources/tools, current product surface, data classification, and action authority.
- Owns: a confidentiality-safe work plan, least-data source selection, reference/local-compute/redaction choices, and explicit disclosure limits.
- Stops: on unconfirmed or non-test high-confidence C4 disclosure, an unnecessary credential-store read, an unapproved high-impact external action, or a claim of enforcement that the current surface cannot provide.
- Hands off: repository lifecycle, architecture, verification, delivery, or domain-specific decisions to their normal owners after the data boundary is safe.

For a user-owned classification, disclosure, or external-action decision, remain in Default mode and follow `../requirements-design/references/user-interaction.md`. Never request a secret through ordinary chat; use a host-approved secure input surface or stop.

## First resolve the surface

Choose one path before reading sensitive sources:

1. **Codex with local Hooks:** use reference-preserving shell/tool calls and let the packaged Hook enforce supported prompt/tool boundaries. Personal mode may offer one exact, expiring, session-bound, one-shot confirmation for an explicitly declared test credential; a tool request advances only after the user submits its marker through `UserPromptSubmit`. Strict mode retains hard blocking. Do not treat a confirmation as a reusable bypass or read credential values merely to inspect configuration.
2. **ChatGPT Work:** minimize selected sources and connector scope, keep computation local when available, draft before an external action, and request confirmation before sending or publishing. Do not claim that a Codex Hook protects this flow.
3. **Ordinary Chat:** ask for only the smallest necessary excerpt, prefer placeholders or synthetic examples, transform locally before upload when possible, and warn briefly if the user is about to paste a high-confidence secret. No deterministic pre-send Hook is assumed.

Read [surface-playbooks.md](references/surface-playbooks.md) when the task uses files, connectors, production data, external actions, or more than one product surface.

## Classify only as far as needed

Use the highest applicable class:

- **C0 Public:** published or intentionally public information.
- **C1 Internal:** ordinary non-public work with low disclosure impact.
- **C2 Confidential:** proprietary plans, code, documents, aggregates, or business records.
- **C3 Restricted:** direct identifiers, customer/employee records, production samples, security findings, or regulated data.
- **C4 Secret:** credentials, private keys, session material, recovery codes, raw authentication headers, or equivalent access-enabling values.

If uncertain between adjacent classes, use the higher class for source selection but do not turn uncertainty alone into a workflow-blocking event. See [data-handling-policy.md](references/data-handling-policy.md) for examples and output rules.

## Apply the low-friction treatment order

Use the first method that still accomplishes the task:

1. **Reference:** use an environment-variable name, secret-manager reference, file path, record ID, schema, or source pointer without opening the value.
2. **Local compute:** run filtering, joins, validation, or summarization where the data already resides; return only the necessary result.
3. **Pseudonymize:** replace entities with stable non-reversible labels while preserving repeated relationships.
4. **Redact and minimize:** remove values, unused columns, irrelevant rows, long log bodies, and unnecessary metadata.
5. **Warn or confirm:** use a short warning for residual disclosure risk and confirm high-impact external actions.
6. **Block:** reserve for non-test or high-risk C4, explicit credential-store/exfiltration paths, invalid confirmation state, or an external disclosure without authority.

Do not ask ordinary users to run a tokenization ceremony. Perform safe transformations yourself when the surface permits it.

## Work without seeing secrets

- Generate commands that reference `$VARIABLE`, a secret-manager key, or a credential file through the target program's native loading behavior; never interpolate the value into the command.
- Inspect configuration shape, key names, permissions, exit codes, and redacted diagnostics before reading values.
- For logs, query around timestamps/error codes and cap results; never dump an entire production log by default.
- For documents/spreadsheets, select required sections/columns and use aggregates or local formulas before upload.
- For customer/HR data, use synthetic rows for method design and execute the final transform locally.
- For connectors, scope the search narrowly and keep send/post/update actions as drafts until confirmed.
- Never repeat a discovered secret in an explanation, generated command, patch, test, log, or evidence file. A user-confirmed test value may cross only the exact supported prompt/tool boundary covered by its consumed one-shot approval; subsequent work returns to category and reference names.

## Use the local helper in Codex

The helper is standard-library-only and does not retain raw mappings:

```bash
python3 "$PLUGIN_ROOT/skills/company-data-security/scripts/data_security.py" scan
python3 "$PLUGIN_ROOT/skills/company-data-security/scripts/data_security.py" redact
python3 "$PLUGIN_ROOT/skills/company-data-security/scripts/dlp_approval.py" configure --mode personal
python3 "$PLUGIN_ROOT/skills/company-data-security/scripts/doctor.py" --plugin-root "$PLUGIN_ROOT"
```

`scan` returns categories and counts, never matched values. `redact` emits only transformed content. The approval helper stores private keyed metadata and configures mode; it exposes no Agent-runnable approval command. `doctor` proves packaged/configuration state at check time, not central immutability, cryptographic isolation from a malicious same-user process, or live account compliance.

## Communicate decisions briefly

- On safe automatic handling: continue the task and mention the transformation only if it changes the result.
- On a C4 block or confirmation: state the category and action status without echoing the value, then provide one platform-appropriate storage command, an environment-variable reference, and the exact retry/confirmation boundary.
- On Work/Chat limitations: say that source minimization and instructions are active guidance, not a guaranteed pre-send interception layer.
- On external actions: prepare the draft and ask for confirmation at the actual disclosure boundary.

## Never overclaim

This Skill and the packaged Hooks are defense in depth. They do not replace enterprise policy, endpoint DLP, network egress controls, access-control review, connector administration, or incident response. Hosted/specialized tool paths can fall outside local Hook coverage. Report live installation, Hook trust, and account configuration as `NOT RUN` or `not_observed` unless they were actually checked.
