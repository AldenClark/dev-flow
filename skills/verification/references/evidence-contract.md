# Evidence privacy and retention

Collect and retain only evidence needed for the claim. Logs, screenshots, traces, captures, crash dumps, databases, device contents, benchmark data, and reports may contain confidential or personal data.

## Before collection

- Prefer a focused command/result, targeted excerpt, structured summary, or hash over a bulk copy.
- Use synthetic or minimized data where it preserves the failure.
- Redact secrets, tokens, cookies, authorization headers, direct identifiers, payload bodies, and production data.
- Do not put credentials in commands, source, workstream documents, briefs, screenshots, or retained artifacts.

## Storage and lifecycle

Use the repository's ignored artifact directory or a private temporary directory with restrictive permissions. Workstream prose may link to a stable, safe artifact when useful, but it does not copy raw logs or test output.

For sensitive, shared, expensive, or long-lived evidence, note enough owner, purpose, access, retention, and cleanup information to avoid orphaned data. Routine local test output needs no evidence ledger.

Do not commit, upload, attach, or externally share artifacts without separate authority and a redaction check. Release browsers, devices, VMs, containers, databases, ports, processes, caches, and temporary credentials after use. If adequate proof would require prohibited collection, report `BLOCKED` or `NOT RUN` and use a safer oracle when possible.
