# Test adapter contract

An adapter maps one test-matrix cell to a repository-native invocation. Do not invent a universal runner when the repository already has authoritative commands.

## Adapter fields

Record:

- adapter ID, project profile, repository root, and supported matrix dimensions;
- discovery/preflight command and required tool versions;
- exact test command, selection/filter syntax, timeout, exit semantics, and pass oracle;
- environment variables by name only, credential source, ports, devices, and leases;
- artifact paths, privacy class, retention, reset, teardown, and leaked-resource checks;
- unsupported dimensions and required manual/physical evidence.

## Built-in routing guidance

- Rust: repository scripts first, then Cargo package/target/feature selection; distinguish format, clippy, unit/integration/doc tests, nextest, Miri, sanitizers, fuzz, loom, benchmarks, and packaged startup.
- React/web: pnpm scripts first; distinguish typecheck/lint/unit/component/build and Playwright projects. Record browser engine, viewport/device, auth setup, workers, retries, and trace policy.
- Apple: distinguish SwiftPM from Xcode; name scheme/test plan/configuration/destination and retain `.xcresult`. Simulator evidence does not substitute for required device evidence.
- Android: distinguish JVM, Robolectric, instrumentation, managed device, emulator, and physical device; name Gradle task, API/ABI, sharding, orchestrator, and report/logcat paths.
- Services/data: allocate unique container/network/port/database/schema names; prove readiness with the tested contract; record migration state and cleanup.
- CLI/TUI/background jobs: capture stdout/stderr/exit, terminal/signal behavior, fake clock/scheduler state, process lifecycle, restart, duplicate delivery, and drain evidence.

## Invocation discipline

Run preflight before acquiring scarce resources. Execute one adapter/cell per recorded lease. Stream concise progress, but write full attempts and artifacts to the packet. Preserve the first failure, reset intentionally, and classify product/test/environment/infrastructure before retrying. A wrapper that hides versions, exits, environment, or artifacts is not acceptable evidence.
