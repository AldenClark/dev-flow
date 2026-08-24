# Dev Flow 2.0 RC.3 implementation

## Objective

Deliver a release-candidate-quality Dev Flow that reliably activates and recalibrates across real multi-turn work; turns warranted assurance methods into decision-useful tests, models, counterexamples, review evidence, or explicit fallbacks; keeps implementation and delegation inside an explicitly admitted boundary; preserves goals, non-goals, terminal conditions, and evidence through compaction and task synthesis; adapts to confirmed personal preferences without silent profiling; isolates unavailable capabilities honestly; binds final claims to current bytes; and integrates `repository-knowledge` without expanding ordinary-task ceremony.

## Actual status

Slices 0-12 and the corrected Slice 13 machinery are implemented but not yet refrozen. The runner accepts only bare exact scanner argv or one fixed absolute system-shell wrapper with canonical exact source; it rejects unsafe, noncanonical, leading-option, or Git-metadata-alias fixture paths, arbitrary same-basename shells, and extra operations. Initial repositories and runner-owned turn fixtures are validated before any write, and every repository-mutation turn declares the exact existing path set it may change. The runner executes only the candidate, retains bounded synthetic response/trajectory/delta evidence, deletes raw sessions and fixture repositories, and ends at manual assessment. The public transition lane owns observation validation. Method routing feeds back established repository/requirement prerequisites and does not let blocked alternatives mask ready methods. After two repairs to the same auxiliary mechanism without primary-terminal progress, the model-facing contract requires simplification, replacement, a qualified manual/native fallback, or deferral unless continued exploration is explicit. Earlier frozen failures remain historical; fresh full gates, a new freeze, reproducible artifact/install checks, complete R4, exact-SHA hosted evidence, publication, and active installation remain separate actions.

## RC.3 source scope

- Route/parser value-contract hardening.
- Routing precision for managed continuity and persisted local state.
- Multi-turn activation and recalibration guidance, fixtures, observation validation, and an opt-in runner.
- Capability-failure isolation and scope/evidence-freshness guidance with deterministic structural checks and semantic cases.
- Final integration and dogfood decision for `repository-knowledge`.
- Deterministic, model-semantic, privacy-safe dogfood, and isolated-install qualification.
- Closed/bounded/open discovery behavior, separate outcome/read/write/verification/action boundaries, and out-of-scope finding disposition.
- Method eligibility, readiness, fallback/abstention, realization, review-to-verification adjacency, and method-specific evidence evaluation without growing the method inventory by default.
- Monotonically narrowed child and nested-child delegation with root-owned scope expansion and actual-diff reconciliation.
- Compaction-resilient semantic continuation, terminal-condition persistence, long-running process supervision, and temporal evidence ownership.
- Explicit cross-task/repeated-attempt synthesis and reference-repository handling grounded in current repository truth.
- Confirmed personal engineering-profile integration plus opt-in sanitized local dogfood analysis and ordinary-conversation negative controls.

The release-orchestration extension boundary remains in `design.md` and `decisions.md`. A product-owned pilot, product-repository mutation, two-release soak, and second-product comparison are separate stable-release inputs and are not part of the RC.3 implementation chain.

## Planned affected source and evidence surfaces

The implementation starts from this bounded inventory and may add a path only after classifying it as a required defect or necessary enabler:

| Concern | Primary expected paths |
|---|---|
| kernel entry, execution, close | `skills/dev-flow/SKILL.md` |
| scope envelope, depth/breadth, continuation | `skills/dev-flow/references/quality-calibration.md`, `skills/dev-flow/references/orchestration.md` |
| method activation and realization | `skills/dev-flow/SKILL.md`, `skills/dev-flow/references/quality-calibration.md`, `skills/dev-flow/references/methodology-system.md`, task-facing method projection in `skills/dev-flow/scripts/dev_flow.py` |
| delegation attenuation | `skills/dev-flow/references/multi-agent-v2-orchestration.md` and active concise brief guidance |
| task/process/reference adapters | `skills/dev-flow/references/codex-native-adapters.md` |
| final-byte and volatile evidence | `skills/verification/SKILL.md`, `skills/verification/references/evidence-contract.md` when current ownership requires it |
| confirmed preference consumption | `skills/manage-engineering-profiles/SKILL.md`, `skills/dev-flow/scripts/engineering_context.py`, `evals/test_engineering_context.py` only where the existing contract is insufficient |
| privacy-safe dogfood analyzer | new maintainer-owned `skills/dev-flow-maintainer/scripts/analyze_dogfood.py` plus a focused test; include method eligibility/disposition/realization aggregates but no host-private storage reader |
| ordered semantic observations | `evals/flow-transition-semantic-cases.json`, `evals/test_flow_transitions.py`, `evals/run_transition_trials.py`, `evals/test_transition_runner.py` |
| deterministic/process contracts | existing closest `evals/test_dev_flow_v2.py`, `evals/contracts/`, and focused new tests only when no current owner can observe the invariant |
| maintained truth | `README.md`, `docs/evaluation-suite.md`, `CHANGELOG.md`, and this workstream only where public behavior or current status changes |

Do not modify routing schemas, capability registries, method inventory, version metadata, plugin inventory, or neutral preference values unless a failing implementation oracle proves that the current owner cannot express a confirmed requirement. Existing method annotations may be clarified or projected more completely only when a focused activation/realization oracle demonstrates the gap; such work must not add a new method family or duplicate catalog.

## Priority and ownership

| Priority | Required outcome | Primary owner | Release expectation |
|---|---|---|---|
| P0 | closed/bounded/open scope, finding disposition, and final-diff scope rejection | `dev-flow` | source and R4 gate |
| P0 | method eligibility, ready/blocked/fallback/abstain disposition, readiness recheck, realization, and review-to-verification adjacency | `dev-flow` + `verification` | source and affected R4 gate |
| P0 | monotonically narrowed delegation and root reconciliation | `dev-flow` | source and R4 gate |
| P0 | semantic continuation, terminal completion, process identity, first-failure preservation, and evidence freshness | `dev-flow` + `verification` | source and R4 gate |
| P0 | explicit task/reference synthesis with current-truth reconciliation and privacy boundaries | `dev-flow` + `repo-context` | source and R4 gate |
| P1 | task-facing method annotation/projection quality, cost-aware ranking, and selected-output negative oracles | `dev-flow-maintainer` | source gate; live effect claim separately budgeted |
| P1 | confirmed personal-profile integration and privacy-safe dogfood, including method funnel aggregates | `manage-engineering-profiles` + `dev-flow-maintainer` | source and privacy gate |
| P1 | bounded paired method marginal-utility trials on representative high-value shapes | `verification` + `dev-flow-maintainer` | qualification evidence only; not a deterministic source gate |

P0 and P1 are both in RC.3. Priority controls implementation order and admission evidence, not whether P1 is silently deferred.

## Implementation gates

| Gate | Required before work starts | Stop/replan condition |
|---|---|---|
| G0 worktree boundary | Reconcile the existing `repository-knowledge` diff and record every in-scope path. | An overlapping unknown/user-owned edit cannot be separated safely. |
| G1 contract baseline | Freeze canonical RC.2 route outputs and positive/negative/mutation cases. | A proposed change breaks an unapproved canonical input or output field. |
| G2 semantic-runner contract feasibility | Prove the CLI/config/identity/privacy/process contracts needed for isolated candidate, resume, fork, and sanitized observations without claiming model behavior. | The current Codex CLI cannot express or deterministically validate a bounded temporary lineage safely. |
| G3 source complete | Focused and full deterministic checks pass on current bytes. | A structural change requires persisted task state, a generic probe service, or a second route schema. |
| G4 release candidate | Separately authorized R4 trials, isolated installation, exact-byte review, and release checks pass. | Model budget/host evidence is unavailable or a required branch/authority gate fails. |
| G5 extension baseline | Freeze the original source-complete bytes and all newly confirmed positive, negative, compatibility, privacy, and mutation claims before changing active guidance. | A requirement has no observable oracle or duplicates an existing contract with conflicting semantics. |
| G6 scope-contract feasibility | Prove the scope envelope can remain ephemeral and that current workstream/brief/final-diff controls can carry it without a new route schema or packet. | Correct behavior requires a hidden persisted task state, generic authorization service, or mandatory lifecycle artifact. |
| G7 host-boundary feasibility | Prove cross-task and dogfood behavior can use supported host reads or sanitized observation input without private host storage coupling. | The only viable implementation requires raw transcript retention, automatic history scanning, or unsupported host internals. |
| G8 extension source complete | Focused and full deterministic/process-contract checks pass for Slices 6-12 on final relevant bytes. | Deep-versus-broad, method realization, delegation narrowing, continuation, privacy, or negative-control claims remain observable only by unbudgeted live-model inference. |
| G9 final release candidate | Separately authorized extended R4 trials, isolated installation, exact-byte review, and release checks pass. | Exact candidate identity, model budget, manual assessment, hosted evidence, or delivery authority is absent. |

G2 and G7 are bounded implementation feasibility checks, not model-quality trials. G2 is satisfied by deterministic command/config/identity/privacy/process contracts; actual candidate interpretation, resume/fork, and manual observation validity belong to G9. A separately authorized focused diagnostic may inspect those live mechanics but cannot satisfy R4. Raw local conversation content is never a repository fixture.

G0-G3 were completed for the original RC.3 scope. G4 is superseded by G9 because qualification against the pre-extension bytes would be stale. G5-G8 govern extension implementation; G9/S13 governs the only current release-candidate qualification path.

## Outcome slices

### Slice 0: Integrate the completed repository-knowledge baseline

Affected areas:

- current modified/untracked `repository-knowledge` files
- plugin manifest, governance, README, changelog, knowledge references
- `evals/test_repository_knowledge.py` and native suite wiring

Work:

- Treat the existing workstream marked `Complete` as an implementation baseline, not as a late parallel feature.
- Reconcile its exact diff before route/parser edits and keep unrelated user-owned changes untouched.
- Re-run structural, security, topology, link, budget, negative-trigger, and representative workspace checks.
- Add a stable `docs/index.md` because this repository has multiple durable knowledge surfaces that README does not enumerate.
- Record that a root `AGENTS.md` is not required for RC.3 unless the bootstrap plan identifies a concise repository-specific instruction that is not discoverable from README, Skills, manifests, or native checks. Do not create an empty router merely to silence a warning.

Completion evidence:

- Focused repository-knowledge tests and maintainer/contract validation pass on the reconciled bytes.
- `repository_knowledge.py check --root .` has no stable-index warning; a remaining root-AGENTS warning is paired with the recorded owner decision and is not suppressed in the checker.
- No repository outside this Git root is modified.

### Slice 1: Freeze the compatibility and behavioral baseline

Affected areas:

- `docs/workstreams/dev-flow-2.0-rc.3/`
- activation and large-task catalogs
- current RC.2 route/process tests

Work:

- Snapshot canonical fields for each public intent in compact and full modes, including route order, reasons, overlays, method/review projections, and exit status.
- Record the two approved semantic deltas: managed continuity no longer routes requirements by itself; `persisted-data` alone no longer adds migration.
- Convert dogfood shapes into sanitized cases for missed implicit activation, diagnosis-to-change, change-to-audit, blocked optional scanner, new-platform expansion, interruption/resume, and fork continuation.
- Add negative controls for lookup, one-line mechanical edit, local diagnosis with a known oracle, unchanged follow-up, and ordinary nearby documentation change.
- Define one failure-sensitive mutation/negative control for every changed claim.

Completion evidence:

- Every planned behavior has a positive oracle and a negative or mutation oracle.
- Baseline fixtures contain no transcript, credential, production value, external repository name, or personal absolute path.

### Slice 2: Make documented route values structured and replayable

Affected areas:

- `skills/dev-flow/scripts/dev_flow.py`
- `evals/test_dev_flow_v2.py`, activation cases, and CLI documentation

Work:

- Add a `route-task` argv preprocessor for documented value-taking options before argparse `choices` runs.
- Allowlist `diagnosis -> diagnose` and retain the canonical output `intent=diagnose` with an alias source.
- For invalid documented values, emit `status=invalid`, field, input, allowed values, bounded suggestions, and a correction only when exactly one safe replacement exists.
- Build replay from the original argv so ordering, repeated options, aliases, and all unrelated flags are preserved.
- Keep unknown flags, missing option values, and mutually exclusive syntax errors as argparse programmer diagnostics.
- Do not broaden fuzzy suggestions into automatically accepted aliases.

Documented value families to cover:

| Family | Expected invalid-value behavior |
|---|---|
| `intent` | accepted explicit aliases or structured invalid/correction |
| `risk`, `need`, `method-signal` | preserve the existing structured contract |
| `requirement-class` | preserve U1-U5 normalization and structured invalid output |
| `ui-impact`, `method-depth`, `mutation`, `unknown`, `work-mode`, `knowledge-impact`, `overlay` | structured invalid output; correction only when unambiguous |

Completion evidence:

- `diagnosis` routes successfully as `diagnose`; `diagnoise` exits 2 with JSON and a replayable correction.
- A matrix test proves every documented family avoids raw usage text for an invalid value.
- Unknown option and missing-value tests prove syntax errors remain clearly distinguished.
- All original flags survive correction replay and canonical RC.2 fixtures remain equivalent outside the two approved deltas.

### Slice 3: Fix routing precision without a new projection

Affected areas:

- route composition and overlay logic in `dev_flow.py`
- focused route tests, activation catalog, and large-task simulations

Work:

- Remove `work_mode == managed` as a standalone `requirements-design` trigger.
- Keep requirements routing for semantic change, design intent, ambiguity, material UI, explicit need, and affected public/data/security/compatibility semantics.
- Remove `persisted-data` as a standalone migration-overlay trigger while keeping its state-lifecycle method signal.
- Keep migration for explicit migration/overlay, schema, mixed-version/compatibility, deletion, rollback, and legacy migration task type.
- Preserve the current compact/full `routes` shapes and existing specialist fallback projection; do not add `route_details`.

Completion evidence:

- Closed managed U5 review omits requirements design; managed U1/design/ambiguous cases retain it.
- Persisted local state alone has no migration overlay; persisted state plus schema/version compatibility/rollback retains it.
- Owner-removal and overactivation mutations fail.

### Slice 4: Add transition-aware activation contracts and runner mechanics

Affected areas:

- main Dev Flow and relevant specialist guidance
- `evals/flow-transition-semantic-cases.json`
- `evals/test_flow_transitions.py`
- a new opt-in transition observation runner/validator, separate from unsupported 1.x paired evaluation code
- `docs/evaluation-suite.md`

Work:

- Define entry, intent change, boundary expansion, evidence invalidation, interruption/resume, fork, and close as recalibration events rather than states.
- Validate a fixture schema containing ordered turns, per-turn expected/forbidden observations, repository mutations allowed for that turn, and lineage mode (`resume`, `fork`, or unchanged follow-up).
- Extend observation evaluation to require one result per turn and preserve the first failure; deterministic CI validates fixture/observation contracts but does not invoke a model.
- Build an opt-in runner using an isolated temporary Codex home and synthetic Git repository. Do not use `--ephemeral` for a lineage that must resume/fork. Export only sanitized branch observations and redacted usage/failure metadata, then remove temporary session data.
- Add a feasibility test for candidate loading, resume, and cleanup before relying on the runner. Fork remains `NOT RUN` if the local candidate cannot exercise it safely.

Representative fixture shape:

```json
{
  "id": "TRANSITION-DIAGNOSE-CHANGE-REVIEW",
  "repository": {"README.md": "# Sample\n"},
  "lineage": "resume",
  "turns": [
    {"prompt": "Diagnose the failure.", "expected": ["diagnosis"], "forbidden": ["source-mutation"]},
    {"prompt": "Implement the proven fix.", "expected": ["route-task", "verification"]},
    {"prompt": "Audit the final diff.", "expected": ["change-review", "final-byte-evidence"]}
  ]
}
```

Completion evidence:

- Deterministic schema/observation tests fail for a missing turn, forbidden activation, authority violation, or reused stale observation.
- Removing an intent-change/final-diff trigger makes its structural or semantic oracle fail.
- Unchanged follow-ups do not repeatedly route or broaden specialists.
- Live host/session behavior remains `NOT RUN` until a separately authorized model attempt actually runs.

### Slice 5: Isolate capability failure and stale evidence honestly

Affected areas:

- `skills/dev-flow/references/quality-calibration.md`
- main Skill continuity/close guidance
- verification evidence guidance
- transition/failure semantic fixtures

Work:

- Add first-failure preservation, transient/invariant/authority/external classification, unchanged-context no-retry, observable retry triggers, safe-gate continuation, qualified fallback, and claim-limit guidance.
- Do not add readiness fields to `governance/capability-contracts.json`, route output, or persisted task state.
- Define managed semantic checkpoint output: completed/current/next outcomes, Git roots, user-owned changes, stale evidence, blockers, and recommended next slice.
- Require post-edit affected-scope freshness checks after implementation, delegated edits, review repair, final-diff expansion, and delivery preparation.
- Keep task/worktree creation and delivery actions advisory until separately authorized.

Completion evidence:

- Structural tests protect the guidance contract and its negative boundary.
- Semantic observations show one invariant failure is not repeated in an unchanged context, safe unrelated checks continue, fallback claims are narrower, and a changed readiness fact permits one retry.
- A post-test affected edit invalidates the earlier PASS; an unrelated documentation edit does not force irrelevant test reruns.
- A new platform/repository updates scope and evidence instead of inheriting another boundary's claims.

### Slice 6: Freeze the extension compatibility and behavior baseline

Affected areas:

- current Dev Flow, profile, orchestration, verification, and host-adapter guidance
- deterministic/process-contract/transition fixture catalogs
- sanitized historical task shapes and ordinary-conversation negative controls

Work:

- Freeze the original RC.3 source-complete deterministic outputs and supported public route behavior before extension edits.
- Map every confirmed P0/P1 requirement to exactly one owner, positive oracle, negative or mutation oracle, and implementation slice.
- Deduplicate scope checkpoints, continuation checkpoints, evidence freshness, and cross-task recovery so one concept has one canonical owner.
- Convert historical evidence into generic task shapes only: closed implementation, broad design exploration, user scope correction, reference-only input, adjacent issue deferral, repeated attempt, explicit task reference, terminal continuation, and long-running gate.
- Add sanitized method shapes for warranted-but-unrouted verification/review, early blocked-only selection, repository-discovery readiness change, explicit fallback, reasoned abstention, review-to-verification adjacency, and selected-without-realization.
- Record ordinary non-repository conversation shapes as negative triggers without content, identity, stable repository scoring, or raw transcript retention.

Completion evidence:

- An affected-contract matrix has no orphan, conflicting owner, duplicated mechanism, or untested material claim.
- Canonical valid route fixtures remain field-equivalent and raw private history is absent from Git diff and fixtures.
- Mutation inventory includes every new behavior family before implementation begins.
- The method baseline separately records eligibility, candidate selection, ready/blocked state, later disposition, visible owned output, and evidence effect; it does not infer hidden reasoning from absent method names.

### Slice 7: Implement bounded execution and exploration guidance

Affected areas:

- `skills/dev-flow/SKILL.md`
- `skills/dev-flow/references/quality-calibration.md`
- managed-work and repository-context guidance where boundaries are reconstructed
- verification evidence/final-diff guidance

Work:

- Define the ephemeral scope envelope: outcome/terminal condition, protected behavior/non-goals, discovery mode, read boundary, mutation boundary, verification boundary, action authority, and expansion/stop triggers.
- Make `closed` the implementation/repair default, `bounded` the diagnosis/review default, and `open` dependent on explicit exploration intent.
- State and test that depth, red/blue methods, formal rigor, managed mode, model capability, and reasoning effort do not grant breadth.
- Add required-defect, necessary-enabler, optional-opportunity, and unrelated finding disposition.
- Recalibrate only for a material premise; keep necessary causal inspection and affected verification available without granting mutation breadth.
- Require final-diff/dependency/tool reconciliation to reject unadmitted implementation.
- Keep the behavior guidance-only where no current deterministic enforcement surface exists; do not add a route field or packet merely to serialize the envelope.

Completion evidence:

- Structural checks protect every envelope dimension and the explicit-open boundary.
- Semantic fixtures distinguish closed, bounded, and open behavior and fail if `deep` alone becomes open.
- A necessary caller/consumer investigation remains allowed while an optional adjacent repair remains excluded.
- Existing direct-mode and narrow-fix negative controls remain quiet and low ceremony.

### Slice 8: Close method activation, readiness, realization, and evidence

Affected areas:

- `skills/dev-flow/SKILL.md`
- `skills/dev-flow/references/quality-calibration.md`
- `skills/dev-flow/references/methodology-system.md`
- task-facing method activation/projection in `skills/dev-flow/scripts/dev_flow.py`
- verification/change-review guidance only where current owner procedures need a method-disposition handoff
- focused selector, route, semantic observation, and dogfood-contract tests

Work:

- Separate method eligibility, candidate selection, readiness/admission, realization, and evidence effect. Do not treat a selected ID, method mention, or generated artifact as success.
- Trigger one bounded method disposition from observed failure mechanisms in verification, testing, review, and audit: weak/easy-to-fake oracle, preservation/compatibility, state/order/concurrency/recovery, interacting rules, conflicting evidence/repeated failure, model/Skill/agent evaluation, or material trust/data/public-contract consequence.
- Preserve three legal dispositions: execute one ready method; execute an explicit blocked-method fallback while retaining the limitation; or abstain because the owning specialist already supplies the sufficient procedure. A selected method cannot silently disappear.
- Recheck readiness after repository discovery and requirement confirmation, then only at an oracle-breaking failure, repeated non-progress, or material verification/review boundary. Never auto-satisfy a prerequisite; identify only an evidence-backed cheapest safe observation or retain the fallback.
- Improve the task-facing projection of existing maintained annotations so an admitted method carries why/avoid conditions, required facts, minimum action, expected output, evidence obligation, limitation, cost, and fallback without loading the full catalog.
- Rank ready, directly relevant, lower-cost methods before blocked/high-cost alternatives. For review plus `oracle-challenge`, compare verification ownership before surfacing independent N-version derivation. Keep one method by default and at most three complementary methods.
- Require realization in an owner artifact or oracle: test/property/mutation, counterexample, state/decision/compatibility model, review attack surface, evidence matrix, or explicit claim limitation. Method depth remains inside the S7 scope envelope.
- Extend deterministic and ordered semantic cases with ready, blocked-to-ready, fallback, abstain, selected-without-realization, review-to-verification, and ordinary-review negative controls.
- Add a bounded paired-evaluation contract for a few high-value task shapes. Freeze requirement, repository bytes, model/tool/Skill identity, deterministic acceptance, and first attempts; compare with-method/without-method outcomes, regressions, trajectory, and cost separately. Do not run the live pairs without separate budget authorization.

Completion evidence:

- An ordinary review with a strong native oracle remains method-quiet, while a weak-oracle review receives a practical verification method or fallback before blocked N-version guidance.
- A repository-discovery fact can move a candidate from blocked to ready; deleting the readiness recheck fails a mutation oracle, and inventing a prerequisite fails a truthfulness oracle.
- Deleting the selected method's concrete output, or returning success after selection without ready/fallback/abstain disposition, fails deterministic or semantic observation validation.
- Method-selection count and method-name mentions cannot satisfy the grader; a sufficient specialist procedure may abstain without penalty.
- Canonical RC.2 method IDs and valid route fields remain compatible, full-pool context is not loaded, and no method inventory expansion occurs.

### Slice 9: Enforce monotonically narrowed delegation

Affected areas:

- `skills/dev-flow/references/multi-agent-v2-orchestration.md`
- concise delegated-brief guidance and any active templates/tests that consume it
- root integration and final-diff audit guidance
- agent routing semantic cases; route profile policy only if a demonstrated gap exists

Work:

- Require each child objective and read/write/tool/dependency/external/re-delegation authority to be a subset of the parent slice.
- Keep product semantics, new repositories/dependencies/platforms, public-contract changes, optional-finding promotion, and scope expansion root-owned.
- Require a child to stop the affected branch and return a bounded expansion request/finding when the subset is insufficient.
- Carry the intersection of all ancestor constraints into nested delegation and require downstream updates or cancellation when the parent boundary changes.
- Prefer one agent; delegate only an independently useful bounded outcome. Do not use reasoning profile, agent count, or breadth role as scope authority.
- Reconcile actual returned writes, dependencies, tools, generated surfaces, and evidence; use host-enforced path/tool boundaries when available without claiming them when unavailable.

Completion evidence:

- Child and nested-child expansion mutations fail.
- A compliant report paired with an out-of-scope diff is rejected.
- A read-only explorer cannot mutate; a bounded writer cannot spawn broader work; a scope change returns to root/user ownership.
- Existing independent-review identity and same-context downgrade contracts remain intact.

### Slice 10: Make continuation, terminal completion, and process supervision semantic

Affected areas:

- Dev Flow continuity/close guidance
- managed orchestration and quality-calibration checkpoint guidance
- Codex-native adapter guidance for task/process/session operations
- verification freshness and transition fixtures

Work:

- Extend resume/compaction/fork/handoff reconciliation with the terminal condition, discovery mode, mutation/action boundary, explicit non-goals, rejected expansions, active process identity, and stale volatile facts.
- Treat workstream/current Git/runtime as authority and conversation summaries as untrusted recovery hints.
- Interpret `implement fully`, `keep going`, and equivalent terminal language as persistence within admitted scope, not dependency/delivery/external/destructive authority.
- Continue safe ready slices automatically; stop at genuine blocker, U1/material expansion, missing authority, or predeclared attempt/exploration limit.
- Supervise only an actually launched process/session; preserve its identity and first failure, wait with bounded backoff, distinguish running/failure/completion, and never duplicate unchanged work.
- Separate repository, runtime, web, and release evidence owners and recheck only volatility that can change the next material decision.

Completion evidence:

- Compaction/resume cases retain non-goals and reject a stale or broader next action.
- Terminal continuation completes the admitted outcome while delivery actions remain unauthorized.
- Process cases reject duplicate restart, false failure while running, and later-success masking of the first failure.
- An unrelated documentation edit does not trigger broad reruns; an affected or volatile fact change invalidates the relevant claim.

### Slice 11: Add explicit cross-task, reference-repository, and repeated-attempt synthesis

Affected areas:

- Codex-native adapter guidance
- repository-context/repository-knowledge integration boundaries
- transition fixtures and sanitized observation schema

Work:

- Trigger cross-task reads only from explicit references, explicit repeated-attempt comparison, or an authorized selected-history audit.
- Require every referenced task to be read through a supported host interface and treated as untrusted history.
- Extract claims, assumptions, evidence, failures, contradictions, open questions, and next actions without persisting raw transcripts.
- Reconcile material claims against current repository/runtime/primary external truth before adoption.
- Keep repeated tasks and forks separate until the user requests synthesis; never auto-rank by recency or auto-merge/archive/modify tasks.
- Treat analogy repositories as references, not program members, authorities, compatibility contracts, or mutation targets. Route confirmed program topology to repository knowledge.

Completion evidence:

- Explicit-reference cases read every named task and surface stale/contradictory evidence.
- An unreferenced ordinary task performs no ambient history scan.
- A reference repository cannot authorize target-repository design or mutation.
- Repeated-attempt cases converge on current evidence without declaring the newest attempt correct by default.

### Slice 12: Integrate confirmed preferences and privacy-safe dogfood

Affected areas:

- Dev Flow to `manage-engineering-profiles` integration guidance
- profile resolution/validation tests where a new consumer behavior is required
- a sanitized dogfood observation contract and maintainer-only analyzer/validator
- company-data-security fixtures and ordinary-conversation negative controls

Work:

- Propose personal workflow preferences only with explicit owner approval and record layer, scope, strength, observable effect, conflict behavior, and review trigger through the existing profile contract.
- Never edit personal values as suite maintenance or let them weaken repository/team must-level controls.
- Add a maintainer-only local analysis path that accepts authorized host-selected reads in memory or a sanitized observation input; emit counts, task shapes, transitions, correction categories, method eligibility/selection/readiness/disposition/realization aggregates, and limitations only.
- Keep raw transcript text, credentials, production values, absolute personal paths, automatic profile writes, external uploads, and stable person/repository productivity scores out of output and Git.
- Add ordinary ChatGPT-style questions, writing, public lookup, and daily-life assistance as Dev Flow negative controls.
- If direct host history access is not portable, retain the sanitized-input analyzer and report the host adapter as `BLOCKED`; do not couple core behavior to private storage.

Completion evidence:

- Profile application requires explicit approval and clean-profile invariance still passes.
- A missing personal layer returns neutral behavior; a repository must-level conflict cannot be weakened.
- DLP/privacy checks reject raw transcript, secret, personal path, or automatic profile persistence mutations.
- Ordinary conversation controls remain silent and dogfood output contains only the documented aggregate schema.
- Method funnel output cannot become a user/repository score, contains no raw content, and distinguishes visible evidence from unobservable internal reasoning.

### Slice 13: Qualify the exact extended RC.3 candidate

Affected areas:

- release documentation and version metadata
- exact-SHA CI/artifact/install surfaces selected by R1-R4 policy

Work:

- Run focused checks first, then the full deterministic/process-contract suite on final relevant bytes.
- Predeclare nine extended R4 categories: implicit entry; material transition; failure isolation; method disposition/realization; evidence freshness; scope convergence; constraint preservation across continuation/delegation; explicit context synthesis/adaptation; and negative-control quietness. Each category contains its relevant subcases, such as ready/blocked/fallback/abstain methods, review-to-verification adjacency, selected-output mutation, closed/open exploration, finding disposition, nested delegation, compaction, terminal continuation, process supervision, task references, profile confirmation, and ordinary chat. Apply the repository rule of at least three cases per affected category and three independent first attempts per case, subject to a separately approved model/token budget; do not multiply one behavioral domain into artificial categories.
- Run isolated candidate installation and candidate-loading/session feasibility in a temporary Codex home.
- Preserve first failures; report activation, method selection fit, readiness/disposition, realization, outcome/trajectory effect, regressions, cost, scope conformance, privacy, and authority separately; and produce no aggregate effect/productivity score.
- Perform final same-context review or an authorized clean-context review against the exact candidate.
- Commit, push, tag, release, publication, active installation, and personal-profile activation remain separately authorized actions.

Completion evidence:

- Deterministic, process-contract, plugin, knowledge, documentation, security, compilation, JSON, and diff checks pass on final bytes.
- Every extension mutation has a failure-sensitive oracle and every protected canonical contract still passes.
- Method live evidence, if authorized, uses fixed paired conditions and cannot be replaced by activation counts; if not authorized it remains `NOT RUN` without blocking deterministic source completeness.
- Required authorized model-semantic cases pass, or unavailable budget/host evidence is honestly `BLOCKED`/`NOT RUN` and RC.3 is not declared release-ready.
- Exact candidate identity, installation result, review independence status, evidence limits, and rollback target are reported.

## Ordering

```text
S0 integrate existing repository-knowledge bytes
  -> S1 freeze compatibility/behavior baseline
  -> S2 structured route values
  -> S3 route precision
  -> G2 runner feasibility
  -> S4 transition contracts/runner
  -> S5 failure isolation and evidence freshness
  -> G5 extension baseline
  -> S6 extension compatibility/behavior baseline
  -> G6 scope-contract feasibility
  -> S7 bounded execution and exploration
  -> S8 method activation/readiness/realization/evidence
  -> S9 narrowed delegation
  -> S10 semantic continuation and process supervision
  -> G7 host-boundary feasibility
  -> S11 cross-task/reference synthesis
  -> S12 confirmed preferences and privacy-safe dogfood
  -> G8 extension source complete
  -> S13 exact-candidate qualification
```

S2 and S3 may share one code slice only if baseline tests isolate the parser and semantic deltas. S4 must not depend on the unsupported 1.x paired-evaluation runner. S5 and S7-S12 include guidance/semantic behavior and must not be presented as deterministic runtime enforcement where the host lacks a control surface. S7 precedes method realization so deeper methods cannot broaden scope; S8 precedes delegation and continuation so the same disposition contract survives child work and long runs; S9 precedes cross-task and profile work so delegated readers cannot receive broader history or personal-data authority than the root. S13 begins only after every source edit and generated surface is frozen.

## Delivery boundary

The current request authorizes RC.3 repository-local release preparation and qualification work. It does not by itself specify a model/token ceiling or authorize independent-agent dispatch, commit, push, tag, GitHub Release, Marketplace publication, active installation, personal-profile activation, deployment, migration execution, or product pilot actions; those action-specific gates remain separate.
