# Dev Flow 2.0 design

## Status

- State: `2.0.0-beta.3` source locally implemented and verified; uncommitted and unpublished
- Product decision: replace the 1.x packet-first default with repository-first direct and managed work
- Compatibility decision: preserve legacy packet readers and explicit maintenance commands, but legacy packets never govern 2.0 work
- Publication state: not released, not tagged, not installed

## Outcome

Dev Flow 2.0 helps Codex and developers complete the requested business change with proportionate engineering quality. It preserves long-running intent and progress in the repository while allowing ordinary work to remain ordinary.

Success means:

- routine persistent work and read-only audits create no packet or continuity document, while durable knowledge still updates its repository owner;
- long-running work maintains concise implementation/progress documents and only adds requirements/design/decision documents when their content has durable value;
- code, tests, Git, CI, runtime checks, and release artifacts remain the evidence owners for technical claims;
- risks add specific controls without changing the base continuity model;
- legacy packet state cannot block searching, editing, testing, delegation, or completion of 2.0 work;
- Dev Flow's own patch release cost is materially lower while preserving cross-platform and artifact-integrity evidence.

## Non-goals

- Replace issue trackers, source control, CI, deployment platforms, or regulated traceability systems.
- Require every repository to use the default document path or filenames.
- Prove production, device, network, account, or human acceptance through local evidence.
- Infer authority to commit, push, publish, deploy, migrate, install, or communicate externally.
- Delete old packet history or break its read/validate/archive tools in the first 2.0 release.

## Design constitution

1. Business outcomes, user semantics, and engineering quality outrank process artifacts.
2. The lifecycle is complete but elastic; task shape determines depth, not fixed phase gates.
3. Engineering capabilities intervene proactively when repository evidence exposes risk.
4. Documents provide shared continuity and durable knowledge, never proof that a prompt or method ran.
5. Git, code, tests, CI, runtime systems, and artifacts remain the owners of technical evidence.
6. Task intent, continuity mode, risk controls, and knowledge impact are independent dimensions.
7. Ordinary work produces no Dev Flow state; it may update current truth or add one decision-useful change record.
8. Hard blocking belongs to the host or a dedicated deterministic security control, not a Dev Flow process Hook.
9. Every new control needs a real failure model, a negative trigger, proportionate cost, and a removal condition.
10. Dev Flow maintenance and release follow the same marginal-value rules as product work.

## Operating model

```text
Tracked business continuity     Native engineering evidence       Minimal safety boundary
---------------------------     ---------------------------       -----------------------
design and trade-offs           code and configuration            secret disclosure
implementation slices           Git diff and history              broad destruction
outcome-based progress          tests, build, CI, runtime         external delivery
important decisions             artifacts and provenance          explicit user authority
```

No plane substitutes for another. A progress document cannot prove tests passed. A green unit test cannot prove a product decision. A local build cannot prove deployment. A Hook warning cannot grant authority.

## Task entry axes

Task entry is a small composition, not one escalation ladder:

| Axis | Values | Purpose |
|---|---|---|
| Intent | research, diagnosis, design, change, review, delivery | Select the capability owner for the requested action |
| Continuity | direct, managed | Decide whether repository-tracked implementation/progress memory is useful |
| Risk overlays | security, migration, external system, release, irreversible, UI/product | Add only failure-specific controls |
| Knowledge impact | none, current truth, direct change record, managed workstream | Preserve durable facts and rationale without process state |

One primary intent may use secondary specialists. Intent does not imply a phase transition, risk level, document set, or authority. The old mixed `task_type` vocabulary remains a compatibility input and maps explicitly to these axes.

Research collects, verifies, or compares facts without judging a target for defects. Review evaluates a stable source, change, or system boundary and returns verified findings; audit language therefore maps to review. Both are read-only. Review-and-fix is a change intent with review as a secondary need.

## Requirement understanding and confirmation

Requirement understanding is a semantic checkpoint inside design/change, not another intent or a persisted lifecycle state. After inspecting repository and product evidence, classify the work:

| Class | Meaning | Understanding and continuation |
|---|---|---|
| U1 semantic creation/change | New or materially changed product behavior, public contract, authorization, data lifecycle, user flow, integration, or migration semantics | Publish a detailed technology-neutral understanding and stop in Default mode for explicit confirmation before technical design |
| U2 structural adjustment | Refactor, dependency/configuration/performance work, or internal interface change | Publish a proportionate understanding; stop only when behavior, compatibility, operations, or another user-owned semantic can change |
| U3 defect correction | Expected behavior is established by a reproducer, test, maintained contract, or clear request | State expected/protected behavior and diagnose without a confirmation stop; upgrade to U1 when product meaning remains open |
| U4 mechanical | Exact spelling, formatting, replacement, generated synchronization, or another deterministic edit | Proceed without a requirements artifact or confirmation stop |
| U5 read-only | Research, review, or delivery assessment | Clarify a material target/scope ambiguity only; do not create a mutation confirmation flow |

A U1 understanding result covers the actual relevant subset of objective/problem, current behavior/evidence, actors/triggers/scenarios, observable outcomes and state/failure behavior, in/out scope, protected behavior, constraints/compatibility, acceptance behavior, facts/decisions/assumptions/open questions, and durable knowledge impact. It contains no premature architecture or implementation choice.

After publishing the result, end the turn. Natural language such as “确认”, “理解正确，继续”, or “按这个实施” is sufficient. A correction produces a complete revised understanding and another stop. The original request may explicitly waive the stop when it names an already accepted requirement source or directs Codex to proceed without reconfirmation. Confirmation authorizes entry into design only; it never grants dependency, destructive, delivery, commit, push, publication, installation, migration-execution, or deployment authority.

Direct work keeps the result in conversation unless durable truth needs a repository owner. Managed work writes complex or cross-team semantics into `requirements.md` or the repository-native requirement source. No approval receipt, content digest, question quota, or Plan mode is used.

## Base modes

### Direct

Direct is the default for:

- routine changes;
- bounded bug fixes;
- small features and refactors;
- dependency maintenance with a clear requested outcome;
- spikes and read-only audits;
- bounded security, performance, migration, or release work whose continuity fits one coherent session/slice.

Direct work:

- reads repository facts and effective instructions;
- clarifies only material ambiguity;
- implements the smallest coherent change;
- runs affected native verification;
- inspects the final diff and reports evidence limits;
- creates no Dev Flow state or continuity document;
- updates current truth and adds one light change record only when durable behavior or rationale would otherwise be lost.

### Managed

Managed is selected by continuity and coordination need, not by a generic risk score. Use it when one or more are true:

- work is expected to span sessions or context compactions;
- the outcome requires multiple independently useful slices;
- several modules, repositories, or teams must coordinate;
- business scope, architecture, or rollout contains material trade-offs;
- the user explicitly asks for a plan, durable design, milestone control, or handoff record.

Large features, large refactors, and substantial migrations default to managed. Other task types remain direct unless their actual shape requires managed continuity.

When a repository has no stronger convention, managed work uses:

```text
docs/workstreams/<slug>/
|-- implementation.md
|-- progress.md
|-- requirements.md     # conditional; only when semantics need a durable source
|-- design.md           # conditional; only for real trade-offs
`-- decisions.md        # conditional; only without an existing ADR home
```

The files are ordinary tracked project knowledge. They do not have manifests, hashes, lifecycle states, acceptance identifiers, generated ledgers, or a hidden authoritative copy.

`implementation.md` and `progress.md` are the minimum managed continuity surface. Duration alone does not require a design document.

## Document contracts

### Direct change record

Use the repository's convention, or `docs/change-notes/<slug>.md` when none exists. Record final behavior, affected and protected boundaries, non-obvious implementation/decision rationale, current-truth or contract impact, and verification limits. Do not create it when code, tests, an issue, changelog, ADR, or maintained docs already preserve the same knowledge. `docs/changes/<change-id>/` remains reserved for legacy 1.x dossiers.

### `requirements.md`

Create only when complex or cross-team business semantics need a durable source beyond the request, issue, or existing product documentation. Keep users/scenarios, in/out scope, observable acceptance behavior, protected constraints, and material open decisions. Do not duplicate implementation design or technical evidence.

### `design.md`

Write only when the solution contains real trade-offs. Keep:

- business outcome and non-goals;
- observed current state;
- selected design and credible alternatives;
- affected boundaries, failure behavior, compatibility, and rollout/rollback where relevant;
- material open decisions.

Do not copy source interfaces, schemas, commands, test logs, or implementation details that are better owned elsewhere.

### `implementation.md`

Maintain an outcome-oriented slice plan:

- scope, observable acceptance behavior, and protected behavior;
- slice and business/technical outcome;
- affected areas and dependencies;
- completion evidence expected from native tooling;
- ordering and real blockers.

It is not a task-event ledger. Tool calls, timestamps, fingerprints, agent attempts, and routine file edits do not belong here.

### `progress.md`

Keep one small current snapshot:

- completed outcomes;
- current slice;
- next slice;
- blockers and decisions needed;
- evidence limitations.

Update only at design change, coherent slice completion, blocker, handoff, scope change, or final closure. Replace stale current-state text; use Git history for chronology.

### `decisions.md`

Create only when several durable decisions need a compact home and the repository has no ADR convention. Each decision records context, choice, alternatives, consequences, and status. Supersede rather than erase old decisions.

## Zero-artifact quality calibration

Every task performs a brief calibration before selecting controls:

1. observable outcome and authority boundary;
2. confirmed repository facts, assumptions, and user-owned decisions;
3. affected product, trust, data, compatibility, dependency, external, operational, UI, delivery, and durable-knowledge boundaries;
4. smallest coherent slice and most sensitive native oracle;
5. whether a specialist, P0-P6 child route, bounded method, or independent review has positive marginal value.

The calibration is not written to the workstream. Re-run it after scope/design change, a new dependency or boundary, the first assumption-breaking failure, two failed repairs/hypotheses for the same symptom, slice expansion, or imminent delivery/irreversibility. Persist only durable consequences such as a changed design, slice plan, blocker, or decision.

## Advanced capability activation spine

The retained specialist Skills, engineering profiles, method pool, independent review, and model routes are useful only when realistic work reaches them. After initial repository discovery, and again after material requirement confirmation, perform one ephemeral activation pass:

1. Match current product/technology/risk evidence to an effective specialist Skill or an honest fallback.
2. At a high-leverage concrete failure mechanism, use the specialist's established method or perform one bounded method lookup.
3. Decide whether an independent context can expose a material blind spot beyond root diff inspection.
4. If child work has positive isolation/parallel value, select model and effort from closedness, breadth, uncertainty, and consequence.

The effective current-turn Codex surface is authoritative. An installed file, remembered capability, version, feature flag, or registry entry does not prove that a Skill, tool, model override, native review, Goal, browser/device surface, or worktree operation is callable. Missing optional capability degrades to a named fallback and does not block ordinary work.

Evidence sources include the request, effective instructions, manifests and touched paths, current call/data/state/artifact flow, confirmed requirements, current diff, native failures, and exposed Skill/tool metadata. Recheck only after a relevant scope/design/boundary change, an assumption-breaking first failure, repeated failed hypothesis, final-diff exposure, or imminent irreversible/delivery action.

Activation is not a document or quality claim. Do not store candidate Skills, skipped methods, profile IDs, model routes, or review decisions merely to prove this pass occurred.

### Specialist activation

Use repository-native controls first, then load the smallest effective specialist that owns a real decision or evidence surface. Relevant examples include Rust ownership/unsafe, Tokio cancellation/backpressure, FFI/ABI/lifecycle, Swift concurrency/SwiftUI, React rendering/data flow, SQL/schema/migration, security/privacy, accessibility, packaging/signing, and browser/device verification. Check the Skill's negative trigger before loading it. If the effective host does not expose the route, use its qualified manual/native fallback and state the limitation only when it affects the claim.

### Method activation

Actively match a bounded method when a concrete mechanism exposes migration/mixed-version operation, FFI/ABI/unsafe lifecycle, concurrency/nondeterminism/distributed ordering, authorization/privacy/trust, public contract compatibility, irreversible/data-loss consequence, conflicting evidence, oracle sharing, repeated failure, or complex rule/state combinations. If the owning specialist already supplies a discriminating procedure, use it without a selector call. Otherwise select at most one-to-three decision-useful methods and load only their relevant reference family. Method use remains advisory and non-persisted.

### Review activation

Root final-diff challenge is universal. Specialist review applies only to its affected boundary. Independent `change-review` or an independent reviewer applies to material security/privacy, persistent data/migration/rollback, FFI/unsafe/concurrency/public protocol, irreversibility/data-loss, consequential trade-offs with credible alternatives, conflicting evidence/shared-oracle blind spots, explicit request, or repository policy. Blue and red are review lenses; they do not require two agents or two files.

## Risk overlays

Overlays are orthogonal to direct/managed mode and compose only the controls relevant to the exposed risk.

| Overlay | Activation | Additional controls |
|---|---|---|
| Security/privacy | auth, secrets, untrusted input, privacy, regulated data | threat/trust-boundary review, security-focused tests, secret/privacy handling, independent review for material exposure |
| Migration/data | persistent schema/data, cutover, deletion, compatibility | inventory, forward/backward compatibility, resumability, observation, rollback/restore, migration rehearsal |
| External system | protocol, external write, distributed state | contract/sandbox evidence, idempotency, timeout/retry, reconciliation, real-system gates kept `NOT RUN` until observed |
| Release/delivery | package, signing, deployment, publication | immutable target/artifact, provenance, rollback, explicit action authority, post-action verification |
| Irreversible | destructive action or unrecoverable consequence | exact target resolution, backup/recovery evidence, explicit confirmation immediately before action |
| UI/product | material workflow or information-architecture change | product intent, complete user states, accessibility, rendered verification at affected breakpoints/devices |

An overlay does not require a packet, mandatory independent agents, or a fixed prose artifact. It may make managed mode useful when the work becomes long-running, but the decisions remain independent.

## Skill routing

The main Skill performs only:

1. establish request authority and repository facts;
2. identify the primary task intent;
3. choose direct or managed from continuity needs;
4. identify risk overlays and knowledge impact;
5. load the minimum specialist Skills;
6. integrate native evidence and report honest limits.

Default routes:

| Intent | Routes |
|---|---|
| Research | repository context; add a subject specialist only when needed |
| Diagnosis | repository context + systematic debugging |
| Design | requirements/design; add UX/architecture/dependency specialists only for actual decisions |
| Change | repository context + affected verification; diagnosis or decision owners compose when needed |
| Review | verification + change review against current source/evidence |
| Delivery | delivery readiness plus the applicable technical owner |

Methodology selection is bounded and non-persisted. Actively consider it for uncertain migration/data, FFI/ABI/unsafe, concurrency, security/privacy/authorization, public API/protocol, irreversible/data-loss, conflicting-evidence, oracle-challenge, or repeated-failure work. Skip the selector when the owning specialist already supplies a clear method. It is never a lifecycle gate.

`route-task` adds `change-review` only when calibration explicitly identifies a review need. An overlay label alone is not evidence of material exposure; security, migration, release, and irreversible controls still apply without forcing a separate reviewer.

## Multi-agent work

Single-agent work remains the baseline. Delegate only when parallelism or independent context has a credible net benefit.

Every actual child dispatch uses `route-agent` with its role, workload, risks, and reasoning signals, then applies the returned model, effort, and fork request. The route is not persisted and does not prove quality. If the routed child would cost more context/coordination than it saves, keep the work in root.

The dispatch profiles are capability/effort combinations, not task prestige:

| Profile | Model / effort | Intended child work |
|---|---|---|
| P0 | Luna low | exact lookup, fixed command, filtering, formatting |
| P1 | Luna medium | directed extraction/summary, mechanical edit, exact verification |
| P2 | Luna high | confirmed, bounded implementation or repetitive change with a deterministic oracle |
| P3 | Terra medium | ordinary exploration, implementation, or failure classification with some uncertainty |
| P4 | Terra high | complex causal analysis, routine independent review, or bounded multi-file trade-offs |
| P5 | Sol high | broad ambiguity, cross-component/public contract, architecture, migration, security, concurrency, FFI, or complex review |
| P6 | Sol xhigh | critical adversarial acceptance, irreversibility, or data-loss exposure |
| PX | Sol max | explicitly acknowledged and evaluated exceptional work only |

Large context or many steps alone does not require Sol. Confirmed semantics, bounded ownership, and a deterministic oracle make directed work Luna-eligible. Requirements meaning, dependency choice, architecture adjudication, consequential risk decisions, authority, integration, and final claims remain root-owned. Never create a child merely to use a cheaper model.

A child brief contains only:

- objective and expected outcome;
- relevant repository/business context;
- owned paths or read-only boundary;
- allowed verification/resources;
- stop condition and return format.

Do not require packet IDs, fingerprints, AC/SC/VO mappings, model profiles, lease epochs, generated reports, or checkpoint transitions unless the actual external system requires them. The root reconciles returned work against the current Git diff and reruns affected checks.

## Host safety and data security

Dev Flow 2.0 has no process, lifecycle, command-authorization, packet, delegation, or completion Hook. Command-string classification duplicated host permissions, covered only some tool paths, imposed cost on every Bash call, and could create false confidence.

The dedicated data-security Hook remains independent because it has a bounded deterministic detector, negative triggers, local redaction, and focused adversarial tests. It cannot infer workflow quality or grant authority. Broad destruction, irreversibility, and external-action confirmation remain governed by the host, current instructions, and exact user authority.

## Codex-native adapters

Dev Flow uses current native Codex capability where it has positive value and a safe fallback:

- Default-mode interaction: use the effective structured question surface when exposed; otherwise one focused conversational question. Never enter Plan mode.
- AGENTS health: read the effective hierarchy and report conflicts, stale commands, broken references, or harmful scope; never rewrite it without an explicit change request.
- Native review: use an exposed read-only review surface when it fits the target; otherwise use `change-review` with current source and evidence.
- Goal: create or update a Codex Goal only when the user explicitly requests a durable Goal. Workstream documents remain repository truth.
- Worktrees: isolate concurrent writers only when independent work has disjoint ownership and the coordination benefit exceeds setup/merge cost.
- UI/device: use browser, simulator, device, preview, screenshot, accessibility, and runtime evidence only for affected rendered/platform surfaces.
- External context/MCP: retrieve only decision-relevant facts. When a fact materially affects a decision, retain only four light fields in conversation or an existing relevant document: source plus freshness, fact used, limitation, and read/write authority.

No adapter is a mandatory plugin dependency. Capability absence remains `NOT RUN` or a named fallback, not a reason to enable experiments or mutate global configuration.

## Verification model

Technical evidence stays native and proportional:

1. focused test/reproducer for the changed behavior;
2. affected module/package checks;
3. broader integration, compatibility, UI, migration, or security gates only when the change can affect them;
4. final diff, scope, generated/dependency/secret, and documentation inspection;
5. explicit `NOT RUN`, `BLOCKED`, `FAILED`, `FLAKY`, or `WAIVED` for unproven gates.

Black-box and white-box thinking remains useful specialist guidance. It is not mandatory prose accounting.

## Knowledge model

Repository knowledge has three ordinary forms:

- current truth: architecture, contracts, runbooks, module documentation, and other maintained facts;
- direct change records: concise behavior or rationale that has no adequate existing home;
- workstream history: design, implementation plan, progress, and decisions that explain a material change.

Git already supplies authorship, timestamps, diffs, review, and history. New 2.0 knowledge needs no `catalog.json`, per-change manifest, authority digest, packet binding, or promotion transition. Repositories with regulated or generated documentation may keep stronger native controls.

Runtime logs and temporary evidence remain ignored/generated. Promote only durable information a future maintainer needs.

## Release model

### CI lanes

- Semantic lane: one primary Linux/latest-Python job runs the full behavioral and structural suite.
- Compatibility lane: a small matrix runs only platform/version-sensitive tests on supported OS/Python boundaries.
- Artifact lane: release-only construction, SBOM, checksums, provenance, and attestation.

### Release tiers

| Tier | Change class | Required evidence |
|---|---|---|
| R1 standard | docs, Skill prose, fixtures, ordinary logic | focused local checks + semantic CI + affected compatibility tests |
| R2 runtime | installer, host integration, or cross-platform process/path behavior | R1 + compatibility lane + isolated install/uninstall smoke |
| R3 artifact/security | builder, release workflow, attestation, data-security controls | R2 as applicable + deterministic archive/SBOM/provenance negative tests |
| R4 model-semantic | material change whose branch activation depends on Codex interpretation | affected deterministic gates + semantic fixtures and bounded isolated first-attempt activation pilots when needed; no effect score |

Higher tiers are additive only where relevant. A documentation patch does not rehearse install rollback. A data-security Hook change uses security-specific gates without a full model acceptance run. A model evaluation never substitutes for deterministic or artifact evidence.

Publication remains separately authorized after the applicable tier passes.

## Metrics and feedback

`flow-metrics` is a compatibility name for Flow Activation Coverage, not an effect or productivity measurement system. It verifies whether representative tasks reach the intended intent, continuity, requirement-confirmation, overlay, specialist, method, review, model/effort, verification, knowledge, and delivery branches, and whether negative-trigger cases remain quiet.

Use three lanes:

1. deterministic normalized routing contracts;
2. natural-language plus repository fixtures that must infer hidden signals and use the effective capability surface;
3. negative/cost-boundary cases for simple work, generic labels, repository-resolvable facts, unnecessary questions, methods, review, documents, agents, and stronger models.

Report pass/fail, expected versus observed activation, missing activation, unexpected activation, and unmet prerequisites. Do not emit a composite score, productivity/effect metric, developer ranking, Skill/method usage target, or persistent task telemetry. Use pairwise/boundary cases rather than a Cartesian product; add a case when a real activation failure is observed.

## Legacy migration

- Keep schemas 1.0-2.0 packet validation, archive, and explicit legacy CLI commands readable.
- Stop creating packets from the 2.0 Skill and new `route-task` defaults.
- Remove the Dev Flow process Hook, including packet lifecycle, command authorization, delegation, and Stop handling.
- If a legacy packet is active, ignore it for 2.0 work; the user may archive it later without blocking current work.
- Existing tracked `docs/project` and `docs/changes` remain valid history. New work uses the repository's convention or `docs/workstreams`.
- Mark packet/methodology/catalog APIs as legacy in documentation before a later major removal decision.

## Acceptance scenarios

1. A one-file bug fix routes direct, creates no files before the fix, reproduces the bug, changes code/tests, runs focused checks, and closes.
2. A read-only audit routes direct and cannot be redirected into implementation by an old packet.
3. A multi-session product rewrite routes managed and initializes exactly two default workstream documents in the repository; a real architectural trade-off adds `design.md` explicitly.
4. A managed resume reads `progress.md`, verifies current Git/repository facts, and continues without a checkpoint or digest ceremony.
5. A security-sensitive one-file fix can remain direct while receiving the security overlay.
6. A legacy active packet does not block ordinary search, mutation, tests, interactive input, delegation, or final response.
7. A bounded but semantically important change remains direct, updates current truth, and may add one light change record without creating managed state.
8. No Dev Flow process Hook runs on Bash, edits, agent lifecycle, or completion; the independent data-security Hook retains its dedicated tests.
9. Ordinary CI runs full semantic gates once and platform-sensitive gates in a focused matrix.
10. Release candidate construction does not rerun the entire semantic suite after the exact commit already passed CI.
11. A delegated mechanical change and a critical FFI review use different P0-P6 routes without storing routing receipts.
12. A first surprising failure triggers risk/assumption recalibration, while methodology selection remains bounded and non-persisted.

## Rollback

Before publication, rollback is a normal Git revert of the 2.0 changes. After publication, restore the last remotely verifiable stable tag (`v1.1.2`) or a separately preserved exact pre-2.0 source snapshot while retaining the 2.0 research and workstream documents as historical knowledge. The 1.1.3 source history is not an immutable release tag. Legacy packet code remains available throughout the first 2.0 release, so rollback does not require packet-data migration.

Recommendations intentionally outside this implementation are tracked in [recommendations.md](recommendations.md).
