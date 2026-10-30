# Evidence privacy and retention

Collect and retain only evidence needed for the claim. Logs, screenshots, traces, captures, crash dumps, databases, device contents, benchmark data, and reports may contain confidential or personal data.

## Before collection

- Prefer a focused command/result, targeted excerpt or short summary over a bulk copy. Use a hash only when byte identity is the question being checked.
- Use synthetic or minimized data where it preserves the failure.
- Redact secrets, tokens, cookies, authorization headers, direct identifiers, payload bodies, and production data.
- Do not put credentials in commands, source, workstream documents, briefs, screenshots, or retained artifacts.

## Storage and lifecycle

Use the repository's ignored artifact directory or a private temporary directory with restrictive permissions. Workstream prose may link to a stable, safe artifact when useful, but it does not copy raw logs or test output.

For sensitive, shared, expensive, or long-lived evidence, note enough owner, purpose, access, retention, and cleanup information to avoid orphaned data. Routine local test output needs no evidence ledger.

Do not commit, upload, attach, or externally share artifacts without separate authority and a redaction check. Release browsers, devices, VMs, containers, databases, ports, processes, caches, and temporary credentials after use. If adequate proof would require prohibited collection, report `BLOCKED` or `NOT RUN` and use a safer oracle when possible.

## Freshness binding

Reuse native results unless a subsequent change can affect what they established. Follow changed behavior through affected callers and usage paths; rerun the smallest check that observes the affected outcome. Changes to a test, fixture, runner, configuration, generated output or environment matter when they can alter that result, even if product code is unchanged. Ordinary local work needs no full input inventory, artifact identity sweep or separate binding for each conclusion.

For an intermediate repair, retain unaffected results and unresolved failures instead of rerunning the cumulative PR scope. Investigate uncertain dependencies only when they could change the correctness or delivery decision. Installed, packaged and release claims need enough identity to establish that the tested artifact and configuration are the ones being claimed; an earlier similar command is insufficient. Unrelated edits do not invalidate a result.

Retain a valid pre-fix failure or negative control while its protected fault and oracle remain applicable. Rechallenge a changed or doubtful boundary; do not repeat fault injection solely because a new test run started. Explicit user requests for full reruns or repeated stability observations remain part of the authorized outcome.
