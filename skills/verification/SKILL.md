---
name: verification
description: Verify changed behavior with risk-based oracles and fresh native evidence.
---

# Verification

Own evidence that can falsify a claim; broaden only for affected promises or risks.

Use `dev-flow` to coordinate material mutation, cross-boundary or managed work. A bounded read-only check may run alone.

Route suspected runner/fixture/cache/retry/skip/isolation false evidence to `test-system-engineering`.

## Procedure

1. Start from the changed behavior, affected callers and usage paths, and credible failures. Check the intended user outcome; an unrelated event cannot satisfy the user's flow.
2. Choose the cheapest native check that can expose a material error. Use black-box outcomes or white-box branches, states and boundaries to resolve a concrete blind spot, rather than deriving both for every change. Add checks only when they can change a correctness or delivery decision.
3. Reuse valid results and rerun only checks affected by the final changes under `references/evidence-contract.md`. Ordinary tests need no input inventory, per-conclusion proof bundle, or per-check risk and stopping record.
4. Preserve the focused run's first failure. When evidence is suspicious, easy to fake, or protects a credible high-consequence failure, reuse applicable sensitivity proof or challenge the oracle with a pre-fix failure, negative fixture, seeded fault, mutation or independent relation. Confirm failure at the protected assertion, restore any perturbation and rerun the affected check.
5. For installed/external/production claims, verify the applicable artifact, actual target, effective configuration/data and intended flow or effect. Build, upload, install, or health checks prove only their own link. Check changed links and affected downstream behavior, including recovery when the promise depends on it.
6. Re-read the final diff against the accepted behavior and affected callers, then consume native results directly. Report the command, result and material limits; include source, artifact or environment detail only where needed to distinguish the claim. Use `PASSED`, `FAILED`, `FLAKY`, `BLOCKED`, `NOT RUN`, or `WAIVED` truthfully. A retry does not turn a flake into `PASSED`; a successful tool exit or output file does not prove its contents satisfy the oracle.

After a semantic correction, reconcile code/data, affected callers and test expectations, and discard superseded child evidence. `dev-flow/references/core-lifecycle.md` owns affected freshness.

Read `references/test-strategy.md` for strategy, `references/coverage-techniques.md` for a concrete gap, `references/test-environments.md` before controlled resources, and `references/evidence-contract.md` before retaining artifacts.

## Budget and stopping

- **Core:** principal outcomes, material failure/recovery, affected contracts and consumers, regressions, and credible high-consequence failures connected to the change.
- **Extended:** combinations, environments and abnormal paths only when they add meaningful fault sensitivity.
- **Stop:** omit further work when it cannot change a material correctness or delivery decision. Severity alone does not make an imagined failure part of this change.

## Boundaries

- Configuration is not execution or effective runtime state. Host/mock/simulator/emulator evidence cannot prove device/platform/hosted/production behavior. Unobserved required targets remain `NOT RUN` or `BLOCKED`; unrelated environments create no test obligation.
- A fallback proves only its own narrower claim, never a blocked real-boundary or target-environment gate.
- Coverage/counts/method names cannot replace an oracle.
- Do not modify product code during an explicitly independent test-runner assignment.
- Do not retain unnecessary sensitive payloads or bulk logs.
