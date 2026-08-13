# Design for quality-kernel-continuity-knowledge-20260812

[Manifest](./manifest.json)

## Decision

Adopt `quality-kernel-v1` for newly created persistent-mutation packets: a compact always-on quality spine supplies durable semantics, exact authority binding, recoverable execution state, complementary verification, final challenge, and knowledge disposition, while provisional routing adds only applicable specialist depth.

## Repository facts and constraints

- The [plugin manifest](../../../.codex-plugin/plugin.json) exposes the Skill tree as a Codex plugin.
- The [capability registry](../../../governance/capability-contracts.json) is the machine-readable ownership and routing inventory.
- The [orchestrator Skill](../../../skills/dev-flow/SKILL.md), [lifecycle implementation](../../../skills/dev-flow/scripts/dev_flow.py), and [hook](../../../hooks/dev_flow_hook.py) jointly implement process guidance, durable packet state, and early mutation guards.
- The [contract-check runner](../../../evals/run_contract_checks.py) and focused unit suites are the repository's native verification surfaces.
- Runtime packets are repository-local and ignored; tracked documentation must not depend on raw local logs to remain understandable.

## Engineering preferences applied

Use repository-native Python/Markdown/JSON, existing lifecycle/event/digest seams, explicit failure states, no new dependency, no composite score, and no universal loading of all installed Skills. Preserve user-owned dirty work, existing evaluation repairs, legacy packet behavior, privacy boundaries, and independent delivery authority.

## Architecture and failure behavior

This tracked document is the authoritative sanitized design baseline; the manifest binds its exact bytes and the new quality-tagged lifecycle packet must adopt those same bytes. The SC and VO declarations therefore have one stable meaning across tracked knowledge and runtime approval. `TD-*` labels below are elaboration only and do not extend the authoritative scope or verification sets. The earlier change-set-only packet remains legacy execution history rather than current design authority.

Instruction mapping: INS-1 makes development-process quality primary; INS-2 makes documentation and knowledge a first-class authority; INS-3 requires recovery from context loss without prescribing a timer; INS-4 requires constructive and adversarial self-challenge across phases; INS-5 requires applicable technical guidance, black-box/white-box testing, coherent slices, team bindings, and useful comments; INS-6 preserves privacy, compatibility, user-owned work, and separate delivery authority.

### 1. Always-on quality kernel with additive routing

Every persistent mutation receives a small non-optional kernel: requirement/source traceability, stable AC/SC/VO identity, design binding, semantic continuity, separate black-box and white-box accountability, cross-phase challenge, knowledge disposition, and evidence-based final claims. Routing adds bounded capability owners; it cannot remove the kernel after a low-risk classification.

### 2. Semantic recovery rather than timer-driven rereading

The lifecycle packet records a digest-bound checkpoint over the requirement revision, approved design, engineering context, declared-root identity, Git HEAD and full worktree summary, active IDs, current objective, last evidence, next safe action, stop conditions, and drift disposition. OPEN triggers permit expected same-slice edits after a cheap identity/HEAD check; resume classifies them as reconciliation-required. SEALED handoff or claim boundaries freeze the full worktree and later byte changes block. A changed HEAD needs an explicit old-to-new review plus the exact accepted root/OID, so ordinary resume cannot silently replace the implementation premise. Non-Git roots are recorded as mechanically unobservable rather than falsely verified.

### 3. Three-plane knowledge system

Tracked current truth answers what is true now, tracked change dossiers preserve what a change meant and proved, and ignored runtime evidence supports local recovery. A standard-library validator checks containment, declared files, backlinks, traceability IDs, separate test accounting, knowledge disposition, local links, common placeholders, machine-local paths, and secret-like values. Semantic correctness and promotion remain review decisions.

### 4. Repository-specific engineering context

Context discovery records repository instructions, profiles, controls, path-specific artifact facts, installed specialist capabilities, provenance, collisions, and a fingerprint. Guidance is admitted as advisory or policy according to its authority. Unknown or conflicting coverage is surfaced rather than silently treated as safe.

### 5. Evidence-shaped implementation and collaboration

Work is split into coherent slices with a focused oracle, then broader integration and smoke evidence. Team briefs bind base/worktree, requirement and design identity, engineering-context fingerprint, AC/SC/VO ownership, exclusive paths, shared resources, black-box and white-box obligations, report shape, and stop conditions. Independent challenge occurs at requirements, design, implementation, tests, and final diff boundaries.

## Alternatives

| Decision | Alternative not selected | Reason |
|---|---|---|
| TD-1: universal quality kernel | Depend entirely on conditional routing | A false-negative risk classification would silently remove the very controls intended to detect hidden risk. |
| TD-2: semantic recovery triggers | Reread all documents on a fixed schedule | Cadence is a proxy for staleness; digest and lifecycle triggers target actual loss of meaning with less ritual. |
| TD-3: three authority planes | One universal packet directory or only two tracked layers | Current truth, change history, and raw recovery evidence have different authority, retention, and privacy needs. |
| TD-4: capability-derived topology | Treat twelve Skills as a permanent quality invariant | Capability coverage and clear ownership matter; a fixed count blocks evidence-backed evolution and can hide overlap. |
| TD-5: separate test views | A generic instruction to add tests | Boundary behavior and internal failure/state paths expose different omission classes and need explicit accounting. |
| TD-6: thin structural checks | Composite weighted quality scoring | Mechanical checks can catch contract violations, while prose quality and test adequacy require evidence-based review rather than pseudo-precision. |

## Product and UX contract

There is no application UI change. The workflow user receives explicit requirement/design truth, recovery state, test accountability, and knowledge status; no rendered UX or accessibility artifact is applicable.

## Requirement baseline and reopening

Revision 1 of the exact tracked requirements file is authoritative. AMB-1 through AMB-5 are disposed. A later user correction or material semantic/scope conflict reopens only affected AC/SC/VO, invalidates dependent approval/checkpoint evidence, and requires a fresh exact-byte approval cycle.

## Dependency decisions

No library, tool, runtime, service, plugin, manifest graph, or lockfile dependency is added, updated, removed, installed, or enabled.

## Change scope

- **SC-D1:** Update the Dev Flow, Requirements Design, Repository Context, Architecture Decisions, Verification, Change Review, Delivery Readiness, profile, and maintainer contracts needed to expose the quality spine, specialist binding, engineering habits, testing, comments, collaboration, and knowledge lifecycle without copying full specialist policy.
- **SC-D2:** Update routing, packet initialization, approval binding, validation, transition, resume/checkpoint behavior, readiness, and hooks for `quality-kernel-v1`, exact design digest, route/context snapshots, continuity, test accountability, commit-ready, and knowledge disposition.
- **SC-D3:** Add tracked-knowledge validation/templates and update packet templates, README, public docs, agent configs, and industry-practice mapping for source-chain requirements, design, implementation, verification, current truth, change history, ADR supersession, privacy, comments, and team handoffs.
- **SC-I1:** Update deterministic route, packet, hook, knowledge, engineering-context, test-practice, legacy, workflow, contract, plugin, maintainer-budget, and documentation tests, including fail-closed counterexamples.
- **SC-C1:** A target repository creates or updates tracked project/change knowledge only when the change records `current` or `history` impact and the user has mutation authority; an established repository documentation convention takes precedence over the default path.
- **SC-P1:** Preserve old packet validation, accepted history, evaluation-policy behavior and repaired atomic contracts, owner boundaries, personal-versus-team authority, user dirty work, installed runtime separation, and exact delivery authority.
- **SC-O1:** No live model run, new evaluator/score, external dependency, automatic semantic doc generation, vector/graph search, docs site, bulk old-packet migration, or automatic archive/move.
- **SC-L1:** Local source, tests, tracked design documentation, and ignored packet state only; no commit, push, PR, tag, release, deployment, installation, or external message.

## Verification obligations

- **VO-1:** Deterministic routing and engineering-context tests prove persistent mutation receives the quality spine, context, verification, root challenge, provisional rerouting, collision visibility, neutral capability selection, and conservative specialist escalation; absent caller flags cannot count as negative evidence.
- **VO-2:** Packet/approval/resume tests prove exact governed design binding, continuity and context freshness, final-diff drift rejection, open-ambiguity blocking, test/commit/knowledge disposition, and old-packet compatibility.
- **VO-3:** Hook tests prove active tagged packets inject the short recovery state and reject mechanically stale/invalid mutation or completion without guessing prose semantics.
- **VO-4:** Knowledge validator and template tests prove authority separation, safe paths/links, stable records, promotion rules, privacy exclusions, black-box/white-box accountability, and no automatic semantic publication.
- **VO-5:** The complete evaluation suite, contract checks, plugin check, maintainer budget, compile checks, relative-link checks, diff checks, and changed-file accounting pass on final bytes.
- **VO-6:** Independent blue and red reviewers verify requirement fidelity, integration, proportionality, bypass resistance, compatibility, privacy, knowledge authority, testing/comment/team obligations, and residual limits.

## Testing and implementation strategy

Implement in coherent slices that keep behavior, black-box and white-box regressions, necessary documentation, and why/invariant comments together. Run the cheapest focused oracle first, then packet/hook/knowledge/contract/module checks, the complete suite, static validators, and an independently frozen blue/red review. Preserve first failures and do not convert an unrun live-model, installation, or delivery gate into a pass.

## Compatibility, rollout, rollback, and cleanup

- Quality-tagged persistent mutation fails closed when requirements, design, engineering context, repository identity/HEAD, checkpoint, knowledge disposition, or event projection is missing or stale. Full worktree evidence is evaluated at recovery, handoff, slice, verification, and final-claim boundaries rather than rehashed on every edit. Error output distinguishes an open-slice delta needing review from sealed-boundary drift.
- Legacy packets remain on their prior validation path; they do not receive false claims that the new kernel was applied.
- Specialist discovery is bounded and provenance-aware. Missing, conflicting, or inapplicable guidance produces a neutral recorded outcome or blocker according to risk, not fabricated compliance.
- Knowledge validation never generates, promotes, migrates, or rewrites documents. Invalid paths, links, inventory, privacy patterns, or lifecycle combinations return concrete errors.
- Rollback is a cohesive source revert of the new kernel and knowledge-system behavior while retaining recoverable tracked history. Physical rollback is outside this task's authority.
- Black-box validation covers public CLI, hook, routing, compatibility, and validator outcomes. White-box validation covers digests, branches, event bindings, containment, symlinks, failure states, lifecycle transitions, and drift. Test code and final changes receive independent challenge before acceptance.

## Approval record

The user statement `我同意，请实施到位` approves this integrated local design and SC-D1, SC-D2, SC-D3, SC-I1, and SC-C1 while preserving SC-P1, SC-O1, and SC-L1. It does not authorize dependencies, commit, push, PR, installation, release, deployment, migration execution, or external messaging.

[Current Dev Flow governance](../../project/dev-flow-governance.md)
