# Flow quality metrics

Use metrics to improve the workflow, not to pressure agents into hiding risk or reducing necessary evidence. Record only values available from the packet/tooling; never fabricate token, latency, or cost data.

## Per-change measures

- first-attempt acceptance: whether the first implementation reached verification without a requirement/design correction;
- requirement churn: confirmed AC changes after design approval;
- late clarification: material requirement, instruction, or UX decisions first discovered after their readiness gate;
- ambiguity yield: material `AMB-n` decisions that prevented a plausible wrong implementation, with affected scope and evidence;
- clarification precision: questions judged necessary and answerable after repository investigation; track avoidable questions separately without rewarding silence;
- reopening cost: affected work invalidated after a late ambiguity, separated from unaffected work preserved by scoped reopening;
- instruction health: missed sources, unresolved conflicts, justified exceptions, and final `INS-n` evidence gaps;
- product/UX rework: user overrides or substantial UI direction corrections after UX Ready or implementation;
- collaboration effectiveness: decisions resolved at the intended checkpoint, preventable blocking, and assumption reversals;
- scope drift: conditional activations, design defects, unrelated opportunities rejected, and material expansions requested;
- repair depth: verified blue/red findings and repair rounds;
- evidence health: missing mappings, stale commands, unresolved required cells, waived gates, and leaked resources;
- test stability: first failures, flaky cells, retry count, and environment failures;
- delegation efficiency: children used, accepted/revised/rejected reports, ownership conflicts, and prevented drift;
- delivery lead time and rollback/recovery evidence when actual delivery occurs;
- token, elapsed-time, and cost observations only when the platform exposes them reliably.

## Workflow evaluation

Use representative task contracts and grade the first produced artifact separately from later repaired output. Measure requirement fidelity, evidence quality, scope discipline, forbidden-action avoidance, structural delegation boundaries, total turns/tokens/latency/cost, and final correctness. Keep executor and grader roles separate for live evaluations.

Do not optimize a single proxy. A token reduction that increases missed defects, repair loops, or unverified claims is a regression. More questions, messages, approvals, instruction files, or design artifacts are not evidence of better collaboration. Use deployment-frequency/lead-time/change-failure/recovery measures only for real delivery systems, not for a local code-edit task.
