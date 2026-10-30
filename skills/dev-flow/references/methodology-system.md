# Bounded assurance-method research

The method pool is an optional reasoning aid. Direct and managed work never record, bind, or validate methods as lifecycle gates. A risk category alone creates no method obligation.

Use normal repository practices or the owning specialist's established procedure when sufficient, then stop. Consult the pool only for a specific unresolved question when an additional method is likely to improve a decision or oracle enough to justify its cost.

Migration, concurrency, FFI, security, persistence, compatibility, or another technical boundary may contain a concrete high-consequence risk. Inspect that risk and verify the affected behavior; these categories do not themselves require method selection, a disposition, or deeper study.

## Bounded study

Choose one directly relevant, lower-cost method for the unresolved question and check its prerequisites honestly. If a prerequisite is unavailable, use a valid native fallback or retain the claim limit instead of broadening research to make a method ready. Use a useful conclusion in its normal owner; it may confirm the existing decision without requiring a new artifact or change. Stop when the question has sufficient evidence, and persist rationale only when a future maintainer needs it.

Method names never authorize actions, decide product meaning, or prove a claim. Missing tools, models, environments, domain experts, users, or live systems are reportable limitations only when they affect the requested claim.

## Ordinary task entry

For explicit method guidance, the integrated public route translates observed signals into the maintained method vocabulary and resolves the methodology source from the installed Skill. Opt in with `--method-signal` or `--method-depth`; risk labels alone do not select methods, and the default method depth is `starter`:

```text
python3 skills/dev-flow/scripts/dev-flow.py route-task \
  --intent design \
  --risk ffi \
  --method-signal multi-version-coexistence \
  --method-prerequisite repository-facts \
  --method-prerequisite requirement-baseline \
  --compact
```

Use only prerequisites actually established in repository or user evidence. The task route feeds back `repository-facts` when at least one valid `--repo-fact key=value` is present and `requirement-baseline` when its understanding contract reports `requirement_baseline_ready`: the business scope is settled, independently of first-implementation confirmation. An unresolved material business choice does not satisfy that baseline. Independent authorized investigation may continue while dependent work waits; no prerequisite grants implementation authority. Other prerequisites remain explicit. Reconsider a selected method only when its relevant facts or prerequisites change. A blocked method permits a valid fallback or an honest claim limit; it is not a reason to broaden research, invent a prerequisite, or load the method catalog.

An explicit method selection accepts canonical signals (`complex-rules`, `conflicting-evidence`, `cross-participant-flow`, `model-evaluation`, `multi-version-coexistence`, `oracle-challenge`, `repeated-failure`, `state-lifecycle`, and `trust-boundary`) plus bounded aliases for common engineering language. It normalizes only the supplied signals; risk labels never add signals. `model-evaluation` is an explicit high-cost signal routed to verification; use an explicit `oracle-challenge` for a concrete weak-oracle question. `data-loss` remains a task-facing risk alias for `persisted-data`.

Task-facing guidance ranks directly matching ready methods separately from blocked fallbacks, preferring lower cost after relevance. It exposes at most three ready methods and two relevant blocked methods; none is a required execution list. When at least one ready method exists, top-level status is `selected`; blocked alternatives remain visible but do not downgrade readiness. Each projection states why/avoid conditions, owner, required facts, cost, expected output, steps, evidence obligation, fallback, and limitation. When change/implementation has no matching method but the observed signal belongs to requirements, diagnosis, design, or verification, the route selects that adjacent owner phase. Review plus oracle challenge prefers a practical ready verification method over a blocked high-cost independent derivation. A valid actionable result contains ready steps or an exact blocked prerequisite and fallback; otherwise it reports `no-actionable-match` and returns control to ordinary engineering judgment. Privacy, persistent-agent-memory, and multi-agent coordination methods remain gated by observed privacy data, an agentic memory store, or actual delegation respectively.

An invalid task-facing signal or risk returns the canonical values, accepted aliases, a nearest suggestion when one exists, and risk-versus-signal guidance. When every invalid value has an unambiguous suggestion, the correction replays the loaded plugin's absolute entrypoint and preserves the original route semantics from any target working directory; otherwise it returns no speculative command. The lower-level maintainer vocabulary remains unchanged.

## Integrated example: status presentation and recovery

This illustrative continuation is not a measured product result. A user asks to hide a persistent “saved; applies next connection” status. The existing card also carries retry and diagnostics actions.

1. **Discover and design.** An example/counterexample separates hiding routine status from removing recovery after apply failure. Inspect existing consumers to find whether equivalent recovery exists. Explain the resulting business behavior and material technical consequences; do not infer acceptance of action removal from the presentation request. Settled business scope permits design, while materially important first implementation still waits for same-scope confirmation or an explicit waiver.
2. **Implement and verify.** Carry the accepted distinction into the card design and its affected tests. Reuse unchanged save/apply evidence. Check the hidden routine status and the actual failure-to-retry/diagnostics path; a cold-start screenshot cannot establish the latter. A negative control that removes the recovery action must fail the protected assertion. Stop when these affected promises have valid evidence, or report the missing recovery observation instead of adding unrelated platform runs.
3. **Preserve and consume.** In the existing requirement owner, link the original request and the accepted presentation-only subset with its reason. If action placement is still unresolved, leave that choice open. If only one platform implements the accepted behavior, show that gap. A later accepted retry-placement change supersedes that clause, not the whole save/apply contract; a binary rollback leaves the accepted requirement in force. The next task follows that owner and uses the recovery distinction in design and assertions, without needing this conversation or a method ID.

## Maintainer CLI

The machine-readable pool is `governance/methodology-pool.json`. The lower-level selector is for pool maintenance or an explicit methodology study, not the ordinary runtime entry:

```text
python3 skills/dev-flow/scripts/dev-flow.py validate-methods
python3 skills/dev-flow-maintainer/scripts/select-methods.py \
  --phase design \
  --intent change \
  --risk public-api \
  --signal multi-version-coexistence \
  --available repository-facts \
  --available representative-examples \
  --depth deep
```

Its `--root` identifies the Dev Flow methodology source repository, never the target product repository. `--method-task-type` can narrow an explicit maintainer study without reviving the 1.x packet CLI. A standalone selection is advisory, ephemeral, and non-persisted. It is not a workstream artifact, approval, checkpoint, or verification result. Persist only a resulting durable design decision, test strategy, or finding when a future maintainer needs it.

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
