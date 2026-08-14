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
