---
name: verification
description: Verify changed behavior with risk-based oracles and fresh native evidence.
---

# Verification

Own evidence that can falsify a claim; broaden only for affected promises or risks.

A bounded read-only check may run alone. With material mutation, cross-boundary coordination, or managed continuity, load `dev-flow` as the coordinating kernel when it is available and not already active.

Route suspected runner/fixture/cache/retry/skip/isolation false evidence to `test-system-engineering`.

## Procedure

1. State the promise, credible failure, target environment, and disproof.
2. For new or material behavior, derive both views:
   - **Black-box:** user outcomes/contracts, including material failure, recovery, permission, and compatibility.
   - **White-box:** final implementation branches/conditions, states, boundaries, errors, concurrency, resources, cancellation, retry, and rollback.
   They may share a test. Use views where they add distinct failure sensitivity. Do not require each view or a prose `N/A`.
3. Choose the cheapest truthful layer: unit, component, real-boundary integration/contract, runtime E2E, or native platform/device. Do not fill a fixed matrix.
4. Preserve the focused run's first failure. Challenge high-risk or easy-to-fake evidence with a practical negative control: pre-fix failure, negative fixture, seeded fault, changed-code mutation, or independent cross-oracle. Restore it, then broaden.
5. Re-read the final diff, invalidate stale runs, and report `PASSED`, `FAILED`, `FLAKY`, `BLOCKED`, `NOT RUN`, or `WAIVED` with command, environment, result, and limit. A retry does not turn a flake into `PASSED`.

Read `references/test-strategy.md` for strategy, `references/coverage-techniques.md` for a concrete gap, `references/test-environments.md` before controlled resources, and `references/evidence-contract.md` before retaining artifacts.

## Budget and stopping

- **Core:** principal outcomes, material failure/recovery, changed structure/contracts, regressions, and high-consequence risks.
- **Extended:** common combinations/environments and plausible abnormal paths that add confidence.
- **Fringe:** stop when costly low-probability, low-consequence cases add no obligation or sensitivity. Rare high-consequence failures stay core.

## Boundaries

- Configuration is not execution. Host/mock/simulator/emulator evidence never upgrades to device/platform/hosted/production evidence.
- A fallback proves only its own narrower claim, never a blocked real-boundary or target-environment gate.
- Coverage/counts/method names cannot replace an oracle.
- Do not modify product code during an explicitly independent test-runner assignment.
- Do not retain unnecessary sensitive payloads or bulk logs.
