---
name: verification
description: Derive risk-based oracles, run native checks, control environments and resources, and report fresh compatibility, security, performance, accessibility, and runtime evidence.
---

# Verification

Use the narrowest evidence that can falsify the changed behavior, then broaden only across affected risks.

## Procedure

1. Map changed behavior, failure states, contracts, and risks to observable oracles.
2. Run the smallest relevant reproducer or focused test first, followed by affected module, integration, compatibility, security, UI, performance, or migration checks.
3. Use black-box, white-box, property, differential, manual, or adversarial views where they add distinct failure sensitivity. Do not require each view or a prose `N/A` for every ordinary change.
4. Challenge whether changed tests would fail if protected behavior regressed. Use a practical negative control for high-risk or easy-to-fake oracles.
5. Preserve the first failure and diagnose it before retrying. A retry does not turn a flake into `PASSED`.
6. Bind conclusions to final relevant bytes, environment, platform/device/account, and affected compatibility direction.
7. Report `PASSED`, `FAILED`, `FLAKY`, `BLOCKED`, `NOT RUN`, and `WAIVED` distinctly, with concise commands/results and evidence limits.

Read `references/test-strategy.md` for non-trivial strategy, `references/test-environments.md` before shared or controlled resources, and `references/evidence-contract.md` before retaining artifacts.

## Boundaries

- A configured test is not executed evidence and a green test does not prove an unobserved runtime or delivery environment.
- Do not modify product code during an explicitly independent test-runner assignment.
- Do not retain unnecessary sensitive payloads, bulk logs, or generated ledgers.
