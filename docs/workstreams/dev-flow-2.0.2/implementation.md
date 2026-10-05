# Dev Flow 2.0.2 DLP release

> Status: published stable `2.0.2`

<!-- dev-flow-workstream-contract: v1 -->

Deliver the audited DLP repairs as a stable patch, preserving existing policy/authority boundaries and exact source-to-artifact-to-install identity. The user explicitly authorized preparation, commit, push, tag, stable publication and primary local installation. Five live-model journeys are explicitly waived for this patch; no additional model spend is authorized. Existing DLP audit evidence is retained at its owner.

| Slice | Outcome | Write prefixes | Protected paths | Evidence | Status | Decision |
|---|---|---|---|---|---|---|
| S1 | Maintain version, cumulative review and local candidate evidence | `.codex-plugin/`, `.github/workflows/`, `governance/`, `README.md`, `CHANGELOG.md`, `docs/`, `skills/company-data-security/references/` | - | Stable-to-candidate six-method review, final native suite, validators and source identity | complete | Scope is the DLP repair delta and necessary version/docs |
| S2 | Freeze, commit, push and qualify exact hosted artifacts | `docs/workstreams/dev-flow-2.0.2/progress.md` | - | Exact-SHA CI/platform matrix, deterministic builds, hosted SBOM/checksums/attestations and isolated runtime lifecycle | complete | Preserve first failures; never promote missing evidence |
| S3 | Publish and observe public/installed/current truth | `governance/product-state.json`, `README.md`, `CHANGELOG.md`, `docs/releasing.md`, `docs/workstreams/dev-flow-2.0.2/` | - | Immutable public tag and asset byte comparison, public-tag isolated install/uninstall and verified primary installed bytes | complete | Separate truth commit; existing chats require fresh loading |

No dependency or installer redesign is needed. Publication reuses verified hosted assets. The rollback installation is exact public stable `v2.0.0`; credentials/current approval state are not inspected or migrated during release testing. Stop publication on a consequential source, CI, artifact or installation mismatch and repair only invalidated evidence.
