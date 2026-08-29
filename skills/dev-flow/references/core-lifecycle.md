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

## Incremental route continuity

The caller may retain one full RC.4 route result in active context. When outcome, roots, discovery mode, authority/mutation boundary, risks, needs, method prerequisites, repository facts, review requirement, and terminal condition are unchanged, continue without another route call. Dev Flow does not write, discover, or cache that result.

After a material fact changes, pass the caller-owned prior JSON with `route-task --previous-route <file>`. The returned route is always a complete current route; `recalibration` states whether the prior basis was unchanged, changed with bounded invalidated decision classes, or incompatible. A malformed, oversized, symlinked, or semantically incompatible prior route never grants reuse: continue from the full current route and retain the reported comparison limitation. Do not treat formatting-only changes or repeated narration as a material transition.

## Managed contract check

Workstreams carrying `<!-- dev-flow-workstream-contract: v1 -->` opt into structural checking. Before completing a slice and before a terminal claim, run:

```text
python3 <dev-flow-skill-dir>/scripts/dev-flow.py check-workstream \
  --root <git-root> --path <workstream-directory> --check-worktree
```

The checker may reject contradictory state, gates, convergence disposition, unsafe prefixes, or undeclared changed paths. Its claim is `structural-consistency-only`: it never edits files, infers authorship, proves semantics/evidence freshness, or authorizes delivery. Older unmarked workstreams remain readable and are not silently migrated.

## Evidence status

Keep `PASSED`, `FAILED`, `FLAKY`, `BLOCKED`, `NOT RUN`, and `WAIVED` distinct. A later green result does not erase an unresolved earlier cause, and evidence from one OS, device, account, environment, or compatibility direction does not prove another.

Commit, push, PR, tag, release, deploy, migration execution, installation, and external communication are separate actions and authorities.

## 1.x boundary

2.0 has no 1.x state, command, migration, upgrade, or rollback compatibility contract. An old pointer never governs 2.0 work. Do not load or operate residual packet internals during a 2.0 task.
