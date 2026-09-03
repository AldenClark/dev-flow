# Coverage expansion and oracle techniques

Use this reference after black-box and white-box derivation identifies a concrete blind spot. Choose the technique because of the problem it exposes, not to make every change exhibit every test type.

## Input ranges and independent rules

Use equivalence classes, boundary values, table-driven tests, and properties for pure or mostly deterministic rules. Write the semantic invariant first, then generate across the useful domain and retain minimized failing seeds.

Example: for a range normalizer, examples protect named contract cases while properties assert idempotence, ordered output, and preservation of membership. Fuzzing can explore parser inputs, but it needs an invariant such as “never crash and accepted output re-parses canonically”; generated volume is not an oracle.

Stop when the meaningful partitions and boundaries are represented and new generators only repeat the same obligation.

## Rules, states, combinations, and event order

Use a decision table or state model when rules interact or events change allowed transitions. Apply model-based tests when an executable reference state can predict actions and results.

For many parameters, build a constrained factor/value model:

1. remove impossible or semantically invalid combinations;
2. begin with pairwise coverage for ordinary interactions;
3. raise selected high-risk factors to higher t-way strength;
4. add known failure combinations and material event sequences explicitly;
5. attach an outcome or invariant to each generated case.

This is variable-strength coverage, not permission to enumerate the Cartesian product. Stop when selected interactions cover the credible mechanism; increase strength only when history, architecture, or consequence supports a higher-order interaction.

## Weak or unavailable expected answers

When a direct expected value is expensive or unknown, triangulate the oracle:

- **Differential:** compare old/new versions, two implementations, readers/writers, or a trusted reference over the same input. First decide which differences are allowed.
- **Metamorphic:** transform an input in a way that implies a predictable relation, such as permutation invariance, scaling, encode/decode stability, or monotonicity.
- **Invariant/property:** assert facts that must hold across all valid outcomes, including conservation, ordering, uniqueness, boundedness, or legal state transitions.
- **Model:** compare with a smaller executable semantic model, not a copy of the production algorithm.

Use at least two reasonably independent sources when AI generated both code and tests—for example, a public contract plus final-code branch analysis, or a property plus a seeded fault. Another agent repeating the same assumption is not an independent oracle.

Stop once the target fault is rejected and the sources no longer disagree materially. Preserve disagreement as a requirement or evidence gap rather than choosing the convenient answer.

## Failure, recovery, and resources

Use fault injection, negative fixtures, clock/control substitution, and replay when correctness depends on partial failure, retry, crash, rollback, cleanup, or ordering.

- Inject at the boundary that can create the suspected state, not only at a distant mock.
- Observe both the immediate response and durable aftermath: ownership, persisted state, duplicate effects, open resources, retry amplification, and recovery.
- Replay retained minimal events or migration data when the promise includes resume, compatibility, or rollback.
- Keep fault controls deterministic where possible and tear them down after the run.

For concurrency, use controlled scheduling or repeatable interleavings when available; assert state invariants or linearizability properties rather than relying only on “did not crash.” Randomized stress can supplement, not replace, a known critical interleaving.

## Assertion sensitivity

Use the cheapest controlled fault that resembles a credible implementation error:

- pre-fix behavior for a bug regression;
- a negative fixture that crosses the protected boundary;
- a small seeded fault such as inverted condition, omitted state write, swallowed error, missing cleanup, or duplicate effect;
- changed-code mutation with operators suited to the changed logic;
- semantic mutation of a contract, fixture, selector, or environment attribution.

Confirm the intended test is discovered and fails for the right reason. Restore the fault before recording a pass. Filter equivalent mutants and mutations whose only effect is to constrain an internal representation; a score is not the goal.

## Legacy, compatibility, and real boundaries

Use characterization or a focused golden master when old behavior is insufficiently understood, then add semantic assertions for the behavior that must remain. Avoid expanding snapshots that make every irrelevant byte contractual.

For APIs, protocols, schemas, and FFI, test applicable producer/consumer and old/new directions, invalid inputs, lifecycle/ownership, packaging/loading, and rollback. A one-version round trip does not prove mixed-version compatibility.

For platform behavior, execute on the environment that owns the promise. Host, mock, simulator, and emulator runs may localize faults or provide fast feedback, but their green result cannot become device/platform evidence. If access is unavailable, report the exact narrower pass and the target path as `BLOCKED` or `NOT RUN`.
