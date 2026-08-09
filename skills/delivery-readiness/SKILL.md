---
name: delivery-readiness
description: Determine whether an implemented change is verified, accepted, release-ready, and eligible for separately authorized delivery. Use after implementation/review or before commit, push, PR, tag, release, migration, deployment, or external communication to account for acceptance, compatibility, rollback, changed files, residual risk, and exact delivery authority.
---

# Delivery Readiness

Keep implementation, verification, acceptance, release readiness, and delivery as distinct claims.

## Procedure

1. Read `references/readiness-contract.md` completely.
2. Confirm the final requirement revision/digest and account for every AC/SC/VO ID.
3. Re-read the final diff, all real Git roots, generated artifacts, migrations, public contracts, documentation, packaging, and runtime consequences.
4. Require fresh static, dynamic, blue, and red evidence appropriate to the risk. Preserve failed, flaky, blocked, not-run, and waived cells explicitly.
5. Validate compatibility direction, rollout order, rollback trigger and executable path, cleanup, observability, and residual data/protocol limitations.
6. Resolve every changed file as in scope, approved conditional scope, user-owned unrelated work, or drift requiring action.
7. State exact readiness: `implemented`, `verified`, `accepted`, `release-ready`, or `delivered`.
8. Perform commit, push, PR, tag, release, deploy, migration, marketplace update, or external message only when that exact action is authorized; verify it afterward.

## Boundaries

- A local green test suite is not proof of unrun device, OS, signing, migration, or production gates.
- A design approval is not delivery authority.
- Do not archive the active packet before acceptance and recorded delivery outcome.
