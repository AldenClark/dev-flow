---
name: verification
description: Verify changed behavior with risk-based oracles and fresh native evidence.
---

# Verification

Own evidence that can falsify a claim; broaden only for affected promises or risks.

Use `dev-flow` to coordinate material mutation, cross-boundary or managed work. A bounded read-only check may run alone.

Route suspected runner/fixture/cache/retry/skip/isolation false evidence to `test-system-engineering`.

## Procedure

1. State the promise, intended actor or source when relevant, credible failure, target environment, and disproof. An unrelated event cannot satisfy the user's flow.
2. For new or material behavior, derive both views:
   - **Black-box:** user outcomes/contracts, including material failure, recovery, permission, and compatibility.
   - **White-box:** final implementation branches/conditions, states, boundaries, errors, concurrency, resources, cancellation, retry, and rollback.
   They may share a test. Use views where they add distinct failure sensitivity. Do not require each view or a prose `N/A`.
3. Choose the cheapest truthful layer that can disprove the claim. For each added check, name its risk, decision and stopping limit. Reuse valid original evidence; rerun only affected claims under `references/evidence-contract.md`. No fixed matrix or duplicate proof bundle.
4. Preserve the focused run's first failure. For high-risk or easy-to-fake evidence, reuse valid sensitivity proof or challenge the oracle with a pre-fix failure, negative fixture, seeded fault, mutation or independent relation. Confirm failure at the protected assertion, restore any perturbation and recheck affected inputs. Rechallenge when sensitivity is unknown or invalidated.
5. For installed/external/production claims, connect final bytes, artifact identity, actual target and install, effective configuration and data, intended flow or effect, observation, and consequential recovery. Build, upload, install, or health checks prove only their own link. Recheck affected downstream evidence when a link changes.
6. Re-read the final diff against the accepted behavior, invalidate only affected claims, and consume native results directly. Report `PASSED`, `FAILED`, `FLAKY`, `BLOCKED`, `NOT RUN`, or `WAIVED` with command, actor/source, artifact and target identity where applicable, effective environment, result, and limit. A retry does not turn a flake into `PASSED`; a successful tool exit or output file does not prove its contents satisfy the observation contract.

After a semantic correction, reconcile code/data, test expectations, and late child evidence; recheck the example and counterexample. `dev-flow/references/core-lifecycle.md` owns affected freshness.

Read `references/test-strategy.md` for strategy, `references/coverage-techniques.md` for a concrete gap, `references/test-environments.md` before controlled resources, and `references/evidence-contract.md` before retaining artifacts.

## Budget and stopping

- **Core:** principal outcomes, material failure/recovery, changed structure/contracts, regressions, and high-consequence risks.
- **Extended:** common combinations/environments and plausible abnormal paths that add confidence.
- **Fringe:** stop when costly low-probability, low-consequence cases add no obligation or sensitivity. Rare high-consequence failures stay core.

## Boundaries

- Configuration is not execution or effective runtime state. Host/mock/simulator/emulator evidence cannot prove device/platform/hosted/production behavior. Unobserved required targets remain `NOT RUN` or `BLOCKED`.
- A fallback proves only its own narrower claim, never a blocked real-boundary or target-environment gate.
- Coverage/counts/method names cannot replace an oracle.
- Do not modify product code during an explicitly independent test-runner assignment.
- Do not retain unnecessary sensitive payloads or bulk logs.
