# Acceptance and delivery readiness

Use this reference for releases, migrations, deployments, signing, publication, or another high-consequence delivery. Select evidence from the changed surface and exact requested action.

## Claim states

- `implemented`: the requested change exists in the working tree.
- `verified`: fresh named evidence supports it in stated environments.
- `accepted`: agreed local/business criteria are satisfied.
- `release-ready`: applicable artifact, compatibility, security, migration, rollback, and target gates are satisfied.
- `delivered`: the specifically authorized external action completed and its result was checked.

Never collapse these states.

## Readiness

1. Resolve all real Git roots, current diff, generated/dependency changes, version sources, user-owned unrelated changes, and the exact delivery target.
2. Select the applicable release tier or equivalent repository-native policy. Do not run a maximum gate set simply because it exists.
3. Confirm focused and affected evidence is fresh for final bytes. Keep failed, flaky, blocked, not-run, and waived gates visible.
4. For compatibility or migration, cover only relevant reader/writer, client/server, platform, data, ordering, resumability, observation, restore/rollback, and cleanup directions.
5. Freeze exact source commit, version, configuration, artifact names, and intended target before constructing or publishing immutable artifacts.

## Artifact integrity

For an artifact/security change, verify archive contents, manifest/version/commit, non-empty SBOM, checksums, provenance or signature as applicable, and rejection of the concrete tamper/substitution failures the builder can expose. Two clean builds are useful when reproducibility is claimed; they are not mandatory for unrelated documentation or Skill prose changes.

Use isolated temporary profiles for installer/runtime lifecycle checks. Test fresh install/uninstall for runtime changes; add upgrade, rollback, re-upgrade, modified-file ownership, credentials, and target-platform cells only when compatibility or lifecycle behavior changed.

A local snapshot does not prove remote tag resolution, hosted CI, signing service, target platform, deployment, or public distribution. Keep each unrun real-world gate as `NOT RUN`.

## Authority and result

Local edit, stage, commit, fetch, merge/rebase, push, PR, tag, release, publish, migration execution, deploy, marketplace update, installation, and external message are separate actions. Perform only the authorized action and verify its external result.

Lead the final report with the narrowest supported outcome. Include material decisions, fresh evidence, residual risk, and unrun gates; do not produce a packet closeout, acceptance trace, evidence-row ledger, or immutable failure packet.
