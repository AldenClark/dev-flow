<!-- dev-flow-workstream-contract: v1 -->
# Dev Flow 2.0 RC.4 progress

## Status

- State: active
- Current slice: S9
- Terminal condition: S0-S9 are complete; all required deterministic, independent-review, three-attempt complete-catalog R4, semantic-runtime identity, qualification-execution identity, final-release commit, artifact, and compatibility gates pass; every residual condition is honestly disposed; delivery actions remain separately authorized.
- Updated: 2026-08-29

## Completed outcomes

- Inspected the clean `main` baseline at `v2.0.0-rc.3` and traced the route, lifecycle, capability, evaluation, workstream, dogfood, and release surfaces affected by RC.4.
- Published and received explicit confirmation of the technology-neutral RC.4 requirement understanding.
- Routed the confirmed design as managed work through repository context, requirements, architecture, verification, change review, and migration compatibility.
- Realized the selected state-transition model, compatibility expand/contract, and change-impact graph in the workstream design and implementation order.
- Recorded the host-local short-lease exception, additive RC.3 compatibility, and post-RC.4 soak requirement as user-confirmed decisions.
- Produced and adversarially revised the implementation-ready S0-S9 slice plan, hard gates, rollback, failure matrix, ownership boundaries, context budgets, and qualification policy.
- Traced incremental routing, convergence/workstream truth, resource coordination, test-system integrity, dirty-worktree accounting, task-history fallback, privacy-safe dogfood, compatibility, and candidate identity through owned slices and terminal gates.
- Implemented stateless route-basis comparison across all 29 public route-affecting inputs, including bounded privacy-safe facts and invalid-prior fallback to a complete current route.
- Implemented the opted-in workstream contract/checker, convergence dispositions, accumulated dirty-path accounting, and read-only claim limits.
- Implemented local cooperative resource leases and measurement-only preflight with token privacy, crash-released OS locks, live-holder non-theft, corruption/clock rejection, and platform-sensitive CI coverage.
- Added and routed `test-system-engineering`; executable fixtures distinguish zero discovery, wrong selection, inert oracles, fixture pollution, and skip-only green results.
- Added dogfood v2 aggregates, RC.3 residual semantic cases, semantic-runtime and qualification-execution identities, RC.4 static traceability, drift scanning, and candidate/release-state documentation.
- Completed the first local full regression: 594 tests ran; three stale RC.3 release/guidance expectations failed, were causally corrected, and their focused reruns passed.
- Completed the post-review local full regression, then the maturity-model, CLI exit, and staged-scan repairs: 607/607 tests passed on macOS/Python 3.14, followed by structural, plugin-manifest/suite, methodology, knowledge, data-security, compile, and diff checks.
- Closed the implementation review findings for TTL live-holder theft, self-referential static coverage, external-candidate identity domains, and stale workstream truth; `/root/rc4_independent_review` rechecked those repaired implementation bytes, ran 184 focused tests, and reported no new Major/Moderate finding. The later theoretical-validation diff has only same-context review and therefore reopens the frozen-candidate independent gate.
- Added bounded theoretical refinement checks: all 1,764 workstream state/slice/gate combinations and 216 three-step lease transition sequences conform to the documented state models. Static scanning now enforces current-truth anchors so unqualified planning-time claims cannot silently reappear.
- Corrected a final-diff review finding where `resource-lease acquire` returned process success for a JSON `conflict`; action-specific CLI exit contracts now fail conflict, forbidden, unavailable, and expired transitions so shell callers cannot infer false ownership.
- Corrected the local static-scan change source so staged tracked additions/modifications remain in the release-freeze coverage set; a red-first temporary-repository test proves index-only changes cannot disappear from the 100% ownership check.
- Applied the selected SSDF release controls: required packaged data-security checks passed, no per-file secret/identifier finding remained, all workflow actions are immutable-SHA pinned, no dependency was added, and RC.3 remains the executable rollback target. Five optional live/manual data-security surfaces remain `not_observed`.
- Received explicit authority to continue the bounded macOS diagnosis, dispatch the frozen-candidate independent review, and choose/execute the R4 model budget. The selected qualification contract is `gpt-5.6-terra`/`medium`, 12,000,000 aggregate tokens, 600,000 tokens per call, and 900 seconds per call; its non-spending full-catalog dry run is qualification-eligible for 23 cases, 50 turns per attempt, and three attempts.
- Completed the final bounded variance diagnostic in run `33227465070`: the semantic job and all five compatibility cells passed, including 25/25 additional instrumented public CLI round trips on macOS 15/Python 3.14. This did not reproduce or erase the first failure, so HC4 remains `flaky` pending an explicit version-owner waiver.
- The frozen-candidate independent review blocked on three Major findings: malformed/missing candidate identities could compare equal, the post-R4 evidence allowlist admitted policy/design files, and successful Windows parent exits did not clean descendant processes. Red-first identity tests reproduced the first two; the repair now validates the complete identity envelope, narrows evidence-only mutation to audit/progress/CHANGELOG, binds Windows children to kill-on-close Job Objects, and routes the real Windows runner integration through compatibility CI. Final-byte hosted proof and independent recheck remain open.
- The corrected local snapshot passed 612/612 tests on macOS/Python 3.14 with the real Windows integration test explicitly skipped on the non-Windows host, followed by 39 structural contracts, 100% coverage of all 10 changed paths, zero static drift findings, methodology/knowledge/plugin/Suite/data-security validators, compilation, and diff checks.
- Hosted run `33228235799` converted HC4's unknown flake into a deterministic token/CLI defect: diagnostic attempt 23 generated an opaque URL-safe token beginning with `-`, so argparse rejected the separate `--token VALUE` argument with return code 2. Issued tokens now carry a fixed `lease_` prefix and a forced-leading-dash regression proves CLI release. The same run proved the real Windows Job Object descendant-cleanup test on Python 3.11 and 3.14; its remaining Windows failure was an unrelated test portability error when mocking absent `os.O_NOFOLLOW`, now corrected with an explicit synthetic attribute.
- Interim independent recheck rejected two incomplete repairs: section digests could remain stale while identity manifests/execution inputs changed, and post-spawn Job assignment left a pre-assignment descendant escape race that the delayed integration test did not exercise. Frozen verification now compares complete identity sections and recomputes the execution-input digest. Windows 10+/Server 2016+ creation uses `PROC_THREAD_ATTRIBUTE_JOB_LIST` plus an explicit inherited-handle list, so containment is established before the initial thread runs; the hosted integration removes the delay and repeats ten immediate-spawn attempts.
- The resulting local snapshot passed 614/614 tests with only the real Windows test skipped on macOS, followed by all 39 structural contracts, 100% ownership coverage of all eight changed paths, zero static drift findings, methodology/knowledge/plugin/Suite/data-security validators, compilation, and diff checks.
- Final independent review of the D15 release diff passed with no Major, Moderate, or Minor actionable finding. Its fresh checks produced 628 passes and one macOS-only Windows integration skip, 73 focused runner/identity/static passes with the same skip, an eight-process campaign contention pass, 100% D1-D15 traceability, zero drift, and 16/16 changed paths owned.

## Current slice

S9 is active on the exact release candidate. The causal token/CLI, identity-section, creation-time Windows containment, and portability repairs passed the complete hosted matrix at run `33228757027`; changes through candidate `066c924` did not touch their platform-sensitive implementation. Independent assessment of `066c924` attempt 1 validated all evidence/digest/mutation chains and found 21/24 cases matched, no forbidden branch, authority violation, out-of-scope mutation, or Git HEAD change. The three mismatches and exact-candidate evidence limits are retained in `audit.md`.

The version owner directed formal RC.4 release after identifying repeated R4 execution and unbounded rerun behavior as the controlling process defect. HC7 is therefore a bounded RC-only `WAIVED` decision, not a model-semantic pass. Because the campaign-control implementation and governance record change both qualification-execution and broad semantic-runtime identities after attempt 1, HC8's post-R4 unchanged-identity condition is also explicitly `WAIVED`; no new R4 run is authorized or useful merely to refresh those identities. D15 now makes future live runs cumulative, identity-aware, interrupt-safe, and fail-closed.

## Next

Complete local final-byte verification and exact-diff independent review, commit and push the candidate, require exact-SHA semantic plus compatibility CI, then build and verify reproducible local and hosted artifacts, provenance, SBOM, isolated plugin lifecycle, annotated tag, and GitHub prerelease. Do not perform any further model execution. Primary-profile installation and stable 2.0 promotion remain outside this release action.

## Hard conditions

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | Technology-neutral RC.4 requirement baseline confirmed | implementation | passed | User confirmed on 2026-08-28 |
| HC2 | Implementation-ready architecture and slice plan passed traceability, feasibility, counterexample, and internal-consistency review | implementation | passed | Same-context pre-implementation validation completed 2026-08-29 in `audit.md`; `common-mode-risk` retained |
| HC3 | RC.3 public compatibility and current context budgets frozen before source behavior changes | implementation | passed | Baseline captured; current measured budgets are 2,634/2,660 description characters and 17,999/18,000 ordinary static bytes |
| HC4 | Resource lease/preflight behavior passes the supported Ubuntu/macOS/Windows matrix or unsupported cells remain release-blocking | implementation | passed | Exact implementation passed Ubuntu, macOS, and Windows/Python 3.11/3.14 in run `33228757027`; later `066c924` changes did not touch the platform-sensitive implementation, and final candidate CI must still revalidate the changed runner scope |
| HC5 | RC.3 renewed-authority and reference-comparison waivers closed or explicitly re-waived | qualification | passed | Independent `066c924` attempt-1 assessment matched both `DELEGATION-EXPANSION-REQUIRES-RENEWED-AUTHORITY` and `CONTEXT-REFERENCE-REPOSITORY-BOUNDARY` |
| HC6 | Independent clean-context review completed against frozen candidate | qualification | passed | Final independent diff review against `066c924` baseline reported no actionable finding after fault-injection, admission-ownership, first-failure, and multiprocess-budget corrections |
| HC7 | Three complete-catalog model-semantic attempts completed within separately authorized budget | qualification | waived | Version owner authorized formal RC.4 release after repeated R4 repairs exceeded the intended budget; exact `066c924` attempt 1 is `MISMATCHED` at 21/24 and is retained as bounded evidence, not relabeled as a pass |
| HC8 | Semantic-runtime identity, qualification-execution dependency closure, and post-R4 evidence-only allowlist are proved | qualification | waived | Identity machinery is deterministically tested, but D15 runner/governance corrections changed both broad identity domains after attempt 1; owner release disposition forbids another identity-refresh R4 and accepts this RC-only freshness gap |
| HC9 | Exact final-commit artifact/install/delivery readiness established | qualification | not-run | S9; does not authorize publication |

## Active convergence checkpoint

None.

## Worktree boundary

- Active Git root: `/Users/ethan/Repo/dev-flow`
- Branch/baseline at planning start: `main` / `v2.0.0-rc.3`
- Current task writes: the accumulated S0-S8 prefixes declared in `implementation.md`; S9 is evidence-only unless a reviewed repair reopens S8.
- User-owned pre-existing changes observed at planning start: none.
- Protected current paths: all released source, RC.3 workstream evidence, tags, and external installations.
- User authorized continuing through formal RC.4 release on 2026-08-29, including final candidate commit/push, hosted CI/artifacts, annotated tag, and GitHub prerelease publication. Isolated install/uninstall verification is in scope; primary-profile installation, stable promotion, deployment, and unrelated external mutation remain unauthorized.

## Evidence limits

- Independent implementation-byte review passed for the final D15 diff. Independent attempt-1 assessment is exact-candidate evidence for `066c924`, not a complete three-attempt R4 pass.
- RC.4 source behavior exists and local deterministic evidence is being finalized; implementation completion is not release qualification.
- Hosted semantic and complete cross-platform lease evidence passed after the causal token fix. The exact final campaign-control bytes still require hosted CI, artifact/provenance/SBOM, isolated lifecycle, and independent-diff proof. RC.4 retains an explicit model-semantic waiver and makes no stable-release or population-effectiveness claim.
- Static repository search may miss external or runtime-only consumers.
- The installed Codex CLI no longer exposes the historical `codex plugin check` subcommand; manifest, inventory, isolated lifecycle, release-artifact, and suite validators pass as the bounded fallback, while the removed CLI surface is `NOT RUN` rather than inferred.
- Stable 2.0 soak remains future separately authorized work after RC.4 release.
