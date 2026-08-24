# Dev Flow 2.0 RC.3 decisions

## D1: RC.3 prioritizes behavioral reliability over new methodology

- Status: accepted for implementation
- Context: RC.2's strongest dogfood gains came from activating existing specialists, methods, and reviewers; its failures came from late/missed activation, transitions, tool failure, and oversized task continuity.
- Decision: add no methodology families by default. Invest in discovery, routing, transition, fallback, scope, and oracle reliability.
- Consequence: the release remains bounded and existing advanced capabilities become more dependable.

## D2: Repository knowledge becomes a first-class explicit capability

- Status: accepted for implementation
- Context: AGENTS.md alone cannot own human/agent knowledge, stable documentation navigation, generated retrieval maps, operational runbooks, and enforceable facts.
- Decision: ship `repository-knowledge` with audit, plan, map, bootstrap, and check modes and strict negative triggers.
- Consequence: repositories gain a maintainable knowledge-system path without burdening ordinary nearby documentation updates.

## D3: Task transitions remain ephemeral

- Status: accepted for implementation
- Context: multi-turn tasks need reliable recalibration, but a persisted lifecycle engine would duplicate Git/workstreams and recreate 1.x ceremony.
- Decision: define and test transition events without persisting Dev Flow task state.
- Consequence: behavior improves while repository-native continuity remains authoritative.

## D4: Documented route value failures are structured

- Status: accepted for implementation
- Context: argparse currently rejects some invalid public values before Dev Flow can return its documented correction contract.
- Decision: allowlist `diagnosis -> diagnose`; normalize documented route values before argparse `choices`; return structured failures for invalid documented values while leaving unknown flags and missing-value syntax to argparse.
- Consequence: agents can safely replay one exact correction and invalid commands become observable test failures rather than prose noise.

## D5: One capability failure does not erase independent progress

- Status: accepted for implementation
- Context: an unavailable deep scanner delayed an otherwise viable release workflow and repeated the same immutable permission failure.
- Decision: classify failures, preserve the first failure, avoid unjustified retries, continue independent safe gates, and report the isolated blocked claim.
- Consequence: delivery remains honest without turning optional tool availability into a global workflow failure.

## D6: Scope checkpoints advise; they do not seize task authority

- Status: accepted for implementation
- Context: very large multi-repository task lineages can outgrow their original oracle and accumulate stale evidence.
- Decision: checkpoint semantic expansion and evidence freshness, then recommend continuation, a new slice/task, or candidate freeze. Do not automatically create tasks, worktrees, commits, or tags.
- Consequence: long work becomes reviewable without hard numeric bureaucracy.

## D7: Release orchestration incubates in product ownership

- Status: accepted for implementation
- Context: a complete release spans audit, documentation, versions, commits, tags, CI observation, publication, and recovery, but these details differ across products and carry external-write authority.
- Decision: define a generic integration boundary in RC.3 and implement the first workflow as a product-owned Skill plus resumable CLI. Consider core extraction only after a second product validates the common contract.
- Consequence: Dev Flow does not fossilize one product's release process into a premature universal engine.

## D8: Activation coverage remains the release metric

- Status: accepted for implementation
- Context: real dogfood is necessary, but productivity or composite quality scores are noisy, privacy-sensitive, and easy to optimize perversely.
- Decision: measure expected/observed activation, transitions, invalid routes, blocked capabilities, evidence freshness, and negative controls without an aggregate score.
- Consequence: qualification targets behavioral contracts rather than maximizing visible process.

## D9: RC.3 evolves RC.2 additively

- Status: accepted for implementation
- Context: route and Skill behavior is public to model callers even without a formal external API.
- Decision: preserve canonical values and existing route fields; add an explicit intent alias, structured value errors, and stronger semantics. Do not add an unconsumed `route_details` projection, persisted state, or repository data migration.
- Consequence: RC.2 remains a viable rollback installation and maintained Markdown artifacts remain readable across versions.

## D10: Product release pilots are stable inputs, not RC.3 gates

- Status: accepted for implementation
- Context: the pilot lives outside this Git root, needs separate mutation/external-action authority, and must span two real releases; placing it in the RC.3 slice chain contradicted the source-readiness definition.
- Decision: RC.3 retains only the extension boundary and extraction criteria. A product-owned workstream executes the pilot separately, and its evidence informs stable `2.0.0` rather than RC.3 source qualification.
- Consequence: RC.3 has a closed in-repository completion path without weakening the product pilot's recovery and authority requirements.

## D11: Readiness isolation is behavioral, not a new registry/state machine

- Status: accepted for implementation
- Context: `governance/capability-contracts.json` owns built-in Skill topology and cannot describe every host/plugin tool; no universal readiness probe exists.
- Decision: put first-failure preservation, unchanged-context no-retry, retry triggers, safe continuation, and claim limits in active guidance and semantic cases. Do not add readiness state to the route or capability registry in RC.3.
- Consequence: the observed failure mode is addressed without claiming deterministic enforcement or expanding public schema.

## D12: Implementation is closed by default; exploration is explicit

- Status: implemented in the RC.3 working tree; qualification pending
- Context: historical tasks repeatedly combined deep design exploration with later implementation, and users then had to narrow unrelated research, platforms, reference artifacts, or adjacent repairs.
- Decision: implementation/repair uses closed discovery, diagnosis/review uses bounded discovery, and open exploration requires an explicit breadth request. `Deep`, red/blue analysis, managed mode, reasoning effort, or model capability never changes the discovery mode by itself.
- Consequence: Dev Flow can remain rigorous without interpreting rigor as permission to enlarge the deliverable.

## D13: Scope is an ephemeral multi-boundary envelope

- Status: implemented in the RC.3 working tree; qualification pending
- Context: one undifferentiated “scope” cannot express that a review may read broadly, an implementation may write narrowly, and verification may run affected broad checks without granting broad mutation authority.
- Decision: reason about outcome, discovery, mutation, verification, and action/delegation boundaries separately, plus protected behavior, non-goals, terminal condition, and expansion triggers. Keep the envelope ephemeral and persist only durable workstream facts.
- Consequence: RC.3 gains observable boundary behavior without a new route schema, packet, lifecycle database, or authorization service.

## D14: Findings do not enter implementation by discovery alone

- Status: implemented in the RC.3 working tree; qualification pending
- Context: adjacent findings and attractive future improvements were sometimes implemented or planned merely because they were found during deep work.
- Decision: classify every material new finding as required defect, necessary enabler, optional opportunity, or unrelated. Only admitted required work proceeds; material enablers recalibrate, and optional/unrelated items remain reports or deferrals.
- Consequence: discovery remains useful while “while we are here” scope creep becomes testable.

## D15: Delegated authority can only narrow

- Status: implemented in the RC.3 working tree; qualification pending
- Context: path ownership and stop conditions already exist, but constraints can weaken through broad context forks, nested delegation, child interpretation, and report-only integration.
- Decision: each child receives a subset of parent outcome and read/write/tool/dependency/external/re-delegation authority; nested scopes are the intersection of ancestors; root owns expansion and checks actual diffs/evidence.
- Consequence: multi-agent work gains least-authority behavior without a persistent delegation ledger. Host enforcement is used when available and otherwise remains guidance plus root verification.

## D16: Continuation preserves terminal meaning and non-goals

- Status: implemented in the RC.3 working tree; qualification pending
- Context: long tasks, frequent compaction, repeated attempts, and “keep going/implement fully” requests can lose non-goals or turn persistence into unapproved breadth.
- Decision: continuation reconstructs terminal condition, discovery mode, mutation/action boundary, non-goals, deferred expansions, active process, and stale evidence from repository/workstream truth. Persistence continues safe admitted work only.
- Consequence: long-running autonomy becomes more useful without granting commit, release, external, destructive, dependency, or broader product authority.

## D17: Cross-task history is explicit, untrusted evidence

- Status: implemented in the RC.3 working tree; qualification pending
- Context: referenced and repeated tasks are useful, but stale summaries, contradictory attempts, and analogy repositories can be mistaken for current authority.
- Decision: read history only when explicitly referenced or selected; reconcile it against current repository/runtime/primary external truth; never auto-scan, auto-rank, merge, archive, or mutate tasks; keep analogy repositories non-authoritative.
- Consequence: cross-task synthesis supports the user's workflow without turning conversation history into hidden memory or program policy.

## D18: Personal adaptation uses confirmed profiles and sanitized dogfood

- Status: implemented in the RC.3 working tree; qualification pending
- Context: stable user preferences can improve fit, but automatic inference would violate profile ownership, privacy, and neutral-suite boundaries.
- Decision: propose/write personal preferences only through the existing profile contract and explicit approval. Dogfood consumes authorized host reads in memory or sanitized observations and emits aggregates/task shapes only; ordinary conversations remain negative controls.
- Consequence: user fit improves without hard-coded personal values, raw transcript retention, productivity scoring, or ambient Dev Flow activation.

## D19: Frontier authorization research informs invariants, not architecture

- Status: implemented in the RC.3 working tree; qualification pending
- Context: recent work on goal drift, constraint drift, and bounded delegation supports scope preservation and least authority, but the newest multi-agent authorization proposals are preprints and disproportionate for a plugin RC.
- Decision: adopt explicit scope, monotonic narrowing, external enforcement when the host already provides it, exit conditions, and failure-sensitive evaluation. Do not add a general principal-chain service, policy engine, or cryptographic authorization layer in RC.3.
- Consequence: the plan uses the strongest stable insight while preserving implementation simplicity and rollback compatibility.

## D20: Method usefulness requires disposition, realization, and evidence

- Status: implemented in the RC.3 working tree; qualification pending
- Context: the 117-method registry and deterministic selector are structurally healthy, but sanitized post-RC.2 task evidence shows that natural-language recognition is incomplete, most observed selections are blocked-only, readiness is rarely rechecked after discovery, and selection is not consistently converted into a test, counterexample, model, review surface, or claim limitation.
- Decision: retain the existing method inventory; separate eligibility, candidate selection, readiness, ready/fallback/abstain disposition, realization, and evidence effect; project existing annotations more actionably; prefer one low-cost ready method; and evaluate method value with output mutations plus bounded fixed-condition paired trials rather than invocation counts.
- Consequence: methods become more likely to improve verification, review, and audit work while ordinary deterministic tasks remain quiet, missing prerequisites remain honest, and method depth cannot broaden implementation scope.
