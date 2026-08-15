# Change requirements: dev-flow-1-1-1-method-enforcement

[Tracked change manifest](./manifest.json)

## Requirement source and understanding revisions

The user observed that a GLM system-design task completed its design phase without activating any methodology, then asked for a fresh assessment, a final design, complete implementation, Dev Flow `1.1.1`, commit/push, and upgrade of the primary local Codex installation. Repository and prior-task evidence confirmed that `select-methods` was documented but not persisted or enforced, `release` was valid routing input but invalid methodology input, and `ffi`/`abi` were accepted methodology risks without a matching failure model. This document is the complete requirement revision; no material user-owned ambiguity remains.

## User and product outcome

A Codex user can describe a material system-design task without knowing method names. Dev Flow must visibly activate a proportionate method stack, carry that choice into owner artifacts, and prevent design, verification, or final review from advancing on missing or stale method reasoning. Users of existing packets and the standalone selector must retain their compatible behavior and authority boundaries.

## Requirement delta

Current behavior relies on an instruction telling the model to run a selector, so a task can produce a substantial design without any selection record. Routing and methodology risks are not one closed contract, which rejects `release` and permits `ffi`/`abi` foundation-only false coverage. Desired behavior makes governed activation automatic and lifecycle-gated, translates every engineering risk explicitly, and adds source-grounded methods only for observed design/review failure classes.

## Acceptance criteria

- AC-1: Creating a governed packet automatically writes a preliminary design `method.selection.v1` into event-projected JSON and deterministic Markdown with owner/artifact mappings.
- AC-2: Design approval, verification entry, and acceptance require fresh non-preliminary design, verification, and review records bound to the current registry, task, risk set, requirement revision, and requirement/design bytes.
- AC-3: All 55 engineering-context risks are canonical methodology risks or have an explicit validated alias; `release` maps to `deployment`, and routing reports translations and unmapped risks.
- AC-4: `ffi` and `abi` match a dedicated cross-language boundary failure model and can select a source-grounded ABI/ownership contract rather than foundation-only coverage.
- AC-5: Architecture viewpoint consistency, architecture reflexion/conformance, BPMN collaboration, data-quality reconciliation, CBAM-style investment analysis, and cross-language ABI contracts have bounded triggers, prerequisites, fallbacks, evidence, owners, sources, and deterministic positive/negative scenarios.
- AC-6: `method.selection.v1`, owner/authority boundaries, context caps, standard-library operation, direct/traced behavior, and packets without immutable `method-selection-v1` remain compatible.
- AC-7: Public/current-truth documentation, version surfaces, contracts, plugin checks, strict tests, compile checks, and two deterministic `1.1.1` release builds pass against final source bytes.
- AC-8: The exact accepted commit is pushed to `origin/main`, an immutable `v1.1.1` tag is pushed and verified, and the primary local Codex plugin/cache resolves to version `1.1.1` and that remote commit.

## Non-functional requirements

- The implementation uses Python standard library and existing packet/event/path primitives only.
- Selection remains bounded and deterministic; it does not load the full pool or treat selection as execution, proof, approval, deployment, or production evidence.
- Missing prerequisites retain fallback/unresolved evidence instead of being silently dropped.
- Lifecycle enforcement fails closed on partial sidecars, projection drift, registry drift, requirement/design drift, and invalid phase/state use.
- Ordinary static context remains within the repository's 18,000-byte contract.

## Compatibility and exclusions

- Compatibility: additive packet capability under schema 2.0; standalone output remains `method.selection.v1`; schemas 1.0-1.2 and previously created schema-2 packets are read without retrospective enforcement.
- Excluded: new top-level Skills, third-party dependencies, evaluator-score optimization, GitHub Release/PR/deployment/publication, production or device claims, and modification of historical accepted dossiers.
- Delivery boundary: local commit, push of `main`, immutable `v1.1.1` tag, and primary local Codex plugin upgrade are authorized; force push, tag movement, PR, GitHub Release, and deployment are not.

## Requirement Ready gate

- Status: ready.
- Evidence: the user's explicit 2026-08-15 instruction, repository behavior, the observed GLM task trace, selector/routing command evidence, and current clean `main == origin/main` baseline.
- Remaining decisions: none; architecture and implementation details are Codex-owned within the approved outcome and compatibility boundary.

## Requirement baseline

- Revision: 1.
- Baseline content: this complete requirements file; its exact SHA-256 is bound by the manifest and runtime approval.
- Reopen conditions: material semantic correction, incompatible contract/dependency, or a finding that changes AC/SC/VO meaning.

## Ambiguity ledger

- No material AMB record is required. “升级到 1.1.1” is implemented as source/version update, deterministic local release artifacts, commit/push, an immutable annotated stable tag, and primary local marketplace/plugin update; it does not imply GitHub Release or deployment.

## Confirmation record

- The user's request explicitly authorizes implementation, local commit, push, stable tag delivery, and local Codex installation upgrade.
