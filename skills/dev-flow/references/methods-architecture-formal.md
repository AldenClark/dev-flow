# Architecture and formal methods

Choose the representation from the failure mechanism. “Complex system” is not a sufficient formal-method trigger.

## Representation selector

| Dominant question | Representation | Typical method |
|---|---|---|
| Which objects/relations/configurations can coexist? | Relational sets and constraints | Alloy |
| Which event sequences/interleavings preserve safety and progress? | Temporal transition system | TLA+/PlusCal |
| How can an abstract invariant-bearing system gain concrete detail? | Stepwise refinement and proof obligations | Event-B |
| Does a concrete implementation preserve abstract observations? | Abstraction function and simulation relation | Refinement mapping |
| Can concurrent workflows deadlock or violate token/resource conservation? | Places, transitions, tokens, reachability | Petri/process model |
| Does a stable high-value theorem hold under explicit axioms? | Interactive proof | Theorem proving |
| Which architecture tradeoffs/sensitivity points threaten qualities? | Quality scenarios and utility tree | ATAM-style analysis |
| Do stakeholder views describe one coherent system? | Viewpoints, concerns, and correspondence rules | Architecture viewpoint consistency |
| Does source structure still implement the intended architecture? | Intended/actual relation mapping | Reflexion and conformance analysis |
| Do participants/messages/timers/compensation form one valid workflow? | Collaboration process and token/message traces | BPMN collaboration model |
| Is business data fit and reconcilable for its intended use? | Quality scenarios, invariants, thresholds, source-of-truth rules | Data quality scenario/reconciliation |
| Which architecture investment returns the most stakeholder value under cost/schedule uncertainty? | Quality benefit, cost, uncertainty, and sensitivity | CBAM-style analysis |
| Do both sides of a language/runtime boundary agree? | Symbol/layout/ownership/error/threading/packaging matrix | Cross-language ABI contract |

## Architecture decision protocol

1. Bind the requirement revision and repository/current behavior.
2. Name the decision owner and the forces that make it material.
3. Compare credible alternatives, including “extend existing owner” and “do nothing/defer.”
4. Model state, data, errors, concurrency, cancellation, limits, lifecycle, observability, and cleanup.
5. Bind protected behavior, compatibility directions, rollback, and verification.
6. Record facts that would invalidate the decision.

Use `change-impact-graph`, `bounded-context-context-map`, `data-lineage-provenance`, and `information-hiding-modularity` before inventing a cross-cutting abstraction.

## ATAM-style lightweight protocol

Create 6–12 concrete quality scenarios, prioritize consequence and likelihood qualitatively, then inspect each candidate design for:

- sensitivity points: one decision strongly changes a quality response;
- tradeoff points: one decision improves one quality and degrades another;
- risks: an important scenario is unsupported or unvalidated;
- non-risks: the architecture already supports a scenario with evidence;
- risk themes: several risks share a root boundary/assumption.

The output is a validation plan, not an architecture score.

## Multi-view and implementation-conformance protocol

Use architecture viewpoint consistency when different diagrams or models share elements but answer different stakeholder concerns. Name each stakeholder, concern, viewpoint, model kind, and correspondence rule; then classify missing or contradictory relations before design approval. Do not create views for presentation volume: one coherent decision record remains the fallback for a small boundary.

Use architecture reflexion only after an intended architecture and a reviewable source-to-architecture mapping exist. Freeze intended relations, extract actual source relations, and classify convergence, divergence, and absence. A divergence is either a design defect or an explicit architecture revision; it must not become an undocumented exception. Static source relations do not prove dynamic/runtime conformance.

## Collaboration workflow protocol

Use BPMN when correctness crosses business participants or systems and depends on messages, events, gateways, correlation, timers, errors, cancellation, or compensation. Walk nominal, timeout, duplicate, out-of-order, cancellation, compensation-failure, and terminal-state traces. Map each participant and message to repository ownership and a test observation point. Prefer a state-transition model and participant/message table when the process is local and simple.

## Data quality and architecture investment

For material data flows, turn accuracy, completeness, consistency, credibility, currentness, uniqueness, and traceability into context-specific measurable scenarios. Bind source of truth, matching tolerance, reconciliation, exception ownership, and before/after evidence. Standards supply characteristics; domain owners decide acceptable thresholds.

Use cost-benefit architecture analysis only when finite budget/schedule must choose among credible strategies. Compare stakeholder-valued quality benefit, implementation cost, schedule, uncertainty, and sensitivity without collapsing them into a magic score. If estimates are not credible, fall back to qualitative ATAM tradeoffs and keep cost evidence unresolved.

## Cross-language ABI worksheet

For every FFI/ABI boundary record symbols, calling convention, type representation/alignment, allocation and ownership, strings/buffers, errors and panic/exception containment, callbacks, threading, cancellation, teardown, versioning, generated bindings, linkage, and consumer packaging. Build or contract-check both producer and representative consumers. A single-language build, one architecture, or static declaration is partial evidence; unbuilt consumer/device/package combinations remain `NOT RUN`.

## Alloy guardrails

- State the finite scope and why it is useful.
- Distinguish facts (model assumptions) from assertions (claims to challenge).
- Ask for counterexamples, not confirmation screenshots.
- Convert counterexamples into requirements, implementation constraints, or tests.
- Report “no counterexample within scope,” never “proved correct” unless a separate proof justifies it.

## TLA+ guardrails

- State variables, initial condition, and next-state actions.
- Separate safety, liveness, and fairness assumptions.
- Model retry, duplicate, cancellation, recovery, message loss/reorder, and resource limits that matter.
- Minimize counterexample traces and map each abstract action to code/runtime observations.
- A model-checker pass without a refinement mapping is model evidence, not code proof.

## Refinement mapping worksheet

| Obligation | Question |
|---|---|
| Initial states | Does every valid concrete initial state map to an allowed abstract state? |
| Steps | Does each concrete step correspond to an abstract step or justified stutter? |
| Observations | Are public outputs/errors/order/termination preserved? |
| Exceptional behavior | How do timeout, cancellation, retry, crash, and recovery map? |
| Liveness | Do fairness/progress assumptions survive implementation scheduling? |
| Environment | Which compiler/runtime/hardware/external assumptions are outside the model? |

Prefer differential/contract/characterization evidence when proof cost is unjustified; state the weaker assurance explicitly.

## Formal stop conditions

Stop or fall back when the specification is volatile, domain ownership is absent, the model does not map to implementation, a tool/dependency is unapproved, the state bound is misleading, fairness assumptions are unjustified, or proof cost exceeds the consequence being controlled.
