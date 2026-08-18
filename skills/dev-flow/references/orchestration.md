# Managed work orchestration

## Choose managed for continuity

Managed work is justified by multi-session duration, multiple independently useful slices, cross-module/repository/team coordination, material trade-offs, or an explicit durable plan/handoff request. Risk alone does not choose the mode.

## Workstream setup

Follow the repository's existing planning or ADR convention. Otherwise use `docs/workstreams/<slug>/` with `implementation.md` and `progress.md`. Add `requirements.md` only for complex or cross-team semantics that lack another durable source, `design.md` only for real trade-offs, and `decisions.md` only for durable decisions without an ADR home.

The documents must live in the repository that owns the business change. Do not put the authoritative copy in `.codex`, a user profile, or an ignored runtime directory.

These files are a shared human-agent control surface. A user should be able to read the outcome, slice order, current position, next step, blockers, and evidence limits without understanding Dev Flow internals.

## Plan slices

Each slice should produce a coherent business or technical outcome that can be reviewed and verified independently. Record:

- outcome and affected areas;
- real predecessors or external dependencies;
- the native evidence that will show completion;
- current status and any genuine blocker.

Avoid file-by-file task inventories, time-based activity logs, method records, generated IDs, fingerprints, and repeated scope restatement.

## Run and update

At start or resume:

1. read current implementation, progress, any design/decision records, and relevant repository facts;
2. verify current Git root, branch/HEAD, worktree, changed paths, and user work;
3. reconcile meaningful drift in the documents with one concise update;
4. continue the smallest ready slice.

Update progress only after a coherent slice, design/scope change, blocker, handoff, or closure. Replace stale current-state text; rely on Git for event history.

Run the zero-artifact quality calibration at initial planning and after the re-evaluation triggers in `quality-calibration.md`. Put only durable results into the workstream: a changed design, changed slice plan, material blocker, or decision. Do not record the calibration itself.

## Collaboration

Delegate only isolated work with a credible net benefit. For every actual child dispatch, resolve the role/workload through `route-agent` and use the returned model, reasoning effort, and fork request. Do not persist the route. Briefs contain objective/outcome, context, owned paths/read-only boundary, allowed checks/resources, stop conditions, and the expected return. The root owns integration, conflict resolution, current-diff review, and affected verification.

Parallel workers must have disjoint writes or isolated worktrees. Do not use agent count, profile depth, report count, or concurrency as progress metrics.

## Close

Closure requires the requested scope implemented or explicitly deferred, native evidence run against final bytes, final diff/scope inspection, documents updated to current truth, and residual gates reported honestly. No packet transition or generated closeout artifact is required.
