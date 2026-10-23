# Dev Flow 2.0 adaptive development loop

## Three evidence planes

1. Business continuity: repository-tracked implementation/progress and conditional requirements/design/material decisions for managed work.
2. Engineering evidence: code, Git, tests, builds, CI, runtime observation, and artifact provenance.
3. Safety boundary: host permissions and explicit authority for destructive, irreversible, or external actions, plus the independent data-security Hook on its supported confidentiality surfaces.

Keep ownership separate. A document does not prove runtime behavior; a test does not choose product meaning; a local result does not authorize delivery.

## Development spine

Establish the observable outcome, current repository facts, assumptions, affected boundaries, smallest coherent slice, native oracle, and delivery limits. Scan for risks visible in code and dependencies, not only risks named by the request. This creates no file or approval state.

For substantial managed work, material risk, delegation, or repeated failure, use `quality-calibration.md` to decide whether a specialist Skill, P0-P6 child route, bounded assurance method, or independent review has positive decision value.

Classify requirement understanding for the next decision. Distinguish business choices from technical unknowns: ask proactively for the former and investigate the latter. Settled business meaning permits technical design. Before an important new feature's first implementation, synthesize the business scenarios, UI, rules, states and exceptions with material technical effects (fields, thresholds, conditions, algorithms, dependencies, data paths, compatibility and risk), then obtain explicit whole acceptance or an explicit waiver. Undecided technical choices remain visible. Reuse accepted same-scope understanding; a partial answer only settles its subset and silence never confirms. Unresolved material business choices or explicit review-first requests pause dependent work; independent authorized investigation and reversible probes may continue. Established defects use proven expected/protected behavior; mechanical and read-only work acquire no confirmation ceremony. `requirements-design` owns details.

A method matters when its counterexample, causal finding, state distinction, or alternative changes a downstream design, oracle, or acceptance claim. Pass that conclusion and its limitations through existing owners and child briefs; do not repeat the study or create a method ledger. For simplification, retain the user's net-benefit objective through implementation and review; an incidental reliability finding becomes a prerequisite only if it blocks the requested outcome.

Load a specialist, method, independent reviewer, or child model only when it can change a real decision or evidence surface. Reconsider only the affected owner when evidence changes; ordinary continuation does not repeat routing.

## Direct path

1. Resolve objective, authority, roots, instructions, current behavior, scope, and user changes.
2. Clarify material business choices and investigate technical unknowns. For an important new feature, design within settled scope and confirm the combined understanding once before first implementation. Reuse prior same-scope acceptance.
3. Reproduce a defect before repair when practical.
4. Implement one coherent slice.
5. Run the narrowest sensitive oracle, then affected broader checks.
6. Reconcile the goal, source/contract, final diff, last sensitive oracle, and unrun environments before reporting the exact outcome.

Direct work has no Dev Flow continuity artifact or lifecycle transition. It still updates the canonical repository owner when architecture, contracts, runbooks, product behavior, testing strategy, or operational truth changes. Create a new owner only when none exists. Add a minimal change note only when cross-session, cross-owner, or independently sliced continuation cannot be carried by those owners; do not duplicate code, tests, issues, changelogs, ADRs, or maintained docs.

## Managed path

Use when continuity or coordination exceeds one coherent slice and existing canonical owners cannot carry current progress. Read the repository's current workstream documents at start/resume, verify their assumptions against current Git/repository facts, and update them only at meaningful boundaries.

The implementation plan keeps scope, acceptance behavior, and a dependency-aware list of outcomes; it is not a tool ledger. `progress.md` is the current handoff snapshot. Add `requirements.md` only when complex or cross-team semantics need a durable source beyond the request or issue. Create `design.md` only for real trade-offs; material design changes update it. Durable decisions use the repository ADR convention or optional `decisions.md`.

## Re-evaluation

Re-evaluate mode, design, or overlays when:

- the user changes the outcome or scope;
- a new module/root/team makes continuity material;
- evidence disproves a design premise;
- a dependency, migration, destructive action, production system, public contract, or external delivery appears;
- repeated repairs show the reproducer, model, design, environment, or oracle may be wrong.

The first surprising failure triggers a focused assumption/risk recheck. Two failed repairs or hypotheses for the same symptom trigger explicit recalibration before another repair.

On a user correction or a fact that changes meaning, identify the invalid assumption and trace its consumers in design, code/data, tests/oracles, children, and external actions. Pause or update affected work, invalidate dependent evidence, and preserve unaffected results. Changing only a summary does not repair old implementation or test expectations. Update or cancel affected children through an actually available host control; inspect late child output and actual writes against current semantics before integration. Steering does not automatically cancel tools, and already-executed effects are not automatically undone: report them and use only authorized recovery. Reverify the revised user example and a counterexample on current bytes.

After an interrupted Code Mode call, inspect actual process identity, partial writes and external state before replay. Active cells and nested tools may have terminated while retained store values remain; those values are recovery hints, not evidence that a new attempt completed. Cancellation does not roll back external effects. Reconcile late child results once against the current scope and user interruption; host wakeups cannot cross Plan or child-session boundaries.

At resume or handoff, retain user constraints, repository facts, bounded assumptions, and rejected alternatives distinctly; reread their existing owners and relevant original constraints. A restatement or compaction alone does not invalidate evidence. At closure, compare the current user goal with authoritative source/contract, final changed bytes, last applicable oracle, and the environments actually observed; report the narrowest supported claim. Do not replace the intended product outcome with an easier substitute when a technical gate is blocked.

Escalation adds the specific missing control. It does not recreate a full governance lifecycle or automatically change direct work into managed work.

## Incremental route continuity

The caller may retain one full route result in active context. `route-task` is a stateless diagnostic: confirmation flags are caller reports, not verified consent or permission. `design_allowed` concerns settled business scope; `implementation_allowed` separately reports the first-implementation checkpoint. Compact output preserves this distinction. A semantic-version change invalidates old route reuse; recompute without adding a persistent approval record. When outcome, roots, discovery mode, authority/mutation boundary, risks, needs, method prerequisites, repository facts, review requirement, and terminal condition are unchanged, continue without another route call. Dev Flow does not write, discover, or cache that result.

After a material fact changes, pass the caller-owned prior JSON with `route-task --previous-route <file>`. The returned route is always a complete current route; `recalibration` states whether the prior basis was unchanged, changed with bounded invalidated decision classes, or incompatible. A malformed, oversized, symlinked, or semantically incompatible prior route never grants reuse: continue from the full current route and retain the reported comparison limitation. Do not treat formatting-only changes or repeated narration as a material transition.

For result reuse, an optional opaque `--target-revision` binds the confirmed objective and scope epoch, including protected paths and authority. Increment it after a material correction; never pass raw task text or secrets. Without it, an unchanged route only permits `reconcile-objective-before-retain`, not automatic child-result reuse. New methods or review obligations invalidate prior terminal evidence.

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
