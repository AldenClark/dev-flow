---
name: verification
description: Derive risk-based test obligations, run repository-native checks, control environments and resources, and record fresh compatibility, security, performance, or accessibility evidence.
---

# Verification

For environment choices, waivers, or manual action, stay in Default mode and follow `../requirements-design/references/user-interaction.md`.

Prove behavior and risk with the smallest sufficient fresh evidence.

## Procedure

1. Map the smallest risk-based oracle. Read `references/test-strategy.md` for governed, multi-environment/layer, weak-oracle, or full-matrix work.
2. Map each `VO-n` to behavior, changed states/errors, contracts, and risks.
3. Prefer native compiler/typecheck, format, lint/static, tests, codegen, dependency/security, and CI-equivalent checks.
4. Run narrow/cheap before broad/environment-heavy; keep compatibility cells explicit.
5. Read `references/test-environments.md` before browsers, devices, VMs/containers, services, credentials, or shared fixtures.
6. Preserve first failures and flakes; never convert retries or waivers into `PASSED`.
7. Read `references/evidence-contract.md` before retaining logs, traces, dumps, benchmarks, or user data.
8. Produce `verification.plan.v1` and `verification.results.v1` with root, environment, command, time, exit, counts, artifacts, freshness, and limits.

## EQAC rule

Execute native controls first. An admitted specialist route can add expert review but does not prove a command passed. When automation is incomplete, record the qualified manual/contextual oracle or explicit waiver; absence of one named Skill is not itself a failure.

Stateful/concurrent work names native oracles first: admission, claim collision/exclusivity, retry/dedup, restart recovery, drain/shutdown. Tie ordinary failures to executable tests or evidence gaps; full-suite labels are insufficient.

## Boundaries

- Do not modify product code during an independent test-runner assignment.
- Do not collect or retain secrets, private data, or bulk artifacts unnecessarily.
- Report `PASSED`, `FAILED`, `FLAKY`, `BLOCKED`, `NOT RUN`, and `WAIVED` separately.
