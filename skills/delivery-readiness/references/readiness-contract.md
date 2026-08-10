# Acceptance and delivery readiness

## Claim states

- `implemented`: the code/artifact exists.
- `verified`: named fresh evidence supports the claim in stated environments.
- `accepted`: all required criteria and gates for the agreed local delivery profile are satisfied.
- `release-ready`: all required compatibility, security, migration, packaging, signing, rollback, and target-environment gates are satisfied.
- `delivered`: the specifically authorized commit/push/PR/tag/release/deploy/message action completed and was checked.

Never collapse these states.

## Acceptance trace

Map each AC/SC/VO ID to implementation paths, exact command/manual evidence, status, and limitation. Requirements are not proven merely because tests pass; tests are not proven because code exists. Validate the packet, re-read approved artifacts and final diff, and rerun stale evidence.

Account for every changed, generated, moved, and deleted file. Classify user-owned unrelated modifications and do not include or revert them without authority.

## Compatibility, migration, and rollback

Record supported versions/targets, forward/backward reader/writer or client/server directions, deployment order, coexistence, data conversion, resumability/idempotency, observation, rollback trigger, executable rollback path, last-known-good state, backup/restore, irreversible consequences, cleanup, and reapplication path.

Missing required migration, protocol, persisted-data, security, FFI, signing, packaging, physical-device, or production-target evidence prevents the corresponding full acceptance/release claim. `WAIVED` remains a visible omission.

## Delivery authorities

Treat separately: local edit, stage, commit, fetch, merge/rebase, push, PR, tag, publish, data migration, deploy, marketplace update, and external message. A user request for implementation or verification does not grant the others.

Before any authorized delivery, resolve all real Git roots, branch/upstream/divergence, exact files, generated content, versions, credentials, release target, observation, and rollback owner. Verify the resulting commit/remote/PR/tag/artifact/runtime state afterward.

## Final report

Lead with actual outcome. State implemented scope and important decisions, dependency approvals/exceptions, fresh evidence and counts, compatibility environments by status, residual risks/gates, changed-file accounting, and exact delivery actions performed or not performed.
