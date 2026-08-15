# Change design: dev-flow-1-1-2-agent-dispatch

[Tracked change manifest](../../../docs/changes/dev-flow-1-1-2-agent-dispatch/manifest.json)

## Decision

Add one versioned JSON dispatch registry, one stdlib selector, and an additive `route-agent` CLI. The registry owns profile vectors, current model mappings, workloads/compatible roles, and upgrade rules. The selector resolves a base profile, independently raises minimum capability and effort, then selects the least profile satisfying both axes. Orchestration invokes it before every spawn and records request/effective receipts. Role TOMLs remain model-neutral.

## Engineering preferences applied

- Applicable instructions: INS-1 authorizes delivery; INS-2 requires governed continuity; INS-3 keeps the mechanism small/deterministic; INS-4 separates evidence.
- Effective snapshot: neutral repository baseline plus user quality/portability priorities.
- Language/framework scope: Python 3.11+ stdlib, JSON, Markdown, GitHub Actions YAML, Codex Multi-Agent V2.
- Quality coverage: native unittest/contracts/validators/release builder plus six hosted cells.
- Variation seam: task breadth/capability and bounded reasoning depth justify a resolver, not an adaptive scorer.

## Alternatives

| Option | Capability fit | Costs and risks | Decision |
|---|---|---|---|
| Documentation matrix | explanatory only | inconsistent application | rejected |
| Pin role models | simple | blocks task-relative choice and freezes volatile names | rejected |
| Learned/scored router | potentially adaptive | opaque, costly, premature evaluation surface | rejected |
| Registry plus vector resolver/CLI | deterministic, auditable, additive | schema/tests required | selected |

## Architecture and failure behavior

Task graph chooses child role/workload; root invokes `route-agent` with risks/signals; exact registry validation runs; workload supplies a base vector; rules independently raise capability/effort; the least non-exception satisfying profile is selected; JSON emits spawn fields/reasons; root passes model/effort with `fork_turns=none` unless a bounded context exception is justified; execution records requested and observed values.

P3 B/high represents bounded depth; P4 F/medium represents breadth. Their combination becomes P5 F/high. P6 F/xhigh requires critical signals. PX F/max is never automatic and requires acknowledgement. Root decisions return no spawn request. Registry/input errors exit 2 with `status=invalid`; there is no silent substitution. Host fallback is permitted only when safe and must record observed or not-observed effective values and the reason. Explicit lower profiles require an acknowledgement.

## Product and UX contract

- UI impact: none.
- Users, outcome, and protected product/IA/flow constraints: additive CLI/Skill behavior; existing commands remain valid.
- Design truth, selected direction, states, accessibility, fidelity, and evidence: concise machine-readable output; no visual surface.
- UX Ready: not applicable.

## Requirement baseline and reopening

- Bound revision and digest: revision 1 and CLI-recorded SHA-256.
- Disposed ambiguities: real routing is required; no open AMB.
- Reopening behavior: incompatible public behavior, dependency, or authority change stops affected work.

## Dependency decisions

- DEP-1: no dependency change; Python standard library and existing helpers only.

## Change scope

- SC-D1: dispatch registry, selector, `route-agent`, and stable JSON output.
- SC-D2: orchestration, Dev Flow entrypoint, task brief, execution/agent report, and public usage docs.
- SC-D3: deterministic dispatch cases and black/white tests.
- SC-I1: native cross-platform CI invocation with all six cells preserved.
- SC-I2: plugin/workflow/README/runbook/changelog/attestation/governance/dossier version 1.1.2 surfaces.
- SC-P1: existing commands/schemas, Skill routing, unpinned roles, authority boundaries, and supplemental-only model evaluation.
- SC-P2: Windows portability regressions, native shell signal, LF authority bytes, deterministic artifacts.
- SC-O1: no dependency, role pin, adaptive scorer, PR, GitHub Release, deploy, force push, tag rewrite, or historical dossier edit.
- SC-L1: authorized commit, main/tag push, immutable annotated v1.1.2, and primary local plugin update.

## Compatibility, rollout, rollback, and cleanup

The CLI is additive; orchestration adopts it before child spawn. Rollback is a new revert commit and immutable v1.1.1 marketplace ref. No data migration exists. Build/install temp state is isolated and removed; only the primary local plugin update mutates runtime installation.

## Verification obligations

- VO-1: validate exact profiles, model mappings, role/workload graph, and rule references.
- VO-2: public CLI proves representative defaults, combined breadth/depth, critical/P6, root no-delegation, invalid role/workload, PX guard, downgrade guard, and stable output.
- VO-3: structural tests prove pre-spawn selection/receipt fields and unpinned roles.
- VO-4: negative controls distinguish broken defaults, ignored axes, unsafe exception, and role drift.
- VO-5: focused/full tests, contracts, methods/knowledge, maintainer/plugin/data-security, compileall, JSON, and diff checks pass.
- VO-6: all six hosted CI cells pass without POSIX-only/platform-wording assumptions.
- VO-7: two isolated final-commit 1.1.2 builds are byte-identical and verify.
- VO-8: remote main/tag and local plugin/cache match accepted version/commit/tree.

## Testing and implementation strategy

- Implementation slices: registry/selector/CLI/tests; orchestration/templates; CI/version/dossier; broad verification; delivery/install.
- Black-box design: invoke public CLI for valid/invalid representative inputs and assert exit/status/fields.
- White-box design: validate references, vector combination, exception/downgrade guards, compatibility, and unpinned role assets.
- Oracle and test-code review: incompatible roles, missing PX acknowledgement, lower-than-policy profile, and broad+deep signals are negative controls.
- Specialist controls: architecture, verification, change review, delivery readiness, maintainer validator, release/install commands.

## Approval record

- 2026-08-15: user approved the architecture and explicitly authorized real Phase 1 implementation, commit, tag, push, and primary local Codex update with stated exclusions.
