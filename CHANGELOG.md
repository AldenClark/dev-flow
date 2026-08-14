# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

## [1.0.2] - 2026-08-14

### Added

- A cross-surface `company-data-security` Skill with separate Codex, ChatGPT Work, and ordinary Chat playbooks and instruction templates.
- Standard-library local secret/direct-identifier detection, non-reversible pseudonymization, and bounded redaction without a persistent raw-value map.
- Independent Codex `UserPromptSubmit`, `PreToolUse`, and `PostToolUse` confidentiality Hooks for documented local tool paths.
- A machine-readable doctor that detects protected-file, Hook-schema, capability-registration, and template drift while keeping live trust/account gates explicitly manual.
- Synthetic blue/red tests for detector families, safe decoys, nested/base64/Unicode inputs, Hook leakage and size failures, and doctor tamper cases.

### Changed

- Advanced the source manifest, release workflow default, current-source examples, release runbook, and DLP attestation template to patch version `1.0.2`.

### Security

- Data-security Hook results never include matched values, and oversized or malformed model-bound payloads fail closed with bounded fixed messages.
- Work/Chat templates and doctor output explicitly avoid claiming enterprise immutability, endpoint/network DLP, or deterministic pre-send interception outside supported Codex Hooks.

## [1.0.1] - 2026-08-14

### Added

- A composable engineering workbench whose current 12-Skill topology spans repository context, profile management, requirements/design, product/UX, architecture, dependencies, debugging, verification, review, delivery readiness, and explicit suite maintenance; the count is a compatibility fact rather than a quality target.
- An always-on quality kernel for every persistent mutation, covering durable requirement understanding, repository-grounded design, semantic recovery, black-box and white-box test accountability, root challenge, and knowledge disposition even when specialist routing is incomplete.
- Content-bound design approval, engineering-context fingerprints, event-triggered continuity checkpoints, and `resume-packet` recovery for context compaction, steering, phase, slice, delegation, repair, verification, and final-claim boundaries.
- A three-plane knowledge system for tracked current project truth, tracked per-change dossiers, and ignored runtime recovery evidence, with thin structural validation and explicit promotion/privacy rules.
- Path-aware discovery and admission of repository instructions, profiles, native controls, artifact facts, and installed technical Skills without silently turning personal capabilities into shared policy.
- Separate black-box and white-box test derivation, oracle failure-sensitivity review, coherent-slice and commit-ready checks, proportional comment guidance, and digest-bound multi-agent briefs.
- Six-layer TOML engineering profiles, JSON effective snapshots, deterministic precedence/conflict resolution, review-first profile tooling, and concise `AGENTS.md` projections.
- Task-relative T0-T3 Engineering Context Readiness plus Engineering Quality Assurance Coverage with native-control-first evidence, active-host capability admission, minimal routing, fallback/waiver, and no automatic Skill installation.
- Versioned capability, profile, manifest, snapshot, readiness, and admission contracts with routing, collision, cross-language, and paired-evaluation fixtures.
- Scoped repository-instruction and convention discovery with traceable `INS-n` integration.
- Risk-scaled collaboration profiles and UI impact classification with Requirement Ready and conditional UX Ready approvals.
- Backward-compatible packet schema 1.1 plus new-product UI, protected-IA UI, and nested-instruction evaluation contracts.
- Backward-compatible packet schema 1.2 with structured `AMB-n` semantic ambiguity records, authority-aware resolution commands, requirement revision/digest binding, and scoped late-ambiguity reopening.
- A focused semantic clarification protocol, audit finding classification, agent role constraints, and evaluation coverage for complete designs, product requirements, short requests, sparse bug reports, and late audit ambiguity.
- A suite-wide Default-mode user-interaction contract that prefers host-native `request_user_input` through App Server `item/tool/requestUserInput`, with capability-safe text fallback and separate approval/secret channels.
- Packet schema 2.0 with direct/traced/governed work modes, append-only event ledgers, atomic current-state projections, and unchanged read compatibility for schemas 1.0-1.2.
- A versioned Codex host adapter, personal/team/CI profile modes, compact/full readiness projections, and repository-wide versus task-mapped native evidence.
- Safe idempotent terminal-packet deactivation that preserves packet/event evidence and refuses active, mismatched, or unsafe current pointers.
- Deterministic commit-bound source archives with strict manifest, checksum, version, path, link, and corruption verification.
- Explicit six-cell hosted CI plus a separately trusted manual SBOM/provenance workflow pinned to immutable Action and Syft releases.
- A bounded, schema-constrained Codex executor/grader adapter with ephemeral read-only sessions and minimal per-call usage receipts.

### Changed

- Advanced the source, release workflow defaults, runbook examples, and release artifact contracts to patch version `1.0.1`.
- Stop Hook completion checks are now advisory and lifecycle-scoped, distinguish newer packet/runtime incompatibility from packet corruption, and preserve the first assistant final; explicit pre-final validation, terminal transition, and matching-pointer deactivation remain the hard closeout path.
- Repositioned `dev-flow` as a neutral thin orchestration kernel and migrated stable engineering, dependency, debugging, testing, review, UX, and delivery practices to focused owners.
- Moved personal Rust/frontend/library choices out of public policy into configurable profile examples and current decision/snapshot surfaces.
- Frontend guidance now separates non-visual, preserve, and material product/UX work instead of treating UI as an implementation-only profile.
- Packet templates, agent briefs, independent review, metrics, governance records, and public usage documentation now carry instruction, collaboration, and UX evidence.
- Requirement Ready now proves that material ambiguity has an authorized disposition and that approval matches the current requirement content; schema 1.0/1.1 retain their original validation contract.
- Every focused Skill now preserves Default mode at user-owned checkpoints; cancellation, malformed answers, missing tool capability, and protocol lifecycle ownership have explicit non-defaulting behavior.
- Single-agent operation is the baseline; preflight degrades on optional delegation/hook gaps unless delegation is explicitly required.
- Routine routing no longer adds independent review or delivery readiness automatically, and Skill metadata/static instruction paths have enforced token budgets.
- Multi-Agent V2 now treats native child finals as primary, optional reports as fail-open evidence, terminal packets as lifecycle-inert, and root reconciliation/deadlines/dispositions as the completion contract.
- Marketplace installs now consume the selected immutable marketplace snapshot directly instead of resolving a second hard-coded repository ref.

### Removed

- Removed the former monolithic engineering preference Skill without an alias or compatibility shim, as an explicitly approved breaking cutover.

## [0.2.0] - 2026-08-09

### Added

- Traceable workflow packets for requirements, design, implementation, testing, audits, acceptance, and delivery.
- Task-type and project-profile playbooks, Multi-Agent V2 role contracts, test-resource orchestration, and evidence retention rules.
- An opinionated Rust and frontend engineering preference skill with machine-readable governance data.
- Conservative hooks, deterministic evaluation cases, structural contracts, and a cross-platform CI matrix.
- Safe runtime installation, explicit forced replacement with backups, and ownership-aware uninstall support.

### Changed

- Normalized the public source version to `0.2.0`; local Codex cachebuster suffixes are no longer treated as release versions.

### Security

- Runtime markers no longer persist absolute packet paths, start/stop stay fail-open on marker storage or malformed data, and markers are removed whenever subagent stop is observed.
- Runtime traces, plugin data, secrets, caches, and build outputs are excluded from source control.

[Unreleased]: https://github.com/AldenClark/dev-flow/compare/v1.0.2...HEAD
[1.0.2]: https://github.com/AldenClark/dev-flow/compare/v1.0.1...v1.0.2
[1.0.1]: https://github.com/AldenClark/dev-flow/compare/v0.2.0...v1.0.1
[0.2.0]: https://github.com/AldenClark/dev-flow/releases/tag/v0.2.0
