# Dev Flow 2.0 RC.9 progress

## Current truth

- Released source: immutable `v2.0.0-rc.9` is published from `5d4a569dcbbb67fb21cbc7945945597e342151b5`; publication-state updates do not rewrite the tag or its assets.
- The user explicitly requested direct RC.9 publication and the primary local installation update without testing or verification. Final-release tests, CI, cross-platform checks, independent review, semantic smoke, and isolated installation checks are waived; SBOM and attestations are not run.
- The previous implementation turn ran 645 local tests with one skip and 39 structural contracts, after correcting three old-model activation assertions. Those checks precede the version/release-state edits and are historical development evidence, not final-candidate qualification.
- Commit, atomic main/tag push, local package construction, and [public prerelease](https://github.com/AldenClark/dev-flow/releases/tag/v2.0.0-rc.9) are complete. The three assets are the source archive, release manifest, and checksums; the archive SHA-256 is `6da7b0bcc1bdd5429482875e66c11dfa4400e81b60e3e2a1b73bb4fcf6ad5e2a`. This is package-construction/publication evidence, not archive validation or attestation.
- The first GitHub Release-create attempt returned HTTP 500 and the release was absent. A bounded retry created the public prerelease successfully; the failure is retained, not turned into a test pass.
- The primary Codex profile reports `dev-flow@dev-flow` installed and enabled at `2.0.0-rc.9`, its marketplace configuration is pinned to `v2.0.0-rc.9`, and the cached plugin manifest identifies RC.9. The initial in-place marketplace-add attempt was rejected because the existing source was pinned to RC.8; removing and re-registering only the Dev Flow marketplace completed the update. The old running conversation then referenced the removed RC.8 Hook path and blocked tool calls. On continuation, the effective Skill inventory points at RC.9 and tool calls work again. This does not prove that other already-running conversations have reloaded the plugin.
- No tests, compile, diff checker, check-workstream, suite/knowledge/plugin/security validator, product-state validator, hosted workflow, or model call is run in the release or closeout turns. Only Git/publication/installation identities and action results are inspected. The added RC-waiver contract cases are not executed.

Delivery state: commit=passed; hosted_ci=waived; cross_platform=waived; independent_review=waived; tag=passed; artifact=passed; publication=passed; isolated_install=waived.
