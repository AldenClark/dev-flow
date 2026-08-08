# Test strategy and coverage

Coverage means justified evidence across behavior and risk dimensions, not a universal line-percentage target.

## Verification obligations

Derive tests from:

- acceptance criteria and protected behavior;
- changed branches, states, errors, limits, and cancellation paths;
- public API, protocol, schema, persistence, compatibility, and migration contracts;
- security, concurrency, performance, FFI, platform, accessibility, and operational risks;
- historical regressions and weakly covered impact areas.

Each obligation receives an ID such as `VO-1` and maps to one or more test matrix cells.

## Test layers

Use the smallest sufficient combination:

- static: format, compile/typecheck, lint, generated-code consistency, dependency/security/license scan;
- unit: pure logic, invariants, errors, limits, state transitions;
- property/model/fuzz: broad input or concurrent state spaces;
- component: module with controlled real or fake dependencies;
- integration: database, filesystem, network, process, FFI, platform, or external contract;
- end-to-end: user/system flow in a representative packaged/runtime environment;
- compatibility: versions, browsers, OS, architecture, devices, protocols, readers/writers, toolchains;
- non-functional: performance, memory, load, startup, accessibility, security, recovery, and rollback.

## Change-aware selection

1. Run the narrowest reproducer or affected test while implementing.
2. Run the affected package/module suite.
3. Run repository static gates and relevant integration tests.
4. Run compatibility and environment waves.
5. Run broad/regression/release gates only when risk and delivery require them.

Do not skip cheap required tests because a broad expensive suite will run later. Do not run every possible environment for a micro change with no compatible risk.

## Bug regression proof

When practical:

1. Add or identify a test that fails for the observed defect.
2. Run it against the broken state or temporarily remove/reverse the fix to prove it detects the defect.
3. Restore the fix and run it to green.
4. Run nearby regressions.

If red-green proof is unsafe, destructive, too expensive, or impossible, document the alternative reproduction evidence.

## Compatibility matrix

Specify dimensions and rationale rather than taking a blind Cartesian product. Use representative boundaries and pairwise coverage for low-risk combinations; require every critical contract cell.

Possible dimensions:

- OS/version and CPU architecture;
- browser/engine and viewport/input mode;
- physical device versus simulator/emulator;
- Swift/Kotlin/Rust/toolchain and package version;
- old/new client, server, reader, writer, schema, or protocol;
- debug/release, feature set, packaging/signing, and installation path;
- database/backend/service version and migration state.

## Status vocabulary

- `PASSED`: fresh evidence meets the cell's oracle.
- `FAILED`: the oracle was run and did not pass.
- `FLAKY`: repeated identical runs disagree; do not count as passed.
- `BLOCKED`: required infrastructure or prerequisite prevents execution.
- `NOT RUN`: not executed; reason required.
- `WAIVED`: explicitly accepted omission with owner and rationale; never report as passed.

Migration, security, public protocol, persisted data, release, and FFI work cannot receive a full acceptance or release-ready claim while a required cell is `FAILED`, `FLAKY`, `BLOCKED`, or `NOT RUN`.

## Flaky test handling

- Preserve the first failure evidence.
- Re-run the same cell enough to distinguish deterministic failure from instability; do not use retries to erase failure.
- Classify product race, test race, environment contamination, resource conflict, timeout, or infrastructure outage.
- Quarantine only with explicit policy, owner, issue/removal condition, and retained signal.

## Evidence freshness

Completion evidence must be generated after the final relevant change. Record command, root, environment, configuration, timestamp, exit code, counts, artifacts, and limitations. A previous run, child report, or linter cannot prove a final build, test, behavior, or release claim.
