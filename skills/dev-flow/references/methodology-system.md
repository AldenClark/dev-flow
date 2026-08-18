# Bounded assurance-method research

The method pool is an advisory reasoning aid. Direct and managed work never record, bind, or validate methods as lifecycle gates, but high-leverage risk signals should actively prompt a bounded method check when the owning specialist does not already provide a clear procedure.

Use normal repository practices and the owning specialist Skill first. At a strong signal below, actively match a method: use the specialist's established procedure when sufficient, otherwise query this pool when naming a method is likely to change the analysis, design, experiment, or oracle enough to justify its context and maintenance cost.

Strong signals are migration or mixed-version data, FFI/ABI/unsafe ownership, concurrency or nondeterminism, security/privacy/authorization, public API or protocol compatibility, irreversible/data-loss exposure, conflicting evidence, oracle challenge, repeated failed hypotheses, interacting business rules, or state/cross-participant requirement flows. A signal requires a bounded method disposition, not necessarily a CLI call or record, when the established specialist method is already clear.

## Bounded study

1. State the observed facts and the specific failure mechanism, not a broad topic label.
2. Identify the decision or evidence that a method could improve.
3. Check prerequisites honestly and select the smallest useful method or stack.
4. Select at most one-to-three methods and apply only the bounded steps that can change the decision; route resulting design, test, or finding to its normal repository owner.
5. Record a durable result only when a future maintainer needs the rationale. Do not persist a selection merely to prove the tool was used.
6. Stop using the method when it is not producing decision value.

Method names never authorize actions, decide product meaning, or prove a claim. Missing tools, models, environments, domain experts, users, or live systems remain explicit limitations.

## Ordinary task entry

Ordinary Dev Flow tasks use the integrated public route, which translates observed task signals into the maintained method vocabulary and resolves the methodology source from the installed Skill:

```text
python3 skills/dev-flow/scripts/dev-flow.py route-task \
  --intent design \
  --risk ffi \
  --method-signal multi-version-coexistence \
  --method-prerequisite repository-facts \
  --method-prerequisite requirement-baseline \
  --compact
```

Use only prerequisites actually established in repository or user evidence. One bounded selection is enough for the current decision. A blocked method means use its fallback or state the limitation; it is not a reason to broaden research or load the method catalog.

## Maintainer CLI

The machine-readable pool is `governance/methodology-pool.json`. The lower-level selector is for pool maintenance or an explicit methodology study, not the ordinary runtime entry:

```text
python3 skills/dev-flow/scripts/dev_flow.py validate-methods
python3 skills/dev-flow/scripts/dev_flow.py select-methods \
  --phase design \
  --intent change \
  --risk public-api \
  --signal multi-version-coexistence \
  --available repository-facts \
  --available representative-examples \
  --depth deep
```

Its `--root` identifies the Dev Flow methodology source repository, never the target product repository. A standalone selection is advisory, ephemeral, and non-persisted. It is not a workstream artifact, approval, checkpoint, or verification result. Persist only a resulting durable design decision, test strategy, or finding when a future maintainer needs it.

`record-methods` remains only for explicit maintenance of an existing legacy packet whose schema already requires that record. Do not invoke it for 2.0 direct or managed work.

## Depth and context

`starter` covers low-cost foundations. `deep` admits additional model, interaction, adversarial, and evidence-strengthening methods. `formal` admits specialist formal or safety methods only when the concrete failure mechanism, prerequisites, and consequences justify the cost.

Formal depth is not a quality badge. Never load the full pool into working context. If the bounded result is not better than ordinary specialist reasoning, stop and use the simpler path.

## Reading a selection

`method.selection.v1` reports:

- matched observations and failure hypotheses;
- selected methods and their owners, limits, prerequisites, and evidence obligations;
- blocked methods and safe fallbacks;
- exclusions caused by depth, negative triggers, or the context cap;
- unresolved conditions that limit the claim.

Treat this output as research guidance. The actual code, design decision, test, review finding, or release evidence remains authoritative.

## Legacy compatibility

Legacy packet schemas and explicit CLI commands remain readable and validatable. Their historical phase-selection, event projection, digest binding, and approval rules apply only when a user deliberately operates that packet. They never activate from 2.0 routing, workstream documents, Hooks, or ordinary Skill use.

## Progressive references

Read only the family relevant to the explicit study:

- Discovery and requirements: `methods-discovery-requirements.md`
- Architecture and formal reasoning: `methods-architecture-formal.md`
- Security, privacy, safety, and supply chain: `methods-security-safety.md`
- Implementation and debugging: `methods-implementation-debugging.md`
- Verification, review, and assurance: `methods-verification-assurance.md`
- Delivery, operations, and AI agents: `methods-delivery-agent.md`
- Agent control, safety, memory, coordination, and evaluation: `methods-agent-control-evaluation.md`
