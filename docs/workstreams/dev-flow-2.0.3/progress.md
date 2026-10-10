# Dev Flow 2.0.3 release progress

<!-- dev-flow-workstream-contract: v1 -->

- State: active
- Current slice: S1
- Source candidate: `2.0.3`
- Terminal condition: final candidate qualified, committed/pushed, publicly published as stable 2.0.3 and primary installation verified; report fresh-session loading separately.

## Current truth

- Workspace base and previous published stable: `v2.0.2`; rollback: `v2.0.2`.
- User authority: pre-release checks/docs, commit, push, stable tag/publication and primary installation on 2026-10-10.
- Five functional journeys: WAIVED by explicit user decision on 2026-10-10 for this 2.0.3 release. No journey calls, PASS or quality-equivalence claim are inferred; the prior DLP exception was not reused.

Delivery state: commit=not-run; hosted_ci=not-run; cross_platform=not-run; independent_review=passed; tag=not-run; artifact=not-run; publication=not-run; isolated_install=not-run.

## Local evidence

The preceding model-policy implementation passed 806 tests (805 pass, one native Windows Job Object skip), 47 affected checks, final document checks and independent Sol-medium review. These do not qualify subsequent version/projection changes. First failed policy and context-budget observations were preserved; final entrypoint bytes remain unchanged at 13,469/13,500 ordinary static bytes. Final release candidate checks and cumulative review follow separately. Initial workstream checking detected a missing ID condition table; the existing contract table was added, without changing any release gate. A second check rejected the invented `planned` slice status; disposition: simplify to the contract’s existing `pending` vocabulary and keep the plan stable thereafter.

## Cumulative stable-to-candidate review

Independent clean-context Sol-medium review covered the cumulative public v2.0.2-to-candidate delta. One consequential P2 finding was found and closed: active build instructions selected 2.0.3 but comparison/verification/attestation examples still selected 2.0.2. All active example names and expected versions now select 2.0.3; reviewer closure recheck and diff check pass. No unresolved consequential finding remains.

- Traceability/V-model: registry, CLI, guidance and native tests align on ordinary P4, compound P5/P6 and explained explicit promotion. No dropped maintained requirement found.
- Change impact: public entrypoint → parser → public handler → router → host checks/output; both handlers forward selection_reason. Hooks and protected DLP source remain unchanged.
- Specification by example: fixed commands P0; adaptive verification P4; ordinary cross-component/high-risk review P4; complex positive controls retain P5/P6.
- Feature interaction: independent expected-value sweep of 2,048 signal combinations passes, including settled markers paired with unresolved signals.
- Black/white oracle accounting: 29 native routing checks pass, covering explicit override errors, host inventory, root/coupled boundaries and blanket-promotion negative controls. Full final regression separately passes 806 tests (805 pass / one Windows-only skip).
- Assumption mapping/premortem: caller reasons and host inventory remain assertions, not human permission or verified reasoning evidence. Suggestions do not spawn automatically; static routing is not proof of model-quality equivalence or savings. Recovery pins v2.0.2 after a material workflow regression and verifies installed bytes/fresh-session loading.

## Final local qualification

86 affected tests pass; 44 version/stable-method checks and 15 active-guidance checks pass after the runbook repair. The complete suite passes 806 tests in 81.898 seconds with ResourceWarnings treated as errors (805 pass / one native Windows Job Object integration skip). Suite (15 Skills), knowledge, plugin, packaged data-security doctor, 39 contracts, RC.4 static scan, RC.5 coverage, maintained methods, compilation and diff checks pass. Doctor has zero required failures and five live/manual gates not_observed. One additional targeted test command named a nonexistent test module; that invocation error is preserved in dev-flow-203-release-docs.log and corrected to the existing modules without product change. Workstream setup errors and simplification disposition remain recorded above.

Five live-model journeys are explicitly WAIVED for this release; no comparison/model spend or quality-equivalence result is inferred. Native Windows/platform, hosted artifacts and public/installed identity await separate observations.

## Bounded functional plan

Use the existing five stable journeys: ordinary bugfix; material semantic change with requirement confirmation; diagnose-fix-verify; unrelated local MCP isolation; continuation without inferred delivery authority. Each journey runs once on isolated final-candidate bytes, at most 13 total model calls/turns, at most 600,000 exposed tokens per call and 2,000,000 total. Stop on failure, budget exhaustion or consequential oracle/identity mismatch; no automatic retry, model comparison, production resource, real credential or primary-profile mutation. The user explicitly waived all five journeys for this release; this retained plan was NOT EXECUTED and authorizes no spend.

## Evidence limits

Five actual journeys remain WAIVED. Exact-SHA hosted CI/platform/artifacts, public publication, isolated/public installation and primary updated bytes remain NOT RUN until observed. Packaged security checks do not validate live account policy. Existing chats are not inferred reloaded.

## Hard conditions

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | Final local regression, affected controls and maintained projections | qualification | passed | 805 local passes / one native Windows skip; validators and focused checks pass |
| HC2 | Cumulative v2.0.2-to-candidate semantic and six-method static review | qualification | passed | Independent review found and closed stale release example versions; six conclusions below |
| HC3 | Five live-model functional journeys | qualification | waived | Explicit user exception for this 2.0.3 release on 2026-10-10 |
| HC4 | Exact-SHA semantic CI and applicable platform matrix | qualification | not-run | Inspect hosted native results |
| HC5 | Hosted artifact/SBOM/checksums and bound attestations | qualification | not-run | Verify exact source and signer workflow |
| HC6 | Immutable public stable tag/assets and isolated public lifecycle | qualification | not-run | Record actual release and byte identity |
| HC7 | Primary installed source/cache identity | qualification | not-run | Preserve old Hook cache; loading stays separate |
