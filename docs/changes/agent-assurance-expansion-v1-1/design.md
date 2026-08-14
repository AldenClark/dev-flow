# Change design: agent-assurance-expansion-v1-1

[Tracked change manifest](./manifest.json)

## Decision

Add 17 method cards, 14 narrowly scoped risk models, controlled signal/prerequisite vocabulary, one progressively loaded Agent-control guide, strengthened existing Agent cards, scenario contracts, current-truth docs, and `1.1.0` release surfaces. Preserve selector/schema/owner interfaces. Use automatic `starter/deep` only for proportionate controls; HTN, conformal risk control, and contract-net remain `formal` specialists with dedicated failure models and thresholds.

## Engineering preferences applied

- Applicable instructions: INS-1, INS-2, INS-3, INS-4; shared service, deterministic black/white evidence, exact delivery identity, and preserved user changes.
- Effective snapshot: neutral repository policy, no conflicts or waivers; standard library and current owner Skills only.
- Quality coverage: native unit/contract/knowledge/release/plugin validators plus clean-context blue/red review.

## Alternatives

- Continue open-ended exploration: rejected because current sources cover the material failure classes and further enumeration delays executable quality.
- New Skill per family: rejected because methods guide existing owners and must not expand routing/context.
- Model-only selector: rejected because deterministic mapping and negative/prerequisite gates are acceptance-critical.

## Architecture and failure behavior

The unchanged chain is explicit facts → weighted risk models → candidate stable IDs → phase/depth/negative/prerequisite/context-cap filtering → `method.selection.v1` → existing owner artifacts/evidence. New risk models separate autonomy overreach, partial observation, open-loop drift, reactive execution, hierarchical planning, patch overfit, untrusted context, irreversible effects, stochastic eval validity, calibrated selective action, simulation reality gap, memory drift/poisoning, multi-agent topology, and dynamic allocation. AMB-1 review showed that methods are activated by model membership, so specialist methods must not share broad stacks whose neighboring signal is insufficient.

## Product and UX contract

- UI impact: none; CLI JSON and Markdown paths remain stable.
- User outcome: novice users provide task facts, not method names; progressive guidance stays plain-language and source-grounded.
- UX Ready: not applicable.

## Requirement baseline and reopening

- Bound revision: requirement revision 3; digest recorded by `REQ-READY` after AMB-1 and AMB-2 resolution.
- Ambiguities: AMB-1 split specialist failure models and added negative scenarios; AMB-2 made tracked and runtime authority documents byte-identical with a portable relative link. No user-owned semantic changed.
- Reopen on incompatible schema/owner/dependency need, changed AC meaning, or unsafe delivery identity drift.

## Dependency decisions

- DEP-1: no new dependency; Python standard library and existing repository commands only.

## Change scope

- SC-D1: registry vocabulary, sources, 17 methods, 14 risk models.
- SC-D2: Agent control/safety/memory/coordination/evaluation guidance and strengthened existing Agent methods.
- SC-D3: inventory, scenario, formal-depth, and missing-prerequisite tests.
- SC-I1: current truth, public docs, changelog, version/release surfaces, protected data-security attestation digest.
- SC-I2: governed follow-up dossier and source-history link.
- SC-P1: preserve schema/output/CLI/owners/foundations/context caps/standard-library/platform compatibility.
- SC-P2: preserve planned-versus-executed-versus-live evidence and all authority gates.
- SC-O1: external tool platform, dependencies, top-level Skills, incompatible migration, PR/GitHub Release/deploy/unrelated work.
- SC-L1: authorized commit/push `main`, new immutable annotated `v1.1.0`, and primary local Codex update only.

## Verification obligations

- VO-1: registry/source/reference validation and exact inventory.
- VO-2: all new scenario families and stable selected IDs.
- VO-3: formal, negative, missing-prerequisite, cap, and no-authority boundaries.
- VO-4: data-security digest and existing compatibility contracts.
- VO-5: strict full suite, contract/maintainer/plugin/compile/knowledge/diff gates.
- VO-6: clean-context blue/red review with closed findings.
- VO-7: two identical verified release artifacts from the committed SHA.
- VO-8: remote main/tag and installed plugin/cache identity.

## Testing and implementation strategy

- Black-box: public `validate-methods`/`select-methods`, representative Agent signals, invalid/missing prerequisite/formal-depth behavior, release artifact, remote and installed identities.
- White-box: graph integrity, source/reference closure, stable sorting/caps, negative rules, protected digest/version surfaces, knowledge manifest, and final diff.
- Oracle challenge: exact method IDs/counts, deliberate missing prerequisites, depth exclusion, malformed registry/reference mutations, byte comparison, and SHA/version equality.

## Compatibility, rollout, rollback, and cleanup

All registry changes are additive under schema `1.0`. Source rollback requires a new revert commit; local plugin rollback uses immutable `v1.0.2` only if needed. No production/data migration or generated cleanup exists. Temporary release/install test resources are isolated and removed or retained only as explicit evidence.

## Approval record

Approved by the user's 2026-08-14 autonomous implementation/release direction. Revisions 2 and 3 are evidence-backed Codex-owned design/governance refinements inside that delegated authority; no new dependencies or external scope.
