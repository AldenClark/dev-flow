# Dev Flow release model

This runbook selects evidence from the changed surface. It separates implementation, verification, release readiness, artifact construction, publication, and installation; none implies another.

## Principles

- Run the full semantic suite once for an exact commit SHA. Do not repeat it in the release-candidate workflow.
- Run platform/version compatibility only for code whose behavior can vary there.
- Build, SBOM, checksum, provenance, and attestation evidence belongs to the immutable release artifact.
- Flow Activation Coverage is for material model-semantic branch behavior, not productivity or effect measurement.
- Publication, tag creation, push, release creation, and installation always require their own authority.
- A missing hosted, device, signing, account, deployment, or public-network result is `NOT RUN`, never an inferred pass.

## Release tiers

Select the highest applicable tier. Higher tiers add only evidence relevant to the changed surface.

| Tier | Typical changes | Required evidence before publication |
|---|---|---|
| R1 standard | documentation, Skill wording, routing fixtures, ordinary deterministic logic | focused local checks, one full semantic CI job, affected focused compatibility cells |
| R2 runtime | Hook, installer, process, path, shell, host integration, cross-platform behavior | R1 plus full compatibility lane and isolated install/uninstall smoke; upgrade/rollback only when compatibility changed |
| R3 artifact/security | builder, archive format, workflow permissions, SBOM, attestation, confidentiality/security control | R1/R2 as applicable plus deterministic artifact negative tests, candidate SBOM/checksum/provenance/attestation, security-specific checks |
| R4 model-semantic | routing or instructions whose material branch activation depends on Codex interpretation | R1 plus affected semantic fixtures and bounded isolated first-attempt activation pilots when deterministic coverage is insufficient; no effect score or repeated-trial quota |

Examples:

- Correcting a typo is R1 and does not rehearse marketplace rollback.
- Changing Hook registration or `data_security_hook.py` is R2/R3 as applicable; it needs focused platform and confidentiality tests plus isolated runtime smoke, not an automatic full model acceptance run.
- Changing `tools/build_release.py` or attestation permissions is R3.
- Changing the model-facing meaning of direct/managed selection may be R4 even when the code diff is small.
- A mixed change uses the union of applicable evidence, not every gate ever created by the project.

## Evidence lanes

The ordinary CI workflow has two lanes:

1. `semantic`: Ubuntu 24.04/Python 3.14 runs the full unit suite, structural contracts, shipped legacy-data validators, plugin/suite/data-security checks, compilation, and clean-tree check once.
2. `compatibility`: a focused matrix across Ubuntu, macOS, Windows and Python 3.11/3.14 runs only agent dispatch, preflight, installer, and isolated runtime-lifecycle tests.

The manual release-candidate workflow is a third lane. It fetches and binds the approved exact SHA, creates the deterministic source archive, verifies it, generates and validates SPDX 2.3 SBOM data, finalizes checksums, creates provenance/SBOM attestations, and uploads immutable candidate evidence. It intentionally does not rerun semantic CI.

## Candidate sequence

1. Classify the change as R1-R4 and record the rationale in the PR/release decision, not a generated packet.
2. Freeze a clean full commit SHA, source version, candidate target, and required evidence cells.
3. Run focused local checks first. Run broader local checks only when they can change the release decision.
4. Push only with authority and require the exact SHA's semantic job plus applicable compatibility cells.
5. For R2, exercise fresh install/uninstall in an isolated temporary Codex home. Add prior-version upgrade, rollback, re-upgrade, and modified-file protection only when installer/runtime compatibility changed.
6. For R4, predeclare affected branch families and expected/forbidden activation. Preserve first attempts and report unmet prerequisites; do not turn the pilot into an effect comparison.
7. Merge only with merge authority. The RC workflow definition must already exist on the default branch.
8. Dispatch the RC workflow for the exact merged SHA and matching source version.
9. Download and verify archive, manifest, SBOM, checksums, and both attestations. Reuse those exact bytes for any later release.
10. Create/push a signed RC or stable tag and create a draft/published release only when those exact actions are authorized.

Never rewrite or reuse an RC tag. Any changed byte requires a new commit and candidate identity.

## Local artifact check

For an R3 change, two local builds can establish deterministic behavior before hosted attestation. Use absent output directories:

```bash
git rev-parse HEAD
python3 tools/build_release.py build \
  --root . --output dist-a --version 2.0.0-beta.3 --commit FULL_COMMIT_SHA
python3 tools/build_release.py build \
  --root . --output dist-b --version 2.0.0-beta.3 --commit FULL_COMMIT_SHA
cmp dist-a/dev-flow-2.0.0-beta.3.tar.gz dist-b/dev-flow-2.0.0-beta.3.tar.gz
cmp dist-a/release-manifest.json dist-b/release-manifest.json
cmp dist-a/SHA256SUMS dist-b/SHA256SUMS
python3 tools/build_release.py verify \
  --artifact-dir dist-a --expected-version 2.0.0-beta.3 --expected-commit FULL_COMMIT_SHA
```

Determinism is asserted within the pinned environment. Promotion reuses attested bytes instead of rebuilding on another zlib/toolchain version.

## Hosted candidate

After applicable exact-SHA CI is green:

```bash
gh workflow run release-candidate.yml \
  --ref main -f version=2.0.0-beta.3 -f expected_sha=FULL_COMMIT_SHA
```

The workflow has `contents: read`, `id-token: write`, and `attestations: write`. It has no release-publication permission. After download:

```bash
python3 tools/build_release.py verify \
  --artifact-dir dist --expected-version 2.0.0-beta.3 --expected-commit FULL_COMMIT_SHA
gh attestation verify dist/dev-flow-2.0.0-beta.3.tar.gz \
  --repo AldenClark/dev-flow
gh attestation verify dist/dev-flow-2.0.0-beta.3.tar.gz \
  --repo AldenClark/dev-flow \
  --predicate-type https://spdx.dev/Document/v2.3
```

The SBOM must be SPDX 2.3, name `dev-flow`, contain files, identify the root package and version, and carry a document namespace. Structurally valid but empty inventory is failure.

## Model-semantic activation evidence

Use [evaluation-suite.md](evaluation-suite.md). Deterministic Flow Activation Coverage runs first. For a material R4 trigger change, run only the affected natural-language/repository fixtures and enough isolated first-attempt pilots to observe the changed boundary. Report expected versus observed activation, missing or unexpected branches, authority violations, prerequisites, and evidence limits. Do not emit an effect, productivity, or composite quality score.

The legacy paired-evaluation harness remains available for explicitly authorized compatibility research, but it is not a 2.0 release gate and never substitutes for deterministic, compatibility, security, or artifact evidence.

## Install and rollback

Use an isolated temporary Codex home. Never mutate the maintainer's primary profile as a release test.

```bash
DEV_FLOW_TEST_CODEX_HOME=/absolute/private/temporary-codex-home
CODEX_HOME="$DEV_FLOW_TEST_CODEX_HOME" \
  codex plugin marketplace add AldenClark/dev-flow --ref vX.Y.Z-rc.N --json
CODEX_HOME="$DEV_FLOW_TEST_CODEX_HOME" \
  codex plugin add dev-flow@dev-flow --json
CODEX_HOME="$DEV_FLOW_TEST_CODEX_HOME" \
  codex plugin list --json
```

A local snapshot proves local CLI/manifest behavior only. Remote tag resolution, prior-version upgrade, rollback, re-upgrade, and target-platform loading remain `NOT RUN` until exercised. Modified user-owned runtime files must block whole-set removal rather than being deleted.

## Failure handling

- Preserve and classify the first failure before retrying.
- Do not weaken a threshold, delete a platform, or relabel `NOT RUN` to make a release green.
- Fix on a new commit and rerun only invalidated evidence lanes.
- Do not rebuild or replace bytes behind an existing digest or attestation.
- If rollback is needed after publication, restore the last known-good plugin version and behavior; retain repository research/design history and legacy packet data.
