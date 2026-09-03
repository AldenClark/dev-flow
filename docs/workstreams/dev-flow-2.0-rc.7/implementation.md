# Dev Flow 2.0 RC.7 implementation

> Status: released as `v2.0.0-rc.7`; independent findings and release evidence are maintained in `progress.md`.

This plan implements the RC.7 [development guidance](../../rc7-development-lifecycle.md), [methodology toolbox](../../rc7-methodology-system.md), [Skill evolution design](../../rc7-skill-evolution-design.md), and [acceptance reference](acceptance.md). The [local-task audit](../../rc7-dogfood-audit.md) supplies evidence and regression examples; the [professional-Skill discovery audit](../../rc7-specialist-discovery-audit.md) supplies the activation-gap baseline. Neither audit organizes the product or replaces the Skill-evolution mainline.

## Outcome

RC.7 strengthens the existing main `dev-flow` Skill and professional Skills into one lifecycle-wide development guide. Material work carries maintained knowledge from requirements through operation; testing covers important behavior and risk deeply without spending unbounded effort on low-value fringe cases; ordinary work loads less static context.

## Baseline and invariants

- Freeze current owner boundaries, public names, supported CLI and compatibility behavior before edits.
- Record the current ordinary static path of `14082` bytes. RC.7 must reduce it below the existing `13500` warning line and aims for no more than `12500` without losing core or negative behavior.
- The current contributing bytes are main `dev-flow` `8998`, `repo-context` `2591`, and `verification` `2493`. If the two owners stay near `5100`, use about `7400` bytes as the provisional main-entry ceiling; move new documentation/testing detail to on-demand references.
- Record the second always-visible budget: all Skill descriptions currently total `1979` characters, the early-warning line is `1995`, and the hard target is `2128`. Discovery improvements must fit this budget and improve held-out owner recall/adjacent-negative restraint; longer metadata alone is not success.
- Keep the current representative behavior examples as a non-gating challenge set. Select and integrate only the examples affected by each implementation group; do not turn the catalog into a fixed release checklist or a standalone universal runner.
- Repair dangling method-effect fixtures, method/oracle mismatch and `route-agent --risk` help as affected evaluation/tooling work proceeds.
- Preserve authorization, protected user changes, exact evidence environments and action-specific delivery authority.
- Treat professional-Skill discovery as a suite-wide behavior, not a `repository-knowledge` exception. For every owner distinguish natural recognition, deterministic expression, realized effect and adjacent negative restraint.
- Use evidence-triggered owner discovery: a compact always-visible problem spine plus progressively loaded professional Skills. Keep candidate discovery, admission and application effect independently observable.
- Do not add a second router or embedding index for the current 15 built-in Skills. Reconsider body-aware retrieval only after observed catalog omission/truncation or held-out recall degradation, and keep any retriever advisory and authority-neutral.
- Treat child and nested-child dispatch as internal task allocation requiring no separate user authorization. Preserve action/scope authority inside every descendant; spawning never authorizes commit, delivery, external access, destructive work or semantic expansion.

## Main implementation line

### 1. Thin the main `dev-flow` Skill

- Reduce the entrypoint to the development spine, professional-owner navigation, one documentation-continuity principle, completion synthesis and the few hard boundaries.
- Move detailed routing, model, method, workstream and specialist procedures to focused references or their professional owners.
- Update `skills/dev-flow/agents/openai.yaml`, plugin prompts, capability contracts and affected positive/negative tests with the entrypoint rather than leaving stale RC.6 behavior active.
- Update repository-root `AGENTS.md` in this same migration group: remove the active requirement for separate independent-review authority while preserving authorization for real repository, delivery, external, sensitive and destructive actions. Add a regression check that the old reviewer-authorization wording is absent from every active entry surface.
- Establish the common discovery-contract/matrix infrastructure and the compact main-Skill recognition/rebind spine; do not rewrite every professional owner's trigger before its procedure and oracle are ready.
- For each professional owner, front-load observable user intent/symptoms and one adjacent exclusion in its implicitly discoverable description, or align explicit-only metadata, atomically in that owner's group together with its Skill body, contract, route fixtures and positive/negative tests.
- Keep owner selection sticky under unchanged goals/evidence; allow `none`, one primary owner and at most one justified adjacent candidate.
- Revise the multi-agent reference, main Skill, capability contracts, public routing output and tests so useful ordinary/nested dispatch and clean-context independent review proceed without an authorization flag. Absence of host capability, resource ownership or net decomposition value may prevent dispatch; absence of a user permission prompt may not.
- Remove the current nested-authority loophole: an admitted owner may allocate only actions already authorized by the user and retained by every ancestor envelope. Owner admission, Skill activation or a child request can never add repository/path, dependency, platform, semantic, external-action or destructive authority. Cover this with a nested negative test.
- Treat the authorization migration as an active-surface inventory, not a prose-only edit. The first group owns repository `AGENTS.md`; `skills/dev-flow/SKILL.md`; `skills/dev-flow/references/orchestration.md`, `multi-agent-v2-orchestration.md` and `quality-calibration.md`; `skills/dev-flow/scripts/dev_flow.py` CLI/output/help and its imported `route_incremental.py`; Dev Flow agent profiles and `agents/openai.yaml`; plugin prompt; capability contracts; dispatch/flow-activation fixtures; `evals/test_agent_dispatch.py`, `evals/test_flow_activation.py`, affected `evals/test_dev_flow_v2.py`; and user-facing compatibility/projection text in README, releasing and CHANGELOG. `--independent-review-authorized` may remain a parsed compatibility input temporarily, but it cannot enter dispatch basis, change `route-agent`, or produce an authorization downgrade. Tests and a residual-text/behavior scan must show that no active entry still turns reviewer spawning into an authorization gate.
- Retain the P0-P6 model/effort resolver as the existing owner of task-relative selection, refresh its model/help surface, and remove authorization semantics from ordinary routes. Keep PX and separately metered model campaigns exceptional; treat `--independent-review-authorized` as a compatibility input during migration, never as a gate.
- Measure the ordinary static path after every edit and reject byte reductions that weaken normal bug, material-change, documentation or safety behavior.

Done when the ordinary static path is below `13500`, which with the current `repo-context` and `verification` bytes means the main entry must be no more than `8415` bytes, and preferably the total is at or below `12500` with the main entry near `7400`; total Skill descriptions remain below `2128` and preferably below the `1995` warning line; actual catalog visibility, owner recall and adjacent-negative restraint improve; and representative fast-defect, material-change, documentation and safety cases remain correct.

### 2. Strengthen requirements, UX and repository knowledge

- Deepen `repo-context`, `requirements-design` and `product-ux-discovery` around first actions, examples/counterexamples, states, exceptions, confirmation and stopping.
- Enhance the existing `repository-knowledge` Skill instead of creating another documentation Skill.
- Let the main Skill state only the principle: every material lifecycle position that actually occurs leaves a result consumable by the next position and writes durable truth back to its canonical owner.
- Let `repository-knowledge` own the detailed topology: product/contract truth, UX/design truth, ADRs, testing strategy, runbooks, indexes, freshness and new/old-project adaptation. It establishes a minimal living change record only when existing canonical owners cannot support reliable continuation across sessions, owners or independent slices.
- Repair discovery as part of the owner change: observable missing-entry, chat-only handoff, canonical-owner ambiguity, duplicate/stale truth and unresolved project-level strategy placement select `repository-knowledge`; an ordinary update to a clear existing owner remains direct.
- Add a diagnostic `knowledge` need with the `repository-knowledge` alias, but do not make `route-task` mandatory or let `--knowledge-impact` alone force the full Skill.
- Align main-Skill guidance, `repo-context` handoff, Skill/agent metadata, capability contracts and positive/negative behavior cases so discovery does not depend on one surface.
- Require new projects to place durable non-code knowledge behind a discoverable project-native entry when it first appears. A small library may use its README; establish `docs/`/`docs/index.md` or an equivalent structure when multiple long-lived knowledge domains need navigation. Never create empty phase templates.

Done when a material addition can continue from requirements through technical design using repository documents rather than chat history, the professional owner is found when topology is unresolved, and a mechanical or already-owned documentation update does not load the full Skill or create empty documentation.

### 3. Strengthen technical design and implementation quality

- Deepen `architecture-decisions`, `dependency-decisions` and `systematic-debugging` around boundaries, state, types, errors, resources, concurrency, compatibility, recovery and causal evidence.
- Connect design ablation, AHA, boundary parsing and falsification only at their real problem signals.
- Keep implementation coherent with the confirmed requirement and documented design; record material deviation and update the affected current truth.
- Reassess a separate implementation-quality Skill only after the existing owner combination is behavior-tested.

Done when technical choices are minimal, explainable, falsifiable and reflected in code/tests/documents without turning any one method into the coding core.

### 4. Strengthen verification, test systems and acceptance

- Deepen `verification`, `test-system-engineering` and `change-review` around black-box product outcomes, white-box implementation risks and project-native test layers.
- Maintain coverage across requirements/behavior, risk/recovery, structure/state, combinations/sequences, environments/compatibility and oracle sensitivity.
- Default to unit coverage for independent logic and add component/integration/end-to-end/platform evidence where the claimed boundary requires it.
- Use constrained pairwise/t-wise or variable-strength combinations, property/model/fuzz/differential/metamorphic tests and changed-code mutation where they reduce important uncertainty.
- Audit AI-generated tests independently against requirements, implementation and seeded faults so generated tests cannot self-confirm generated code.
- Divide budget into core, extended and fringe coverage. Stop low-probability, low-consequence fringe expansion unless the user explicitly requests it; rare but catastrophic security, privacy, financial, corruption or irreversible failures remain core risk.
- Preserve durable cross-layer, environment, fixture, lane and coverage-gap decisions in the repository's existing canonical testing owner. Create the smallest discoverable testing-strategy entry only when those decisions will be reused and no owner exists; do not require a separate testing-strategy file for every project or change.
- Teach practical coverage expansion in `verification`: derive black-box cases from product outcomes and white-box cases from final changed branches/state/boundaries; select unit/component/integration/contract/end-to-end/platform layers by the real promise rather than filling a matrix.
- Add problem-driven technique guidance and examples: boundary/equivalence/table/property for input space; decision/state/model and constrained variable-strength t-way for interactions; fuzz for broad generated inputs; differential/metamorphic/invariants for weak oracles; fault injection/replay for recovery; changed-code mutation/seeded faults for assertion sensitivity; contract/compatibility and concurrency-specific checks for their boundaries.
- Use coverage diff, branch/condition reports and mutation as feedback for finding worthwhile blind spots, never as universal target scores. Verify discovery, selection, isolation, cache/retry/skip behavior and environment attribution through the native runner.
- Add new-project and mature-project fixtures: the former must establish fast logic feedback, one real-boundary black-box slice, a native entry and minimal CI lane; the latter must strengthen existing runners/lanes without creating a parallel universal harness.
- Add a real-platform selection variant where host/mock/emulator checks are green but the native device/platform path fails or is unavailable. The correct result selects the native platform or end-to-end check when the promise requires it, otherwise records the exact `FAIL`, `BLOCKED` or `NOT RUN`; host evidence may never be upgraded to platform evidence.

Done when executable new- and mature-project fixtures prove the native test paths and graders detect seeded discovery, assertion, mock-boundary, cache, retry/skip and environment-attribution faults; material and rare high-consequence cases remain selected while low-value fringe expansion stops unless explicitly requested. These deterministic fixtures qualify method and harness sensitivity only. Live-model selection/application effect stays `NOT RUN` until a separate bounded observation is actually executed.

### 5. Connect profiles, security, delivery and operational learning

- Consume confirmed engineering profiles without inferring personal policy from code frequency.
- Keep company-data-security as the cross-cutting sensitive-data owner without duplicating it throughout the suite.
- Strengthen delivery readiness around functional Git units, identity, compatibility, observation, stop and rollback while preserving separate authority.
- Route incidents, real usage and support findings back to product, design, testing and long-term knowledge owners.

Done when preferences and operational learning affect real decisions, while engineering evidence never silently authorizes delivery.

### 6. Converge routing, methods, evaluation and product truth

- Deepen `dev-flow-maintainer` itself around promotion decisions, dogfood-slice closure and evidence qualification. Add positive/negative tests proving that structural/schema/coverage success cannot be reported as behavior or productivity improvement, while a real observed behavior regression or repair is routed to the affected owner and carried through to a bounded conclusion.
- Reconcile Skill descriptions, discovery metadata, capability contracts, routes, method navigation and compatibility surfaces after the professional owners are strengthened.
- Complete the all-owner discovery matrix: deterministic positive/negative coverage for every professional Skill, semantic recognition for implicit owners, quietness for explicit-only owners, and outcome-sensitive mutations rather than Skill-name counting.
- Grade discovery in seven independent stages: availability, candidate recall, admission, timing/rebind, application effect, cost/restraint and trust. Use explicit, embedded implicit, adjacent negative and mid-task cases; keep description tuning and held-out representative behavior examples separate when live-model observations are run.
- Add catalog truncation/omission, same-name collision, unexposed Skill and adversarial metadata controls. A candidate may never grant installation, scope, data or delivery authority.
- Add dispatch invariants: no authorization prompt for root/child dispatch, nested scope attenuation, automatic P0-P6 selection, clean-context review when the host supports it, and honest capability downgrade rather than an authorization downgrade.
- Use local dogfood and representative behavior examples to challenge affected integrated behavior; do not reorganize implementation around those historical task shapes. As each group changes behavior, place its affected examples and negative controls in an existing deterministic or behavior-evaluation catalog/runner; do not create an RC.7-wide acceptance runner or release gate.
- Keep the `dev-flow.product-state.v1` shape. Before pointing candidate/source/workspace at RC.7, change the validator so source/workspace workstreams require only `implementation.md` and `progress.md`, with other maintained references optional. Remove the unconditional RC.6 `HC7` progress projection from the generic contract or limit it to the legacy RC.6 workstream/phase that actually owns it. Add a source-candidate fixture where both source and workspace use only the two RC.7 files; prove it passes, prove each required file missing fails, and prove RC.6's five-file workstream plus historical `HC7` projection remains valid as a superset. Keep marker-based `check-workstream` for legacy or explicitly opted-in v1 workstreams; leave RC.7 unmarked and do not add empty requirements/design/decisions.
- After those validator tests pass, perform the candidate transition as one coherent projection bundle: update `.codex-plugin/plugin.json`, `governance/product-state.json`, `README.md`, `docs/releasing.md`, `CHANGELOG.md`, and RC.7 `progress.md` to the same source-candidate identity while RC.7 delivery actions are reset to incomplete/not-observed, the latest published RC remains RC.6, and rollback still points to the actual latest published tag. Negative tests must reject inherited RC.6 delivery evidence, manifest/version drift, rollback drift and stale projections. Validate that exact source-candidate fixture and the real tree before treating the pointer switch as complete; no released, published or installed evidence is inferred.
- Run deterministic suite, knowledge, plugin, data-security, compilation, affected unit and behavior checks.
- Keep separately authorized live-model comparisons `NOT RUN` until actually executed.

Done when the integrated suite, documentation topology, coverage model, context budget and canonical product state agree.

## Documentation rule during implementation

Each RC.7 group reads the accepted design and prior group results, updates this plan and `progress.md`, and writes durable decisions to their existing owner. This is repository continuity for RC.7 itself, not a universal packet format.

## Review strategy

Use one review strategy for each material Skill group: targeted professional review or one clean-context cross-cutting review. Recheck only repaired findings and affected bytes unless conflicting evidence reveals a new blind spot.

## Change discipline

Each group must remain internally coherent: active Skill text, discovery metadata, contracts, documentation and affected tests change together. This prevents half-updated releases, but it does not replace the main Skill/professional-Skill evolution with a task-archetype workflow. Commit, push, tag, publish and installation remain separately authorized actions.
