# Evidence privacy and retention

Collect the minimum evidence needed for the claim. Treat logs, screenshots, traces, network captures, crash dumps, databases, simulator/device contents, benchmark data, and reports as potentially sensitive.

Before collection, classify public/internal/confidential/credential-bearing/personal. Prefer targeted excerpts, structured summaries, hashes, and canonical paths over bulk copies. Use synthetic/minimized data and redact secrets, tokens, cookies, authorization headers, personal identifiers, payload bodies, and production data.

Keep local artifacts under the active packet with restrictive permissions when sensitive. Never put credentials in packets, commands, screenshots, profiles, briefs, or source; use the platform/repository secret mechanism. Do not commit, upload, attach, or externally share artifacts without separate authority and redaction review.

Record artifact owner, purpose, sensitivity, access, retention, and removal trigger. Preserve first-failure evidence through repair and acceptance. Release browsers, devices, VMs, containers, databases, ports, processes, caches, and temporary credentials. If adequate proof requires prohibited collection, mark the cell `BLOCKED` and request authority or a safer oracle.
