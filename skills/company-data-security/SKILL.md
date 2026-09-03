---
name: company-data-security
description: Protect credentials and sensitive data in requirements, fixtures, logs, connectors, and delivery evidence; exclude public-only work.
---

# Company Data Security

Use this Skill when the next action may expose credentials, personal/customer records, non-public material, or disclose sensitive data through a tool or external action. Do not load it for ordinary public-only code, public documentation, or routine build/test work with no sensitive source, connector, output, or disclosure path.

This is the cross-cutting owner for the data boundary, not a second repository lifecycle. Make the smallest safe data-handling decision, hand the resulting constraint back to the active product, design, debugging, verification, delivery, or knowledge owner, and return to the task.

## First action: identify the data boundary

Before opening a sensitive source, name the source, recipient/tool, intended result, and smallest data needed. Classify only as far as needed: C0 public, C1 internal, C2 confidential, C3 restricted, or C4 secret. If uncertain between adjacent classes, select the safer handling level without manufacturing a blocker.

Use the first option that accomplishes the task:

1. Reference a path, record ID, environment-variable name, or secret-manager key without opening the value.
2. Compute, filter, join, or summarize where the data already resides.
3. Pseudonymize repeated identifiers, then redact unused values, columns, rows, log bodies, and metadata.
4. Warn about residual disclosure or seek confirmation at the actual high-impact external action.
5. Stop for non-test/high-risk C4, unnecessary credential-store access, an unauthorized external disclosure, invalid one-shot approval, or a claimed control the surface cannot enforce.

Never request a secret in ordinary chat or repeat a discovered secret in a command, patch, test, log, or evidence file. Use a secure input surface or a reference instead.

## Short routes for common surfaces

- **Requirements and design:** use representative synthetic values or a minimal redacted schema. Return the privacy constraint to `requirements-design` or `product-ux-discovery`; do not choose the product policy on their behalf.
- **Fixtures and tests:** make synthetic data the default. A production-derived fixture needs the smallest permitted, redacted or pseudonymized subset and belongs with the test/verification owner after this boundary is set.
- **Logs and failures:** query a narrow time/error slice, cap output, and retain only redacted diagnostics. Hand causal evidence to `systematic-debugging`; hand oracle or isolation gaps to `verification` or `test-system-engineering`.
- **Connectors and external tools:** minimize source/search scope and keep send, post, update, publish, and share actions as drafts until confirmed. Connector access does not authorize disclosure or change the action owner.
- **Release and operational evidence:** record hashes, versions, classifications, and redacted summaries rather than raw credentials, customer payloads, or full production logs. `delivery-readiness` owns readiness, target identity, and action authority.

Read [surface-playbooks.md](references/surface-playbooks.md) for files, connectors, production data, external actions, or more than one product surface. Read [data-handling-policy.md](references/data-handling-policy.md) for classification examples and output rules.

## Surface limits

For Codex with local Hooks, use reference-preserving calls and rely only on the packaged Hook's supported prompt/tool boundaries. Personal mode may offer one exact, expiring, session-bound confirmation for an explicitly declared test credential; it is neither reusable nor permission to inspect credential values. Strict mode blocks it. In ChatGPT Work, minimize selected sources and connector scope, compute locally when available, and draft before external action; do not claim Hook protection. In ordinary chat, request the smallest excerpt, prefer placeholders/synthetic examples, and warn briefly before a likely secret paste.

The helper is standard-library-only and does not retain raw mappings:

```bash
python3 "$PLUGIN_ROOT/skills/company-data-security/scripts/data_security.py" scan
python3 "$PLUGIN_ROOT/skills/company-data-security/scripts/data_security.py" redact
python3 "$PLUGIN_ROOT/skills/company-data-security/scripts/dlp_approval.py" configure --mode personal
python3 "$PLUGIN_ROOT/skills/company-data-security/scripts/doctor.py" --plugin-root "$PLUGIN_ROOT"
```

`scan` returns categories/counts and `redact` emits transformed content. `doctor` proves packaged/configuration state at check time only. Hooks and this Skill are defense in depth, not enterprise DLP, egress control, connector administration, or incident response; unobserved installation, account, and enforcement state remains `NOT RUN` or `not_observed`.
