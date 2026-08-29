# Dev Flow 2.0 RC.4 requirements

## Outcome

Dev Flow 2.0 RC.4 makes the quality kernel converge reliably during long and operationally constrained repository tasks. It preserves RC.3's activation, evidence, authority, and negative-trigger behavior while making repeated routing, auxiliary non-progress, managed-work contradictions, shared-resource conflicts, test-system false greens, dirty-worktree ownership, and task-history failure observable and actionable.

RC.4 is a convergence and operations hardening release. It is not a larger methodology catalog, a generic task manager, or a return to the persisted 1.x workflow engine.

## Confirmed context

- The version owner confirmed the detailed RC.4 requirement understanding on 2026-08-28.
- `main` was clean at `v2.0.0-rc.3` when this workstream was created.
- Post-RC.3 dogfood found strong use of negative controls, black-/white-box verification, systematic debugging, honest evidence states, evidence freshness, narrow authority, and ordinary-task quietness.
- Seven material repository tasks used Dev Flow after RC.3 and produced about forty actual `route-task` invocations. The cost was concentrated in a small number of long test/UI tasks rather than uniformly spread.
- RC.3 already states unchanged-follow-up suppression, cumulative auxiliary convergence, explicit task-history boundaries, final-byte evidence, and semantic continuation. Those controls are primarily guidance plus semantic evaluation and were not followed consistently in the observed long tasks.
- RC.3 release qualification retained two explicit `WAIVED` semantic gaps: delegation reconciliation did not explicitly request renewed authority, and reference-repository comparison was absent or weak in some attempts.
- The repository uses Python standard-library tooling, Markdown workstreams, JSON catalogs/contracts, and deterministic `unittest`-based checks. RC.4 does not need a new external dependency.

## Actors and goals

### Repository contributor or coding agent

Needs to:

- continue an admitted objective without repeatedly reloading an unchanged route;
- know when a material fact invalidates only part of the prior route or evidence;
- stop auxiliary repair loops before they replace the primary outcome;
- distinguish product-test success from test-system validity;
- operate safely when another task owns a simulator, emulator, port, cache, container, or device;
- preserve user-owned dirty-worktree changes and report only the active slice's writes.

### Supervising user or repository owner

Needs to:

- read the actual current slice, terminal condition, hard conditions, blockers, evidence limits, and owned paths without reconstructing the task transcript;
- trust that a completion claim cannot silently contradict the managed workstream;
- retain authority over scope expansion, destructive cleanup, delivery, dependencies, and external actions;
- receive honest degraded results when host history, resources, reviewers, or model budget are unavailable.

### Dev Flow maintainer

Needs to:

- prove that new controls are used only on positive triggers and that ordinary tasks remain quiet;
- evolve RC.3 additively and keep RC.2/RC.3 install and rollback boundaries understandable;
- evaluate convergence and activation without productivity scores, raw transcript retention, or method-count incentives;
- qualify final candidate bytes without repeating large model evaluations after every auxiliary repair.

## Required behavior

### Incremental routing and recalibration
<!-- requirement: RC4-ROUTE -->

- An unchanged follow-up inside the same outcome, roots, discovery mode, mutation/action boundary, risks, required capabilities, method prerequisites, and terminal condition must continue without a fresh full route.
- A material change must invalidate only the affected routing decisions and evidence. Material dimensions include intent, requirement class/confirmation, work mode, repository/platform facts, needs, risks, scope/authority boundaries, method readiness, review requirement, and knowledge impact.
- The public router must support an optional caller-supplied prior RC.4 route for deterministic comparison. Dev Flow must not persist, discover, or ambiently cache prior routes itself.
- The comparison basis must cover every public input that can affect any route output and bind the router-semantics version. Free-form repository facts are equality-compared through a bounded digest rather than copied into the basis.
- Comparison must distinguish `unchanged`, `changed`, and `incompatible-prior-route`. An incompatible or invalid prior route causes a normal full route plus an explicit comparison limitation, not guessed reuse.
- The normal no-comparison route contract remains valid. No caller is required to persist a route artifact.

### Convergence guard
<!-- requirement: RC4-TRUTH -->

- The primary terminal condition, not local parameter changes or tool activity, defines progress.
- Two consecutive repairs or retries to the same auxiliary mechanism without advancing the primary terminal condition create a hard convergence checkpoint.
- The checkpoint must resolve to exactly one of: prove the mechanism indispensable and continue with explicit authority/evidence; simplify; replace; use a qualified narrower fallback; defer; or report `BLOCKED`/`NOT RUN`.
- A changed prompt, retry parameter, wrapper, rubric, selector, timeout, or implementation detail does not reset the count when the primary outcome is unchanged.
- A third same-mechanism tweak is forbidden until the checkpoint has a valid disposition.
- Managed work records only an active material checkpoint in `progress.md`; it does not retain an attempt log. Direct work keeps the checkpoint in the active task context.

### Managed Truth Checker

- Opted-in RC.4 workstreams expose a small versioned Markdown contract across `implementation.md` and `progress.md`.
- A read-only checker must detect structural contradictions among workstream state, slice status, current slice, terminal condition, hard conditions, deferrals, path ownership, and evidence limits.
- Every hard condition declares whether it gates `implementation` or `qualification`. `implementation-complete` requires all implementation gates; `release-qualified` and this release's terminal `closed` state require both classes. Future qualification gates may remain `NOT RUN` while implementation is active or complete, but may not be represented as passed.
- A terminal state is invalid while a required in-scope slice is incomplete, an applicable hard condition is open/failed/flaky/blocked/not-run without an allowed disposition, an active convergence checkpoint is unresolved, or the current slice contradicts the implementation table.
- A deferred slice requires an explicit decision reference. A waived hard condition remains `WAIVED`, never `PASSED`, and requires an owner decision reference.
- The checker must state its claim limit: structural consistency is not semantic correctness, test coverage, evidence freshness, independent review, or delivery authorization.
- Existing workstreams without the RC.4 contract marker remain readable and valid; strict checking is opt-in unless their repository later migrates them.

### Shared resource ownership
<!-- requirement: RC4-RESOURCE -->

- RC.4 may use host-local, short-lived, volatile leases for scarce resources. This is the confirmed narrow exception to RC.3's no-lease rule.
- The initial resource classes are simulator, emulator, physical device, TCP port, DerivedData/build cache, and Docker/container runtime namespace. Additional classes require evidence and a maintained allowlist change.
- Acquire, conflict, renew, expiry, release, and stale recovery must be explicit and race-safe on one host.
- Every lease transition must be serialized on one validated local filesystem; unsupported or environment-controlled roots whose ownership/atomicity cannot be established fail closed. Windows open/delete behavior and crash residue are explicit compatibility cases.
- A lease is scoped to one opaque resource identity and one opaque owner identity. It stores no task title, prompt, repository contents, source paths in clear text, secret, personal data, or cross-host identity.
- Release requires the matching lease token. Expiry permits bounded stale recovery; active unexpired leases cannot be stolen or cleaned by default.
- Lease failure produces a structured outcome: acquired, conflict, expired-recovered, released, invalid, or unavailable. It does not authorize killing processes, deleting caches, shutting down devices, or mutating another task.
- If a stable owner identity or safe host-local store is unavailable, the task uses isolation, waits, serializes work, or reports `BLOCKED`; it must not pretend a lease exists.

### Resource and evidence preflight

- High-growth or scarce-resource work can measure free disk, estimated growth, configured reserve, writability, and requested-resource ownership before launch.
- A preflight with no repository-, user-, or caller-supplied budget may report observations but cannot claim sufficient capacity from an invented universal threshold.
- Cleanup is limited to verified current-task artifacts and remains separately authorized when destructive. No recursive broad cleanup target, ambient cache purge, or other-task cleanup is inferred.
- First failure, bounded logs, final evidence, and rollback-critical artifacts have explicit retention priority. Disposable generated intermediates may be removed only through a scoped owner rule.

### Test-system engineering
<!-- requirement: RC4-TEST-SYSTEM -->

- A new `test-system-engineering` specialist owns the integrity of test discovery, selection, harness wiring, fixture isolation, runner result interpretation, oracle sensitivity, negative controls, flake discrimination, and test-resource cleanup.
- `verification` continues to own the product or repository claim and evidence status. The specialist cannot turn a valid harness into proof of untested product behavior.
- The specialist activates only when the task changes test infrastructure or exposes weak-test facts such as false green, zero-test discovery, selector uncertainty, inert assertions, mock bypass, environment pollution, or flaky baseline. Ordinary feature tests continue through `verification` alone.
- A green result is insufficient when discovery or oracle sensitivity is in question. At least one practical negative control must demonstrate that the relevant gate can fail.
- The existing methodology pool does not grow merely because the specialist is added.
- Capability admission must preserve explicit context budgets. Freeze the current aggregate Skill-description and ordinary-static byte baselines before source changes; any description-cap increase is limited to the measured new specialist description plus a small documented margin, while the existing ordinary-static cap remains unchanged and detail moves to on-demand references.

### Dirty-worktree slice ownership
<!-- requirement: RC4-DIRTY -->

- Managed slices declare repository-relative write prefixes, read-only prefixes when material, and protected/user-owned paths.
- At start/resume and before completion, current Git roots and changed paths are reconciled with that boundary.
- In an uncommitted multi-slice worktree, accumulated work is the union of completed-slice and active-slice write prefixes. The active mutation boundary remains only the active slice. The checker may account for the accumulated union but cannot prove which slice authored a path or that a completed slice was not later modified.
- Paths outside the active slice are not automatically reverted, staged, reformatted, regenerated, or attributed to the current task.
- Concurrent writers require disjoint declared writes or isolated worktrees. A declared boundary is advisory unless the host provides enforcement; final Git inspection remains authoritative.
- The checker may detect undeclared changed paths but cannot infer authorship. Ambiguous ownership remains a blocker or explicit limitation.

### Task-history fallback
<!-- requirement: RC4-HISTORY -->

- Explicit named-task synthesis continues to use every named task when the host interface is available.
- The first host read failure is preserved. An unchanged failure is not retried. One bounded retry is allowed only after a changed host fact, corrected task identity, restored connection, or explicit user request.
- After fallback, only current context, current repository/runtime truth, and user-supplied task content can support the result. Missing historical claims remain `BLOCKED` or an explicit synthesis limitation.
- Dev Flow never ambiently scans, ranks, archives, merges, mutates, or treats task history as authority.

### Privacy-safe dogfood
<!-- requirement: RC4-DOGFOOD -->

- The dogfood analyzer accepts sanitized observations for material transitions, route comparison, convergence checkpoints, resource conflicts, workstream consistency, test-system activation, evidence state, and ordinary-task negative controls.
- Observations contain bounded enums/counts and opaque case identities only. They do not contain prompts, task titles, source snippets, file contents, secrets, personal data, or raw transcripts.
- Reports expose funnels and failure categories. They do not produce productivity, agent, user, or aggregate quality scores.

### RC.3 residual-risk closure
<!-- requirement: RC4-WAIVERS -->

- Delegated work that discovers a required expansion must return a bounded expansion request; root continuation requires explicit renewed authority before the expanded action.
- Reference-repository comparison must either inspect the explicitly admitted source, reject it as non-authoritative or irrelevant with rationale, or report the source as unavailable. Silent omission does not pass.
- RC.4 qualification does not automatically inherit RC.3 waivers. Each residual gap must be `PASSED`, explicitly re-waived by the version owner, or remain release-blocking.

## State model

The observable task states are `QUIET`, `ADMITTED`, `ROUTED`, `EXECUTING`, `RECALIBRATION_REQUIRED`, `CONVERGENCE_DECISION`, `BLOCKED`, `NOT_RUN`, `EVIDENCE_READY`, and `COMPLETE`.

Required transitions:

| Current state | Event/guard | Next state | Required action |
|---|---|---|---|
| `QUIET` | material repository task admitted | `ADMITTED` | establish scope, facts, authority, and oracle |
| `ADMITTED` | routing required | `ROUTED` | run one bounded route |
| `ROUTED` | route decisions available | `EXECUTING` | start the smallest ready slice |
| `EXECUTING` | material routing fact changes | `RECALIBRATION_REQUIRED` | invalidate affected decisions/evidence only |
| `RECALIBRATION_REQUIRED` | delta route resolved | `EXECUTING` | continue with updated boundaries |
| `EXECUTING` | two auxiliary non-progress repairs | `CONVERGENCE_DECISION` | choose and record one allowed disposition |
| `EXECUTING` | unavailable authority/resource/capability | `BLOCKED` or `NOT_RUN` | preserve failure and narrow the claim |
| `EXECUTING` | all terminal conditions met on current bytes | `EVIDENCE_READY` | inspect final scope and claim limits |
| `EVIDENCE_READY` | no unresolved hard condition | `COMPLETE` | report outcome without implying delivery authority |

Forbidden edges include unchanged `ROUTED -> ROUTED`, unresolved `CONVERGENCE_DECISION -> auxiliary retry`, unresolved hard condition `-> COMPLETE`, unowned resource `-> destructive cleanup`, and green command exit `-> EVIDENCE_READY` when test discovery or oracle sensitivity is unproved.

## In scope

- Additive route comparison and recalibration projection.
- RC.4 workstream Markdown contract and read-only consistency checker.
- Active convergence checkpoint semantics and deterministic checks.
- Host-local resource lease helper and resource preflight.
- `test-system-engineering` Skill, capability admission, routing, and evaluation.
- Dirty-worktree slice boundaries and undeclared-path detection.
- Bounded task-history retry/fallback semantics.
- Privacy-safe dogfood schema/report extensions.
- RC.3 waived-gap closure, documentation, compatibility, packaging, and exact-candidate qualification.

## Out of scope

- A generic task/project manager, scheduler, lifecycle database, or hidden task ledger.
- Cross-host/distributed resource scheduling or a daemon.
- Automatic process killing, simulator shutdown, cache deletion, port eviction, or disk cleanup.
- Ambient task-history collection, automatic history mining, task mutation, or long-term memory.
- Productivity scoring, composite quality scoring, method-count targets, or user/agent ranking.
- New methodology families or broad catalog expansion.
- A universal test runner that replaces repository-native commands.
- A general authorization/policy service, cryptographic principal chain, or security boundary claim.
- Automatic worktree/task creation, commit, push, tag, release, installation, deployment, or external communication.
- Product-specific release orchestration.

## Acceptance behavior

- Zero unchanged duplicate routes in deterministic and semantic continuation cases.
- Every declared material route-basis change produces exactly one bounded recalibration with the expected invalidated decisions.
- Every two-strike auxiliary case blocks a third same-mechanism tweak until an allowed disposition is present.
- The workstream checker rejects every seeded contradiction and accepts a consistent active and implementation-complete fixture while retaining its claim limitation.
- All lease race, token, expiry, renewal, conflict, privacy, and cleanup-boundary tests pass on supported local platforms; unsupported primitives are `NOT RUN` or use a documented safe fallback.
- Resource preflight never invents a capacity threshold and never deletes data.
- Test-system negative controls detect zero discovery, wrong selectors, inert assertions, polluted fixtures, and misleading runner exits in representative fixtures.
- Ordinary feature verification does not activate the test-system specialist without a positive trigger.
- Dirty-worktree fixtures preserve pre-existing changes and expose undeclared paths without attributing or reverting them.
- Task-history fixtures preserve the first failure, forbid unchanged retry, allow one changed-fact retry, and produce an honest fallback limitation.
- Dogfood output remains aggregate, bounded, non-scoring, and content-free.
- Existing RC.3 route commands and output fields remain valid when no RC.4 option is used.
- Candidate qualification closes or explicitly disposes every RC.3 waiver and binds evidence to final candidate bytes.

## Static traceability and drift
<!-- requirement: RC4-SCAN -->

- RC.4 keeps a bidirectional machine-checked trace from stable requirement IDs and D1-D15 decisions to implementation owners and executable test/case IDs.
- Local implementation scans cover every changed worktree path; clean CI scans derive changed files from the immutable event base/head diff rather than an empty checkout worktree.
- A reported 100% means every declared RC.4 requirement has existing implementation and a structurally verified executable test/case reference, and every changed path is owned. It does not claim branch, statement, semantic, runtime, or cross-platform coverage.

## Qualification policy
<!-- requirement: RC4-IDENTITY -->

- R1-R3 remain deterministic and repository-native.
- Development uses focused RC.4 transition and failure cases; failed auxiliary evaluator work obeys the same two-strike convergence rule.
- Final R4 retains three complete-catalog independent first attempts on one frozen semantic candidate. Spend is bounded by completing dry-run runner/observer/catalog contracts and focused semantic development before freeze; qualification has no content retries or local evaluator tuning.
- Every live execution reserves its complete allowance from one cumulative campaign ledger before model spend. Unchanged semantic-runtime and qualification-execution identities reject a rerun and reuse prior evidence; changed identity invalidates only the affected claim and does not itself renew spend authority. Interruptions terminate the process tree and preserve bounded partial evidence and known usage.
- After two auxiliary repairs without primary qualification progress, further execution requires an explicit owner disposition. A bounded release-specific exception is `WAIVED`, not `PASSED`, and cannot support stable-release or population-effectiveness claims.
- Model evidence binds to the exact semantic runtime inputs and a separate qualification-execution identity covering the runner's transitive repository-local dependencies, complete catalog/fixtures, observer/scoring contracts, Codex executable digest, model/reasoning settings, and environment policy. Bounded evidence-only documentation may be recorded afterward only when an allowlist proves both identities unchanged. Deterministic, artifact, manifest, and install evidence binds to the final release commit.
- Live model execution requires separate model and token-budget authority. Lack of that authority is `NOT RUN` and cannot qualify the release.
- Independent review requires an actually dispatched clean-context reviewer. Without that authority, same-context review reports `common-mode-risk` and does not satisfy the independent gate.

## Constraints and protected behavior
<!-- requirement: RC4-COMPAT -->

- RC.4 evolves RC.3 additively. Existing canonical route inputs, fields, Skills, negative triggers, installation layout, and Markdown workstreams remain valid.
- RC.2 remains a readable/installable rollback boundary. RC.4 introduces no repository data migration.
- Host-local leases are volatile operational coordination only and cannot become repository or cross-host task state.
- Workstream structure is repository continuity; it is not runtime authority or semantic proof.
- Existing evidence statuses remain distinct: `PASSED`, `FAILED`, `FLAKY`, `BLOCKED`, `NOT RUN`, and `WAIVED`.
- Final evidence, review, delivery readiness, and external action authority remain separate.

## Facts, decisions, and assumptions

- Confirmed user decisions: use host-local short-lived leases; keep RC.3-to-RC.4 compatibility additive; require post-RC.4 real-task soak before stable 2.0 consideration.
- Confirmed scope: P0 and P1 capabilities are both in RC.4; priority controls order, not silent deferral.
- Bounded assumption: current standard-library filesystem primitives are sufficient for single-host lease atomicity. Implementation must re-open the design if supported platforms disprove this.
- Bounded assumption: opted-in Markdown headings/tables can support useful contradiction detection without becoming a semantic database. Seeded false-positive/false-negative tests must challenge this assumption.
- Planning-time evidence baseline (historical): live host integration behavior, cross-platform lease behavior, independent review, and model-semantic qualification had not run, and the runner had not yet implemented RC.4 semantic-runtime identity separation. Current implementation and evidence status is owned by `progress.md`; this baseline does not override it.

## Open decisions

- None at requirement level. Implementation discoveries that change public fields, supported resource classes, authority, persistence, or qualification strength must return to requirements/design.
