# Risk-based test strategy

## Technique accountability

For every non-trivial behavior change, design and account for these perspectives separately before implementation is considered complete:

- **Black-box:** derive tests from approved requirements, `AC-n`, protected behavior, public/API/CLI/UI/component contracts, normal and error outcomes, authorization, recovery, equivalence classes, boundaries, and state transitions without using implementation structure as the source of coverage.
- **White-box:** inspect the changed implementation and derive tests for branches, states, error paths, cancellation, retries, timeouts, lifecycle/resource ownership, concurrency, idempotency, rollback, and warranted property/model/fuzz/fault-injection cases that external examples may miss.
- **Experience-based / exploratory / adversarial:** use defect history, threat and misuse models, reviewer intuition, red-team challenges, and surprising sequences to discover additional risks. This is a third perspective and cannot substitute for black-box or white-box work.

For each perspective, record its applicability, derived obligations, and mapped test cells. If black-box or white-box testing is applicable, implement and run it. Use `N/A` only with a concrete reason tied to the actual change; lack of time, a broad suite, coverage percentage, or another perspective is not a reason.

Black-box and white-box describe how obligations are derived, not where tests run. Either perspective may produce unit, component, integration, end-to-end, compatibility, or non-functional cells.

## Obligation derivation

Derive `VO-n` from acceptance and protected behavior; changed branches/states/errors/limits/cancellation; public API, protocol, schema, persistence, compatibility, migration; security, concurrency, performance, unsafe/FFI, platform, accessibility, and operations; historical regressions; and weakly covered impact areas.

Each matrix cell declares obligation, scope/environment, setup/fixture, command or manual procedure, oracle, resources/owner, attempts, status, artifacts, teardown, and limitation.

When a task requires exercise, validation, or checking, create a separate verification-owned test cell for every independently observable outcome. A behavior, interaction, decision, or implementation claim never substitutes for that evidence cell. Keep the cell explicit even when execution is unavailable: record its stimulus, oracle, environment, `NOT RUN` status, and limitation.

When a task contrasts available and unavailable paths, success and failure, virtual and physical environments, or old and new versions, retain each side as its own cell. Evidence for one side never proves the other.

## Oracle challenge

Review test code as production evidence. For every new or materially changed test, state the protected behavior, the observation point, and why the assertion discriminates correct from broken behavior. Demonstrate failure sensitivity with the strongest practical method: a focused pre-fix failure, negative fixture/control, deliberate local perturbation or mutation, assertion-path inspection against the changed branch, or an independent cross-oracle. Restore any perturbation before retaining evidence.

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

1. Freeze the requirement/design baseline, `AC/SC/VO` mapping, affected surface, and black-box/white-box obligations.
2. Add or update the focused tests with the implementation, challenge their oracles, and run the narrow reproducer or affected cells.
3. Run the affected package/module suite and representative smoke path at the integration point.
4. Inspect the final diff, generated artifacts, comments, test changes, and scope drift before broader evidence.
5. Run repository static gates and relevant integration, then required compatibility/environment waves.
6. Run broad regression/release gates only when risk or delivery requires them.

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
