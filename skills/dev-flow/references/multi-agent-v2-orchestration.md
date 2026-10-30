# Multi-agent orchestration

Use one agent by default. Delegate only an independently useful unit when parallel isolation or a clean independent review is likely to save more time or improve evidence than coordination will cost. A long sequential chain, high tool-call density, or large context does not by itself justify more agents; coupled steps remain with one owner unless a safe interface makes them genuinely separable.

Starting a child, allowing a child to start another child inside the inherited envelope, and dispatching a clean-context reviewer are internal work allocation and need no separate user authorization. Real actions and scope expansion keep their own authority requirements.

Routine same-model delegation can dispatch directly within available capacity and inherited limits. Use `route-agent` when a real model/effort choice or host-capability uncertainty matters, and reuse its advice while that basis remains unchanged. When using a route, respect the returned model, effort, fork request, and dispatch limits. Do not create routing receipts or treat a profile as proof of quality.

Consult [model-selection.md](model-selection.md) when choosing a different profile. Do not inherit the parent's hardest signals or explicitly raise P5/P6 without a concrete `--selection-reason`. This caller explanation is not user approval. Do not split work or spawn solely to change a model label.

Delegation starts only after a successful dispatch returns a valid, non-empty child identity. Before that identity is obtained, never wait for that child or poll its status. A failed creation, missing identity or uncertain response does not establish a started task: reconcile the actual dispatch/host state under the existing failure/recovery rules before any wait or retry, preserving the original failure. Empty receiver lists or agent state are not delegation; never attribute a result to a child that was not started, or substitute self-execution for child evidence. Report unavailable branches honestly. Prefer completion, failure or attention notifications. When waiting is necessary, bound it by the next actual deadline rather than a fixed short polling interval; shorten it when needed and interrupt at the deadline. Combine time and budget reads with dispatch/completion records instead of separate clock-only round trips.

When the next work and boundaries are settled but parent context is costly, continue with a compact working context: objective, accepted decisions, unresolved choices, authority and revocations, scope, remaining budget, live children and canonical evidence paths. Retrieve older material when it changes the next decision. Reuse existing continuity owners; do not create another summary artifact or coordinator merely to carry history.

`parallel_units` is the total independent work to process, not simultaneous admission. Active width intersects observed host limits/remaining slots, user budget, independent ready ownership and integration capacity. Unknown capacity calls for bounded dispatch and observation, not an unlimited pool. Preflight caller inputs and legacy advisory fields are neither verified host inventory nor slot reservations; batch work when its total exceeds available simultaneous capacity.

## Brief

Give the child enough context to work independently: the outcome, relevant constraints, owned paths or read-only boundary, resource/action limits, stopping point, and useful return shape. Include a prior method conclusion only when it affects this work. A short brief is sufficient for a small task; no fixed report or method checklist is required.

Every child boundary is a subset of the parent envelope. Carry the intersection of all ancestor outcome, read/write, tool, dependency, external-action, resource, and re-delegation limits into nested work. A child may narrow its own work but cannot restore authority removed by an ancestor, promote an optional finding, add a platform/repository/dependency, reinterpret product semantics, or expand a public contract. When the subset is insufficient, stop the affected branch and return a bounded expansion request or finding to the root.

The root must not execute that expansion merely because the child requested it. An admitted owner may allocate work only inside authority already granted by the user and retained by every ancestor envelope; owner admission never creates authority. Continue beyond the original envelope only after exact renewed user authority for the added repository, path, dependency, platform, external action, destructive action, or semantic scope; otherwise narrow, defer, or block the branch.

Do not require packet IDs, AC/SC/VO mappings, context fingerprints, generated reports, profile IDs, lease epochs, or copied parent history unless a repository-native system genuinely consumes them.

## Isolation and integration

- Shared writers need disjoint paths; otherwise use isolated worktrees or serialize.
- One owner controls each external resource, database, device, port, or generated output at a time.
- Before integrating child changes, inspect the actual diff against its delegated scope, resolve conflicts, and recheck only affected evidence. Verify read-only findings against the source needed for the decision. A child report never overrides an out-of-scope diff or proves integration passed.
- When a parent boundary narrows or changes, update or cancel affected descendants before accepting their work. Use host-enforced path/tool/resource boundaries when available, but do not claim enforcement when only guidance exists.
- An interrupt is not rollback: inspect actual child writes and external effects before resuming or retrying. Aborted cells and retained session values do not establish a fresh successful attempt; keep cancelled, incomplete, and unknown outcomes separate from passed checks.
- A child result belongs to the objective, slice, paths, oracle, and resource owner in its brief. After user steering, late output from an old brief is evidence to inspect, never a current-scope integration instruction; rebase the relevant child or reject that result. Unchanged children may continue.
- Report changed readiness, relevant failures, resource boundaries, and required user action. Report usage when requested or when it affects a resource decision; reuse existing evidence instead of rescanning completed tasks. Preserve first failures and leave unobserved amounts unknown.
- Stop or narrow delegation when coordination, rework, conflicts, or context cost exceed accepted progress.

Independent review should receive the objective and ranking criteria, relevant contracts, current bound diff/scope, prior method evidence and affected assumptions, and raw evidence, without the implementer's verdict. For simplification, preserve the mechanism cost/benefit question and necessary versus negotiable guarantees; do not turn incidental bugs into prerequisites without a demonstrated blocker. Findings and late results must be rechecked against current scope, source, and actual writes before repair or integration.
