# Discovery and requirements methods

Use these methods to prevent “correct implementation of the wrong thing.” Requirements-design retains semantic ownership; product-ux-discovery owns material product/interaction truth.

## Failure families and method choices

| Observed failure mechanism | Start with | Escalate when | Avoid when |
|---|---|---|---|
| Unknown actors/outcomes/decision owners | stakeholder-outcome-map | journey-service-blueprint or user-research-prototype for cross-channel/user uncertainty | bounded technical repair with known outcome |
| High-impact unverified premises | assumption-mapping-premortem | architecture spike or formal model for a falsifiable structural premise | premises already have direct evidence |
| Complex/disputed domain events | domain-storytelling-event-storming | bounded-context-context-map | simple stable vocabulary |
| Synonyms/homonyms/units/null meanings | ubiquitous-language-glossary | ontology-identity-ledger when equality/lifecycle matters | terminology is established and unchanged |
| Identifier/equivalence/alias/merge/split risk | ontology-identity-ledger | Alloy for bounded relational counterexamples | identity is local, immutable, single-source, unchanged |
| Rule edge cases and competing interpretations | specification-by-example | decision-table or state-transition-model | behavior is purely structural and preserved |
| Many categorical conditions | decision-table | combinatorial t-way for large feasible spaces | temporal order is the primary concern |
| Lifecycle/order/retry/cancel/recovery | state-transition-model | TLA+ when interleavings/progress/fairness matter | stateless pure transformation |
| Non-functional claim | quality-attribute-scenario | ATAM for competing material qualities | no affected quality claim |
| Misuse/abuse at a boundary | use-misuse-abuse-case | STRIDE/attack tree | no meaningful misuse surface |
| Stable boundary invariant | invariant-design-by-contract | typestate, property tests, or formal refinement | trivial glue already enforced by native types |
| Regulated/high-consequence trace | traceability-v-model | GSN assurance case | compact AC/SC/VO is sufficient |

## Ontology and identity worksheet

Do not begin with database keys. Begin with meaning.

| Question | Required answer |
|---|---|
| What kinds exist? | Entity/value/event/role kinds and their context |
| What establishes identity? | Issuer, namespace, key, provenance, and time interval |
| What counts as equal? | Identity equality, value equality, observational equivalence, and non-equivalence examples |
| How does identity change? | Create, alias, rename, merge, split, transfer, tombstone, delete, restore |
| How does it cross a boundary? | Translation, tenant/context qualification, lossless/lossy mapping |
| Which invariants matter? | Uniqueness, continuity, referential integrity, ownership, retention |
| What counterexample would break us? | At least one collision, alias, stale reference, cross-tenant, or replay example |

If the answers require quantifying over sets/relations and bounded counterexamples are valuable, route `alloy-relational-model`. If the issue is progress/order, route a state or temporal method instead.

## Specification-by-example recipe

For each rule:

1. Write one ordinary example in domain language.
2. Write a near-boundary and a counterexample.
3. Write an example for failure/retry/cancel/recovery if the rule has lifecycle.
4. Record questions that could change an observable result; do not hide them inside test data.
5. Map approved examples to AC and a failure-sensitive oracle.

Examples are not complete coverage. Add properties, decision tables, state models, or combinatorial methods for the unbounded parts of the domain.

## State-model recipe

Record state, event, guard, action, next state, externally visible result, owner, idempotency, timeout, cancellation, retry, recovery, and forbidden transitions. Separate safety (“nothing bad happens”) from liveness (“something good eventually happens”). If fairness is assumed, state who/what schedules progress and under which conditions.

## UX evidence boundary

Repository/code evidence can establish implemented states and semantics. It cannot prove comprehension, usability, assistive-technology behavior, or real-user outcomes. Use prototypes/research proportionate to uncertainty; otherwise mark those gates `NOT RUN`.
