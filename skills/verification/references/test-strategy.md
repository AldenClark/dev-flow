# Risk-based test strategy

## Choose decision-useful views

Start from the changed behavior, credible failures, affected contracts, and risk. Use the smallest combination of views that can expose those failures:

- **Black-box:** derive oracles from user-visible behavior, public/API/CLI/UI contracts, normal and error outcomes, authorization, recovery, boundaries, and state transitions.
- **White-box:** inspect changed branches, states, error paths, cancellation, retries, timeouts, ownership, concurrency, idempotency, and rollback.
- **Property, differential, exploratory, or adversarial:** use these when input space, an old/new comparison, defect history, or a threat model makes them more discriminating.

Views are reasoning tools, not mandatory report sections. Use multiple views when they have distinct failure sensitivity; do not require every view or a prose `N/A` for an ordinary change. Any selected view may produce unit, component, integration, end-to-end, compatibility, or non-functional checks.

## Obligation derivation

Derive checks from protected behavior; changed branches, states, errors, limits, and cancellation; public contracts and persistence; compatibility and migration; security, concurrency, performance, unsafe/FFI, platform, accessibility, and operations; historical regressions; and weakly covered impact areas.

For routine work, the test name, code, command, and result are usually enough. Use a written matrix only when several environments, resources, compatibility directions, or high-consequence gates must be coordinated. A behavior or design claim never substitutes for executed evidence. Keep unavailable physical, hosted, account, signing, deployment, or production gates explicit as `NOT RUN` in the final report.

When comparing available/unavailable paths, success/failure, virtual/physical environments, or old/new versions, evidence for one side never proves the other.

## Oracle challenge

Review test code as production evidence. For a high-risk or easy-to-fake oracle, challenge failure sensitivity with the strongest practical method: a focused pre-fix failure, negative fixture/control, deliberate local perturbation or mutation, assertion-path inspection against the changed branch, or an independent cross-oracle. Restore any perturbation before retaining evidence.

A test that passes when the behavior is broken, asserts only setup/internal trivia, swallows the relevant error, or relies on an uncontrolled mock is not a valid oracle. Record unresolved oracle weakness as an evidence gap; a green suite and a coverage percentage do not close it.

## Layers

- static: format, compile/typecheck, selected lint/static analysis, generated consistency, dependency/security/license/secret checks;
- unit: pure behavior, invariants, errors, limits, state transitions;
- property/model/fuzz: broad input or concurrent state spaces;
- component: module with controlled real/fake dependencies;
- integration: storage, filesystem, network, process, FFI, platform, or external contract;
- end to end: representative user/system flow in packaged/runtime environment;
- compatibility: versions, OS, architectures, browsers, devices, readers/writers, schemas, protocols, features;
- non-functional: latency, throughput, memory, startup, accessibility, security, recovery, and rollback.

## Selection order

1. Establish the current requirement/design intent, affected surface, risks, and observable oracles.
2. Add or update focused tests with the implementation, challenge material oracles, and run the narrow reproducer or affected cells.
3. Run the affected package/module suite and representative smoke path at the integration point.
4. Inspect the final diff, generated artifacts, comments, test changes, and scope drift before broader evidence.
5. Run repository static gates and relevant integration, then required compatibility/environment waves.
6. Run broad regression/release gates only when risk or delivery requires them.

Do not skip cheap relevant checks because a broad suite will run later. Build a rationale-driven matrix rather than a blind Cartesian product. Cover every critical migration, security, public-data, protocol, FFI, or release risk that the change actually exposes.

## Status and freshness

- `PASSED`: fresh evidence meets the oracle.
- `FAILED`: executed and did not meet it.
- `FLAKY`: identical attempts disagree.
- `BLOCKED`: infrastructure/prerequisite prevents execution.
- `NOT RUN`: not executed, with reason.
- `WAIVED`: authorized omission with owner/rationale; never passed.

Evidence must be after the final relevant change and identify enough root, environment, command/procedure, result, and limitation to support the conclusion. A stale run, linter, or report from another agent cannot prove the final product.

## Regression proof

For bug fixes, prove the oracle fails before the correction when practical. For migrations/refactors, compare old/new outputs and consumers. For performance, record workload, dataset/distribution, hardware, build profile, warmup/sample method, variance, baseline, target, and correctness guard.

For FFI, keep language-native, package/binding, lifecycle, virtual/physical, invalid/failure/leak, and each applicable directional consumer/core mixed-version cell visible. For overload, cover bounded admission, capacity, rejection/backpressure, retry amplification, and recovery.
