# Test-system integrity obligations

Apply these obligations at the boundary under suspicion. They are independent failure modes, not six boxes that jointly declare product correctness.

## Discovery

Enumerate or otherwise prove that the intended tests were collected by the project-native runner. Zero discovery, silent import failure, disabled suites, conditional registration, naming mismatch, missing generated tests, and skipped modules are distinct from a passing test. Check the new/changed test identity, not only a total count.

## Selection

Prove filters, paths, schemes, tags, feature flags, build variants, shards, and retry rules include the intended target exactly where claimed. Confirm shards cover the full intended set without gaps; check exclusions and quarantine lists. Include one protected negative that must remain excluded when selection correctness is material.

## Sensitivity

Use a pre-fix result, negative fixture, safe changed-code/semantic mutation, seeded fault, deliberate assertion inversion, property violation, or independent oracle to show the gate fails when its claim is false. Confirm it fails because of the target assertion rather than setup or unrelated infrastructure. Restore perturbations before retaining evidence.

## Isolation

Check fixtures, clocks, randomness/seeds, environment, caches, files, ports, processes, devices, databases, network controls, ordering, reset, and teardown that can leak between cases or runs. Exercise order reversal or a fresh cache when that distinguishes pollution. A shared resource needs isolation or serialization, and production/user data must not become a fixture.

## Interpretation

Distinguish runner launch, collection, executed tests, assertion outcomes, skips, expected failures, quarantines, cached results, retries, flaky disagreement, timeout, crash, cancellation, and infrastructure error. Inspect whether a retry hid the first failure and whether a cache reused results for different bytes/configuration. Do not collapse them into exit zero/nonzero.

## Representativeness

Name only the platform, runtime, build mode, configuration, account/data class, integration boundary, and compatibility direction actually observed. A mock proves the caller around the mock; host tests, simulators, and emulators prove their own environments. Missing physical-device, native-platform, hosted, production-like, or cross-version evidence remains `BLOCKED` or `NOT RUN`.

## AI self-confirmation audit

When AI produced both implementation and tests, compare them with at least one independent source: user-visible/public contract behavior, a separately derived final-code risk, a small reference model, a property/metamorphic relation, old/new differential behavior, a retained real example, or a seeded fault. Another prose explanation of the same implementation is not independence.

Inspect tests for assertions on setup, mocks, call counts, snapshots, or internal representation that can stay green while the promised outcome is wrong. A useful seeded fault changes a material branch, state write, error, boundary call, cleanup, or environment attribution and must make the intended native gate fail.

The completion handoff to `verification` contains the six dispositions, focused negative-control result, commands/environment, and claim limits. It does not claim product correctness by itself.
