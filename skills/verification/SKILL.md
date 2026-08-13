---
name: verification
description: Derive risk-based oracles, run native checks, control environments and resources, and record fresh compatibility, security, performance, or accessibility evidence.
---

# Verification

For environment choices, waivers, or manual authority, remain in Default mode and follow `../requirements-design/references/user-interaction.md`.

## Responsibility contract

- Consumes: verification obligations, final relevant bytes, decisions, and environment authority.
- Owns: risk-based oracles, commands, resources, evidence, and status.
- Stops: at missing authority, unsafe shared resources, or an unresolved first failure.
- Hands off: causal failures to debugging, evidence to review/delivery, and results to the control plane.

## Procedure

1. Map each `VO-n` to changed behavior, states/errors, contracts, and risks.
2. For every non-trivial behavior change, derive black-box and white-box obligations separately; run each applicable view or give a concrete change-specific `N/A` reason. Experience/red-team is a third view, never a substitute. Read `references/test-strategy.md`.
3. Challenge whether each new/changed test would fail when protected behavior breaks; record a practical negative control or cross-oracle.
4. Run native narrow/cheap controls before broad/environment-heavy ones. Read `references/test-environments.md` before controlled resources.
5. Preserve first failures and flakes; retries and waivers never become `PASSED`.
6. Read `references/evidence-contract.md` before retaining artifacts. Emit the plan/results with technique accountability, exact evidence, oracle challenge, freshness, and limits.

## EQAC rule

Run native controls first; specialist review never proves a command. Mark incomplete automation as a qualified manual/contextual oracle or waiver.

A behavior or interaction claim never doubles as proof. Emit a separate verification-owned test cell for each falsifiable evidence family; umbrella labels never substitute. Green is insufficient until failure sensitivity is reviewed. Detailed matrices and cell rules live in `references/test-strategy.md`.

## Boundaries

- Do not modify product code during an independent test-runner assignment.
- Do not retain unnecessary sensitive or bulk artifacts.
- Keep `PASSED`, `FAILED`, `FLAKY`, `BLOCKED`, `NOT RUN`, and `WAIVED` distinct.
