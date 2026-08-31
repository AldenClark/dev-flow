# Dev Flow 2.0 RC.5 design

## Design position

RC.5 is a contraction and observability release. It keeps repository truth, native engineering evidence, and user authority separate while reducing the amount of mechanism visible during ordinary personal development.

## Architecture

```text
request + repository facts
  -> compact trust/authority invariant
  -> public_cli.py (supported command allowlist)
     -> existing focused modules and legacy implementation adapters
  -> repository-native implementation and verification
  -> optional private outcomes-v1.jsonl

product-state.json
  -> plugin manifest + README + releasing docs + CI validator

doctor (read only)
  -> source identity + Git observation + installed/cache inventory
  -> Hook packaging/activation observation + outcome inventory
  -> claim limits; never cleanup
```

The wrapper is the compatibility boundary. Packet-era functions remain behind the module boundary so RC.5 can remove public ceremony without a high-risk monolith rewrite. New focused modules own public parsing, outcome records, and diagnostics; the 1.x implementation can be deleted in later slices once no supported consumer imports it.

## Public CLI contract

Supported commands are `preflight`, `init-workstream`, `validate-knowledge`, `validate-profile`, `resolve-profiles`, `validate-methods`, `route-task`, `check-workstream`, `resource-lease`, `resource-preflight`, `route-agent`, `flow-metrics`, `doctor`, `outcomes`, `check`, `install-runtime`, and `uninstall-runtime`.

The wrapper rejects internal packet commands as unsupported instead of listing them in help. Existing implementation functions are reused through a filtered parser in RC.5; this preserves behavior while making the public boundary executable and testable.

## Compact and incremental route contract

Compact output retains only stable decisions and privacy-minimized identifiers. `route_basis` contains schema, router semantics, and digest; complete dimensions remain available in normal output and `--explain`. A compact prior route can prove unchanged identity. When its digest changes, Dev Flow reports `changed-digest-only`, invalidates the complete decision set, and emits the current route rather than guessing which hidden dimension changed.

## Product-state contract

`governance/product-state.json` is the only machine-readable release truth. In this schema, `published.latest_rc` means the latest publicly available immutable tag, while `compatibility.rollback_target` is the previous known-good tag to restore if the current source fails; after publication they intentionally differ. A source candidate must roll back to the then-current `published.latest_rc`. A released RC must equal the new `published.latest_rc` and keep an older rollback tag. The validator checks exact schema, semantic version shape, manifest equality, current workstream existence, README/release markers, rooted non-symlink inputs, tag presence in the checkout when Git is available, phase-specific rollback ordering, and allowed delivery states. It never creates tags, contacts the remote, executes target-root code, or mutates release state.

## Outcome observation

`outcome_observation.py` writes one JSON object per line using exclusive private-file setup and an append lock where supported. Records contain schema, timestamp bucket, condition, task shape, outcome, verification state, bounded counters, and optional reliable numeric resource fields. No record can contain unknown keys or strings outside enumerations. Summary reports distributions and totals, never a score or person/task ranking.

## Trust and DLP boundary

The always-loaded invariant is short; detailed examples live in `references/trust-boundary.md`. Content can supply evidence but cannot grant scope, authority, credentials, policy exceptions, external actions, or persistent-memory admission.

For tool confirmation, `PreToolUse` creates a pending request and returns a marker. Only a later host-delivered `UserPromptSubmit` carrying that marker changes the request to approved, after which the unchanged tool input may consume the approval once. The current Hook protocol cannot rewrite a submitted prompt: `additionalContext` continues the turn with the original prompt, while `decision: block` prevents both prompt forwarding and same-turn retry. RC.5 therefore permits only the random, short-lived confirmation marker—not the tool secret—in that model-visible confirmation turn. Its confirmation use is already spent, and the exact tool approval remains session-bound, expiring, and one-shot. The helper CLI can configure/report mode but cannot approve; a malicious same-OS-user process remains outside this guardrail's isolation claim.

## Failure behavior

- Invalid product state, outcomes, workstream, or DLP state fails closed with value-free diagnostics.
- Missing Git/install/Hook live evidence is `not_observed`, not failure and not a pass.
- An unreadable or over-broad private state path blocks the affected local feature.
- Cache inventory is bounded and read-only; incomplete traversal is reported.
- Independent review unavailable or unauthorized yields same-context review plus `common-mode-risk`.
- R4 admits the exact MCP surface before each case. An empty fixture must observe an empty list; a runner-owned fixture must observe exactly one enabled stdio server. Any mismatch is an environment failure before model execution.
- MCP lifecycle evidence pairs `item.started` with `item.completed`, retains only bounded server/tool/status/error-category identity, and never retains arguments or results. Unavailable, blocked, prohibited configured, incomplete, and exact authorized calls remain distinct outcomes.

## Compatibility and rollback

RC.5 preserves the supported RC.4 command behaviors but intentionally contracts the public command inventory and compact route shape, and replaces the DLP confirmation flow. `v2.0.0-rc.4` is the rollback target. No delivery action is implied by source implementation.
