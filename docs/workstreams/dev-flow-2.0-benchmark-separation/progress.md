<!-- dev-flow-workstream-contract: v1 -->
# Dev Flow 2.0 release validation and benchmark separation progress

## Status

- State: implementation-complete
- Current slice: S4
- Terminal condition: the release contract and benchmark are separated, affected and full deterministic checks pass, and a non-spending stable-validation simulation completes without starting a 2.0 stable release.
- Updated: 2026-09-01

## Completed outcomes

- Confirmed that 2.0 stable publication is intentionally deferred.
- Confirmed the replacement release evidence: cumulative semantic review from the previous public stable, a deeper consolidated methodology review, and bounded real-function acceptance.
- Confirmed that the former R4 becomes an independent research benchmark and never a release tier or automatic stable gate.
- Removed `model_qualification` from canonical delivery state and removed universal independent review from the stable schema; attempted failed/blocked review still blocks release.
- Added independent regression, capability, and safety-authority suites with accepted/provisional health, non-spending plans, explicit live-spend bounds, separate grading/comparison, and no aggregate score.
- Simulated `v1.1.2` to the current worktree: 38 commits and 216 changed files were inventoried; policy status was ready and every mutation/model/delivery action remained false.

## Current

Stage-two native Bench migration and active R4 retirement are complete. Stable `2.0.0` remains deliberately unstarted.

## Next

The confirmed stage-one Bench hardening is complete. Stage two migrated all 26 cases, the bounded executor, contract validator, and deterministic MCP fixture into `benchmarks/`, gave every case an accepted or provisional suite disposition, replaced the R4 catalog and transition-observation schemas with Bench-owned schemas, and removed the old runner CLI, qualification threshold, campaign ledger, and public transition grading lane. Historical RC evidence, historical RC.4 identity validation, and the stable-policy negative guard remain intentionally; none is imported by the active Bench path. A future live study, commit, tag, push, installation, or stable publication requires its own authority.

## Hard conditions

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | Stable release no longer requires complete repeated model qualification | implementation | passed | release/state/docs/tests agree |
| HC2 | Dev Flow Bench is release-state-independent and non-spending by default | implementation | passed | CLI, spend boundary, symlink, identity, exclusive-output, native catalog/executor, and comparison negative tests pass |
| HC3 | Existing cases have explicit health and suite disposition | implementation | passed | all three suite audits valid; provisional cases excluded by default |
| HC4 | Simulation covers semantic delta, static methods, and functional journeys | qualification | passed | 216-file worktree inventory; ready; no model or delivery actions |
| HC5 | Final deterministic and same-context review evidence is current | qualification | passed | complete suite run plus failed/newly affected reruns and consolidated static review |

## Consolidated static review

One same-context pass applied all six stable methods and consolidated findings before repair:

- Traceability/V-model found no missing requirement owner after release docs, product-state schema, Bench commands, suites, and negative tests were aligned.
- Change-impact graph found stale current-governance and documentation-index R4 statements; they were removed while historical RC statements were preserved.
- Specification by example covered RC affected smoke, stable cumulative validation, default no-spend Bench planning, explicitly authorized live study, grading/comparison, and deferred publication.
- Feature-interaction analysis found that the RC.5 worktree ownership test incorrectly captured all future work; it now validates fixed RC.5 history while the current workstream checker owns current changes.
- Black/white oracle accounting added expected/forbidden-overlap, missing-baseline, obsolete-R4-policy, spend-acknowledgement, and input/output symlink negative controls.
- Assumption mapping/premortem found that a HEAD-only simulation omitted uncommitted implementation; the simulator now includes tracked working bytes and untracked files and parses NUL-delimited Git paths.

No consequential static finding remains. Review is same-context and retains `common-mode-risk`; it is not described as independent.

## Verification result

- Stage-two focused Bench, native-contract, and executor coverage passed; the broader affected batch passed 292 tests with one hosted-Windows-only skip. The complete deterministic run before the final mechanical contracts/MCP-fixture ownership move passed all 703 discovered tests with the same single platform skip. After that move, the 117-test directly affected batch exposed only one duplicated test-directory setup error; its failed case passed after the fixture repair. The lower full-suite total is the expected retirement of 20 campaign/qualification/old-CLI tests plus the obsolete transition-lane test, offset by native Bench migration and anti-regression coverage.
- Stage-one Bench hardening added 17 focused contract tests; the affected Bench/runner/data-security/stable-validation batch passed 128 tests with one hosted-Windows-only skip. The final complete deterministic run then passed all 722 discovered tests with the same single platform skip.
- The one complete deterministic run executed 712 tests: 710 passed, one obsolete RC.5 worktree-ownership contract failed, and one hosted-Windows-only test was skipped. After the contract correction, its three-test module passed.
- Newly affected Bench, simulation, product-state, and release-contract checks passed; the final focused batch ran 21 tests.
- All three Bench suite audits and default no-spend plans passed.
- Product state, 39 public contracts, historical RC.4/RC.5 scans, methods, knowledge, plugin, maintainer suite, protected data-security controls, compilation, workstream reconciliation, and `git diff --check` passed.

## Worktree boundary

- Active Git root: `/Users/ethan/Repo/dev-flow`.
- Baseline: clean `main` at `079f9a37d0141ec08f8db8689f65e3b690425996`.
- Mutation is limited to the confirmed release-validation, benchmark, tests, and maintained current-truth surfaces.
- Commit, tag, push, publication, live model spend, and primary-profile installation are not authorized.

## Evidence limits

- The simulated functional journeys are plans until a separately authorized live model run occurs.
- Same-context final review retains `common-mode-risk`; no independent reviewer was separately authorized.
