# Surface playbooks

## Codex

Prefer environment-variable and secret-manager references. Inspect key names and file permissions, not values. Use local scripts to filter/redact tool output. The packaged Hook covers documented local UserPromptSubmit, PreToolUse, and PostToolUse paths after the user trusts the exact Hook definition.

The Hook does not cover every hosted or specialized tool path, cannot undo a tool side effect that already happened, and must not be bypassed. Treat network permissions, sandboxing, repository access, and MCP allowlists as separate least-privilege controls.

## ChatGPT Work

Before using files or connectors:

1. choose the smallest source and time range;
2. exclude credential stores and raw exports when an aggregate will do;
3. ask the assistant to preserve schema/relationships while removing identifiers;
4. keep send/post/update actions as drafts;
5. confirm destination and minimized content at the action boundary.

Work may provide additional workspace/connector administration depending on the account, but this Skill does not assume or attest to those controls. No Codex local Hook is claimed for a Work chat.

## Ordinary Chat

Use synthetic examples to design methods. Paste only the necessary excerpt, replace names/IDs with stable placeholders, remove document metadata, and keep secrets as variable names. If raw sensitive data is already visible, do not repeat it; switch to category/location references and recommend rotation when a credential may have been exposed.

There is no assumed deterministic pre-send inspection layer. The practical control is the shared Skill/instruction baseline plus user-visible minimization and confirmation.

## Common task examples

- **Production incident:** model sees error codes/timestamps/redacted stack frames; local shell uses `$DATABASE_URL`; raw logs remain local.
- **Spreadsheet analysis:** model designs formulas against synthetic columns; local compute produces aggregates; direct identifiers become stable labels.
- **Contract summary:** select the relevant clauses, remove signatures/contact details, preserve obligations/dates/amount categories.
- **Customer support:** summarize the issue and state transitions; remove account identifiers and attachments not needed for diagnosis.
- **Connector action:** search narrowly, draft a message/update, show the minimized payload, then ask before sending.
