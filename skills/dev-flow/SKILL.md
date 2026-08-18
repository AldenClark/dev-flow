---
name: dev-flow
description: Deliver repository work with Default-mode semantic confirmation, direct or managed continuity, proactive specialist/method/model routing, native evidence, and explicit authority boundaries.
---

# Dev Flow

Optimize for the requested business outcome, not process artifacts.

## Start

1. Confirm action and authority; implementation does not imply commit, push, publish, deploy, migrate, install, or external communication.
2. Resolve Git roots, instructions, current behavior, user changes, and affected paths. Use `repo-context` when unclear.
3. Identify the primary intent: research, diagnosis, design, change, review, or delivery. Research gathers or compares facts without defect judgment; review evaluates a target and reports verified findings. An explicit audit or review remains review intent even when its subject is a proposed design, architecture, migration, or delivery plan. Intent selects capability owners; it is not a lifecycle tier.
4. Calibrate business meaning, uncertainty, boundaries, consequences, native evidence, and durable knowledge impact without an artifact.
5. Classify requirement understanding as U1 semantic creation/change, U2 structural adjustment, U3 defect correction, U4 mechanical, or U5 read-only. U1 publishes a detailed technology-neutral understanding and stops in Default mode for explicit confirmation before technical design; an established defect or mechanical edit does not acquire that stop. Use `requirements-design` for the full contract.
6. Choose a base mode from continuity needs:
   - `direct`: default for ordinary changes, bounded fixes, research, reviews, spikes, and one coherent slice;
   - `managed`: multi-session/slice, cross-module/repository/team work, material design trade-offs, or a durable-plan/handoff request.
7. Identify overlays from repository facts and the request: security/privacy, migration/data, external system, release/delivery, irreversible, or UI/product.
8. Run the ephemeral capability-activation pass from current request/repository evidence and the effective Codex surface. Load only specialists that own real decisions or evidence.

`route-task` is an optional deterministic aid; it never creates or activates a packet.

## Continuity

Direct work creates no Dev Flow state or continuity document. First update maintained architecture, product rules, contracts, runbooks, and user or operational truth when the change makes them stale. When no existing home captures a durable behavior or non-obvious rationale, add one concise repository-native change record; if the repository has no convention, use `docs/change-notes/<slug>.md` and `templates/change-record.md`. Do not create a record when code, tests, an issue, changelog, ADR, or maintained docs already preserve everything a future maintainer needs.

For managed work, follow the repository's own convention. If none exists, initialize:

```text
docs/workstreams/<slug>/
|-- implementation.md
|-- progress.md
|-- requirements.md     # conditional complex semantics
|-- design.md           # conditional trade-offs
`-- decisions.md        # conditional; use ADRs first
```

`implementation.md` holds scope, acceptance, outcome slices, ordering, affected areas, and native completion evidence. `progress.md` is the human-agent handoff: status, completed/current/next outcomes, blockers, and evidence limits. Add `requirements.md` for complex or cross-team semantics beyond the request/issue, `design.md` for real trade-offs, and `decisions.md` for durable decisions without an ADR home. `init-workstream` creates the first two by default.

Update progress only at design/scope change, slice completion, blocker, handoff, or closure. Git owns chronology; prose does not copy commands, logs, hashes, test output, tool activity, or source schemas.

## Quality spine

Without a file, establish the outcome, facts/assumptions, affected business/trust/data/compatibility/dependency/operational/UI/delivery boundaries, smallest slice/native oracle, durable knowledge impact, and evidence limits. Recalibrate after scope/design change, a new boundary/dependency, assumption-breaking or repeated failure, or delivery/irreversibility. Read `references/quality-calibration.md` for substantial managed work, material risk, delegation, or repeated failure.

After initial repository discovery and after material requirement confirmation, use `references/quality-calibration.md` to consider four independent decisions: applicable specialist Skill, bounded method, independent review, and child model/effort. Recheck only an affected decision after a new boundary, assumption-breaking failure, repeated failed hypothesis, final-diff exposure, or imminent delivery/irreversibility. Do not persist activation decisions.

When an affected claim needs AGENTS inspection, native review, an explicitly requested Goal, worktree isolation, UI/device evidence, or external context, use `references/codex-native-adapters.md`. Its adapters are trigger-based and optional; never enable host experiments or mutate global configuration to satisfy the flow.

## Execute

1. Clarify only ambiguity that changes business behavior, scope, irreversible consequences, or external authority. For U1, publish the complete requirement-understanding result and end the turn for confirmation before design. Stay in Default mode and follow `../requirements-design/references/user-interaction.md` for user-owned decisions.
2. For a bug or unexplained failure, use `systematic-debugging` to reproduce and prove the earliest actionable cause before repair.
3. Treat an explicit review-and-fix request as change intent with a review need: diagnose and implement first, verify the final bytes, then use `change-review` against the final diff.
4. Use `architecture-decisions`, `dependency-decisions`, or `product-ux-discovery` only when their decisions are actually present.
5. Implement the smallest coherent slice; align code, tests, generated surfaces, comments, and maintained docs.
6. Run focused checks first, then affected module/integration/risk checks. Preserve the first failure and distinguish `PASSED`, `FAILED`, `FLAKY`, `BLOCKED`, `NOT RUN`, and `WAIVED`.
7. Inspect the final diff for intent, scope, user changes, dependencies, generated files, secrets, stale comments/docs, and untested claims.

Code, Git, native tests, CI, runtime checks, and release artifacts own technical evidence. Workstream prose never substitutes for them.

## Risk overlays

- Security/privacy: trust/abuse boundaries, focused tests, and review for material exposure.
- Migration/data: compatibility, ordering, resumability, observation, restore/rollback, and cleanup.
- External system: contracts, idempotency, timeout/retry, reconciliation, and separated real-system evidence.
- Release/delivery: exact target/artifact, provenance, rollback, authority, and post-action evidence.
- Irreversible: exact targets, recovery assets, and immediate confirmation.
- UI/product: intent, complete states, accessibility, and affected rendered surfaces.

An overlay adds only its relevant controls. It does not force managed mode, a packet, an independent agent, or a fixed document set.

## Advanced quality

Use `references/quality-calibration.md` to discover applicable effective-host Skills from repository technology/risk evidence, actively match bounded methods at concrete high-leverage failure mechanisms, route every actual child through P0-P6, and select independent review by exposure/consequence/evidence. These are non-persisted decisions. Prefer the simplest capable workflow and escalate only when the signal justifies its cost.

## Multi-agent work

Single-agent execution is the baseline. Delegate for credible isolation or independent-context value, and run `route-agent` before dispatch. Brief objective/outcome, context, owned/read-only scope, checks/resources, stop condition, and return. Root reconciles the diff and reruns affected checks. Do not require packet IDs, fingerprints, AC/SC/VO, reports, leases, or lifecycle transitions unless the repository does.

## Close

Recheck knowledge impact before closing. For direct work, update current truth and keep a change record only when it adds durable information. For managed work, update workstream documents to current truth and do not create a duplicate change record. Report outcomes, fresh evidence, residual risk, unrun real-world gates, and explicit delivery boundaries without a packet closeout or evidence ledger.

Read `references/core-lifecycle.md` for the operating model, `references/orchestration.md` for managed work, `references/quality-calibration.md` for quality triggers, `references/codex-native-adapters.md` for affected native surfaces, and `references/knowledge-system.md` for repository knowledge. Methodology and legacy packet details use progressive disclosure; packet material is compatibility-only.
