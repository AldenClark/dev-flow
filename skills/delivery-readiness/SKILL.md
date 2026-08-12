---
name: delivery-readiness
description: Check acceptance, compatibility, rollback, changed files, residual risk, and authority before commit, push, PR, release, migration, deployment, or external delivery.
---

# Delivery Readiness

For delivery authority or residual-risk acceptance, remain in Default mode and follow `../requirements-design/references/user-interaction.md`; discussion does not imply approval.

Keep implementation, verification, acceptance, release readiness, and delivery as distinct claims.

## Responsibility contract

- Consumes: final requirement digest, final artifact/diff, verification, routed review, and action-specific authority.
- Owns: the exact readiness level, changed-file accounting, residual gates, rollback, and eligibility for the named delivery action.
- Stops: at any required failed/flaky/blocked/not-run cell, identity mismatch, unsigned required artifact, or missing exact authority.
- Hands off: an unmet condition to its owner and an authorized action to the control plane or host.

## Procedure

1. Read `references/readiness-contract.md` completely.
2. Confirm the final requirement revision/digest and account for every AC/SC/VO ID.
3. Re-read the final diff, all real Git roots, generated artifacts, migrations, public contracts, documentation, packaging, and runtime consequences.
4. Require fresh static, dynamic, blue, and red evidence appropriate to the risk. Preserve failed, flaky, blocked, not-run, and waived cells explicitly.
5. Validate compatibility direction, rollout order, rollback trigger and executable path, cleanup, observability, and residual data/protocol limitations.
6. Resolve every changed file as in scope, approved conditional scope, user-owned unrelated work, or drift requiring action.
7. For release artifacts, freeze source commit, version, configuration, release target, artifact set, signing identity, observation owner, and rollback owner; compare SHA-256 from two clean builds; verify contents, version, and commit; require a non-empty standards-format SBOM and provenance bound to the final digest; verify the signature; then keep tag and Draft prerelease actions separately authorized.
8. Before returning an RC or release plan, explicitly account for: first-failure packet; a separate executed check and evidence row for each of stale/wrong subjects, nondeterminism, post-build mutation, and upload substitution, including intended-local versus uploaded asset name/size/digest; causal repair in a distinct attempt; two clean builds and manifest/identity checks; completion of tamper and mismatched-pair rejection before generating any fresh signature; only then fresh signature generation and verification; local-snapshot versus remote-tag/target-platform evidence; lifecycle ownership/cleanup; and every `NOT RUN` cell.
9. Failed, flaky, blocked, not-run, mismatched, or unsigned required release cells block tag and release-ready claims; retain their status and first evidence.
10. State exact readiness: `implemented`, `verified`, `accepted`, `release-ready`, or `delivered`.
11. Perform commit, push, PR, tag, release, deploy, migration, marketplace update, or external message only when that exact action is authorized; verify it afterward.

## Boundaries

- A local green test suite is not proof of unrun device, OS, signing, migration, or production gates.
- A design approval is not delivery authority.
- Do not archive the active packet before acceptance and recorded delivery outcome.
