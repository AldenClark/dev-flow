# Dev Flow 2.0 RC.5 requirements

## Outcome

RC.5 makes Dev Flow a quieter, inspectable personal AI programming assistant: one truthful product state, a narrow supported command surface, compact decision output, local privacy-safe outcome observation, and explicit trust and authority boundaries.

## Confirmed context

- The version owner defined the new source version as `2.0.0-rc.5` and authorized design plus local implementation on 2026-08-31.
- `v2.0.0-rc.4` exists at the current baseline and is the latest published rollback tag; RC.5 is not yet committed, tagged, installed, or published.
- Existing personal-mode DLP changes are user-owned work in progress. RC.5 must preserve their intent while replacing agent-mediated approval with a real `UserPromptSubmit` confirmation event.
- No commit, push, tag, release, installation, external model campaign, or independent reviewer dispatch is authorized by this workstream.

## Required behavior

<!-- requirement: RC5-STATE -->
1. One machine-readable product-state record owns source candidate, latest published RC, stable version, rollback target, and delivery status. Maintained release surfaces must be validated against it.
<!-- requirement: RC5-CLI -->
2. The public CLI exposes only current 2.0 operations. Packet-era lifecycle commands remain importable internal residue only until deletion and are absent from help and compatibility tests.
3. `route-task --compact` returns decisions, selected/blocked method IDs, review disposition, knowledge action, and a route-basis digest without replaying the explanatory envelope or free-form facts.
4. Incremental comparison accepts both complete and compact prior routes. Digest-only changes trigger conservative full recalibration without invented field-level deltas.
<!-- requirement: RC5-CONTEXT -->
5. Ordinary static context and aggregate descriptions have target budgets below their hard caps. Validation warns before saturation and fails at the cap.
<!-- requirement: RC5-OBSERVE -->
6. A read-only doctor reports source/install/Hook/cache/outcome state and explicit claim limits without deleting, loading secrets, or claiming live activation it did not observe.
7. Outcome observation is local, opt-in, append-only, bounded, private by default, and accepts only enums/counts. It stores no prompt, title, transcript, path, source, secret, person, session, stable user, or free-form note and emits no productivity/composite score.
<!-- requirement: RC5-TRUST -->
8. Repository, web, tool, task-history, memory, and retrieved content are untrusted data, never authority. Provenance must survive summarization; lost provenance blocks consequential sinks or requires trusted confirmation.
<!-- requirement: RC5-DLP-MEMORY -->
9. A confirmable tool secret is released only after the user submits an exact short-lived marker through `UserPromptSubmit`; an agent-accessible local approve command cannot confer approval.
10. Persisted personal engineering preferences remain explicit, scoped, attributed, expiring, correctable, and non-authoritative. Inferred cross-task preference storage is forbidden.
<!-- requirement: RC5-AGENT -->
11. Single-agent execution remains the default. Parallel dispatch requires useful decomposability and independence; sequential/tool-dense work does not become multi-agent merely because it is large.
<!-- requirement: RC5-CI -->
12. CI removes repeated diagnostic loops, validates the canonical product state and compatibility inventory, and retains focused cross-platform coverage for platform-sensitive code.

## Evidence and claim boundaries

- Deterministic tests can establish schema, parser, privacy, compatibility, and oracle behavior on current local bytes.
- Same-context review is not independent review and must retain `common-mode-risk`.
- No local result establishes population productivity, live account Hook activation, hosted compatibility, publication, installation, or real-world outcome improvement.

## Out of scope

- A task database, ambient transcript miner, user/agent score, telemetry upload, raw dogfood corpus, or hidden long-term memory.
- Automatic cache cleanup, process termination, destructive resource reclamation, or primary-profile mutation.
- Removing all packet-era implementation in one risky rewrite; RC.5 contracts the supported boundary first.
- Live model qualification, commit, tag, push, release publication, or installation.
