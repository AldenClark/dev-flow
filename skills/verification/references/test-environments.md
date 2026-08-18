# Test environment orchestration

Use this reference for shared, stateful, expensive, physical, credentialed, or externally visible test environments. A normal isolated unit test needs no resource record.

## Ownership and isolation

- Give each concurrent writer an isolated browser profile, simulator/device, VM/container, port, database/schema, filesystem fixture, cache, build directory, or external sandbox.
- Serialize a resource when isolation is not proven, especially physical devices, fixed ports, shared databases, signing/notarization, release credentials, and production-like external systems.
- Resolve who owns teardown before starting a long-lived or shared resource.

## Controlled run

1. Check the relevant configuration and prerequisites.
2. Allocate temporary state through a safe platform primitive.
3. Start the narrowest environment and wait on an observable readiness condition.
4. Run the focused check; preserve a first failure before retry or repair.
5. Capture only the artifact needed for the oracle and redact it.
6. Tear down on success or failure and confirm important resources were released.

Record detailed configuration, isolation key, reset, and cleanup only when another participant must coordinate the same resource or reproduce the result.

## Environment-specific evidence

- Browser/UI: distinguish engine/version, viewport, input mode, server/build, console/network errors, keyboard/focus, accessibility, and screenshot/trace evidence that matter to the claim.
- Apple/Android: distinguish simulator/emulator from physical device, toolchain, architecture, signing/entitlements, install/launch, permissions, lifecycle, logs, and packaged consumer.
- Services/data: use explicit endpoints/storage/configuration, readiness, schema/seed identity, timeouts, and shutdown. Exercise restart, partial failure, duplicates, rollback, or mixed versions only where the changed behavior depends on them.

Never point destructive tests at production or user data. Classify contradictory identical attempts as flaky; quarantine only with a real owner and removal condition.
