# Project profiles

Compose every applicable profile. A Rust-backed native app with a web console may require backend, frontend, app, FFI, and release obligations simultaneously.

## Rust backend or network service

- Trace request/job lifecycle through routing, auth, state, persistence, external calls, shutdown, and telemetry.
- Verify timeouts, limits, cancellation, overload, idempotency, slow consumers, graceful drain, and secret redaction.
- Test handlers and domain behavior, real persistence boundaries, protocol compatibility, and container/process startup when relevant.

## Background worker, scheduler, or daemon

- Define job identity, ownership, concurrency, retry, backoff, deduplication, checkpoint, poison handling, shutdown, and recovery.
- Test restart at each durable boundary and prove duplicate delivery does not corrupt state.
- Verify service-manager/container lifecycle, signals, leases, and observability.

## CLI or TUI

- Treat stdout, stderr, exit codes, JSON/JSONL modes, terminal restoration, signals, cancellation, and non-interactive behavior as contracts.
- Test parsing, invalid inputs, piping, terminal size, Unicode, interruption, and recovery.
- Do not introduce a full-screen TUI when a simple CLI flow is sufficient.

## React web frontend

- Trace route, loader/query, cache ownership, mutation, error, loading, empty, optimistic, and permission states.
- Verify semantic HTML, keyboard, focus, accessible name, responsive layout, reduced motion, and browser-visible behavior.
- Run typecheck, lint, unit/component tests, Playwright projects, axe checks, bundle or render measurements when relevant.
- Use pnpm for new projects and preserve one authoritative lockfile.

## Rust native desktop UI

- Prefer GPUI with `gpui-component`; use Slint only when its platform/support tradeoff is better. Do not introduce Tauri or egui.
- Verify windows, commands, focus, input method, accessibility, scaling, platform integration, startup, memory, and packaging.
- Treat pre-1.0 framework API and platform gaps as compatibility risks requiring pinned versions and target-platform evidence.

## Apple or Android app

- Include UI lifecycle, background execution, permissions, signing, entitlements, packaging, store/runtime constraints, device/simulator differences, and OS-version matrix.
- Use platform-native Skills and debugger/test tooling.
- Distinguish simulator/emulator evidence from physical-device evidence.

## Rust FFI library or SDK

- Apply `rust-swift-ffi` or `rust-kotlin-ffi` plus `ffi-code-review`.
- Verify both languages, ABI layout, ownership, panic/error mapping, concurrency, callback quiescence, cancellation, handle generation, packaging, symbols, loader, and final consumer artifact.
- Required device, architecture, sanitizer, CheckJNI, or packaging cells that were not run remain explicit release blockers.

## Library or public SDK

- Treat public API, feature flags, MSRV, SemVer, docs, examples, downstream compilation, and minimal dependency surface as contracts.
- Test default/minimal/all feature combinations and representative consumers.

## Data/schema/protocol component

- Define versioning, unknown-field behavior, canonicalization, limits, forward/backward compatibility, migration order, golden fixtures, fuzz/property tests, and rollback.
- Test old reader/new writer and new reader/old writer directions when required.

## Composite profile rule

Create the union of obligations, then remove only genuinely irrelevant cells with a reason. Do not average risks across profiles. The strictest applicable release and compatibility gate governs the final claim.
