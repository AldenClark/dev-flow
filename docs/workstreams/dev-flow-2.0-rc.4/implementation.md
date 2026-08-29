<!-- dev-flow-workstream-contract: v1 -->
# Dev Flow 2.0 RC.4 implementation

## Outcome

Ship an additively compatible RC.4 candidate whose long-task routing, convergence, managed truth, shared-resource coordination, test-system integrity, dirty-worktree ownership, and history fallback are deterministic where this repository owns the boundary and honestly limited elsewhere.

## Scope and acceptance

- In scope: every capability and qualification rule in [requirements.md](requirements.md), implemented in coherent slices below.
- Protected behavior: RC.3 canonical route behavior, simple-task quietness, evidence-status distinctions, final-byte freshness, least authority, privacy-safe dogfood, no repository lifecycle database, and separate delivery authority.
- Observable completion: S0-S9 are `complete`; every applicable hard condition in [progress.md](progress.md) is `passed` or has an explicit owner `waived` decision; deterministic gates pass on final bytes; independent review and the three-attempt complete-catalog R4 are completed or the release remains unqualified.

## Slice plan

| Slice | Outcome | Write prefixes | Protected paths | Evidence | Status | Decision |
|---|---|---|---|---|---|---|
| S0 | Confirm requirements and freeze an implementation-ready architecture | `docs/workstreams/dev-flow-2.0-rc.4/`, `docs/index.md` | `docs/workstreams/dev-flow-2.0-rc.3/`, `skills/` | traceability, feasibility, counterexample, link/contract, and same-context design audits | complete | D1-D15 |
| S1 | Freeze RC.3 compatibility and add failing RC.4 contract fixtures | `evals/`, `docs/workstreams/dev-flow-2.0-rc.4/` | `skills/dev-flow/`, `docs/workstreams/dev-flow-2.0-rc.3/` | focused fixture/schema tests failed for missing RC.4 behavior while RC.3 regression tests passed | complete | D11 |
| S2 | Add stateless route basis and incremental comparison | `skills/dev-flow/`, `evals/` | `docs/workstreams/dev-flow-2.0-rc.3/` | route unit/property cases; compact/full compatibility; malformed prior-route tests | complete | D2, D11 |
| S3 | Add the workstream contract, consistency checker, and convergence guard | `skills/dev-flow/`, `evals/`, `docs/workstreams/dev-flow-2.0-rc.4/` | `docs/workstreams/dev-flow-2.0-rc.3/` | contradiction/acceptance matrix; convergence transition tests; worktree fixtures | complete | D3, D4, D8 |
| S4 | Add host-local resource leases and resource preflight | `skills/dev-flow/`, `skills/verification/`, `evals/` | - | race/token/TTL/permission/privacy/preflight tests; hosted platform cells remain HC4 | complete | D5, D6 |
| S5 | Add and route `test-system-engineering` | `skills/test-system-engineering/`, `skills/dev-flow/`, `skills/dev-flow-maintainer/`, `governance/`, `evals/` | `governance/methodology-pool.json`, `skills/verification/` | inventory/routing negative controls; discovery/selector/sensitivity/isolation fixtures | complete | D7 |
| S6 | Complete dirty-worktree and task-history recovery behavior | `skills/dev-flow/`, `evals/` | - | path-prefix fixtures; changed-fact retry semantic cases | complete | D8, D9 |
| S7 | Extend privacy-safe dogfood and close RC.3 waived semantics | `skills/dev-flow-maintainer/`, `skills/dev-flow/`, `evals/` | - | v1/v2 analyzer tests; renewed-authority and reference-boundary cases | complete | D10, D13 |
| S8 | Integrate documentation, packaging, compatibility, and release policy | `README.md`, `CHANGELOG.md`, `docs/`, `.codex-plugin/`, `.github/`, `tools/`, `governance/`, `skills/`, `evals/` | `docs/workstreams/dev-flow-2.0-rc.3/` | suite validator; plugin check; static trace/scan; local regression; hosted compatibility workflow | complete | D11, D12, D15 |
| S9 | Freeze and qualify the exact RC.4 candidate | `docs/workstreams/dev-flow-2.0-rc.4/`, `docs/releasing.md`, `CHANGELOG.md` | `docs/workstreams/dev-flow-2.0-rc.3/` | final R1-R3; independent review; complete R4 evidence or explicit owner waiver; reproducible artifact and exact identity checks | in-progress | D12, D13, D14, D15 |

## Slice details

### S0: Confirm and design

Outcome:

- preserve the confirmed technology-neutral requirement baseline;
- realize the state-transition model, compatibility expand/contract, and change-impact graph;
- record public contracts, failure behavior, rollback, security/privacy boundaries, and implementation order.

Completion evidence:

- all local links among requirements, design, decisions, implementation, audit, and progress resolve;
- `docs/index.md` routes to the new workstream;
- same-context review finds no unresolved major design contradiction;
- `common-mode-risk` remains explicit because no independent reviewer was authorized for planning.

### S1: Freeze executable contracts before production behavior

Affected areas:

- new `evals/test_rc4_convergence.py` for route comparison, workstream consistency, convergence, resources, dirty paths, and analyzer contracts;
- new/extended transition catalog cases for unchanged route, material delta, two-strike stop, history fallback, renewed authority, and reference-source disposition;
- compatibility fixtures containing representative RC.3 route commands and required output fields;
- focused test-system fixtures that intentionally produce zero discovery, a wrong selector, inert assertions, fixture leakage, misleading runner exit, and a correct control.

Implementation obligations:

1. Capture public RC.3 defaults before changing source.
2. Each RC.4 behavior begins with a failure-sensitive oracle and at least one protected negative.
3. Seed mutations prove that the checker and test-system cases fail for the intended reason.
4. Freeze current context budgets: 2,496 aggregate Skill-description characters and 17,812 ordinary static bytes under caps 2,500/18,000.
5. Do not encode implementation wording as the semantic oracle when observable behavior is sufficient.

Native completion evidence:

```text
python3 -m unittest evals.test_dev_flow_v2 evals.test_rc3_extensions evals.test_rc4_convergence
python3 -m unittest evals.test_flow_activation evals.test_flow_transitions evals.test_large_task_simulations
```

S1 is complete when RC.3 compatibility remains green and RC.4 missing-behavior cases fail at the expected boundary, not from malformed fixtures.

### S2: Stateless route comparison

Affected areas:

- `skills/dev-flow/scripts/dev_flow.py`
- `skills/dev-flow/SKILL.md`
- `skills/dev-flow/references/core-lifecycle.md`
- `skills/dev-flow/references/quality-calibration.md`
- `evals/test_dev_flow_v2.py`
- `evals/test_rc4_convergence.py`
- activation and transition catalogs

Implementation order:

1. Define and validate `dev-flow.route-basis.v1` from an exhaustive table of normalized routing inputs, including legacy task type and router-semantics version; store only an aggregate digest for free-form repository facts.
2. Add bounded prior-route file loading using existing path/file safety conventions.
3. Compare bases and map each changed dimension to invalidated decision classes.
4. Add the optional `recalibration` projection while retaining the complete current route.
5. Update Skill guidance: retain one route basis in active context; skip the call when facts are unchanged; use comparison only after a material transition or uncertain resume. Keep the three ordinary static Skills at or below the existing 18,000-byte cap by moving detail to on-demand references.
6. Add a mutation case for every route-affecting parser option plus compact/full, ordering, alias normalization, router-version mismatch, malformed file, oversize, symlink, free-form fact privacy, and unrelated-format-change tests.

Native completion evidence:

- old commands produce all prior fields and equivalent values;
- identical normalized inputs yield `unchanged` regardless of input ordering or aliases;
- every material dimension has one positive delta test;
- protected non-material differences do not invalidate decisions;
- the router writes no cache or prior-route file.

Stop/recheck:

- stop if comparison needs prompt/task identity, automatic persistence, or removal of an RC.3 field.

### S3: Workstream consistency and convergence

Affected areas:

- `skills/dev-flow/scripts/dev_flow.py` or a narrow `workstream_contract.py` module imported by it;
- workstream templates and `init-workstream` generation;
- managed orchestration, quality calibration, and core lifecycle references;
- `evals/test_rc4_convergence.py`, `evals/test_dev_flow_v2.py`, and transition cases;
- this workstream, which remains the first checked real fixture.

Implementation order:

1. Implement bounded marker, heading, table, ID, status, and decision parsing without a general Markdown dependency.
2. Emit exact line-oriented findings and `claim_limit` without mutation.
3. Enforce current-slice, terminal-state, gate-aware hard-condition, deferral, waiver, and convergence invariants.
4. Add optional `--check-worktree` path-prefix reconciliation using Git's NUL-delimited porcelain output. Compare current changes with the union of completed and active slice prefixes for accumulated accounting, while retaining active-slice-only mutation guidance.
5. Update templates and `init-workstream`; retain old generation behavior only if an explicit legacy option is needed by tests/consumers.
6. Seed every invariant violation, including a mutation that removes each checker branch to prove sensitivity.

Required fixture states:

- valid planning, active, blocked, implementation-complete with future qualification gates `not-run`, release-qualified, and closed workstreams;
- missing/duplicate IDs, two in-progress slices, stale current slice, invalid terminal completion, implementation/qualification gate confusion, open/waived hard conditions without decisions, pending two-strike checkpoint, invalid/multiline/pipe-containing table cells, unsafe/root-wide prefix, undeclared dirty path, completed-slice accumulated path, protected dirty path, non-Git root, and legacy unmarked workstream.

Native completion evidence:

```text
python3 skills/dev-flow/scripts/dev-flow.py check-workstream --root . --path docs/workstreams/dev-flow-2.0-rc.4 --check-worktree
python3 -m unittest evals.test_rc4_convergence evals.test_dev_flow_v2 evals.test_flow_transitions
```

Stop/recheck:

- stop if the parser needs to interpret arbitrary prose, persist digests, infer authorship, or claim semantic/evidence truth.

### S4: Resource leases and preflight

Affected areas:

- `skills/dev-flow/scripts/resource_coordination.py`
- CLI parser/dispatch in `skills/dev-flow/scripts/dev_flow.py`
- verification/resource guidance and Codex-native adapters
- `evals/test_resource_coordination.py` and platform-sensitive CI scope

Implementation order:

1. Define allowlisted kinds, input bounds, explicit/derived runtime-root validation, restrictive permissions, local/same-filesystem claim limits, and structured result schema.
2. Implement a held non-blocking OS file lock on a stable private guard inode plus same-filesystem replacement; serialize every lease transition without TTL theft and protect state with a generation check.
3. Implement resource/owner/token digests and atomic acquire with deterministic conflict behavior.
4. Implement inspect, token-bound renew/release, expiry, process-crash lock release/lease recovery, corrupt-state rejection, and Windows sharing/deletion failure behavior.
5. Implement measurement-only resource preflight and explicit-budget evaluation; use a zero-content secure target-directory probe for `--require-writable` and report cleanup failure.
6. Add multiprocess race tests, fake-clock tests, environment-controlled temp-root tests, same/cross-filesystem tests, network/unknown-filesystem downgrade, permissions/symlink tests, wrong-token tests, concurrent renew/release/expiry, crash/guard-expiry tests, Windows open/delete tests, and output privacy assertions.
7. Add resource tests to the existing Ubuntu/macOS/Windows Python 3.11/3.14 compatibility matrix; unsupported evidence remains explicit.

Native completion evidence:

- exactly one winner under concurrent acquire attempts;
- no unexpired lease can be renewed/released by a wrong token or reclaimed by PID inference;
- raw resource/owner/token values never appear in the runtime record or inspect output;
- preflight produces no deletion and no `passed` without supplied budgets;
- the entire user-scoped runtime path is never used as an unvalidated recursive deletion target.

Stop/recheck:

- stop if a supported platform requires a daemon, external dependency, cross-host state, automatic cleanup, or a weaker ownership guarantee than documented.

### S5: Test-system engineering owner

Affected areas:

- new `skills/test-system-engineering/` Skill, reference, and agent metadata;
- `governance/capability-contracts.json`;
- `skills/dev-flow-maintainer/references/capability-registry.json` and admission validation;
- route needs/aliases in `skills/dev-flow/scripts/dev_flow.py`;
- expected inventories, plugin checks, routing cases, and test-system fixtures.

Implementation order:

1. Write strict positive/negative triggers and the six-obligation specialist procedure; measure its description exposure before admission.
2. Register ownership and handoff: harness integrity to `verification`, product claim remains with `verification`.
3. Add canonical `test-system` need and alias, plus `quality.test-system.integrity` selector `risk=weak-tests`.
4. Add routing cases for explicit harness work, false green, ordinary feature tests, ordinary verification, and unavailable specialist fallback.
5. Realize the specialist against the S1 broken fixtures and ensure each diagnosis changes an oracle or claim limitation.
6. Raise the aggregate Skill-description budget only by the measured admitted description plus a small documented margin; do not remove or weaken security/privacy triggers merely to recover characters.
7. Validate packaging, agent metadata, references, route ordering, context budgets, and capability admission.

Native completion evidence:

- explicit test-system tasks route the new owner;
- ordinary feature/test tasks without a weak-test fact do not;
- every broken fixture is distinguished from product failure;
- a correct harness passes discovery, selection, sensitivity, isolation, interpretation, and representativeness checks;
- no methodology registry growth occurs.

### S6: Dirty-worktree and history recovery

Affected areas:

- workstream checker/path parser and orchestration guidance;
- `skills/dev-flow/references/codex-native-adapters.md`;
- multi-root/worktree transition fixtures and semantic cases.

Implementation order:

1. Validate repository-relative prefixes and protected-path declarations.
2. Reconcile NUL-delimited Git changed paths against accumulated completed-plus-active prefixes, including spaces, Unicode, renames, untracked files, submodules, and multiple explicit roots.
3. Report ambiguity without authorship inference or mutation.
4. Strengthen history adapter with first-failure, changed-fact one-retry, and repository-only fallback rules.
5. Add semantic cases that preserve an unrelated dirty file and forbid unchanged task-history retries.

Native completion evidence:

- seeded user-owned changes remain byte-identical;
- outside-prefix changes fail the scoped completion check but are neither attributed nor reverted;
- one changed fact permits one history retry; unchanged facts permit none;
- unavailable history narrows the final synthesis claim.

### S7: Dogfood v2 and waived-gap closure

Affected areas:

- `skills/dev-flow-maintainer/scripts/analyze_dogfood.py`
- dogfood schema fixtures and focused tests;
- delegation and reference-boundary guidance/cases;
- transition observer labels where needed.

Implementation order:

1. Add v2 validation while preserving v1 acceptance/output semantics.
2. Add bounded route/convergence/resource/workstream/test-system aggregates with no total score.
3. Reject content-like keys, unbounded strings/counts, raw paths, prompts, and task titles.
4. Add behavioral renewed-authority and reference-source disposition oracles.
5. Prove the oracles reject silent omission, child self-expansion, literal-only gaming, and non-authoritative analogy use.

Native completion evidence:

- v1 and v2 analyzers pass fixed fixtures;
- negative privacy/scoring mutations fail;
- both RC.3 waived behaviors pass focused deterministic/semantic observation or remain explicit hard conditions.

### S8: Integration and release preparation

Affected areas:

- maintained product/release docs, changelog, manifests, inventories, CI scope, plugin artifacts, and all changed Skills/references/tests.

Implementation order:

1. Update README and release docs only after behavior and commands are final.
2. Add RC.4 identity only when source is ready for candidate qualification; do not claim release publication.
3. Update plugin inventory, expected Skill list, capability registry, documentation catalog, and link checks.
4. Run full deterministic and focused compatibility matrices.
5. Freeze the semantic-runtime identity and qualification-execution identity—including transitive local runner/helper dependencies, complete catalog/fixtures, observer/scoring contracts, Codex executable digest, model/reasoning settings, environment policy, and total budget—before model execution; prove the non-spending qualification dry run first.

Native completion evidence:

```text
python3 skills/dev-flow-maintainer/scripts/validate-suite.py
python3 skills/dev-flow/scripts/dev-flow.py check
python3 skills/dev-flow/scripts/dev-flow.py validate-methods
python3 -m unittest discover -s evals -p 'test_*.py'
```

Also require repository-native documentation/link, plugin artifact, data-security, release-artifact, and supported compatibility checks already owned by the suite.

### S9: Exact-candidate qualification

Preconditions:

- S0-S8 complete;
- worktree reconciled and candidate identity frozen;
- model/token budget separately authorized;
- clean-context independent review separately authorized and successfully dispatched, or release remains blocked at that gate;
- complete R4 catalog/fixtures, semantic-runtime identity, qualification-execution dependency closure, model/environment, and three-attempt budget frozen before execution.

Execution:

1. Set workstream truth to qualification-ready, then freeze the semantic candidate identity used by the runner.
2. Run final deterministic R1-R3 and independent review against that frozen scope.
3. Execute three independent first attempts for the complete catalog in one qualification run; do not use content retries, subset-only repetition, post-hoc rescoring, or evaluator tuning.
4. Perform manual observation separately; preserve first failures and distinct evidence statuses.
5. Re-run affected deterministic checks after every accepted repair; any runtime semantic source/config/generated behavior repair invalidates the frozen model evidence and requires a new candidate.
6. Record bounded evidence in progress/audit. Prove the post-observation diff contains only designated evidence/release records and that the exact semantic-runtime and qualification-execution identities are unchanged; otherwise freeze and rerun.
7. Run final R1-R3 again on the release commit, then build two artifacts from that exact commit and compare them; verify manifest, version, commit, inventory, and isolated install behavior.
8. Commit, push, tag, Marketplace publication, active installation, and stable-release soak remain separate actions.

Release qualification requires:

- zero mechanical gate failures;
- zero unchanged duplicate routes in RC.4 cases;
- all material deltas correctly recalibrated;
- all convergence, checker, resource, test-system, dirty-worktree, and history hard conditions passed;
- both RC.3 waived gaps passed or explicitly re-waived by the version owner;
- independent review completed with reviewer identity and current-byte result;
- exact usage and candidate identity closed;
- three complete-catalog attempts and manual observations are closed without content retry;
- semantic R4 evidence is bound to an unchanged, runtime-reachable semantic candidate digest plus runner/catalog/observer identities, while deterministic/artifact evidence is bound to the final release commit;
- no required cell `FAILED`, `FLAKY`, `BLOCKED`, or `NOT RUN`.

## Ordering and dependencies

```text
S0
 └─> S1
      ├─> S2 ─┐
      ├─> S3 ─┼─> S6 ─┐
      ├─> S4 ─┤       │
      └─> S5 ─┘       ├─> S7 -> S8 -> S9
                       │
                       └───────────────
```

- S1 precedes every behavior slice because it freezes compatibility and negative controls.
- S2-S5 can be implemented as separate coherent branches only with disjoint writes or isolated worktrees; otherwise serialize them in the listed order.
- S6 depends on S3's checker/path model.
- S7 consumes behavior from S2-S6.
- S8 freezes public behavior and evaluation catalogs.
- S9 starts only once; any accepted source change reopens S8 and invalidates frozen qualification evidence.

## Hard implementation gates

- **G0 — Scope:** no implementation outside the confirmed requirements or declared slice paths without recalibration.
- **G1 — Oracle:** every capability has a failure-sensitive deterministic oracle and protected negative before source completion.
- **G2 — Compatibility:** default RC.3 paths remain valid; additive fields/commands have explicit consumers; every route-affecting input is covered by basis mutation tests.
- **G3 — State:** no hidden route/task lifecycle store; workstream and leases remain separate, narrow ownership planes.
- **G4 — Safety:** no new command deletes underlying resources, cleans broad paths, kills processes, or infers authority.
- **G5 — Privacy:** route basis, leases, history behavior, and dogfood store no content-bearing task data beyond the already-sensitive caller-owned full route; free-form facts use equality digests in the basis.
- **G6 — Convergence:** two auxiliary non-progress repairs force disposition; evaluator/tooling repairs obey the same rule.
- **G7 — Test validity:** discovery and sensitivity negative controls prove that green gates can fail.
- **G8 — Freshness:** accepted source changes invalidate affected evidence; final claims bind to final bytes.
- **G9 — Review:** independent review is either actually completed or explicitly unsatisfied; same-context review retains `common-mode-risk`.
- **G10 — Delivery:** planning and implementation do not authorize commit, push, tag, release, install, deploy, or external action.
- **G11 — Context cost:** ordinary top-level static guidance stays within 18,000 bytes; any description-budget increase is measured, bounded to the new specialist, and protected by negative activation tests.

## Evidence limits

- Planning evidence is current-repository inspection plus same-context reasoning; it is not independent review.
- Planning-time baseline (historical): no RC.4 source behavior, test, host lease, resource race, model-semantic case, artifact, installation, or delivery evidence had run. Current execution evidence is owned by `progress.md` and must not be inferred from this baseline.
- Static impact tracing cannot prove unknown external consumers.
- The workstream checker can prove only structural consistency and declared path accounting.
- A host-local lease coordinates cooperating same-user processes only; it is not a security boundary.
- Stable `2.0.0` additionally requires the confirmed post-RC.4 real-task soak: at least two real long tasks and one shared/destructive-resource task under separate task authority.

## Delivery boundary

The original confirmed request authorized repository-local RC.4 implementation and proportionate verification, not delivery. On 2026-08-29 the version owner separately authorized further theoretical validation and starting the release process. Delivery readiness still treats commit, push, tag, GitHub/Marketplace publication, active installation, model spending, deployment, cleanup of live resources, and stable-release soak as distinct actions and evidence boundaries; `progress.md` owns the current authorization and execution status.
