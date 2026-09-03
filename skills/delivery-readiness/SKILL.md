---
name: delivery-readiness
description: Assess a specific Git or delivery action for identity, evidence, compatibility, observation, recovery, and separate authority.
---

# Delivery Readiness

Use this Skill when assessing an explicit commit, push, PR, tag, release, migration, deployment, installation, publication, or external delivery action. Do not load it for ordinary implementation or a final local diff with no delivery intent.

Implementation, verification, acceptance, readiness, and delivery are separate claims. This Skill establishes whether one named action can safely proceed; it never grants that action. Read [readiness-contract.md](references/readiness-contract.md) for releases, migrations, deployments, signing, publication, or other high-consequence delivery.

## Start with the concrete unit and action

Name the requested action, target, and authority separately. `commit`, `push`, `PR`, `tag`, `release`, `migration execution`, `deploy`, `install`, `publish`, and `external message` each need their own authorization and post-action result. A successful build, local test, commit, or artifact does not authorize or prove the next action.

For Git integration, first identify every real root, base/head or exact diff, user-owned unrelated changes, and the functional change being integrated. A commit should represent one understandable, reviewable, and reversible behavior change; split unrelated formatting, refactoring, generated churn, or another feature rather than hiding it behind a green suite. Respect repository conventions for branch strategy, message format, and squash policy rather than inventing global Git policy.

## Establish an identity and evidence chain

Record only the identities that the action needs: exact source commit/tree and version; relevant dependency/configuration inputs; artifact name, checksum/provenance/signature where applicable; target environment and recipient; and the evidence run against those final bytes. Re-read the final diff and distinguish fresh pass, fail, flaky, blocked, waived, and `NOT RUN` evidence.

Then check the relevant compatibility direction and operational path: reader/writer or client/server versions, data/ordering/resume behavior, platform and consumer compatibility, observation signal and owner, stop trigger, restore/rollback trigger, executable recovery path, cleanup, and residual limits. Do not run a maximum checklist for an irrelevant tier, but do not call a recovery plan real until its trigger and path are concrete enough to execute.

State the narrowest supported status: `implemented`, `verified`, `accepted`, `release-ready`, or `delivered`. Perform only the authorized action, then verify its actual external result; unobserved CI, signing, target device, deployment, distribution, and production evidence remain `NOT RUN`.

## Return operational learning to its owner

An acceptance gap, incident, real failure, latency regression, support event, or user feedback is new development evidence, not a delivery footnote. Route the smallest useful finding back to the owner that can change it:

- promised behavior, scope, compatibility expectation, or user-visible acceptance gap → `requirements-design`;
- task flow, error/recovery experience, accessibility, or user comprehension → `product-ux-discovery`;
- missing regression oracle, fixture, environment evidence, or false-green runner mechanism → `verification` or `test-system-engineering`;
- a recurring runbook, release observation, recovery practice, or reusable operating fact → `repository-knowledge`.

Use `systematic-debugging` when the cause of a failure is still unknown. The handoff should preserve the exact observation, identity/environment, affected users or contract, and known limitation; it must not convert an unverified report into a product conclusion. Return to delivery only when the new evidence materially changes the requested action's readiness.

## Boundaries

- A bounded read-only readiness assessment may run alone. Material repository mutation, cross-repository coordination, or high-risk preparation can use `dev-flow` as coordinator while this Skill remains evidence owner.
- Do not create a packet closeout, acceptance ledger, or maximum-gate ritual for ordinary work.
- For an RC, perform one lightweight static review of the final diff through the integrated task route. For a stable release, review the cumulative public-stable-to-candidate semantic delta and apply the consolidated static pass defined in `docs/releasing.md`; each method must yield a finding, counterexample, changed oracle, or explicit no-finding conclusion.
- Model-facing RC changes use affected semantic smoke; stable releases use the repository's stated cumulative validation. Repeated model studies belong to Bench, not a release gate.
