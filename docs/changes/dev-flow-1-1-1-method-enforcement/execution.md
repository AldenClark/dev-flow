# Execution: dev-flow-1-1-1-method-enforcement

[Tracked change manifest](./manifest.json)

- SC-D1: implemented; governed creation, deterministic sidecars, event projection, `record-methods`, and cumulative lifecycle gates are integrated.
- SC-D2: implemented; all 55 engineering risks are canonical or explicitly aliased, and route/selection output preserves input, canonical values, and translations.
- SC-D3: implemented; six bounded method/source/model additions and their progressive architecture guidance are registered.
- SC-D4: implemented; current truth, public docs, changelog, and this authority-bound dossier are updated.
- SC-I1: implemented; focused selector and packet contracts plus the strict non-release repository suite pass on the frozen working tree.
- SC-I2: implemented; `1.1.1` manifest/readme/runbook/attestation surfaces and both CI/release-candidate workflow gates agree.
- SC-P1 and SC-P2: preserved by immutable capability gating, unchanged standalone output schema, standard-library implementation, and explicit authority/evidence boundaries.
- SC-O1: no dependency, top-level Skill, incompatible schema migration, PR, GitHub Release, deploy, force-push, or unrelated change has been introduced.
- SC-L1: delivered; release commit `e2212f0f9df196cb8e9c0cc864b3c9018eb8eb43`, immutable annotated `v1.1.1`, deterministic artifacts, remote tag, and the primary `1.1.1` installation agree. A normal follow-up commit `54e1baeada851a33d0599d9e5de250f161467548` fixes Windows authority-byte checkout on `main` without moving the release tag.

## Execution controls

- INS-1, INS-2, INS-3, and INS-4 govern the implementation and final diff.
- Root owns repository bytes, tests, release artifacts, Git delivery, and the primary plugin update; no sub-agent or shared device/service resource is used.
- Work proceeds as one coherent slice: lifecycle enforcement and risk unification, method content, tests, docs/version, final audits, immutable delivery, local installation.
- Any failed gate preserves its first failure and is repaired without weakening the oracle or relabeling `NOT RUN`.

## Review findings and next gate

- The first strict broad run found one existing governed-packet fixture that needed an explicit design record and an ordinary-static context overage caused by the longer orchestrator sentence; both were repaired without weakening either gate.
- Blue review found an unconstrained `record-methods --phase` parser and incomplete semantic binding checks. Red review showed a coordinated local sidecar/event rewrite could disguise `recorded_state`, and that extra non-routing alias keys were not rejected. The parser, record-state/digest/input-risk bindings, alias-set validator, and a coordinated-tamper regression were added; no review finding remains open.
- Final evidence includes 396 strict tests, 26 focused methodology tests, 39 repository contracts, plugin/maintainer/knowledge/compile/JSON/diff checks, and a data-security doctor with zero required failures. Two commit-bound artifact builds are byte-identical; the remote tag and primary cache resolve to the release commit; GitHub Actions run 31855056832 passes the six Linux/macOS/Windows and Python 3.11/3.14 cells.
- The first hosted run passed Linux/macOS but exposed CRLF drift in exact authority-document hashes on Windows. The correction forces `docs/changes/**` to LF, has a repository contract, and passed both a local `core.autocrlf=true` checkout replay and the final hosted Windows jobs.
