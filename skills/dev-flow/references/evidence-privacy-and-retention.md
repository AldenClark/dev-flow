# Evidence privacy and retention

Collect the minimum evidence needed to prove the claim. Treat logs, screenshots, traces, network captures, crash dumps, databases, simulator/device contents, benchmark data, and agent reports as potentially sensitive.

## Before collection

- Classify the artifact as public, internal, confidential, credential-bearing, or personal data.
- Prefer targeted excerpts, structured summaries, hashes, and paths over bulk copies.
- Disable or redact secrets, tokens, cookies, authorization headers, personal identifiers, payload bodies, filesystem home paths, and production data unless the user explicitly authorizes their necessity.
- Use synthetic or minimized representative data. Do not copy production data into a test packet by convenience.

## Storage and access

- Keep local artifacts under the packet's `artifacts/` directory with restrictive permissions when sensitive.
- Store credentials only through the platform/repository secret mechanism; never in packet documents, commands, screenshots, or agent briefs.
- Give children only the artifact paths and credentials required for their bounded task. Record access in the agent/resource ledger.
- Do not commit, upload, attach, or share packet artifacts without separate authority and a redaction review.

## Retention and teardown

Record an owner, reason, and removal trigger for large or sensitive artifacts. Retain first-failure evidence through repair and acceptance. After acceptance, keep durable summaries and hashes; delete or move sensitive raw artifacts through a recoverable, explicitly authorized cleanup. Verify browser profiles, simulator/device state, VMs, containers, databases, ports, processes, and credentials are released or revoked.

If adequate proof requires prohibited sensitive collection, mark the cell `BLOCKED` and ask for authority or a safer oracle.
