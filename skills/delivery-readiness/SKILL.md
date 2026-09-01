---
name: delivery-readiness
description: Check identity, evidence, rollback, risk, and authority before commit, push, release, migration, deployment, or delivery.
---

# Delivery Readiness

Implementation, verification, acceptance, release readiness, and delivery are distinct claims. Read `references/readiness-contract.md` for releases, migrations, deployments, signing, or other high-consequence delivery.

This Skill may operate alone for a bounded read-only readiness check. If readiness includes material repository mutation, cross-repository coordination, managed continuity, or high-risk delivery preparation, load `dev-flow` as the coordinating kernel when it is available and not already active; keep this Skill as the delivery-evidence owner.

## Procedure

1. Name the exact requested action and confirm its authority. Commit, push, PR, tag, release, deployment, migration execution, installation, and external communication are separate actions.
2. Re-read every real Git root, final diff, generated artifact, dependency, migration, public contract, documentation, packaging, and user-owned unrelated change in scope.
3. Confirm affected evidence is fresh for the final bytes. Keep failed, flaky, blocked, not-run, and waived gates explicit.
4. For an RC, perform one lightweight static review of the final diff through the integrated task route and apply at most three ready starter methods. For a stable release, review the cumulative public-stable-to-candidate semantic delta and apply the six-method consolidated static pass defined in `docs/releasing.md`, plus at most two risk-specific methods. Each method must produce a concrete finding, counterexample, changed oracle, or explicit no-finding conclusion; names and counts are not evidence. This static review does not rerun tests.
5. Check applicable compatibility direction, rollout order, observability, rollback/restore trigger and executable path, cleanup, and residual data/protocol limitations.
6. For release artifacts, freeze the exact source commit, version, target, configuration, artifact set, and owners; verify contents, checksums, SBOM/provenance/signature where the changed surface and release tier require them.
7. State the narrowest supported status: implemented, verified, accepted, release-ready, or delivered.
8. Perform only the authorized action and verify its external result afterward.

## Boundaries

- Local checks do not prove hosted CI, target devices, signing, migration, deployment, production, or public distribution.
- Do not replay a complete maximum gate set when the release tier and unchanged exact-SHA CI evidence make it decision-irrelevant.
- Model-facing RC changes use affected semantic smoke. Stable validation uses five bounded real functional journeys; complete repeated-model studies belong to Dev Flow Bench and are never a release gate.
- No packet closeout, AC/SC/VO accounting, or generated readiness ledger is required for 2.0 work.
