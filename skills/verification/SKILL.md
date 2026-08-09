---
name: verification
description: Derive risk-based verification obligations, select and execute repository-native checks, control test environments and resources, and record fresh evidence. Use for implementation verification, test planning, compatibility matrices, CI parity, performance/security/accessibility evidence, or independent test execution; it does not redesign product behavior or repair product code unless separately authorized.
---

# Verification

Prove observable behavior and risk with the smallest sufficient fresh evidence set.

## Procedure

1. Read `references/test-strategy.md` for obligation derivation, layers, matrix selection, regression proof, statuses, and freshness.
2. Map every `VO-n` to acceptance/protected behavior, changed states and errors, contracts, and active risks.
3. Prefer repository-native compiler/typecheck, formatter, selected lint/static analysis, tests, codegen validation, dependency/security checks, and CI-equivalent commands.
4. Run waves from narrow/cheap to broad/environment-heavy; keep required compatibility cells explicit.
5. Read `references/test-environments.md` before using browsers, simulators, devices, VMs, containers, services, ports, credentials, or shared mutable fixtures.
6. Preserve first failures, classify flakes, and never convert retries or waivers into `PASSED`.
7. Read `references/evidence-contract.md` before retaining logs, screenshots, traces, dumps, benchmarks, or user data.
8. Produce `verification.plan.v1` and `verification.results.v1` with exact root, environment, command, time, exit, counts, artifact, freshness, and limitation.

## EQAC rule

Execute native controls first. An admitted specialist route can add expert review but does not prove a command passed. When automation is incomplete, record the qualified manual/contextual oracle or explicit waiver; absence of one named Skill is not itself a failure.

## Boundaries

- Do not modify product code during an independent test-runner assignment.
- Do not collect or retain secrets, private data, or bulk artifacts unnecessarily.
- Report `PASSED`, `FAILED`, `FLAKY`, `BLOCKED`, `NOT RUN`, and `WAIVED` separately.
