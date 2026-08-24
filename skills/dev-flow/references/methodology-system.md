# Bounded assurance-method research

The method pool is an advisory reasoning aid. Direct and managed work never record, bind, or validate methods as lifecycle gates, but high-leverage risk signals should actively prompt a bounded method check when the owning specialist does not already provide a clear procedure.

Use normal repository practices and the owning specialist Skill first. At a strong signal below, actively match a method: use the specialist's established procedure when sufficient, otherwise query this pool when naming a method is likely to change the analysis, design, experiment, or oracle enough to justify its context and maintenance cost.

Strong signals are migration or mixed-version data, FFI/ABI/unsafe ownership, concurrency or nondeterminism, security/privacy/authorization, public API or protocol compatibility, irreversible/data-loss exposure, conflicting evidence, oracle challenge, repeated failed hypotheses, interacting business rules, or state/cross-participant requirement flows. A signal requires a bounded method disposition, not necessarily a CLI call or record, when the established specialist method is already clear.

## Bounded study

1. State the observed facts and the specific failure mechanism, not a broad topic label.
2. Identify the decision or evidence that a method could improve.
3. Check prerequisites honestly and prefer one ready, directly relevant, lower-cost method; use up to three only for distinct failure mechanisms with separate evidence obligations.
4. Choose an explicit disposition: execute a ready method, execute the maintained fallback while retaining a blocked limitation, or abstain because the owning specialist already provides the sufficient procedure.
5. Realize the disposition in a normal owner surface—a test/property/mutation, counterexample, state/decision/compatibility model, review attack surface, evidence matrix, or explicit claim limitation. A selected ID or method mention is not completion.
6. Record a durable result only when a future maintainer needs the rationale. Do not persist a selection merely to prove the tool was used.
7. Stop using the method when it is not producing decision value.

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

Use only prerequisites actually established in repository or user evidence. The task route feeds back `repository-facts` when at least one valid `--repo-fact key=value` is present and `requirement-baseline` when the route's own understanding contract permits design; an unconfirmed U1 does not satisfy that baseline. Other prerequisites remain explicit. Recheck readiness after discovery, material requirement confirmation, an oracle-breaking failure, repeated non-progress, or the material verification/review boundary; unchanged facts do not justify another selection. A blocked method means use its fallback or state the limitation; it is not a reason to broaden research, invent a prerequisite, or load the method catalog.

The task-facing route accepts canonical signals (`complex-rules`, `conflicting-evidence`, `cross-participant-flow`, `model-evaluation`, `multi-version-coexistence`, `oracle-challenge`, `repeated-failure`, `state-lifecycle`, and `trust-boundary`) plus bounded aliases for common engineering language. It normalizes aliases to canonical output and supplements them with any uncovered foundational signal derived from observed risks such as concurrency/ordering/recovery, distributed state, migration/version coexistence/rollback, trust boundaries, persisted-data lifecycle, or weak-test/oracle exposure. An explicit but partial signal therefore cannot suppress a distinct risk family. `model-evaluation` is an explicit high-cost signal routed to verification; `weak-tests` alone derives the lower-cost `oracle-challenge`. `data-loss` is accepted as a task-facing risk alias for `persisted-data`.

Task-facing guidance ranks directly matching ready methods separately from blocked fallbacks, preferring lower cost after relevance. It exposes at most three ready methods and two relevant blocked methods, so a missing prerequisite cannot consume the ready-guidance budget. When at least one ready method exists, top-level status is `selected`; blocked alternatives remain visible but do not downgrade readiness. Each projection states why/avoid conditions, owner, required facts, cost, expected output, steps, evidence obligation, fallback, and limitation. When change/implementation has no matching method but the observed signal belongs to requirements, diagnosis, design, or verification, the route selects that adjacent owner phase instead of returning an empty implementation result. Review plus oracle challenge prefers a practical ready verification method over a blocked high-cost independent derivation. A valid actionable result contains ready steps or an exact blocked prerequisite and fallback; otherwise it reports `no-actionable-match` and returns control to the owning specialist. Privacy, persistent-agent-memory, and multi-agent coordination methods remain gated by observed privacy data, an agentic memory store, or actual delegation respectively.

An invalid task-facing signal or risk returns the canonical values, accepted aliases, a nearest suggestion when one exists, and risk-versus-signal guidance. When every invalid value has an unambiguous suggestion, the correction replays the loaded plugin's absolute entrypoint and preserves the original route semantics from any target working directory; otherwise it returns no speculative command. The lower-level maintainer vocabulary remains unchanged.

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

`record-methods` is unsupported 1.x residue. Do not invoke it for 2.0 direct or managed work.

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

## 1.x boundary

Historical packet records and method ledgers are unsupported in 2.0. Do not route to or validate them from 2.0 work. Residual implementation code does not create a compatibility promise.

## Progressive references

Read only the family relevant to the explicit study:

- Discovery and requirements: `methods-discovery-requirements.md`
- Architecture and formal reasoning: `methods-architecture-formal.md`
- Security, privacy, safety, and supply chain: `methods-security-safety.md`
- Implementation and debugging: `methods-implementation-debugging.md`
- Verification, review, and assurance: `methods-verification-assurance.md`
- Delivery, operations, and AI agents: `methods-delivery-agent.md`
- Agent control, safety, memory, coordination, and evaluation: `methods-agent-control-evaluation.md`
