# Assurance Method System

This layer answers a different question from Skill routing:

- routing chooses the decision owner;
- method selection chooses a proportionate way to reason about an observed failure class;
- verification decides whether the resulting claim has failure-sensitive evidence.

Method names never authorize actions, decide product meaning, or prove a claim.

## Risk-to-method reasoning chain

Use this chain after `repo-context` and repeat it at every lifecycle/risk/premise change:

1. Record observed facts: phase, task type, canonical risks, failure signals, and genuinely available prerequisites.
2. State the failure mechanism, not just a topic label: identity collapse, feature composition, temporal starvation, abstract-behavior drift, weak oracle, unsafe control, rollout blindness, and so on.
3. Select the smallest method stack that can expose or control that failure.
4. Route each method's artifact to its registered owner. Requirements owns meaning; architecture owns structural models; verification owns oracles/evidence; review owns independent findings; delivery owns release authority.
5. Keep missing prerequisites unresolved. Apply the method's fallback and write `NOT RUN` for any absent tool, model, environment, domain expert, real user, or live system.
6. Close only the claim that the executed artifact and evidence support.

The machine-readable authority is `governance/methodology-pool.json`. Run:

```text
python3 skills/dev-flow/scripts/dev_flow.py validate-methods
python3 skills/dev-flow/scripts/dev_flow.py select-methods \
  --phase design \
  --task-type migration \
  --risk public-api \
  --signal cross-boundary-identity \
  --signal multi-version-coexistence \
  --available repository-facts \
  --available requirement-baseline \
  --available representative-examples \
  --depth deep
```

For a governed schema-2 packet, use the packet-bound command instead of leaving the result in terminal output:

```text
python3 skills/dev-flow/scripts/dev_flow.py record-methods .codex/dev-flow/<change-id> \
  --phase design \
  --signal cross-language-boundary \
  --available repository-facts \
  --available requirement-baseline \
  --available boundary-inventory \
  --available consumer-toolchain \
  --depth deep
```

Packet creation writes a preliminary design selection automatically. It is intentionally insufficient for approval because later repository facts, requirements, design bytes, signals, and prerequisites can change the result. Record a non-preliminary `design` selection before approval, `verification` after entering implementation and before verification, and `review` after entering verification and before acceptance. Each record is event-projected into `method-selection.json`, rendered into `method-selection.md`, bound to requirement/design bytes and the registry digest, and maps every selected owner to an existing packet artifact.

Do not pass a prerequisite because it would produce a nicer answer. `--available` means current evidence demonstrates that prerequisite.

## Depth and context budget

`starter` selects cheap foundations and directly applicable low-cost methods. `deep` adds model-, interaction-, adversarial-, Agent-control-, and evidence-strengthening methods. `formal` permits specialist methods such as Alloy, TLA+, Event-B, semantic mutation, refinement proof, STPA, Cleanroom, N-version programming, symbolic execution, theorem proving, HTN planning, conformal risk control, and contract-net allocation.

Formal depth is not a quality badge. It requires an explicit failure signal, applicable lifecycle phase, prerequisites, and consequences that justify model/proof cost. A low-risk routine task must not select formal methods merely because it is large or unfamiliar.

The default cap is part of the safety contract. If applicable methods exceed it, name the residual failure class before increasing `--max-methods`. Never load all pool entries into working context.

## Reading a selection

`method.selection.v1` contains:

- `reasoning_model`: matched observations and weighted model thresholds;
- `foundation`: the phase's always-needed discipline;
- `stacks`: observation → failure hypothesis → candidate method → evidence obligation;
- `selected_methods`: bounded cards with owner, steps, output, evidence, limitation, fallback, and sources;
- `blocked_methods`: missing prerequisites and safe fallbacks;
- `excluded_methods`: depth, negative-trigger, or context-cap exclusions;
- `unresolved`: conditions that prevent a complete assurance claim.

Standalone and legacy schema-1 selections remain advisory and are recorded in existing design/execution/test artifacts. New governed schema-2 packets advertise the additive `method-selection-v1` capability and fail lifecycle gates when the required phase selection is missing, preliminary, stale, or no longer covers packet risks. Older packets are never upgraded into the contract by mutable metadata alone.

## Novice-use protocol

The human user does not need to name a methodology. Explain each selected method in four sentences:

1. “The likely failure is …”
2. “We will use … because it can expose/control that failure.”
3. “It will produce …, owned by …”
4. “It will not prove …; if prerequisite … is unavailable, we will … instead.”

Use `record-methods` for governed packets. Use `templates/method-selection.md` only for standalone or legacy work that does not carry the packet capability.

## Reselection and stops

Reselect on phase, risk, premise, requirement, architecture, oracle, or verification-failure drift. Do not retain a method simply because work was already invested in it.

Stop the affected slice when:

- the signal requires user-owned semantics;
- a new dependency/tool is necessary but unapproved;
- a formal/safety/privacy/security method lacks qualified/domain ownership;
- external, destructive, delivery, or production action lacks authority;
- the selected oracle cannot distinguish the target defect;
- model-to-code or evidence-to-claim correspondence is unresolved.

## Progressive references

- Discovery and requirements: `methods-discovery-requirements.md`
- Architecture and formal reasoning: `methods-architecture-formal.md`
- Security, privacy, safety, and supply chain: `methods-security-safety.md`
- Implementation and debugging: `methods-implementation-debugging.md`
- Verification, review, and assurance: `methods-verification-assurance.md`
- Delivery, operations, and AI agents: `methods-delivery-agent.md`
- Agent control, safety, memory, coordination, and evaluation: `methods-agent-control-evaluation.md`

Read only the family selected for the active slice.
