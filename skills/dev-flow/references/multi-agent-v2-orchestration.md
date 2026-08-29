# Multi-agent orchestration

Use one agent by default. Delegate when parallel isolation or a clean independent review is likely to save more time or improve evidence than coordination will cost.

Before every actual child dispatch, resolve the task-relative route with `route-agent` using the intended role, workload, observed engineering risks, and reasoning signals. Use the returned model, reasoning effort, and fork request. Do not create a routing receipt, add the profile to a workstream, or treat a high profile as proof of quality.

Delegation exists only after a successful dispatch returns a non-empty child identity. Never wait or poll before that identity exists. An empty receiver list or empty agent state is not delegation; self-execution, rereading, or an inferred answer cannot substitute for a child result. Report the branch as unavailable or downgraded and never attribute a result to a child.

If routing shows that a child needs broad/high-cost context but the work is not independently useful, keep it in the root context instead of delegating.

## Brief

Every delegated task states:

1. objective and expected outcome;
2. relevant business/repository context;
3. owned paths or an explicit read-only boundary;
4. allowed verification and resource limits;
5. stop conditions, including scope/dependency/destructive/external boundaries;
6. expected return: changed paths or findings, checks, limits, and recommended disposition.

Every child boundary is a subset of the parent envelope. Carry the intersection of all ancestor outcome, read/write, tool, dependency, external-action, resource, and re-delegation limits into nested work. A child may narrow its own work but cannot restore authority removed by an ancestor, promote an optional finding, add a platform/repository/dependency, reinterpret product semantics, or expand a public contract. When the subset is insufficient, stop the affected branch and return a bounded expansion request or finding to the root.

The root must not execute that expansion merely because the child requested it. Continue beyond the original envelope only after explicit renewed authority from the user or already-admitted owner for the exact added repository, path, dependency, platform, external action, or semantic scope; otherwise narrow, defer, or block the branch.

Do not require packet IDs, AC/SC/VO mappings, context fingerprints, generated reports, profile IDs, lease epochs, or copied parent history unless a repository-native system genuinely consumes them.

## Isolation and integration

- Shared writers need disjoint paths; otherwise use isolated worktrees or serialize.
- One owner controls each external resource, database, device, port, or generated output at a time.
- The root reconciles returned work against the current Git state, inspects the actual diff, resolves conflicts, and reruns affected checks.
- The root verifies actual returned writes, dependencies, generated surfaces, tools, resources, and evidence against the delegated subset; a compliant report never overrides an out-of-scope diff.
- When a parent boundary narrows or changes, update or cancel affected descendants before accepting their work. Use host-enforced path/tool/resource boundaries when available, but do not claim enforcement when only guidance exists.
- A child final is a report, not proof that integration or repository-wide behavior passed.
- Stop or narrow delegation when coordination, rework, conflicts, or context cost exceed accepted progress.

Independent review should receive the objective, relevant contracts, frozen diff/scope, and raw evidence, without the implementer's conclusion. Findings must be rechecked in current source before repair.
