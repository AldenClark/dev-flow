---
name: verification
description: Derive risk-based oracles, run native checks, control environments and resources, and record fresh compatibility, security, performance, or accessibility evidence.
---

# Verification

For environment choices, waivers, or manual authority, remain in Default mode and follow `../requirements-design/references/user-interaction.md`.

Prove behavior and risk with minimal fresh evidence.

## Responsibility contract

- Consumes: verification obligations, final relevant bytes, owner decisions, and environment authority.
- Owns: risk-based oracles, native commands, environments, resources, evidence, and evidence status.
- Stops: at a missing environment/data authority, unsafe shared-resource boundary, or unresolved first failure.
- Hands off: causal failure to debugging, raw evidence to review, the final matrix to delivery, and results to the control plane.

## Procedure

1. Map the smallest risk-based oracle. Read `references/test-strategy.md` for governed, multi-environment/layer, weak-oracle, or full-matrix work.
2. Map each `VO-n` to behavior, changed states/errors, contracts, and risks.
3. Prefer native compiler/typecheck, format, lint/static, tests, codegen, dependency/security, and CI-equivalent checks.
4. Run narrow/cheap before broad/environment-heavy; keep compatibility cells explicit.
5. Read `references/test-environments.md` before browsers, devices, VMs/containers, services, credentials, or shared fixtures.
6. Preserve first failures and flakes; never convert retries or waivers into `PASSED`.
7. Read `references/evidence-contract.md` before retaining logs, traces, dumps, benchmarks, or user data.
8. Produce `verification.plan.v1` and `verification.results.v1` with root, environment, command, exit/counts, artifacts, freshness, and limits.

## EQAC rule

Run native controls first; specialist review never proves a command. Record incomplete automation as a qualified manual/contextual oracle or waiver.

Each falsifiable evidence family gets a verification-owned claim with stimulus, oracle, status, and limitation; umbrella labels never substitute. Detailed FFI, overload, compatibility, and environment matrices live in `references/test-strategy.md`.

## Boundaries

- Do not modify product code during an independent test-runner assignment.
- Do not retain unnecessary secrets, private data, or bulk artifacts.
- Keep `PASSED`, `FAILED`, `FLAKY`, `BLOCKED`, `NOT RUN`, and `WAIVED` distinct.
