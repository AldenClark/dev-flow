# Dev Flow 2.0 release validation and benchmark separation requirements

## Confirmed outcome

Implement the approved release-process redesign while keeping `2.0.0-rc.5` as the current published source identity and deliberately not advancing stable `2.0.0`.

## Required behavior

- Active release tiers are R1 standard, R2 runtime, and R3 artifact/security only.
- Stable validation reviews the whole previous-public-stable-to-candidate semantic delta, uses a deeper consolidated static review, exercises bounded real functional journeys, and runs one complete deterministic regression.
- Repeated and comparative model work runs as independent Dev Flow Bench research. It does not read or update product state and never produces a release verdict.
- Bench case health, model execution, assessment, comparison, and cost remain separate. Defaults perform no model calls.
- Historical R4 runs remain historical evidence and are not relabelled, deleted, or inherited as current proof.
- This work may simulate stable promotion, but must not commit, tag, push, publish, mutate primary installation state, or claim that stable `2.0.0` exists.

## Acceptance evidence

- Product-state and release-contract focused tests.
- Bench suite audit, plan, spend negative control, case-health negative control, and per-case comparison tests.
- Non-mutating stable simulation from `v1.1.2` to the current worktree, including untracked implementation files.
- One final deterministic repository regression and same-context diff review.
