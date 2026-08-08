# Test environment orchestration

Use this reference when tests require browsers, simulators, emulators, devices, VMs, containers, databases, external services, ports, signing identities, or other scarce/shared resources.

## Resource ledger

Before launching a wave, record:

- resource ID, type, version, image/snapshot, architecture, and ownership;
- exclusive or shareable status;
- ports, accounts, test data, credentials source, and network assumptions;
- startup, health, reset, artifact, and teardown commands;
- lease deadline and cleanup owner.

Do not let two agents mutate the same simulator, emulator, VM, database, browser profile, port, working tree, or build output concurrently.

## Controlled waves

1. **Preflight:** verify toolchain, licenses, images, device health, disk, ports, credentials, and baseline.
2. **Cheap local:** unit/component/static checks without scarce resources.
3. **Representative smoke:** one browser/device/runtime per critical flow.
4. **Compatibility:** expand to selected matrix cells with isolated resources.
5. **Stress/adversarial:** concurrency, load, recovery, interruption, malformed input, or security cases.
6. **Packaged/final:** test the actual release artifact, installation, signing, loader, permissions, and update path.
7. **Teardown:** stop processes, release leases, collect artifacts, reset or destroy ephemeral state, and verify no leaked resources.

Advance only when the current wave's blocking failures are understood. Parallelize cells only when resources and outputs are isolated.

## Determinism and isolation

- Prefer immutable VM/container images, managed virtual devices, clean browser profiles, disposable databases, temporary directories, and seeded test data.
- Reset state between cells according to the product contract, not only between suites.
- Replace arbitrary sleeps with condition-based waits and explicit deadlines.
- Capture exact versions and random seeds. Make clock, RNG, IDs, and external responses injectable where the product permits.
- Avoid network-dependent tests unless the external contract is the subject; bound retries and preserve the first failure.

## Browser testing

- Define Playwright projects for supported engines, device/viewport, locale, color scheme, authentication state, and dependency setup. Use project dependencies for shared authenticated setup, not implicit suite order.
- Keep CI retries explicit and small. Preserve the first failure and use trace-on-first-retry or equivalent evidence policy; a passing retry changes the cell to `FLAKY`, never `PASSED`.
- Retain trace, screenshot, video, console, network, and accessibility evidence on failure according to privacy policy.
- Use sharding only when tests and accounts are isolated; avoid serial bottlenecks disguised by parallel workers.
- Verify keyboard/focus/accessibility and visible behavior, not DOM implementation alone.

## Apple platforms

- Separate Swift package tests, Xcode unit/UI tests, simulator runtime tests, packaged app tests, and physical-device evidence.
- Use Xcode Test Plans to make configurations, localization, sanitizers, repetitions, and target selection reviewable. Name destinations explicitly and retain `.xcresult` bundles before teardown.
- Record Xcode, SDK, runtime, simulator/device, architecture, signing, entitlement, and configuration.
- Treat simulator-only evidence as insufficient for hardware, background, networking, extension, entitlement, energy, or performance claims that differ on device.

## Android

- Prefer reproducible Gradle Managed Devices for matrix execution when appropriate; isolate emulator data and ports.
- Use instrumentation isolation/orchestrator for state-sensitive suites where supported.
- Group managed devices by required API/ABI/form factor and use sharding only when tests, app data, ports, and reports are isolated.
- Enable CheckJNI for JNI changes and retain logcat, tombstone, ANR, and test reports.
- Distinguish JVM, Robolectric, emulator, and physical-device evidence.

## VMs, containers, databases, and services

- Pin images and snapshots; verify architecture and acceleration.
- Allocate unique names, networks, ports, volumes, schemas/databases, and credentials per cell.
- Use readiness checks that prove the tested contract, not only process existence.
- Test restart, interruption, partial failure, clock/network disturbance, and rollback when required.
- Preserve diagnostics before teardown and report host-resource failures separately from product failures.

## Failure handling

On failure:

1. Freeze or preserve the failing state when safe.
2. Capture logs, traces, screenshots, process status, versions, resource usage, and environment changes.
3. Classify product, test, environment, compatibility, or infrastructure failure.
4. Re-run only after recording the original evidence and resetting intentionally.
5. Do not broaden retries until the failure mechanism is understood.

Use `test-adapters.md` to translate this contract into repository-native commands. Apply `evidence-privacy-and-retention.md` before retaining any artifact.
