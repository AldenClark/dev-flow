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

## Current slice

S8 remains blocked by contradictory hosted evidence. Exact candidate `e808c1a697ab04617d722e5d8ed8864237cc89a1` passed semantic Ubuntu 3.14 and four compatibility cells, but macOS 15/Python 3.14 failed because the release CLI subprocess produced no parseable stdout. After diagnostic assertion `d90c85a` exposed a compatibility-scope omission, red-first repair candidate `75150a3800626039d9d3807963fdb64f13be98aa` ran the complete matrix: semantic Ubuntu 3.14 and all five compatibility cells passed. The product lease implementation did not change between the failed and passing macOS 15/Python 3.14 observations, so that cell is classified `flaky`, not repaired or stably passed. The theoretical-validation diff also lacks a new clean-context review. Live three-attempt R4 model evidence and final hosted artifacts have not run.

## Next

Diagnose the macOS 15/Python 3.14 subprocess flake with a bounded, hypothesis-bearing change or record an explicit owner waiver; repeated unchanged-SHA runs cannot convert the contradictory evidence into a stable pass. Then obtain a clean-context review of the frozen bytes and separately authorize the three-attempt model/token budget before S9. Do not dispatch hosted artifacts, tag, publish, or install while these prerequisite gates remain open.

## Hard conditions

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | Technology-neutral RC.4 requirement baseline confirmed | implementation | passed | User confirmed on 2026-08-28 |
| HC2 | Implementation-ready architecture and slice plan passed traceability, feasibility, counterexample, and internal-consistency review | implementation | passed | Same-context pre-implementation validation completed 2026-08-29 in `audit.md`; `common-mode-risk` retained |
| HC3 | RC.3 public compatibility and current context budgets frozen before source behavior changes | implementation | passed | Baseline captured; current measured budgets are 2,634/2,660 description characters and 17,999/18,000 ordinary static bytes |
| HC4 | Resource lease/preflight behavior passes the supported Ubuntu/macOS/Windows matrix or unsupported cells remain release-blocking | implementation | flaky | `e808c1a` failed macOS 15/Python 3.14; complete-matrix repair candidate `75150a3` passed all cells without a product lease change, so the contradictory observation remains release-blocking |
| HC5 | RC.3 renewed-authority and reference-comparison waivers closed or explicitly re-waived | qualification | open | S7/S9 |
| HC6 | Independent clean-context review completed against frozen candidate | qualification | blocked | Prior implementation review closed four findings, but the later theoretical-validation diff has only same-context review; new delegation authority is absent and `common-mode-risk` remains |
| HC7 | Three complete-catalog model-semantic attempts completed within separately authorized budget | qualification | not-run | Requires model/token authority at S9 |
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
- User authorized starting the release process on 2026-08-29; candidate staging, commits, pushes, and hosted CI have occurred. Tagging, publication, installation, unrelated external mutation, and model execution remain unauthorized. A new independent frozen-byte review still needs explicit delegation authority.

## Evidence limits

- Independent implementation-byte review passed after one repair/recheck cycle; the later theoretical-validation diff has only same-context review and does not satisfy frozen-candidate independence.
- RC.4 source behavior exists and local deterministic evidence is being finalized; implementation completion is not release qualification.
- Hosted semantic and complete cross-platform lease evidence has run, but macOS 15/Python 3.14 is contradictory across candidates with unchanged product logic and therefore `flaky`. No model-semantic, live shared-resource, hosted artifact, publication, or install evidence has run; the prior independent review does not cover the final theoretical-validation bytes.
- Static repository search may miss external or runtime-only consumers.
- The installed Codex CLI no longer exposes the historical `codex plugin check` subcommand; manifest, inventory, isolated lifecycle, release-artifact, and suite validators pass as the bounded fallback, while the removed CLI surface is `NOT RUN` rather than inferred.
- Stable 2.0 soak remains future separately authorized work after RC.4 release.
