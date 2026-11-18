# Task-relative model selection

Default to GPT-6.2 Sol medium for ordinary engineering. Delegate when the independent unit saves more context or coordination than it costs. Use the child's actual workload to choose effort and preserve the task's verification obligations.

| Profile | Model / effort | Current task |
|---|---|---|
| P0 | GPT-6.2 Sol low | Exact symbol lookup, fixed build/test command, log filtering |
| P1 | GPT-6.2 Sol medium | Narrow research, bounded log classification, specified mechanical edit |
| P2 | GPT-6.2 Sol high | Confirmed bounded fix/feature slice, directed mapping with a known oracle |
| P3 | GPT-6.2 Sol xhigh | Large context or many steps with closed semantics |
| P4 | GPT-6.2 Sol medium | Ordinary coding, diagnosis, independent review, cross-component integration, adaptive native verification |
| P5 | GPT-6.2 Sol xhigh | Deep unresolved causes, genuinely conflicting oracles, interacting open contract/high-consequence decisions |
| P6 | GPT-6.2 Astra xhigh | Deep unresolved reasoning + interacting unknowns + cross-boundary impact; or documented current-Sol failure + deep unresolved reasoning |
| PX | GPT-6.2 Astra max | Explicit exceptional evaluation/campaign inside its separately authorized scope |

Exact commands use `exact-verification`. Adaptive native UI or device checks use `adaptive-verification`. Ordinary and high-risk reviews start at P4 and retain their applicable controls.

## When to increase depth

Use observed facts and the decision they block. One doubtful oracle, conflicting observation, or nondeterministic result starts at P4. P5 applies to a concrete deep unresolved cause, a documented GPT-6.2 Sol reasoning failure, conflicting evidence that disputes the oracle, or interacting unknowns in an open contract or high-consequence decision. A tool, fixture, or environment failure calls for diagnosis of that failure.

P6 applies to deep unresolved work with interacting unknowns and cross-boundary impact, or deep unresolved work after a documented GPT-6.2 Sol reasoning failure. P0–P6 form a policy order. P1/P4 and P3/P5 share model and effort while serving different workloads.

## Dispatch

Reuse a supported parent GPT-6.2 Sol or Astra pair when it fits. Otherwise, use `route-agent` with the actual host inventory:

```text
python3 skills/dev-flow/scripts/dev-flow.py route-agent --role <role> --workload <workload> \
  --host-capability <model:effort>
```

Include relevant observed signals when they change the route. Above-policy P5/P6 requires a concrete `--selection-reason`. Use `--acknowledge-downgrade` for below-policy requests and `--acknowledge-exception` for PX within an independently authorized scope.

A capability limit stops the requested dispatch. A suggested pair requires an explicit follow-up choice. Reuse the route for an unchanged continuation and reassess a materially different child brief. The router provides advice for child dispatch. Select the root model through the host.

Report the policy requirement, host availability, and observed outcome separately. Local routing checks cover policy and caller-reported host inventory. Task quality and cost require separate live comparisons.
