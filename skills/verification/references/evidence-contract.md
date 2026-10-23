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

## Freshness binding

Bind each conclusion to its relevant source and transitive consumers, assertions, fixture, runner/selector, configuration, generated output, toolchain, environment and artifact identity. A change to an input that can affect the conclusion invalidates that PASS until the smallest affected check runs on the final inputs. Unchanged product code alone does not establish freshness. An unrelated documentation-only edit does not require an irrelevant runtime rerun.

For an intermediate repair, compare with the last valid evidence for each claim, including unresolved failures and transitive impact; do not automatically rerun the cumulative PR scope. If identity or dependencies are uncertain, state the uncertainty and use a conservative affected check, not an assumed cache hit or a new evidence registry. A frozen delivery candidate still needs the repository's applicable acceptance evidence; an earlier similar command is insufficient.

Apply this rule to sensitivity evidence too: retain a valid pre-fix failure or negative control while its protected fault, oracle and relevant inputs remain applicable. Rechallenge a changed or doubtful boundary; do not repeat fault injection solely because a new test run started. Explicit user requests for full reruns or repeated stability observations remain part of the authorized outcome.
