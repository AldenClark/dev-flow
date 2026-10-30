---
name: test-system-engineering
description: Build or repair native test feedback when harness results or coverage may mislead.
---

# Test System Engineering

Use this Skill when the test system itself must be established or changed, or evidence shows false green, zero discovery, selector uncertainty, inert assertions, mock bypass, wrong actor/source attribution, stale cache, fixture pollution, misleading runner success, or baseline flakiness.

Do not activate it merely because a feature has tests or verification is requested. `verification` still owns the product/repository claim; this Skill owns whether the harness can produce trustworthy evidence and hands the result back to `verification`.

## Choose the mode

- **Diagnose/repair:** preserve the first suspicious result, separate product failure from harness failure, and use the relevant part of `references/test-system-integrity.md` to investigate the suspect boundary. Reuse valid results; use a negative control when sensitivity is doubtful or a credible high-consequence failure warrants it.
- **Establish/strengthen:** when a real task lacks the start, health, focused-test, boundary-oracle, targeted-log, or recovery feedback needed to see its outcome, read `references/system-design.md`. Build the smallest project-native capability that closes the observed gap. A small closed task with adequate feedback needs no setup expansion.

Consume native discovery and execution results directly; investigate collection or selection only when they are unclear or suspect. For an external effect, observe the intended actor/source and target effect; a background event or mock call is not that outcome. Repair only the causal boundary and rerun affected checks while retaining unaffected results. Return the result and material limits to `verification`, without a six-part disposition or separate handoff record.

Audit AI-authored tests against a source independent of the implementation—requirements/public contracts, final-code branch risks, properties/models, differential or metamorphic relations, or seeded faults. Test count and green execution do not resolve self-confirmation.

## Stop

Stop when the observed feedback gap is closed and the native result supports the intended decision. A sensitivity repair must detect the target fault for the right reason. Do not keep building lanes, frameworks or cases, or audit unrelated harness properties, after that gap is closed.

## Boundaries

- Do not replace repository-native runners with a universal runner.
- Do not turn coverage percentages, collection counts, or runner exit zero into product correctness.
- Lane labels such as Focused, PR, Nightly, or Release are examples of feedback roles, not required names or a fixed matrix.
- Host, mock, simulator, and emulator results never prove a physical-device or native-platform promise.
- Do not retain raw fixtures, credentials, production data, or bulk logs solely for harness diagnosis.
- Hand flaky, blocked, not-run, or platform-limited product evidence back to `verification` without upgrading its status.
