---
name: test-system-engineering
description: Diagnose and harden test discovery, selection, harness sensitivity, fixture isolation, runner interpretation, and representative coverage.
---

# Test System Engineering

Use this Skill when the test system itself is changed or evidence shows false green, zero discovery, selector uncertainty, inert assertions, mock bypass, fixture pollution, misleading runner success, or baseline flakiness.

Do not activate it merely because a feature has tests or verification is requested. `verification` still owns the product/repository claim; this Skill owns whether the harness can produce trustworthy evidence and hands the result back to `verification`.

## Procedure

1. Preserve the first suspicious result and separate product failure from harness failure.
2. Read `references/test-system-integrity.md` and account for all six obligations at the affected boundary.
3. Use the smallest safe negative control that proves the intended gate can fail.
4. Repair only the causal harness boundary, then rerun the focused control and affected native suite.
5. Report discovery, selection, sensitivity, isolation, interpretation, and representativeness independently; a green runner cannot fill an unobserved obligation.

## Boundaries

- Do not replace repository-native runners with a universal runner.
- Do not turn coverage percentages, collection counts, or runner exit zero into product correctness.
- Do not retain raw fixtures, credentials, production data, or bulk logs solely for harness diagnosis.
- Hand flaky, blocked, not-run, or platform-limited product evidence back to `verification` without upgrading its status.
