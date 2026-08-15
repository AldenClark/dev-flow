# Change design: dev-flow-1-1-1-method-enforcement

[Tracked change manifest](./manifest.json)

## Decision

Introduce an additive immutable packet capability, `method-selection-v1`. Governed packet creation runs a preliminary design selection automatically. `record-methods` appends a packet-bound selection record, event-projects it into `method-selection.json`, deterministically renders `method-selection.md`, and maps each selected method's owner to an existing governed artifact. Design approval, verification entry, and acceptance require cumulative fresh design/verification/review records; preliminary, missing, stale, or risk-incomplete records fail closed.

Unify risk semantics through an explicit engineering-risk translation table rather than expanding the methodology vocabulary with routing-only topics. `select-methods` accepts canonical or engineering risks, preserves input and per-risk translations, and selects on canonical failure classes. `validate-methods` proves that all 55 engineering risks are canonical or aliased and every alias target exists. Add a dedicated FFI/ABI model plus five focused design/review models and six source-grounded method cards.

## Engineering preferences applied

- INS-1: preserve user authority boundaries and keep implementation, evidence, commit, push, tag, release, installation, and deployment claims separate.
- INS-2: use repository evidence, standard library, deterministic contracts, native tests, and bounded progressive context.
- INS-3: maintain backward compatibility through immutable creation capabilities; mutable metadata cannot opt an old packet into a new contract.
- INS-4: keep method count subordinate to failure coverage; every addition needs positive/negative triggers, prerequisites, fallback, evidence, owner, source, and scenario.

## Product and UX contract

UI impact is none. CLI JSON gains additive risk-translation and method-gate fields, while governed packets gain generated selection sidecars; users still do not need to name a methodology.

## Requirement baseline and reopening

Requirement revision 1 is ready and content-bound at approval. Reopen only for changed acceptance meaning, a newly required dependency/incompatible schema, material risk-premise drift, or changed user authority.

## Alternatives

- Strengthen prompt text only: rejected because the reported GLM task already bypassed advisory text and left no machine-verifiable record.
- Add method fields directly to every packet schema/version: rejected because it would retrospectively reinterpret old packets and enlarge unrelated traced work.
- Make all routing risks first-class methodology risks: rejected because device, signing, browser, and similar governance topics map to one or more existing failure classes; an explicit alias ledger is clearer and validates drift.
- Add a new top-level Skill for each method family: rejected because methods guide existing decision owners and must not expand routing/context surface.
- Require all blocked prerequisites to close before lifecycle progress: rejected because safe fallbacks and honest unresolved claims are legitimate; the gate proves selection occurred and is current, not that every specialist environment exists.

## Architecture and failure behavior

The packet flow is:

`init-packet` → preliminary design selection → repository/requirement/design work → `record-methods --phase design` → approval → implementation → `record-methods --phase verification` → verification → `record-methods --phase review` → acceptance.

The JSON sidecar contains an ordered full selection history. Each record binds lifecycle phase/state, preliminary status, methodology registry SHA-256, packet task/risks/revision/digests, complete `method.selection.v1`, and owner-to-artifact mappings. Packet metadata binds JSON/Markdown paths, SHA-256 values, and latest sequence; the append-only event stores both the full record and projection. Validation reconstructs records from events, verifies deterministic Markdown, exact fields/sequences/digests, cumulative lifecycle freshness, current registry, current requirement/design bytes, and canonical packet-risk coverage.

Freshness is phase-relative: design follows the active discovery generation, verification follows the latest implementing entry, and review follows the latest verifying entry. A repair transition back to implementation therefore requires a new verification selection, while stable approved requirements/design need not be reselected without premise drift. Partial writes remain detectable and block progress.

The risk translator maps 23 routing-only risks to one or more of the existing 32 canonical failure risks. It never silently discards unknown input. `release → deployment`; `flaky-baseline/incomplete-reproduction → weak-tests`; packaging/toolchain/platform risks map to compatibility/deployment/dependency; external-write/rollback/blast-radius risks map to recovery/security/deployment; resource/startup/SLO risks map to performance/resource/recovery.

The six new methods and matching models are signal-bounded: cross-view inconsistency, architecture-conformance drift, workflow collaboration, data-quality risk, architecture investment choice, and cross-language boundary. Broad `architecture`, `large-feature`, or deep/formal selection alone does not activate the first five. FFI/ABI is the exception: the explicit governed risk itself is sufficient to activate its failure model, while the deep cross-language contract still respects depth and prerequisites.

## Dependency decisions

- DEP-1: no dependency change. Use Python standard library, existing JSON/event/path helpers, Markdown, and repository-native test/release commands.

## Change scope

- SC-D1: packet capability tag, automatic preliminary selection, `record-methods`, sidecars, event projection, lifecycle gates, and tamper/drift validation.
- SC-D2: engineering-to-methodology risk translation, route output, selector input trace, and closed-vocabulary validation.
- SC-D3: six methods, six sources, six risk models, vocabulary additions, architecture guidance, and progressive public documentation.
- SC-D4: tracked/runtime requirements, design, execution, verification, current truth, changelog, and release guidance.
- SC-I1: black-box prompt-to-packet/gate tests plus white-box registry, translation, scenario, projection, drift, and compatibility tests.
- SC-I2: plugin/workflow/attestation/readme/runbook `1.1.1` surfaces and protected data-security digest.
- SC-P1: preserve standalone `method.selection.v1`, owner boundaries, authority/evidence semantics, context caps, direct/traced paths, schemas 1.0-1.2, and old schema-2 packets.
- SC-P2: preserve no-live-authority, `NOT RUN`, no implicit dependency/delivery rights, no history rewrite, and ordinary static-context budget.
- SC-O1: no third-party dependency, new top-level Skill, schema migration, PR/GitHub Release/deploy, force push, tag rewrite, or unrelated change.
- SC-L1: authorized local commit, push `main`, immutable annotated `v1.1.1`, and primary local Codex plugin upgrade with exact identity verification.

## Verification obligations

- VO-1: registry validation reports 117 methods, 73 sources, 38 risk models, 55 covered engineering risks, 23 aliases, and no graph/reference error.
- VO-2: exact scenarios prove release translation, FFI/ABI activation, all six new methods, broad-signal non-triggering, missing prerequisites, negative rules, caps, and stable output.
- VO-3: end-to-end governed packet creation produces a preliminary record; approval rejects it; fresh records pass method gates; sidecar/event/digest/registry/requirement/design/risk drift fails.
- VO-4: legacy packets, direct/traced modes, `method.selection.v1`, route ownership, packet schema readability, static budget, and authority boundaries remain compatible.
- VO-5: focused tests, strict full unittest discovery, contract checks, maintainer validation, plugin check, compileall, JSON validation, data-security doctor, and `git diff --check` pass after final bytes.
- VO-6: clean blue review and adversarial red review classify and close scope, compatibility, tamper, stale-selection, risk-loss, false-assurance, version, secret, and delivery findings.
- VO-7: two release builds from the final commit are byte-identical and pass archive/manifest/checksum verification for `1.1.1`.
- VO-8: remote `main` and `v1.1.1` resolve to the accepted commit; primary Codex lists `dev-flow` `1.1.1`, and installed cache HEAD/source bytes match that remote identity.

## Testing and implementation strategy

- Black-box: public `route-task`, `select-methods`, `init-packet`, `record-methods`, transitions, validators, release builder, remote refs, and installed plugin listing.
- White-box: alias coverage, registry graph, method/model IDs, event/sidecar replay, exact projection hashes, deterministic Markdown, baseline freshness, immutable capability adoption, version/digest surfaces, and diff accounting.
- Oracle challenge: deliberate preliminary-only approval, unknown/duplicate risk, broad-signal non-trigger, digest mutation, event/sidecar mismatch, stale registry/baseline, phase misuse, and archive tamper must fail at the intended observation point.

## Compatibility, rollout, rollback, and cleanup

Source compatibility is additive. Only packets whose immutable creation event advertises `method-selection-v1` and whose work mode is governed are enforced. Rollback uses a new revert commit and the prior immutable `v1.1.0` plugin ref; no data migration exists. Temporary test/release/install directories remain isolated, and no production/runtime process is modified beyond the explicitly authorized primary local Codex plugin installation.

## Approval record

The user approved the complete outcome and delivery boundary on 2026-08-15. The concrete architecture above is a Codex-owned implementation decision within that authority, preserves all specified compatibility, and introduces no dependency or external scope requiring a new checkpoint.
