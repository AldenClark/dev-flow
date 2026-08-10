---
name: verification
description: Derive risk-based test obligations, run repository-native checks, control environments and resources, and record fresh compatibility, security, performance, or accessibility evidence.
---

# Verification

If an environment choice, waiver, or manual user action is required, remain in Default mode and follow `../requirements-design/references/user-interaction.md`.

Prove observable behavior and risk with the smallest sufficient fresh evidence set.

## Procedure

1. Map the smallest risk-based oracle. Read `references/test-strategy.md` for governed work, multiple environments/layers, regressions without a clear oracle, or a full test matrix.
2. Map every `VO-n` to acceptance/protected behavior, changed states and errors, contracts, and active risks.
3. Prefer repository-native compiler/typecheck, formatter, selected lint/static analysis, tests, codegen validation, dependency/security checks, and CI-equivalent commands.
4. Run waves from narrow/cheap to broad/environment-heavy; keep required compatibility cells explicit.
5. Read `references/test-environments.md` before using browsers, simulators, devices, VMs, containers, services, ports, credentials, or shared mutable fixtures.
6. Preserve first failures, classify flakes, and never convert retries or waivers into `PASSED`.
7. Read `references/evidence-contract.md` before retaining logs, screenshots, traces, dumps, benchmarks, or user data beyond the immediate result.
8. Produce `verification.plan.v1` and `verification.results.v1` with exact root, environment, command, time, exit, counts, artifact, freshness, and limitation.

## EQAC rule

Execute native controls first. An admitted specialist route can add expert review but does not prove a command passed. When automation is incomplete, record the qualified manual/contextual oracle or explicit waiver; absence of one named Skill is not itself a failure.

## Boundaries

- Do not modify product code during an independent test-runner assignment.
- Do not collect or retain secrets, private data, or bulk artifacts unnecessarily.
- Report `PASSED`, `FAILED`, `FLAKY`, `BLOCKED`, `NOT RUN`, and `WAIVED` separately.
