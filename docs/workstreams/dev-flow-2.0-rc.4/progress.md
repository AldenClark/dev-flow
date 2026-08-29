<!-- dev-flow-workstream-contract: v1 -->
# Dev Flow 2.0 RC.4 progress

## Status

- State: active
- Current slice: S8
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

## Current slice

S8 remains active on the contradictory macOS 15/Python 3.14 evidence. Failed and passing runs used the same macOS 15.7.7 arm64 image, Python 3.14.6, runner version, product lease bytes, synthetic input, and isolated temporary-root design; deterministic version drift and shared-directory contamination are therefore rejected hypotheses. User-authorized convergence now permits one final auxiliary diagnostic after the assertion and change-scope repairs: 25 black-box CLI round trips on only that hosted cell, preserving return code/stderr on recurrence and never treating repetition as a qualification retry. A newly authorized independent frozen-byte review is running. Live three-attempt R4 execution and final hosted artifacts have not run.

## Next

Run the single bounded macOS variance diagnostic and reconcile the independent review against its final diff. If the diagnostic reproduces, preserve its process evidence and repair only a proven cause; if it does not, retain HC4 as `flaky` until the version owner explicitly waives the low-frequency hosted residual risk. Start the already-authorized R4 execution only after S8/HC4 and final-byte review close. Do not dispatch hosted artifacts, tag, publish, or install while these prerequisite gates remain open.

## Hard conditions

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | Technology-neutral RC.4 requirement baseline confirmed | implementation | passed | User confirmed on 2026-08-28 |
| HC2 | Implementation-ready architecture and slice plan passed traceability, feasibility, counterexample, and internal-consistency review | implementation | passed | Same-context pre-implementation validation completed 2026-08-29 in `audit.md`; `common-mode-risk` retained |
| HC3 | RC.3 public compatibility and current context budgets frozen before source behavior changes | implementation | passed | Baseline captured; current measured budgets are 2,634/2,660 description characters and 17,999/18,000 ordinary static bytes |
| HC4 | Resource lease/preflight behavior passes the supported Ubuntu/macOS/Windows matrix or unsupported cells remain release-blocking | implementation | flaky | `e808c1a` failed macOS 15/Python 3.14; complete-matrix repair candidate `75150a3` passed all cells without a product lease change, so the contradictory observation remains release-blocking |
| HC5 | RC.3 renewed-authority and reference-comparison waivers closed or explicitly re-waived | qualification | open | S7/S9 |
| HC6 | Independent clean-context review completed against frozen candidate | qualification | open | User authorized dispatch; independent reviewer is checking frozen candidate `5d7b344` and will recheck the bounded diagnostic diff before closure |
| HC7 | Three complete-catalog model-semantic attempts completed within separately authorized budget | qualification | not-run | User delegated budget choice; frozen plan is Terra/medium, 12M aggregate, 600k/call, 900s/call, 23 complete cases × 3 attempts; S8 must close before execution |
| HC8 | Semantic-runtime identity, qualification-execution dependency closure, and post-R4 evidence-only allowlist are proved | qualification | not-run | Implementation and deterministic mutation tests exist; post-R4 unchanged-identity proof has not run |
| HC9 | Exact final-commit artifact/install/delivery readiness established | qualification | not-run | S9; does not authorize publication |

## Active convergence checkpoint

None.

## Worktree boundary

- Active Git root: `/Users/ethan/Repo/dev-flow`
- Branch/baseline at planning start: `main` / `v2.0.0-rc.3`
- Current task writes: the accumulated S0-S8 prefixes declared in `implementation.md`; S9 is evidence-only unless a reviewed repair reopens S8.
- User-owned pre-existing changes observed at planning start: none.
- Protected current paths: all released source, RC.3 workstream evidence, tags, and external installations.
- User authorized starting the release process, continuing the bounded macOS diagnostic, dispatching the new independent review, and choosing/executing the R4 model budget on 2026-08-29. Candidate staging, commits, pushes, hosted CI, the review dispatch, and the non-spending R4 plan have occurred. Tagging, publication, installation, and unrelated external mutation remain unauthorized.

## Evidence limits

- Independent implementation-byte review passed after one repair/recheck cycle; the later theoretical-validation diff has only same-context review and does not satisfy frozen-candidate independence.
- RC.4 source behavior exists and local deterministic evidence is being finalized; implementation completion is not release qualification.
- Hosted semantic and complete cross-platform lease evidence has run, but macOS 15/Python 3.14 is contradictory across candidates with unchanged product logic and therefore `flaky`. No model-semantic, live shared-resource, hosted artifact, publication, or install evidence has run; the prior independent review does not cover the final theoretical-validation bytes.
- Static repository search may miss external or runtime-only consumers.
- The installed Codex CLI no longer exposes the historical `codex plugin check` subcommand; manifest, inventory, isolated lifecycle, release-artifact, and suite validators pass as the bounded fallback, while the removed CLI surface is `NOT RUN` rather than inferred.
- Stable 2.0 soak remains future separately authorized work after RC.4 release.
