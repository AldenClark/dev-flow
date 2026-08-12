# Risk-based test strategy

## Obligation derivation

Derive `VO-n` from acceptance and protected behavior; changed branches/states/errors/limits/cancellation; public API, protocol, schema, persistence, compatibility, migration; security, concurrency, performance, unsafe/FFI, platform, accessibility, and operations; historical regressions; and weakly covered impact areas.

Each matrix cell declares obligation, scope/environment, setup/fixture, command or manual procedure, oracle, resources/owner, attempts, status, artifacts, teardown, and limitation.

When a task requires exercise, validation, or checking, create a separate verification-owned test cell for every independently observable outcome. A behavior, interaction, decision, or implementation claim never substitutes for that evidence cell. Keep the cell explicit even when execution is unavailable: record its stimulus, oracle, environment, `NOT RUN` status, and limitation.

When a task contrasts available and unavailable paths, success and failure, virtual and physical environments, or old and new versions, retain each side as its own cell. Evidence for one side never proves the other.

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

1. Narrow reproducer or affected test during implementation.
2. Affected package/module suite.
3. Repository static gates and relevant integration.
4. Required compatibility/environment waves.
5. Broad regression/release gates only when risk/delivery requires them.

Do not skip cheap required checks because a broad suite will run later. Build a rationale-driven matrix rather than a blind Cartesian product. Require every critical migration/security/public-data/protocol/FFI/release cell.

## Status and freshness

- `PASSED`: fresh evidence meets the oracle.
- `FAILED`: executed and did not meet it.
- `FLAKY`: identical attempts disagree.
- `BLOCKED`: infrastructure/prerequisite prevents execution.
- `NOT RUN`: not executed, with reason.
- `WAIVED`: authorized omission with owner/rationale; never passed.

Evidence must be after the final relevant change and include root, environment/configuration/version, exact command/procedure, time, exit, counts, artifact, and limitation. A stale run, linter, or report from another agent cannot prove the final product.

## Regression proof

For bug fixes, prove the oracle fails before the correction when practical. For migrations/refactors, compare old/new outputs and consumers. For performance, record workload, dataset/distribution, hardware, build profile, warmup/sample method, variance, baseline, target, and correctness guard.

For FFI, keep language-native, package/binding, lifecycle, virtual/physical, invalid/failure/leak, and each applicable directional consumer/core mixed-version cell visible. For overload, cover bounded admission, capacity, rejection/backpressure, retry amplification, and recovery.
