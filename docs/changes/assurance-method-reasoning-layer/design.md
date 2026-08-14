# Change design: assurance-method-reasoning-layer

[Tracked change manifest](../../../docs/changes/assurance-method-reasoning-layer/manifest.json)

## Decision

Implement a shared Assurance Method System owned by `dev-flow`, not a new top-level Skill. A canonical `governance/methodology-pool.json` defines method cards, sources, and risk models. A standard-library `methodology_system.py` validates the registry and performs deterministic selection; `dev_flow.py select-methods` exposes it. The result is a bounded `method.selection.v1` reasoning trace consumed by existing owner Skills. Progressive Markdown playbooks teach the selected methods and reusable templates capture the artifacts. This fits the current thin-kernel/owner topology and makes omissions testable without forcing the full corpus into context.

## Engineering preferences applied

- Applicable instructions: INS-1 requires full-lifecycle novice guidance; INS-2 preserves owners/progressive disclosure/negative triggers; INS-3 binds governed evidence; INS-4 adds no constraint.
- Effective snapshot: `sha256:47631e03adcc44556f6186670186b4bad13cfc3e99483262a5ff469f02fd3dc9`; neutral baseline, no conflicts or exceptions.
- Language/framework scope: the selector is domain-neutral Python/JSON; method applicability comes only from explicit lifecycle/risk/signal facts and owner guidance, never filename stereotypes alone.
- Quality coverage: repository-native unit/contract tests plus independent blue/red review; no waiver.
- Dependency thrift: standard library and existing CLI/knowledge surfaces only.

## Alternatives

| Option | Capability fit | Costs and risks | Decision |
|---|---|---|---|
| Add a top-level methodology Skill | Easy to discover | Duplicates owner decisions, grows static routing, encourages monolithic loading | Rejected; methodology is an orchestration service. |
| Prose-only handbook | Rich teaching space | Cannot deterministically select, validate coverage, or prevent cargo-cult loading | Rejected as the primary design; retained as progressive method cards. |
| Registry plus deterministic selector plus progressive cards | Machine-testable, explainable, bounded, extensible, preserves owners | Requires schema and cross-artifact contracts | Selected. |
| Model-only natural-language selector | Flexible | Non-deterministic, hard to regression-test, can invent facts and methods | Rejected; AI supplies observed signals, deterministic code maps them. |
| Add method fields to every packet schema | Strong persistence | Public migration and ceremony before the invariant is proven necessary | Rejected for v1; record the selection in existing design/execution/test sections. |

## Architecture and failure behavior

Control flow is `repo-context facts -> explicit phase/task/risks/signals -> registry validation -> foundation set + matching risk models -> depth/cost/context-budget filtering -> method.selection.v1 -> existing owner artifacts -> phase-change reselection -> verification/review evidence`. Each risk model states the failure hypothesis and evidence obligation; each method states prerequisites, steps, outputs, owner, limits, fallbacks, and sources.

Unknown phase, depth, signal, risk, owner, source, or method reference fails with status `invalid`. A known but unmatched input returns only the bounded foundation appropriate to the phase and explicit exclusions; it never guesses risk closure. Missing method prerequisites are reported as unresolved and route to fallback/escalation, not success. Selection is stable-sorted and capped by depth (`starter`, `deep`, `formal`) plus an explicit maximum. Formal methods require matching high-consequence/state-space/temporal/identity signals and are never selected by generic complexity alone.

The registry is the data authority; Markdown cards are human guidance and link by stable method IDs. Source metadata records provenance, not current web availability. `validate-methods` checks structure/coverage/reference integrity; `select-methods` validates before selection. No external process, network, cache, or cleanup lifecycle is introduced.

## Product and UX contract

- UI impact: none.
- Users, outcome, and protected product/IA/flow constraints: CLI and Skill consumers receive plain-language JSON/Markdown; existing commands and documentation paths remain stable.
- Design truth, selected direction, states, accessibility, fidelity, and evidence: not a visual surface; terminology uses short summaries plus exact method names and stable IDs.
- UX Ready: not applicable.

## Requirement baseline and reopening

- Bound revision and digest: requirement revision 2; exact requirement and design digests are content-bound by reapproval before implementation resumes.
- Disposed ambiguities: AMB-1 is resolved by the exact authority/backlink contract with no product-semantic change; literal exhaustiveness is explicitly excluded while extension governance preserves breadth.
- Reopening behavior: affected implementation stops; material/high-risk semantics return to awaiting approval and new content-bound approval invalidates downstream evidence.

## Dependency decisions

- DEP-1: no new dependency; use Python standard library and existing JSON/Markdown contracts.

## Change scope

- SC-D1: Add the canonical methodology pool, source registry, risk models, and schema validator.
- SC-D2: Add deterministic `validate-methods` and `select-methods` CLI behavior with bounded depth and explainable output.
- SC-D3: Add lifecycle integration, progressive method cards, novice template, and source/adaptation documentation.
- SC-D4: Add deterministic registry/selection/negative-trigger/coverage/compatibility tests and contract-check integration.
- SC-I1: Update tracked Dev Flow current truth, industry-practice registry, README/reference navigation, and governed change dossier.
- SC-C1: Optional model-evaluation fixtures only if deterministic contracts cannot observe a core invariant; current design expects none.
- SC-P1: Existing Skill ownership and route order remain unchanged.
- SC-P2: Existing `route-task`, packets, hooks, plugin manifest/version, and knowledge schemas remain compatible.
- SC-P3: Existing black/white/adversarial quality kernel and authority gates remain mandatory.
- SC-P4: Low-risk tasks remain lightweight; no all-method context loading or method-count target.
- SC-P5: Missing tools/prerequisites/external evidence remain explicit fallback or `NOT RUN`, never passed.
- SC-O1: Tool integrations, regulated certification, exhaustive management theory, new top-level Skills, and unrelated cleanup.
- SC-L1: Local source/docs/tests and packet/dossier only; no stage, commit, push, PR, release, install, deploy, or external publication.

## Compatibility, rollout, rollback, and cleanup

The CLI additions are additive and the registry schema starts at 1.0. Existing commands and packet validation do not depend on method selection, so rollback is deletion of the added module/registry/cards/tests and removal of small orchestration/doc projections. No data migration, feature flag, or runtime cutover is required. A future schema change must retain or explicitly migrate stable method/source IDs.

## Verification obligations

- VO-1: Registry validation proves exact schema, stable/unique IDs, sources, owners, phases, triggers, limitations, steps, outputs, fallbacks, and lifecycle-family coverage.
- VO-2: CLI tests prove deterministic output, stable ordering, valid error behavior, context bounds, depth escalation, and no network/dependency use.
- VO-3: Representative scenario tests prove AC-6 risk-to-failure-to-method mappings and novice explanations.
- VO-4: Negative controls prove routine work excludes heavyweight methods, unknown facts fail closed, negative triggers are honored, and missing prerequisites remain unresolved.
- VO-5: Existing routing, packet, hook, knowledge, plugin, and cross-platform contract suites remain green.
- VO-6: Documentation/reference tests prove every selected method resolves to a card/template/source and no broken progressive-disclosure links exist.
- VO-7: Independent blue/red review challenges owner overlap, cargo cult, formal-method overuse, source fidelity, compatibility, false assurance, and selector blind spots.
- VO-8: Fresh full contract and unit suite passes against final bytes; any external/tool-backed method remains explicitly unexecuted unless separately run.

## Testing and implementation strategy

- Implementation slices: T1 requirements/design/dossier; T2 registry/schema; T3 selector/CLI; T4 cards/templates/lifecycle/docs; T5 contracts/scenarios; T6 verification/review/current-truth promotion.
- Black-box design: exercise public CLI for normal starter/deep/formal selections, representative risk stacks, exclusions, invalid input, missing prerequisites, limits, and byte-stable repeated output.
- White-box design: validate every registry branch/reference, scoring/filtering/dedup/order, foundation inclusion, phase filtering, cap behavior, prerequisite/fallback propagation, and source/card coverage.
- Oracle and test-code review: mutation-style negative controls remove a trigger/source/owner/output or alter a risk mapping and must fail; scenario assertions target stable IDs and causal explanations rather than fragile whole-output snapshots.
- Specialist controls: existing Dev Flow routed owners plus standard Python unittest/contract runner and maintainer suite validation.

## Approval record

- 2026-08-14: The user's explicit request authorizes the broad research-to-implementation scope in revision 1, with no dependency or delivery authority. Content-bound CLI approval will bind the exact requirement bytes before implementation.
- 2026-08-14: Revision 2 changes no product semantics; it adds the common tracked-manifest backlink required by the governed knowledge contract and is reapproved under the same explicit authority.
