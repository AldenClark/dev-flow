# Dev Flow 2.0 lifecycle

## Three evidence planes

1. Business continuity: repository-tracked implementation/progress and conditional requirements/design/material decisions for managed work.
2. Engineering evidence: code, Git, tests, builds, CI, runtime observation, and artifact provenance.
3. Safety boundary: host permissions and explicit authority for destructive, irreversible, or external actions, plus the independent data-security Hook on its supported confidentiality surfaces.

Keep ownership separate. A document does not prove runtime behavior; a test does not choose product meaning; a local result does not authorize delivery.

## Always-on quality spine

Every task briefly establishes the observable outcome, current repository facts, assumptions, affected boundaries, smallest coherent slice, native oracle, and delivery limits. Scan for risks visible in code and dependencies, not only risks named by the request. This calibration creates no file or approval state.

For substantial managed work, material risk, delegation, or repeated failure, use `quality-calibration.md` to decide whether a specialist Skill, P0-P6 child route, bounded assurance method, or independent review has positive decision value.

Classify requirement understanding before technical design. Material new or changed product semantics publish a detailed technology-neutral understanding and stop in Default mode for explicit confirmation. Established defects proceed from proven expected/protected behavior, while ambiguous defects upgrade to semantic confirmation. Mechanical and read-only work never acquire the stop solely because Dev Flow is active.

After repository discovery and after a material requirement confirmation, perform the ephemeral capability-activation pass: applicable effective-host specialist, bounded method, independent review, and child model/effort. It produces no artifact. Re-run only an affected decision when evidence changes.

## Direct path

1. Resolve objective, authority, roots, instructions, current behavior, scope, and user changes.
2. Clarify only a material decision. For semantic creation/change, publish the full understanding and stop for confirmation before design; otherwise proceed with a reversible repository-grounded assumption.
3. Reproduce a defect before repair when practical.
4. Implement one coherent slice.
5. Run the narrowest sensitive oracle, then affected broader checks.
6. Inspect the final diff and report outcomes, evidence, and limits.

Direct work has no Dev Flow continuity artifact or lifecycle transition. It still maintains existing repository documentation when architecture, contracts, runbooks, product behavior, or operational truth changes. When no existing home preserves an otherwise durable product rule, public contract, data/security behavior, recovery rule, cross-boundary invariant, or non-obvious rationale, add one concise repository-native change note; do not duplicate code, tests, issues, changelogs, ADRs, or maintained docs.

## Managed path

Use when continuity or coordination exceeds one coherent slice. Read the repository's current workstream documents at start/resume, verify their assumptions against current Git/repository facts, and update them only at meaningful boundaries.

The implementation plan keeps scope, acceptance behavior, and a dependency-aware list of outcomes; it is not a tool ledger. `progress.md` is the current handoff snapshot. Add `requirements.md` only when complex or cross-team semantics need a durable source beyond the request or issue. Create `design.md` only for real trade-offs; material design changes update it. Durable decisions use the repository ADR convention or optional `decisions.md`.

## Re-evaluation

Re-evaluate mode, design, or overlays when:

- the user changes the outcome or scope;
- a new module/root/team makes continuity material;
- evidence disproves a design premise;
- a dependency, migration, destructive action, production system, public contract, or external delivery appears;
- repeated repairs show the reproducer, model, design, environment, or oracle may be wrong.

The first surprising failure triggers a focused assumption/risk recheck. Two failed repairs or hypotheses for the same symptom trigger explicit recalibration before another repair.

Escalation adds the specific missing control. It does not recreate a full governance lifecycle or automatically change direct work into managed work.

## Evidence status

Keep `PASSED`, `FAILED`, `FLAKY`, `BLOCKED`, `NOT RUN`, and `WAIVED` distinct. A later green result does not erase an unresolved earlier cause, and evidence from one OS, device, account, environment, or compatibility direction does not prove another.

Commit, push, PR, tag, release, deploy, migration execution, installation, and external communication are separate actions and authorities.

## Legacy compatibility

Schemas 1.0-2.0, packet validation, archive, and explicit lifecycle commands remain readable for old work. They are not part of this lifecycle. An active legacy pointer never governs 2.0 work.
