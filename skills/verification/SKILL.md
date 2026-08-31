---
name: verification
description: Derive risk-based oracles, run native checks, and report fresh evidence and limits honestly.
---

# Verification

Use the narrowest evidence that can falsify the changed behavior, then broaden only across affected risks.

This Skill may operate alone for a bounded read-only check. If verification accompanies material repository mutation, crosses compatibility or runtime boundaries, needs managed continuity, or supports high-risk delivery, load `dev-flow` as the coordinating kernel when it is available and not already active; keep this Skill as the evidence owner.

## Procedure

1. Map changed behavior, failure states, contracts, and risks to observable oracles.
2. Run the smallest relevant reproducer or focused test first, followed by affected module, integration, compatibility, security, UI, performance, or migration checks.
3. Use black-box, white-box, property, differential, manual, or adversarial views where they add distinct failure sensitivity. Do not require each view or a prose `N/A` for every ordinary change.
4. Challenge whether changed tests would fail if protected behavior regressed. Use a practical negative control for high-risk or easy-to-fake oracles.
5. For a warranted method, execute a ready method, use a blocked fallback with its limit, or abstain because this procedure is sufficient. Require an owner oracle/counterexample/evidence/claim change; a method name is not evidence.
6. Preserve the first failure and diagnose it before retrying. A retry does not turn a flake into `PASSED`.
7. Bind conclusions to final relevant bytes, environment, platform/device/account, and compatibility direction; invalidate affected evidence after later edits.
8. Report `PASSED`, `FAILED`, `FLAKY`, `BLOCKED`, `NOT RUN`, and `WAIVED` distinctly, with concise commands/results and evidence limits.

Read `references/test-strategy.md` for non-trivial strategy, `references/test-environments.md` before shared or controlled resources, and `references/evidence-contract.md` before retaining artifacts.

## Boundaries

- A configured test is not executed evidence and a green test does not prove an unobserved runtime or delivery environment.
- A fallback proves only its own narrower claim, never a blocked specialist, independent-context, device, or real-system gate.
- Do not modify product code during an explicitly independent test-runner assignment.
- Do not retain unnecessary sensitive payloads, bulk logs, or generated ledgers.
