# Dev Flow 2.0 stable progress

<!-- dev-flow-workstream-contract: v1 -->

- State: active
- Current slice: S2
- Terminal condition: immutable v2.0.0 public stable release with verified assets and the primary local Dev Flow installation updated and observed.

## Current truth

- Source candidate: `2.0.0`; integrated implementation and independent static review are complete; final frozen regression and real functional qualification are pending, not published.
- Started from `7d3fc25118c23b433519b00b88f52b4be73da0a7`; existing task-owned changes were the stable master plan and its docs navigation link. No unrelated changes were observed.
- RC.9 is still the current published source; the installed primary plugin reports `2.0.0-rc.9`, enabled. Stable implementation is in progress. The previous full local baseline was 646 tests, 4 failures and 1 platform skip; these results remain visible until repaired and reverified.
- Five disjoint implementation branches own semantic/interaction rules, methods/maintenance rules, Git/runtime diagnosis, capacity/dispatch logic and product-state migration. Root owns shared contract checks, release projections/artifact tests, integration and delivery.

Delivery state: commit=not-run; hosted_ci=not-run; cross_platform=not-run; independent_review=passed; tag=not-run; artifact=not-run; publication=not-run; isolated_install=not-run.

## Integration evidence and first failures

- Five implementation slices have returned focused evidence. The first integrated complete regression ran 710 tests in 68.464 seconds: two failures and one native Windows Job Object skip on this macOS host. The two failures both identified the stale RC.5 traceability anchor after its safe-alternative regression was renamed; the reference was repaired and the focused coverage tests now pass. This supersedes neither final regression nor native Windows evidence.
- Independent cumulative review applied the six stable lenses to `v1.1.2` through the current candidate. Four material findings were verified: settled-U1 method readiness retained an obsolete confirmation condition; machine-readable semantic stops and the general method ceiling lagged their owners; historical RC.2 navigation was presented as current truth. Those sources and their negative controls were repaired; independent affected recheck found no consequential residual, with 15 focused tests and three public CLI controls passing.
- A new settled-U1 native route test failed before repair because `requirement-baseline` was absent despite `design_allowed=true`. The repaired selector now follows current design permission; unresolved-choice controls remain blocked. Thirteen focused integration tests pass.
- Independent implementation review reproduced ancestor-checkout identity leakage for an untracked distribution package. Exact-root binding now preserves execution failures and true non-Git N/A. Three pre-fix native failures are retained; 87 affected tests and the independent six-control recheck pass with no residual finding.
- The second integration regression ran 715 tests in 68.932 seconds with two failures and the same platform skip: root's progress update had moved the delivery summary outside its required `Current truth` section. The summary was restored to the correct owner section without weakening the validator; both affected native checks pass. Final regression will run on the frozen clean commit.
- Product-state, 39 contracts, 15-Skill/32-dispatch suite, knowledge, plugin, methodology, RC.4/RC.5 static, compilation and diff checks pass at this integration point. The ordinary loaded-byte budget remains 13,469/13,500; it was not raised. Packaged data-security required checks pass with five manual live/account surfaces `not_observed`. RC.5 traceability validates its historical surface, not all stable semantics.
- Five native qualification fixtures have passed suite-health audit after the ordinary journey gained its required continuation turn. No model execution, immutable commit, hosted run, publication or installation has yet occurred. These fixtures use the existing bounded runner; no new product evaluation framework or repeated comparison study was added.

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | Approved semantic and runtime repairs have focused sensitive tests | implementation | passed | Sensitive pre-fix failures, focused repairs and current integration evidence |
| HC2 | Complete deterministic regression and suite/knowledge/plugin/security/compile/diff checks | implementation | not-run | Final integrated bytes required |
| HC3 | Cumulative requirements review and independent consolidated static review | qualification | passed | Stable-to-candidate delta; six lenses; verified findings repaired and independently rechecked |
| HC4 | Five real functional journeys on observed final candidate content | qualification | not-run | First attempts and real native outcomes, no repeated comparison campaign |
| HC5 | Exact-SHA semantic CI and applicable platform compatibility | qualification | not-run | Actual hosted observations required |
| HC6 | Archive/manifest/SBOM/checksums/attestations bind final candidate | qualification | not-run | Verified hosted artifact reused |
| HC7 | Immutable stable public tag/release/assets and isolated installation lifecycle | qualification | not-run | Publication facts and completion gates separate |
| HC8 | Primary local plugin pin, listing, path and content identify 2.0.0 | qualification | not-run | Existing loaded sessions separately reported |

## Next

Freeze the integrated clean candidate and run S2 on its exact bytes, then exact-SHA hosted delivery. Preserve first failures and invalidate only affected observations. Update this snapshot at meaningful slice boundaries; it is not a tool ledger. External evidence is recorded in a later current-truth commit, never by rewriting immutable candidate/tagged bytes.
