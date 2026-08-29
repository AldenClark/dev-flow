# Dev Flow 2.0 RC.4 implementation-plan audit

## Planning-boundary verdict (historical)

The RC.4 workstream is **implementation-ready at the planning boundary**. The confirmed semantics map to concrete owners, additive interfaces, failure behavior, protected consumers, dependency-ordered slices, failure-sensitive oracles, rollback, and release gates. No unresolved planning blocker remains.

At the planning boundary this was a same-context review. No clean-context reviewer had yet been dispatched, so that planning result retained `common-mode-risk` and did not satisfy the future independent-review gate. The later implementation review and its closure are recorded under `Implementation review correction` below.

At that planning boundary no RC.4 production code, live resource operation, model evaluation, artifact, installation, or delivery action had occurred. This sentence is baseline history, not the current implementation state.

## Reviewed baseline

- clean `main` at `v2.0.0-rc.3` before planning edits;
- RC.3 requirements, design, implementation, decisions, progress, audit, release policy, and residual waivers;
- Dev Flow kernel, core lifecycle, quality calibration, orchestration, native adapters, route parser/selection, capability contracts/registry, workstream templates, transition tests, runner tests, dogfood analyzer surface, and documentation index;
- post-RC.3 task observations summarized in the confirmed requirement understanding.

## Method realization

### State-transition model

The method changed owned design and test surfaces:

- requirements define observable states and forbidden edges;
- design defines route, convergence, lease, completion, and fallback transitions;
- implementation requires transition fixtures and seeded invalid states;
- every material/forbidden edge has a black-box, white-box, or negative-control oracle.

Limitation: the state model does not prove fairness among concurrent tasks or infer primary progress automatically. Those remain explicit claim limits.

### Compatibility expand/contract

The method changed rollout and removal behavior:

- RC.3 defaults are frozen before source changes;
- new route comparison, workstream contract, commands, Skill, and dogfood schema are additive;
- first-party consumers migrate before qualification;
- unmarked workstreams and dogfood v1 remain valid;
- no RC.3 public path is removed in RC.4;
- rollback and semantic-candidate/final-release identity are separate and testable.

Limitation: static repository evidence cannot prove every external model caller. Default-path compatibility and explicit additive fields are therefore release gates.

### Change-impact graph

The method changed slice ordering and protected-consumer coverage:

- route, continuity, resources, specialist ownership, history, dogfood, and qualification nodes map to concrete files and tests;
- S1 freezes common contracts before S2-S7 behavior changes;
- S6 depends on S3's path model; S7 consumes S2-S6; S8/S9 own integration and qualification;
- released RC.3 workstream/source and the methodology/verification ownership boundaries are explicitly protected.

Limitation: reflective, host-only, and external consumers remain unobserved until compatibility/dogfood execution.

## Findings and dispositions

### F1: Duplicate slice truth would recreate the contradiction being fixed

- Severity: major during draft; resolved.
- Finding: the initial draft duplicated the full mutable slice table in both `implementation.md` and `progress.md` while design assigned stable slice ownership to implementation.
- Disposition: removed the progress copy. `implementation.md` owns slice status; `progress.md` names only the current slice and current hard conditions.
- Oracle: the future checker compares the current slice to one implementation table rather than reconciling two full tables.

### F2: Protected-path cells must be machine-checkable paths

- Severity: major during draft; resolved.
- Finding: early table cells contained semantic prose such as “released behavior,” which contradicted the path-prefix parser contract.
- Disposition: replaced protected entries with repository-relative paths or `-`; semantic protections remain in scope/gates prose.
- Oracle: S3 path-parser fixtures reject prose, absolute paths, `..`, shell syntax, and root-wide catch-alls.

### F3: Recording qualification evidence changes repository bytes

- Severity: major during draft; resolved in plan.
- Finding: a naive “freeze, evaluate, update progress, build artifact” sequence would bind model evidence to an earlier commit while calling a later artifact the exact same candidate.
- Disposition: D14 and S8-S9 separate a bounded semantic-runtime identity, a qualification-execution identity, and the final release commit. The first covers the manifest, hooks, Skills and their runtime references, and runtime governance. The second covers transitive repository-local runner/helper dependencies, complete catalog/fixtures, observer/scoring contracts, Codex executable digest, model/reasoning settings, and environment policy. After recording bounded evidence, only designated evidence/release records may change; both identities must remain byte-identical. Any omitted reachable input, behavior-source/config/generated change, or non-allowlisted post-observation change requires a new freeze and R4 rerun.
- Oracle: release tests compare both dependency closures and identities, the changed-path allowlist, final commit identity, and artifact manifests separately. A negative test changes an imported helper such as `flow_metrics.py` while leaving the top-level runner unchanged and must invalidate qualification.
- Current status: design resolved; implementation evidence is `NOT RUN`. The RC.3 runner's broad `candidate_source_sha256` does not implement plugin/evidence separation, while its qualification metadata hashes the top-level runner without binding imported `flow_metrics.py`; HC8 therefore remains an explicit qualification blocker until S8 closes both gaps.

### F4: Route comparison must have a real consumer without owning persistence

- Severity: moderate; accepted with controls.
- Finding: RC.3 rejected an unconsumed route-details projection; a route basis would repeat that mistake if only emitted.
- Disposition: the optional prior-route comparison is the direct consumer, and Skill guidance/transition cases consume its `unchanged`/delta result. The caller owns any temporary previous result; Dev Flow writes no cache.
- Limitation: callers that cannot retain a prior result receive a normal full route and rely on unchanged-follow-up guidance.

### F5: Managed Truth Checker naming can overstate assurance

- Severity: moderate; accepted with explicit claim limit.
- Finding: Markdown consistency cannot prove semantic truth, evidence coverage, freshness, authorship, independence, or delivery readiness.
- Disposition: every result includes `claim_limit: structural-consistency-only`; requirements, design, tests, and final reporting preserve the separate evidence planes.
- Negative control: a structurally consistent fixture with a semantically inert test must still fail test-system/verification qualification.

### F6: Host-local leases are coordination, not a security or cleanup capability

- Severity: moderate; accepted with explicit boundaries.
- Finding: same-user processes can ignore or tamper with temporary state, wall clocks can move, and lease ownership does not prove ownership of the underlying simulator/process/cache.
- Disposition: use allowlisted resources, a validated user-scoped runtime root, a held non-blocking OS lock on one stable private guard inode, serialized generation changes, token-bound renew/release, bounded lease TTLs, fail-closed corruption handling, same-filesystem replacement only, and no underlying cleanup/kill behavior. The preflight probe creates and removes a zero-content private file; probe cleanup failure is itself a failure.
- Limitation: malicious/non-cooperating processes, cross-host contention, network/unknown filesystems, and unsupported platform semantics remain outside the guarantee and fail closed rather than being called safe.

### F7: Test-system specialist could overactivate

- Severity: moderate; resolved by ownership and negative triggers.
- Finding: routing the specialist for every test would increase context and duplicate `verification`.
- Disposition: explicit test-system work or observed `weak-tests` mechanisms activate it; ordinary feature verification remains with `verification`. The capability registry adds a separate conditional capability instead of changing the existing general verification capability.
- Oracle: ordinary feature-test and ordinary verification negative cases forbid the specialist.

### F8: Stratified R4 could hide variance outside the repeated subset

- Severity: major during challenge; resolved in plan.
- Finding: route, Skill, registry, and methodology changes are global inputs. One full attempt plus a repeated subset would leave the rest of the catalog with only one stochastic observation and could miss regressions caused by those global inputs.
- Disposition: D12 requires three independent first attempts for the complete frozen catalog on one semantic-runtime identity. Development uses deterministic tests, non-spending dry runs, and focused cases; the complete three-attempt run happens once after freeze. Content retries, subset-only repetition, post-hoc rescoring, and evaluator tuning are forbidden.
- Oracle: the runner proves complete catalog membership and three attempt identities before accepting any semantic result; every attempt is scored against the pre-frozen observer contract.

### F9: Hard conditions lacked a gate class

- Severity: major during challenge; resolved in plan.
- Finding: a single undifferentiated hard-condition list made `implementation-complete` impossible while honest future qualification checks remained `NOT RUN`, encouraging false completion or permanent ambiguity.
- Disposition: every condition declares `implementation` or `qualification`. `implementation-complete` requires only implementation gates; `release-qualified` and RC.4's terminal `closed` require both classes.
- Oracle: state-machine fixtures accept an implementation-complete workstream with honest future qualification gates and reject release-qualified/closed fixtures with any open required gate.

### F10: Dirty-worktree accounting would misclassify completed slices

- Severity: major during challenge; resolved in plan.
- Finding: checking only the active slice's write prefixes would report accumulated uncommitted files from earlier completed slices as undeclared user changes.
- Disposition: the active mutation boundary remains the active slice, while the accumulated accounting set is the union of completed and active slice write prefixes. The checker reports ambiguity and cannot infer authorship or prove that an earlier task-owned file was not later edited by the user.
- Oracle: fixtures distinguish active writes, accumulated declared writes, pre-existing user bytes, later modifications, and truly undeclared paths without deleting or rewriting any file.

### F11: Route basis was incomplete and could retain raw free-form facts

- Severity: major during challenge; resolved in plan.
- Finding: hashing only common routing flags would make `unchanged` unsound when legacy task type, mutation, continuity, profile/maintenance, overlay, or other route-affecting options changed. Retaining raw `repo-fact` values would also increase disclosure.
- Disposition: D2 defines an exhaustive router-semantics version and canonical mapping for every route-affecting parser input. Presentation-only `compact` is excluded. Free-form repository facts are normalized into a bounded digest/count representation; the caller-retained prior route remains as sensitive as the original output and is never persisted by Dev Flow.
- Oracle: parser-introspection coverage fails when a route-affecting option lacks basis treatment; one-at-a-time option mutations and alias/order permutations prove sensitivity and canonical equivalence.

### F12: The new Skill exceeded existing context-budget headroom

- Severity: major during challenge; resolved by an implementation gate.
- Finding: the current capability-description aggregate is 2496/2500 and the ordinary static instruction set is 17812/18000 bytes. Adding a specialist under the old caps is not feasible without measurement and refactoring.
- Disposition: S1 freezes exact baselines. The description cap may rise only by the measured new description plus a small documented margin; the ordinary static cap remains 18000, so specialist details move to on-demand references and existing static surfaces must not grow past the cap.
- Oracle: registry/description and ordinary-static budget tests run before and after S5; exceeding either approved bound blocks implementation completion.

### F13: Lease atomicity was overclaimed across platforms/filesystems

- Severity: major during challenge; resolved in design scope.
- Finding: successful replacement is only atomic on a supported same-filesystem path, temporary-root choice is environment/platform dependent, and Windows open/delete sharing differs from POSIX behavior. A vague “atomic file” promise was not a portable contract.
- Disposition: D5 validates the runtime root, uses exclusive creation for a short transition guard, serializes generation changes, and requires same-filesystem replacement. Network/unknown filesystems and unsupported sharing semantics return `NOT RUN`/fail closed. S4 includes Linux, macOS, and Windows compatibility tests plus current-host probes.
- Oracle: race, stale-guard recovery, generation, wrong-token, cleanup, permission, capacity, filesystem, and Windows-sharing cases are explicit; current-host primitive evidence does not substitute for the platform matrix.

### F14: Planning validation is not independent review

- Severity: residual common-mode risk; not a design defect.
- Finding: the authoring context can miss its own assumptions.
- Disposition: this audit performs same-context structural, semantic, counterexample, native-check, and primitive-probe review. It does not claim the future independent-review gate. Qualification still requires a clean-context reviewer with candidate identity and evidence-plane boundaries.
- Current status: `NOT RUN`; no delegation authority was provided.

## Requirement-to-slice trace

| Confirmed requirement | Design owner | Implementation slice | Primary gate |
|---|---|---|---|
| incremental routing | routing plane | S1-S2 | unchanged/delta compatibility matrix |
| convergence guard | continuity/convergence plane | S1, S3 | two-strike state and forbidden third tweak |
| managed truth | workstream contract | S3 | seeded contradiction matrix and claim limit |
| leases/preflight | resource coordination | S4 | race/token/TTL/privacy/capacity tests |
| test-system integrity | new specialist + verification handoff | S1, S5 | broken harness fixtures and negative activation |
| dirty worktree | workstream/path reconciliation | S3, S6 | user bytes preserved; ambiguity exposed |
| history fallback | native adapter | S6 | first failure/no unchanged retry/one changed retry |
| dogfood privacy | maintainer analyzer | S7 | v1/v2, bounded schema, content rejection, no score |
| RC.3 waiver closure | delegation/reference semantics | S7, S9 | pass/new waiver/block disposition |
| additive compatibility | expand/contract | S1-S2, S8-S9 | old paths plus new consumer matrix |
| exhaustive route identity | canonical route basis | S1-S2 | parser-option coverage and mutation matrix |
| implementation vs qualification truth | gated workstream state model | S1, S3 | valid/invalid state-transition fixtures |
| accumulated dirty accounting | slice/path reconciliation | S3, S6 | completed+active prefix union with claim limit |
| context budget feasibility | capability/context contracts | S1, S5 | measured description/static-byte gates |
| semantic candidate identity | release identity plane | S8-S9 | runtime and qualification dependency closure, allowlist, final-commit binding |
| complete stochastic qualification | frozen R4 protocol | S8-S9 | three complete-catalog independent first attempts |

No confirmed requirement lacks an implementation owner, oracle, or terminal gate. P1 controls ordering only and is not silently deferred.

## Reverse validation

The plan was challenged with these counterexamples:

- identical route facts reordered or expressed through aliases;
- incompatible/malformed/oversized/symlinked prior-route input;
- two in-progress slices or a completed workstream with an open hard condition;
- a two-strike checkpoint whose prompt/timeout changed but primary progress did not;
- two concurrent lease acquisitions, wrong-token release, expired-owner recovery, clock rollback, and corrupt state;
- a green runner that discovers zero tests or uses an inert assertion;
- an undeclared dirty file that predates the task;
- a task-history API failure repeated without a changed fact;
- dogfood fields containing task titles, raw paths, prompt-like strings, or a composite score;
- post-R4 evidence documentation changing the final release commit.
- a route-affecting parser option omitted from the canonical basis;
- an implementation-complete state with honest future qualification gates;
- accumulated task-declared changes from a completed slice;
- a new Skill added with four description characters and 188 ordinary-static bytes of baseline headroom;
- an environment-selected or network temporary root and Windows open-file sharing failure;
- a runtime-reachable input omitted from the semantic identity;
- a runner-imported helper changed while the top-level runner/catalog/observer files remain unchanged;
- variance outside a hand-selected repeated semantic subset.

Each counterexample maps to an explicit rejection, narrower claim, recheck trigger, or implementation test. No counterexample requires a new external dependency or broader authority.

## Planning verification

- Ad hoc plan-contract validation: `PASSED`; checked six owned surfaces, D1-D14, S0-S9, HC1-HC9, 29 current route-affecting parser inputs, five rejected state mutations, and 12 bidirectional trace topics.
- Full RC.3 behavioral baseline: `PASSED`; 555 tests completed under Python 3.14.7 with `ResourceWarning` promoted to errors.
- Structural and registry baseline: `PASSED`; 39 contracts, 117 methods/73 sources, knowledge validation, plugin check, 14-Skill exact inventory, 2,496 description characters, 17,812 ordinary-static bytes, and Python compilation completed successfully.
- Protected data-security doctor: all required checks passed; five live/manual surfaces remained `not_observed`, so its result is `valid_with_manual_gates`, not live-environment proof.
- Current-host resource primitive probe: `PASSED` on macOS 27.0 arm64/Python 3.14.7; 24 concurrent exclusive-create contenders produced one winner, same-filesystem replacement succeeded, and a zero-content writability probe was removed. This proves only current-host primitive feasibility, not S4 behavior or the supported-platform matrix.
- RC.4 local Markdown links and `git diff --check`: `PASSED` on final planning bytes.
- Worktree start baseline was clean; intended planning mutations are limited to `docs/index.md` and `docs/workstreams/dev-flow-2.0-rc.4/`.
- At the planning baseline, no RC.4 source or runtime behavior had been implemented; current implementation evidence is recorded in `progress.md` and the correction section below.

## Remaining evidence limits

- Independent review: `PASSED`; `/root/rc4_independent_review` closed all four findings on repaired current source and found no new Major/Moderate issue after 184 focused tests.
- RC.4 deterministic behavior: the post-repair full suite passed 602/602 on macOS/Python 3.14, followed by final structural and current-byte static checks.
- Cross-platform lease/resource behavior: `BLOCKED`; hosted Ubuntu/Windows candidate cells have not run, and current-host evidence establishes only local behavior.
- Model-semantic R4: `NOT RUN`; model/token authority absent.
- Exact artifact, isolated install, commit, tag, publication, and active installation: `NOT RUN` and separately authorized.
- Stable 2.0 real-task soak: future input after RC.4 release, not current source completion evidence.

## Implementation review correction — 2026-08-29

- The planning probe established only exclusive-create feasibility. Independent implementation review later proved that TTL-based guard unlink could steal from a live holder paused beyond the interval and allow a stale writer to overwrite a newer transition.
- D5 and the implementation were corrected to hold a non-blocking OS file lock on one stable private guard inode. A lock is released by close/process death and is never reclaimed by timestamp. New negative controls first reproduced both live-holder theft and a crash-before-metadata permanent block; both pass after the correction.
- The first independent review also invalidated the self-referential static coverage oracle, external-candidate qualification identity, and stale S8/S9 progress claim. The same reviewer rechecked their repairs against current source, ran 184 focused tests, and closed all four findings with no new Major/Moderate issue.

## Release-maturity theoretical validation — 2026-08-29

- A finite-state refinement check exhaustively evaluated all 1,764 combinations of the six workstream states, six slice statuses, and two seven-status gate classes. The checker accepted exactly the combinations permitted by the documented implementation/qualification lattice.
- A bounded transition exploration evaluated all 216 three-action sequences over lease acquire, valid/invalid renew, valid/invalid release, and expiry. Observable status, token authority, generation, expiry recovery, and final inspection refined the abstract lease model in every sequence.
- Static truth checking now distinguishes historical planning baselines from current evidence and rejects the exact stale claims found during this review. This closes a semantic-drift gap that path/requirement coverage alone could not detect.
- The SSDF release pass found no new dependency, no unpinned workflow action, and no per-file credential or identifier finding. A whole-diff phone-pattern match was proven to span a patch/file boundary and is a diff-format false positive, not retained C3 data.
- The installed Codex CLI no longer provides the historical `plugin check` command. Plugin manifest, exact inventory, isolated runtime lifecycle, release-artifact, and suite validators are the bounded current fallback; the removed CLI check remains `NOT RUN` and is not represented as a pass.
- Same-context final-diff review found that the resource lease CLI emitted exit zero for an acquire `conflict`, allowing shell-only callers to mistake denied ownership for success. A red-first CLI test reproduced the defect; action-specific success sets now return nonzero for conflict, forbidden, unavailable, and expired transitions, while observational inspect and idempotent release-available remain successful.
- Release-freeze review found that local coverage used `git ls-files -m -o`, which omits index-only changes after staging. A red-first temporary Git repository reproduced the disappearance; the shared enumerator now unions `git diff HEAD` with untracked files, and both coverage and static scanning observe all 50 staged/unstaged candidate paths.
- These checks strengthen deterministic maturity but do not substitute for hosted compatibility, complete live R4 model qualification, exact-commit artifacts/attestations, or a new independent review after this validation-only diff. The latter is downgraded to same-context with `common-mode-risk` unless separately authorized.

## First hosted candidate result — 2026-08-29

- Candidate `e808c1a697ab04617d722e5d8ed8864237cc89a1` was pushed to `origin/main`. Semantic Ubuntu/Python 3.14 passed the full suite, static event coverage, drift scan, structural, registry, data-security, compile, and clean-tree gates.
- Compatibility passed on Ubuntu/Python 3.11, macOS 15/Python 3.11, and Windows/Python 3.11 and 3.14. macOS 15/Python 3.14 failed in `test_public_cli_acquire_inspect_release_round_trip`: acquire/inspect completed, while release produced empty captured stdout and the test raised while decoding JSON.
- The test had not asserted the release subprocess return code or surfaced stderr, so the first result cannot distinguish an unhandled implementation exception, process signal, or another launch/runtime failure. The accepted next step is one diagnostic-only assertion repair; unchanged-SHA retry is prohibited and no compatibility pass is inferred.
- Diagnostic candidate `d90c85ab9775f36c4ba0294f8ea9a80718851281` added that assertion, but its compatibility job was skipped because `tools/ci_change_scope.py` omitted the new platform-sensitive test path. A red-first scope test reproduced the omission; `evals/test_resource_coordination.py` now requires compatibility exactly like the other platform-sensitive suites.

## Complete-matrix repair candidate result — 2026-08-29

- Candidate `75150a3800626039d9d3807963fdb64f13be98aa` included the red-first compatibility-scope repair and ran every intended hosted job. Semantic Ubuntu/Python 3.14 passed the behavioral suite, structural contracts, 100% RC.4 static coverage, drift scan, methodology/knowledge validators, plugin and focused-Skill checks, protected data-security controls, compilation, and tracked-file cleanliness.
- Compatibility passed on Ubuntu/Python 3.11, macOS 15/Python 3.11 and 3.14, and Windows/Python 3.11 and 3.14. The completed run is recorded at `https://github.com/AldenClark/dev-flow/actions/runs/33226529464`.
- The only changes after `e808c1a` were release-subprocess diagnostics and compatibility-scope routing; the resource lease implementation was unchanged. Therefore the prior macOS 15/Python 3.14 failure and this pass are contradictory observations of the same product behavior. Per the variance rule, HC4 is `flaky` and release-blocking; one green run does not erase the preserved failure.
- Code-path review found no deterministic transition from a valid acquired token to an empty-output release: expected filesystem and coordination failures are converted to JSON, while an empty stream would require an uncaught runtime/process-level failure or external termination. Because the first test did not preserve return code/stderr and the instrumented run passed, root cause remains unconfirmed. Further work must be a bounded diagnostic hypothesis or an explicit owner waiver, not unchanged-candidate retries.
