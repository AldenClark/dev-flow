---
name: dev-flow
description: "repository engineering: diagnose/fix bugs; change behavior or architecture; design or change public contracts, data lifecycles; review/verify changes; assess delivery; cross-module/persistent-data/concurrency/migration/external-system/long-running work. Exclude narrow read-only."
---

# Dev Flow

Optimize for the requested business outcome, not process artifacts.

## Negative trigger

For narrow Git history, authorship, path, or file-fact lookups, use `repo-context` alone; do not run `route-task`; do not sustain Dev Flow. Re-enter only for material mutation, cross-boundary diagnosis/design, managed continuity, or high-risk delivery.

## Start

1. Confirm action and authority; implementation does not imply commit, push, publish, deploy, migrate, install, or external communication.
2. Resolve Git roots, instructions, current behavior, user changes, and affected paths. Use `repo-context` when unclear.
3. Identify the primary intent: research, diagnosis, design, change, review, or delivery. Research gathers facts without defect judgment; review judges a target. An explicit audit or review stays review intent even for a plan or design. Intent selects owners, not a lifecycle tier.
4. Calibrate business meaning, uncertainty, boundaries, consequences, native evidence, and durable knowledge impact without an artifact.
5. Classify requirement understanding as U1 semantic creation/change, U2 structural adjustment, U3 defect correction, U4 mechanical, or U5 read-only. U1 publishes a detailed technology-neutral understanding and stops in Default mode for explicit confirmation before technical design; an established defect or mechanical edit does not acquire that stop. Already-confirmed U1 semantics remain U1: pass `--understanding-confirmed` and continue, never downclassify them to U2 merely to avoid another stop. Use `requirements-design` for the full contract.
6. Choose a base mode from continuity needs:
   - `direct`: default for ordinary changes, bounded fixes, research, reviews, spikes, and one coherent slice;
   - `managed`: multi-session/slice, cross-module/repository/team work, material design trade-offs, or a durable-plan/handoff request.
7. Identify overlays from repository facts and the request: security/privacy, migration/data, external system, release/delivery, irreversible, or UI/product.
8. Run the ephemeral capability-activation pass from current request/repository evidence and the effective Codex surface. Load only specialists that own real decisions or evidence.

A named reference repository or source is non-authoritative unless explicit scope and repository confirmation establishes a shared edge. Read it, compare target facts, and state differences/authority. Unconfirmed analogy cannot impose a contract; confirmed authority applies only to the confirmed edge. Choose everything else from target truth. If evidence lacks, abstain with the comparison and limitation; never omit it or infer mutation scope.

After repository discovery and before technical design or implementation, one compact `route-task` is mandatory for explicit Dev Flow, managed/cross-boundary work, persistent data/deletion/migration/concurrency/external systems, complete audit/red-blue/delivery certification, or assumption-breaking failure. Do not replace this inspectable activation step with informal reasoning. Run the route as a standalone command; continue only when its JSON says `"status": "routed"`; after an invalid result, use its exact `corrected_command` at most once.

Use the smallest copyable canonical form that preserves the known facts, adding only observed risks or needs:

```bash
python3 <dev-flow-skill-dir>/scripts/dev-flow.py route-task --intent change --requirement-class defect-correction --risk concurrency --need diagnosis --need verification --compact
```

Continuity facts are part of the route contract: when the request says multi-session, multi-slice, cross-module, coordinated, materially traded-off, or durable-plan work, pass the matching `--multi-session`, `--multi-slice`, `--cross-module`, `--coordination`, `--material-tradeoff`, or `--durable-plan` flag. Do not accept a `direct` result caused by omitting a known continuity fact and then silently escalate to managed work afterward.

Requirement classes: `semantic-change`, `structural-adjustment`, `defect-correction`, `mechanical`, and `read-only` (`U1`-`U5`). Confirmed U1 stays semantic-change with `--understanding-confirmed`; explicit waiver uses `--waive-understanding-confirmation`. Confirmation changes the gate state, not the requirement class. Canonical `--need` values are `requirements`, `architecture`, `dependency`, `diagnosis`, `verification`, `review`, and `delivery`; specialist names are aliases. Common risks: `ffi`, `concurrency`, `persisted-data`, `data-deletion`, `schema`, `public-api`, `version-compatibility`, `rollback`, `security`, `privacy`, `external-write`, `recovery`, `backpressure`, and `weak-tests`. Use repeatable `--repo-fact key=value`, not prose. If the runner is unavailable, state the manual route and limitation. Re-run only after a material boundary/evidence change. Narrow read-only is excluded. Routing is optional only for a one-line mechanical change or local defect with a known oracle; these exceptions override explicit invocation. It creates no packet.

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

`implementation.md` owns scope, acceptance, slices, ordering, affected areas, and completion evidence. `progress.md` owns status, completed/current/next outcomes, blockers, and evidence limits. Add `requirements.md` only for confirmed complex semantics; an unknown baseline does not justify a stub requirements file. Add `design.md` for real trade-offs and `decisions.md` for durable rationale without an ADR home. `init-workstream` creates only the first two by default.

At start/resume/fork, reconcile workstream, Git/worktree/user changes, and terminal/non-goal/process/evidence facts; summaries are not authority. For marked RC.4, run `check-workstream --root <git-root> --path <workstream> --check-worktree` before slice completion. Update progress at material change, slice completion, blocker, first failure, handoff, or closure. Before incomplete yield, leave the semantic checkpoint in `references/quality-calibration.md`. Git owns chronology; continuity never automatically creates a host task or worktree.

## Quality spine

Calibrate outcome, facts/assumptions, affected boundaries, smallest slice/oracle, knowledge impact, and evidence limits. Keep the last route in active caller context: an unchanged narrow follow-up does not reroute; after a material transition, pass it through `--previous-route` to invalidate only affected decisions. Read `references/quality-calibration.md` for substantial managed work, material risk, delegation, or repeated failure.

After repository discovery and material requirement confirmation, use `references/quality-calibration.md` to decide specialist, method, independent review, and child route separately. Recheck only an affected decision after boundary/failure/final-diff/delivery changes; never persist activation decisions.

When an affected claim needs AGENTS inspection, native review, an explicitly requested Goal, worktree isolation, UI/device evidence, or external context, use `references/codex-native-adapters.md`. Its adapters are trigger-based and optional; never enable host experiments or mutate global configuration to satisfy the flow.

## Execute

1. Clarify only ambiguity that changes business behavior, scope, irreversible consequences, or external authority. For U1, publish the complete requirement-understanding result and end the turn for confirmation before design. Stay in Default mode and follow `../requirements-design/references/user-interaction.md` for user-owned decisions.
2. For bugs/failures, use `systematic-debugging` to prove the earliest cause. A diagnosis-only request stops there; repair only when requested.
3. Treat an explicit review-and-fix request as change intent with a review need: diagnose and implement first, verify the final bytes, then use `change-review` against the final diff.
4. Load decision specialists only for real decisions. Use `repository-knowledge` only for explicit knowledge-system work, not an ordinary nearby documentation update.
5. Keep the ephemeral scope envelope from `references/quality-calibration.md`: implementation/repair is `closed`, diagnosis/review is `bounded`, and only explicit breadth is `open`; depth never grants breadth.
6. Implement the smallest coherent slice; align code, tests, generated surfaces, comments, and maintained docs.
7. Run focused then affected checks. Preserve the first failure and do not retry unchanged invariants. After two auxiliary repairs without primary progress, simplify/defer instead of a third tweak; see the quality reference.
8. Inspect intent, admitted scope, user changes, dependencies/tools, generated files, secrets, stale docs, and untested claims; reject merely discovered optional work.

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

Single-agent execution is the baseline. Delegate for credible isolation or independent-context value, and run `route-agent` before dispatch. Brief outcome, context, owned/read-only scope, checks/resources, stop condition, and return. Root reconciles the diff and affected checks. Do not require packet IDs, fingerprints, AC/SC/VO, reports, leases, or lifecycle transitions unless the repository does.

Delegation exists only after a successful dispatch returns a non-empty child/receiver identity (a non-empty reviewer/receiver identity for review). Never call `wait` or poll unless that child was actually dispatched. An empty receiver list, empty agent state, self-work, or reread proves no delegation: report it unavailable or downgraded and never attribute a result to a child.

Routing requires independent review for explicit material exposure/review need, consequential deletion/public-contract/rollback compatibility, and cross-system durable acceptance; other risks remain exposure-calibrated. A review requirement never grants delegation authority. Pass `--independent-review-authorized` only when the request and host policy authorize dispatch; otherwise the route returns `execution=explicit-downgrade` and no `route_agent`. If dispatch is unavailable, unauthorized, or returns no reviewer identity, explicitly downgrade the claim: perform the strongest same-context review, label its findings same-context, and report `common-mode-risk`. Same-context work is never independent review or clean-context review.

## Close

Recheck knowledge impact before closing. Direct work updates current truth and adds a change record only for otherwise-lost durable information; managed work updates its workstream without a duplicate record. Bind claims to final relevant bytes and report stale evidence, residual risk, isolated blocked gates, unrun real-world gates, and explicit delivery boundaries without a packet closeout or evidence ledger.

Load linked references only for affected lifecycle, continuity, quality, native, or knowledge decisions. Methodology uses progressive disclosure of bounded methods. 1.x packet material is unsupported internal residue and never part of a 2.0 task.
