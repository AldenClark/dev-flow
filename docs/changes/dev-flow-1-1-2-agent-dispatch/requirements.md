# Change requirements: dev-flow-1-1-2-agent-dispatch

[Tracked change manifest](../../../docs/changes/dev-flow-1-1-2-agent-dispatch/manifest.json)

## Requirement source and understanding revisions

- Original input: implement the approved Phase 1, release Dev Flow 1.1.2, commit, tag, push, update primary local Codex, and avoid another Windows CI repair cycle.
- AI understanding revision 1: Phase 1 is real deterministic spawn-time routing, including profiles, workload/role routing, orthogonal upgrades, receipts, tests, current mapping, version surfaces, and delivery.
- Corrections and decisions: P0-P5 apply automatically; P6 requires explicit critical signals; PX is acknowledged exception only; role configs remain neutral.
- Current requirement truth: this revision supersedes the earlier ambiguous shadow/advisory wording.

## User and product outcome

Dev Flow should consistently and audibly select proportionate child-agent capability and effort without manual prose interpretation or permanent role pins. Exact work uses efficient capacity, bounded engineering uses balanced capacity, and broad/high-risk work escalates deterministically.

## Requirement delta

Add `route-agent`: role/workload/risk input becomes a delegation decision plus profile/model/effort/fork request and reasons that orchestration must use and reconcile.

## Acceptance criteria

- AC-1: valid inputs produce deterministic JSON with delegation, base/selected profile, requested model/effort, selection source, reasons, and `fork_turns=none`.
- AC-2: a public registry defines P0-P6/PX, E/B/F and effort axes, current model mapping, role/workload compatibility, and P3-depth/P4-breadth orthogonality.
- AC-3: breadth/ambiguity raises capability, bounded depth raises effort, critical risks reach P5, critical acceptance/irreversibility reaches P6, and PX is never automatic.
- AC-4: root decisions do not delegate; invalid combinations and unacknowledged PX fail; a lower explicit profile cannot silently bypass policy.
- AC-5: orchestration requires `route-agent` before spawn and records requested/effective configuration, source, fallback, fork, observations, and disposition.
- AC-6: cross-platform black/white tests cover defaults, combined axes, role boundaries, invalid/exception paths, unpinned roles, and docs/templates; all six CI cells remain.
- AC-7: all current version/release surfaces identify 1.1.2; strict gates and two final-commit builds pass byte-identically.
- AC-8: accepted commit and annotated v1.1.2 tag are pushed and verified; six-cell CI passes; primary local plugin/cache matches version, commit, and tree.

## Non-functional requirements

- Deterministic, stdlib-only, additive, cross-platform, concise, and fail-closed for invalid input.
- Model names exist only in the volatile registry; no learned router, dynamic pricing, composite score, or hidden fallback.

## Compatibility and exclusions

- Compatibility: existing Skills, roles, commands, schemas, evaluation, plugin install, Python, and OS matrix remain compatible.
- Excluded: model training, network discovery, third-party install, PR, GitHub Release, deploy, force push, tag rewrite, and historical dossier edits.

## Requirement Ready gate

- Status: ready.
- Evidence: explicit user approval, clean repository, active runtime capability, and inspected release/CI contracts.
- Remaining decisions: none.

## Requirement baseline

- Revision: 1.
- Digest: recorded by the content-bound CLI approval.
- Baseline content: this complete file.
- Reopen conditions: material semantic correction, incompatible contract/dependency, unsupported required mapping, or a gate failure changing AC/SC/VO meaning.

## Ambiguity ledger

| ID | Source and interpretations | Evidence | Materiality and owner | Affected IDs | Recommendation | Status and resolution |
|---|---|---|---|---|---|---|
| none | advisory versus real routing | user's explicit implementation clarification | material; user | AC-1 to AC-5 | implement real routing | resolved |

## Confirmation record

- 2026-08-15: user approved architecture and authorized Phase 1, 1.1.2 commit/tag/push, local plugin update, and proactive Windows completion.
