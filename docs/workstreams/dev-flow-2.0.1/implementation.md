# Dev Flow 2.0.1 DLP patch

> Status: implemented in the source-candidate worktree for `2.0.1`

<!-- dev-flow-workstream-contract: v1 -->

Correct the credential-path regex that consumed source code across lines and mistook Swift dictionary members for key files. Keep secret detection, policy modes, confirmation and actual sensitive-path blocking intact. No dependencies or changes to Loshu are needed. The user authorized version 2.0.1, focused testing, commit, push and primary local update, and explicitly skipped complete regression.

| Slice | Outcome | Write prefixes | Protected paths | Evidence | Status | Decision |
|---|---|---|---|---|---|---|
| S1 | Correct path boundaries and maintain version projections | `skills/company-data-security/`, `evals/test_data_security.py`, `.codex-plugin/`, `.github/workflows/release-candidate.yml`, `governance/`, `README.md`, `CHANGELOG.md`, `docs/` | - | Pre-fix failure; focused DLP and original patch controls; product-state and diff checks | complete | Scoped defect repair |
| S2 | Commit, push and update primary plugin | `docs/workstreams/dev-flow-2.0.1/progress.md`, `governance/product-state.json`, `docs/releasing.md` | - | Remote commit identity; installed version and shipped-byte comparison | ready | User authorized these actions; full regression skipped |
