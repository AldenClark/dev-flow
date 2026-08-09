# Test environment orchestration

## Resource ledger

Record each browser/profile, simulator/emulator/device, VM, container/service, port, database, filesystem fixture, credential, cache, build directory, network route, or shared external system with owner, isolation key, configuration, lease, reset, teardown, and leak check.

Never run concurrent writers against a shared mutable environment unless isolation is proven. Serialize physical devices, named simulators, fixed ports, shared databases, release credentials, signing/notarization, and other exclusive resources.

## Controlled waves

1. Validate configuration and prerequisite versions.
2. Allocate isolated temporary state through a safe platform primitive.
3. Start the narrowest service/environment and wait on an observable readiness condition.
4. Run the exact cell; preserve first failures before retry or repair.
5. Capture the minimum artifact and redact it.
6. Tear down even on failure; verify ports, processes, containers, mounts, profiles, devices, and credentials are released.

## Browser and frontend

Record browser engine/version, viewport, input mode, locale/time zone, reduced-motion/color preferences, fixture/account, server/build, console/network errors, screenshots/traces, keyboard/focus, and axe/manual accessibility cells. A DOM/unit pass does not prove rendered behavior.

## Apple and Android

Record OS/device/simulator, CPU architecture, toolchain, signing/entitlements, build configuration, install/launch, permissions, lifecycle/background state, logs, and packaged consumer. Keep simulator/emulator and physical-device evidence separate; do not report an unrun device cell as passed.

## Services and persistence

Use explicit host/port/storage/configuration, readiness checks, schema/seed identity, timeouts, and shutdown. Test restart, partial failure, duplicate delivery, rollback, and mixed-version order when required. Never point destructive tests at production or user data.

## Flakes

Repeat an identical cell, not a subtly repaired environment. Classify product race, test race, resource collision, timeout, contamination, or infrastructure. Quarantine only with owner, policy, retained signal, issue/removal condition, and explicit acceptance.
