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

## Release completion gate

Preserve the first failure as an immutable packet: archive and manifest digests, commit, configuration, toolchain, builder, environment, SBOM/provenance/signature subjects, uploaded-asset identity, logs, and receipts.

Execute and retain a separate evidence row for each of stale or wrong subjects, nondeterministic builds, post-build mutation, and upload substitution; for upload substitution compare intended-local and uploaded asset name, size, and digest. A general root-cause investigation or aggregate binding check does not satisfy these four cells; fix the causal builder or binding and create a distinct controlled attempt instead of editing metadata or overwriting evidence.

For the new attempt, compare two clean builds and verify archive manifest/contents/version/commit; complete tamper and mismatched-pair rejection before generating any fresh signature; only after those negative checks pass, generate and verify a fresh signature. Remote immutable-tag resolution and Draft Release remain later separately authorized gates.

Lifecycle evidence uses a temporary isolated profile; freezes prior and RC tag/source/version/expected bytes; covers install, upgrade, rollback, re-upgrade, uninstall, modified-file ownership, process/profile/credential cleanup, retained receipts, and a target-platform matrix. A local snapshot proves only local behavior; remote-tag and unrun target cells remain `NOT RUN`.

## Compatibility, migration, and rollback

Record supported versions/targets, forward/backward reader/writer or client/server directions, deployment order, coexistence, data conversion, resumability/idempotency, observation, rollback trigger, executable rollback path, last-known-good state, backup/restore, irreversible consequences, cleanup, and reapplication path.

Missing required migration, protocol, persisted-data, security, FFI, signing, packaging, physical-device, or production-target evidence prevents the corresponding full acceptance/release claim. `WAIVED` remains a visible omission.

## Delivery authorities

Treat separately: local edit, stage, commit, fetch, merge/rebase, push, PR, tag, publish, data migration, deploy, marketplace update, and external message. A user request for implementation or verification does not grant the others.

Before any authorized delivery, resolve all real Git roots, branch/upstream/divergence, exact files, generated content, versions, credentials, release target, observation, and rollback owner. Verify the resulting commit/remote/PR/tag/artifact/runtime state afterward.

## Final report

Lead with actual outcome. State implemented scope and important decisions, dependency approvals/exceptions, fresh evidence and counts, compatibility environments by status, residual risks/gates, changed-file accounting, and exact delivery actions performed or not performed.
