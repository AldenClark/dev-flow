# Delivery, operations, and AI-agent methods

## Delivery boundary

Planning a canary, rollback, migration, release, or external message is not authority to execute it. Delivery-readiness owns target/authority accounting. Every live, production, account, device, network, or human gate remains `NOT RUN` until actually authorized and observed.

## Progressive delivery selector

| Situation | Method | Required controls |
|---|---|---|
| Frequent integration and merge risk | trunk/small-batch CI | native checks, releasable main, bounded repair |
| Cohortable user exposure | canary | baseline, sensitive health signals, stage/abort/rollback |
| Parallel environments or safe mirroring | blue-green/shadow | parity, side-effect isolation, comparison, cutover/recovery |
| Reliability target | SLO/error budget | user-centered SLI, window/target, action policy |
| Recovery/coordination uncertainty | runbook/game day | scenario safety, telemetry, escalation, reset |
| Material incident learning | blameless postmortem/systems analysis | evidence timeline, controls/interactions, owned verified actions |

Use observability to support decisions: trace requests/causes across boundaries, measure meaningful service/resource signals, and log consequential state/decision context. The USE method asks utilization, saturation, and errors per resource; it does not replace workload or user-centered SLOs.

## AI-agent failure model

AI work adds failure classes beyond ordinary code:

- hidden or stale repository truth;
- context overload or missing progressive references;
- plausible narration without executed evidence;
- authority/tool boundary expansion;
- continuity loss across long runs/compaction/delegation;
- mutable model/tool/Skill identity;
- stochastic variance and repair contamination;
- broken, ambiguous, saturated, or leaked evaluation cases;
- graders that reward proxies rather than business outcomes.
- excessive autonomy for stable work and poor human/agent function allocation;
- partial observability, stale beliefs, and open-loop drift;
- patch overfit against visible tests;
- untrusted context, poisoned/stale cross-scope memory, and prompt injection;
- irreversible or partially committed external side effects;
- unsafe trajectories hidden by a correct final result;
- multi-agent ownership, topology, allocation, and integration failure.

## Agent method selector

| Failure | Method |
|---|---|
| Hidden/stale project knowledge | repository legibility and context engineering |
| Repeated structured omission/action | deterministic agent harness |
| Dangerous or ambiguous mutations/tools | authority and tool-boundary model |
| Long-running continuity/drift | semantic checkpoints |
| Model behavior claim | agent evaluation design plus identity pinning |
| Benchmark trust concern | contamination/case-health analysis |
| Stochastic uncertainty matters | multiple independent first attempts |
| Stable workflow but autonomy is proposed | minimum-effective autonomy |
| Stale/partial observations can change action | belief-state and active information acquisition |
| Long plan in changing state | receding-horizon execution |
| AI patch fits visible tests | counterexample-guided repair |
| Consequential adaptive action | runtime assurance/safety shield plus temporal monitoring |
| Non-atomic external side effects | saga/compensating actions plus action ledger |
| Retrieved content can control tools | instruction/data provenance taint |
| Persistent cross-run/user memory | agent-memory lifecycle governance |
| Human/agent authority handoff | human-agent function allocation |
| Multiple agents proposed | topology/ownership before allocation protocol |
| Final result can hide unsafe process | trajectory/intervention evaluation |

## Deterministic harness protocol

1. Keep semantic judgment with the owning Skill/human.
2. Encode repeatable mechanics and invariants as a bounded tool.
3. Define exact input/output/error schemas, containment, authority, idempotency, and teardown.
4. Test positive, negative, forbidden, invalid, drift, and fallback behavior.
5. Make missing host/tool capability explicit; never simulate success.

## Evaluation protocol

Prefer task-realistic outcomes and deterministic repository graders. Separate executor and grader artifacts. Bind model/tool/prompt/Skill/repository/environment identity. Preserve first attempts; iterative repair is a different measurement. Inspect individual failures, trajectories, side effects, recovery, infrastructure errors, and case health before aggregate scores.

Use multiple first attempts only when variance changes a decision. Predeclare pairing/randomization, unit of analysis, stopping/retry rules, and infrastructure-error handling; retain case-level results and uncertainty. Benchmark scores do not substitute for real acceptance evidence, and evidence that AI was faster or slower on one study does not generalize automatically to this repository/task/user. Conformal/selective-action claims additionally require held-out representative calibration data and explicit distribution assumptions.

## Long-running checkpoints

At semantic boundaries bind objective, requirement/design digests, engineering context, repository identity/HEAD/worktree, active IDs/slice, last evidence, next action, stop condition, and drift disposition. For consequential actions also append attempt, side effect, idempotency, compensation, and outstanding-state records. Resume by revalidating these against current bytes and reconciling incomplete effects. A checkpoint supports continuity; it is not tamper-proof storage, a distributed transaction log, or permission.

Load `methods-agent-control-evaluation.md` when any of autonomy, partial observability, dynamic planning, AI repair, runtime safety, external effects, untrusted context, persistent memory, human oversight, multi-agent coordination, trajectory evaluation, calibration, or simulation is selected.
