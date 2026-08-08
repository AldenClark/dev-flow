# Changelog

All notable changes to this project are documented here. The format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) and versions follow [Semantic Versioning](https://semver.org/).

## [Unreleased]

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

- Runtime markers no longer persist absolute packet paths and are removed after successful subagent completion.
- Runtime traces, plugin data, secrets, caches, and build outputs are excluded from source control.

[Unreleased]: https://github.com/AldenClark/dev-flow/compare/v0.2.0...HEAD
[0.2.0]: https://github.com/AldenClark/dev-flow/releases/tag/v0.2.0
