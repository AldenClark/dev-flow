# Test-system integrity obligations

## Discovery

Enumerate or otherwise prove that the intended tests were collected. Zero discovery, silent import failure, disabled suites, and skipped modules are distinct from a passing test.

## Selection

Prove filters, paths, schemes, tags, shards, and retries include the intended target. Include one protected negative that must remain excluded when selection correctness is material.

## Sensitivity

Use a safe mutation, broken fixture, pre-fix result, deliberate assertion inversion, or independent oracle to show the gate fails when its claim is false. Restore perturbations before retaining evidence.

## Isolation

Check clocks, environment, caches, files, ports, processes, devices, databases, ordering, reset, and teardown that can leak between cases. A shared resource needs isolation or serialization.

## Interpretation

Distinguish runner launch, collection, executed tests, assertions, skips, expected failures, flaky disagreement, timeout, crash, and infrastructure error. Do not collapse them into exit zero/nonzero.

## Representativeness

Name only the platform, runtime, configuration, account/data class, integration boundary, and compatibility direction actually observed. Missing physical, hosted, production-like, or cross-platform cells remain `NOT RUN`.

The completion handoff to `verification` contains the six dispositions, focused negative-control result, commands/environment, and claim limits. It does not claim product correctness by itself.
