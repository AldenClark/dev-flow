---
name: test-system-engineering
description: Build or repair native test feedback when harness results or coverage may mislead.
---

# Test System Engineering

Use this Skill when the test system itself must be established or changed, or evidence shows false green, zero discovery, selector uncertainty, inert assertions, mock bypass, fixture pollution, misleading runner success, or baseline flakiness.

Do not activate it merely because a feature has tests or verification is requested. `verification` still owns the product/repository claim; this Skill owns whether the harness can produce trustworthy evidence and hands the result back to `verification`.

## Choose the mode

- **Diagnose/repair:** preserve the first suspicious result, separate product failure from harness failure, read `references/test-system-integrity.md`, account for all six obligations at the affected boundary, and challenge the native runner with the smallest safe negative control.
- **Establish/strengthen:** when a new project lacks sustainable feedback or a mature project's native system cannot cover an important boundary, read `references/system-design.md`. Build the smallest project-native capability that closes the observed gap.

In either mode, confirm what was discovered and executed, repair only the causal boundary, rerun the negative control and affected suite, then hand the six integrity dispositions and exact claim limits to `verification`.

Audit AI-authored tests against a source independent of the implementation—requirements/public contracts, final-code branch risks, properties/models, differential or metamorphic relations, or seeded faults. Test count and green execution do not resolve self-confirmation.

## Stop

Stop when the intended tests are discovered and selected, the target fault is detected for the right reason, fixtures/resources are isolated, runner outcomes are interpreted correctly, and evidence is attributed only to the environment that ran. Do not keep building lanes, frameworks, or cases after the material feedback gap is closed.

## Boundaries

- Do not replace repository-native runners with a universal runner.
- Do not turn coverage percentages, collection counts, or runner exit zero into product correctness.
- Lane labels such as Focused, PR, Nightly, or Release are examples of feedback roles, not required names or a fixed matrix.
- Host, mock, simulator, and emulator results never prove a physical-device or native-platform promise.
- Do not retain raw fixtures, credentials, production data, or bulk logs solely for harness diagnosis.
- Hand flaky, blocked, not-run, or platform-limited product evidence back to `verification` without upgrading its status.
