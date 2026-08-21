---
name: dev-flow
description: "Use for repository engineering: diagnose/fix bugs, change behavior or architecture, design or change public contracts, data lifecycles, review/verify changes, and assess delivery—especially cross-module, persistent-data, concurrency, migration, external-system, or long-running work."
---

# Dev Flow

Optimize for the requested business outcome, not process artifacts.

## Start

1. Confirm action and authority; implementation does not imply commit, push, publish, deploy, migrate, install, or external communication.
2. Resolve Git roots, instructions, current behavior, user changes, and affected paths. Use `repo-context` when unclear.
3. Identify the primary intent: research, diagnosis, design, change, review, or delivery. Research gathers or compares facts without defect judgment; review evaluates a target and reports verified findings. An explicit audit or review remains review intent even when its subject is a proposed design, architecture, migration, or delivery plan. Intent selects capability owners; it is not a lifecycle tier.
4. Calibrate business meaning, uncertainty, boundaries, consequences, native evidence, and durable knowledge impact without an artifact.
5. Classify requirement understanding as U1 semantic creation/change, U2 structural adjustment, U3 defect correction, U4 mechanical, or U5 read-only. U1 publishes a detailed technology-neutral understanding and stops in Default mode for explicit confirmation before technical design; an established defect or mechanical edit does not acquire that stop. Already-confirmed U1 semantics remain U1: pass `--understanding-confirmed` and continue, never downclassify them to U2 merely to avoid another stop. Use `requirements-design` for the full contract.
6. Choose a base mode from continuity needs:
   - `direct`: default for ordinary changes, bounded fixes, research, reviews, spikes, and one coherent slice;
   - `managed`: multi-session/slice, cross-module/repository/team work, material design trade-offs, or a durable-plan/handoff request.
7. Identify overlays from repository facts and the request: security/privacy, migration/data, external system, release/delivery, irreversible, or UI/product.
8. Run the ephemeral capability-activation pass from current request/repository evidence and the effective Codex surface. Load only specialists that own real decisions or evidence.

After repository discovery and before technical design or implementation, one compact `route-task` is mandatory when Dev Flow was invoked explicitly, the work is or may become managed, the scope crosses modules or repositories, the change affects persistent data/deletion/migration/concurrency/external systems, the user requests a complete audit/red-blue/delivery certification, or a failure breaks the current assumptions. Do not replace this inspectable activation step with informal method reasoning or specialist loading. Run the route as a standalone command, never chained with repository inspection, and continue only after its JSON says `"status": "routed"`; after an invalid result, use its exact `corrected_command` at most once instead of guessing new flags.

Use the smallest copyable canonical form that preserves the known facts, adding only observed risks or needs:

```bash
python3 <dev-flow-skill-dir>/scripts/dev-flow.py route-task --intent change --requirement-class defect-correction --risk concurrency --need diagnosis --need verification --compact
```

Continuity facts are part of the route contract: when the request says multi-session, multi-slice, cross-module, coordinated, materially traded-off, or durable-plan work, pass the matching `--multi-session`, `--multi-slice`, `--cross-module`, `--coordination`, `--material-tradeoff`, or `--durable-plan` flag. Do not accept a `direct` result caused by omitting a known continuity fact and then silently escalate to managed work afterward.

Canonical requirement classes are `semantic-change`, `structural-adjustment`, `defect-correction`, `mechanical`, and `read-only` (`U1`-`U5` are accepted aliases). When the request or a prior turn already contains explicit confirmation of a complete U1 understanding, keep `--requirement-class semantic-change` and add `--understanding-confirmed`; use `--waive-understanding-confirmation` only for an explicit waiver. Confirmation changes the gate state, not the requirement class. Canonical `--need` values are `requirements`, `architecture`, `dependency`, `diagnosis`, `verification`, `review`, and `delivery`; the corresponding specialist Skill names such as `requirements-design` and `systematic-debugging` are accepted aliases. Common material risks include `ffi`, `concurrency`, `persisted-data`, `data-deletion`, `schema`, `public-api`, `version-compatibility`, `rollback`, `security`, `privacy`, `external-write`, `recovery`, `backpressure`, and `weak-tests`. Repository facts, when needed for specialist matching, use repeatable `--repo-fact key=value`; do not pass prose facts. If the runner is unavailable, state the equivalent manual route and limitation before continuing. Re-run only after a material boundary or evidence change. The route remains optional only for a one-line mechanical change, narrow read-only lookup, or local defect with a known oracle; these narrow exceptions override explicit invocation. It never creates or activates a packet.

When a route runs, show its non-persisted decision in one compact commentary update: intent, mode, specialists, method, and independent-review disposition.

## Continuity

Direct work creates no Dev Flow state or continuity document. Update maintained truth when stale. Add a concise repository-native change record only when code, tests, an issue, changelog, ADR, or maintained docs do not preserve durable behavior or rationale; without a repository convention, use `docs/change-notes/<slug>.md` and `templates/change-record.md`.

For managed work, follow the repository's own convention. If none exists, initialize:

```text
docs/workstreams/<slug>/
|-- implementation.md
|-- progress.md
|-- requirements.md     # conditional complex semantics
|-- design.md           # conditional trade-offs
`-- decisions.md        # conditional; use ADRs first
```

`implementation.md` holds scope, acceptance, outcome slices, ordering, affected areas, and native completion evidence. `progress.md` is the human-agent handoff: status, completed/current/next outcomes, blockers, and evidence limits. Add `requirements.md` only when enough confirmed complex or cross-team semantics exist to preserve beyond the request/issue; an unknown product baseline, unanswered questions, or a request not to invent semantics belongs as a blocker/current slice in the two core documents and does not justify a stub requirements file. Add `design.md` for real trade-offs and `decisions.md` for durable decisions without an ADR home. `init-workstream` creates only the first two by default.

At start or resume, read and reconcile the workstream with the current Git root, worktree, changed paths, and parallel changes before continuing. Update progress at design/scope change, slice completion, blocker, new boundary, assumption-breaking first failure, interruption/handoff, or closure. Before yielding an incomplete slice, leave the minimum handoff: done, current, next, blockers or unrun gates, and worktree/parallel-change state. Git owns chronology; prose does not copy commands, logs, hashes, test output, tool activity, or source schemas.

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

## Multi-agent work

Single-agent execution is the baseline. Delegate for credible isolation or independent-context value, and run `route-agent` before dispatch. Brief objective/outcome, context, owned/read-only scope, checks/resources, stop condition, and return. Root reconciles the diff and reruns affected checks. Do not require packet IDs, fingerprints, AC/SC/VO, reports, leases, or lifecycle transitions unless the repository does.

Routing requires independent review for explicit material exposure or review need, intrinsically consequential deletion/public-contract/rollback compatibility, and cross-system durable acceptance; other risks remain exposure-calibrated. A review requirement never grants delegation authority. Pass `--independent-review-authorized` only when the current request and host policy affirmatively authorize dispatch; without it, the route returns `execution=explicit-downgrade` and no `route_agent`. When routing returns an authorized reviewer route, use a clean-context reviewer through `route-agent` only after a successful dispatch. A real independent review requires a non-empty reviewer/receiver identity and a returned review result. Never call `wait` or poll unless that reviewer was actually dispatched; an empty receiver list, empty agent state, self-review, reread, or blue/red pass proves that no independent review occurred. If dispatch is unavailable, unauthorized, or returns no reviewer identity, explicitly downgrade the claim before reviewing: perform the strongest available same-context review, label its findings same-context, and report `common-mode-risk`. Same-context work is never independent review. Never describe that work as independent or clean-context review.

## Close

Recheck knowledge impact before closing. For direct work, update current truth and keep a change record only when it adds durable information. For managed work, update workstream documents to current truth and do not create a duplicate change record. Report outcomes, fresh evidence, residual risk, unrun real-world gates, and explicit delivery boundaries without a packet closeout or evidence ledger.

Load linked references only for affected lifecycle, continuity, quality, native, or knowledge decisions. Methodology uses progressive disclosure of bounded methods. 1.x packet material is unsupported internal residue and never part of a 2.0 task.
