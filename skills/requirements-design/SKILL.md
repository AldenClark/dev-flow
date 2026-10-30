---
name: requirements-design
description: Clarify new or changed product behavior and scope; prepare important first implementation understanding, excluding established mechanical work.
---

# Requirements and Design

Own product meaning and scope. Preserve the whole requested outcome and key relationships, then resolve enough detail for the next implementation slice. Do not turn complete understanding into a complete requirements database or additional product promises.

This Skill may operate alone for a bounded requirements result. If the result leads to material repository mutation, cross-boundary design, managed continuity, or high-risk delivery, load `dev-flow` as the coordinating kernel when it is available and not already active; keep this Skill as the semantic owner.

A public-contract or data-lifecycle design that spans compatibility, rollout, recovery, privacy, or deletion boundaries is cross-boundary even when the user requests design only and no repository mutation. Load `dev-flow` before technical design in that case.

## First action

Separate the requested result and hard constraints from preferences and suggested mechanisms. Read enough nearby product or contract evidence to frame the next decision. When a material product choice is already clear, ask through an eligible native question surface before further technical investigation; a complete repository survey or failure model is not a prerequisite. Resolve repository facts yourself and proceed directly when the intended behavior is established.

## Procedure

1. Inspect the nearest relevant source, contract, or example to resolve facts that can change the next action. Stop gathering context when the choice can be answered or the work can proceed correctly.
2. Classify understanding depth: U1 semantic creation/change, U2 structural adjustment, U3 defect correction, U4 mechanical edit, or U5 read-only work. Use `references/semantic-and-scope.md` when the classification or scope is unclear.
3. Describe the intended observable result, scope, and behavior to preserve. Explain states, failures, recovery, or compatibility only when this change affects them or they are necessary to judge the result. Use an example or small model when it resolves an actual ambiguity.
4. Use a bounded discovery method when complex rules, states, journeys, trust boundaries, or mixed versions need it. Produce the resulting business meaning, not a methodology transcript.
5. Resolve user-owned trade-offs that change the result or scope. Add guarantees only when the requested outcome, an existing contract, a real consumer, or a consequential failure needs them. Where stronger guarantees add substantial cost, recommend the sufficient simpler option unless their added value justifies that cost. User acceptance settles authority for the named outcome; it does not establish that a proposed mechanism is worth its complexity. Revisit a costly recommendation when a simpler one meets the same outcome, and ask before weakening an accepted business guarantee. Ask one to three decision-changing questions at a time, allowing additions, compatible combinations and uncertainty; reuse settled decisions.
6. For U1, state the outcome, scope, protected behavior, and remaining material choices. An unresolved user-owned choice pauses its dependent commitments; independent authorized learning may continue. Before an important new feature's first implementation, obtain one explicit whole-understanding confirmation of the result, scope, and major technical trade-offs that affect the user. Include implementation details only when they change that decision. Reuse prior acceptance of the same scope or an explicit waiver; do not repeat confirmation per slice. A local answer, silence, or a caller-filled CLI flag is not whole acceptance. Keep the class U1 after confirmation.
7. For U2, stop only when product/compatibility/operational semantics can change. For U3, state expected and protected behavior and proceed when evidence establishes them; upgrade to U1 when they remain open, but ambiguity alone does not prove a user decision is needed. U4 and U5 never acquire a confirmation ceremony merely because Dev Flow is active.
8. When future work needs a durable product decision and repository mutation is in scope, update the existing product or contract owner. If mutation is not authorized, describe the needed owner update in chat. Use `repository-knowledge` only when a missing or conflicting owner blocks continuation. A separate change record is justified only when existing owners cannot support needed continuity across sessions or owners.
9. Define verification intent as observable behavior. Leave exact technical oracles to `verification` and structural choices to their owning specialists.

After a user correction or contradictory evidence, replace the affected understanding and trace its consumers in design, code/data, tests, and delegated work. Pause or update dependent work, recheck late child results, and verify the revised user behavior; changing a summary alone is insufficient. Preserve unaffected results and separately account for any already-executed external effects. `dev-flow/references/core-lifecycle.md` owns this continuation rule.

Always stay in Default mode. Read `references/user-interaction.md` before a material question or U1 confirmation checkpoint.

## Quality, handoff, and stopping

The result is sufficient when an implementer can deliver the requested result and preserve the affected contract without making an unresolved material product choice. Hand technical design that concise understanding and any remaining user decisions; hand unresolved user-flow questions to `product-ux-discovery`.

Stop dependent work for a material user choice, an explicit review-first request, or the first implementation confirmation described above. Do not ask for repository facts, manufacture a requirements file for an established defect, or keep refining once remaining ambiguity has no material effect. New evidence that changes meaning replaces the prior understanding with one coherent revision rather than a revision ceremony.

## Boundaries

- Do not require AC/SC/VO identifiers, digests, approval records, or packet revisions unless the repository's own regulated process requires them.
- Do not ask the user to resolve repository facts.
- Do not commit to or implement a branch that depends on an unresolved material user-owned choice. Independent learning must stay within authorized data/actions and must not add dependencies, touch production data, or substitute a technical preference for the user's decision.
- Do not force a question, requirements file, or confirmation stop for an established defect or mechanical edit.
- Do not create a stub requirements file merely to inventory unknown product semantics.
- Do not write requirements or product documentation during a read-only or design-only request unless repository mutation is explicitly included.
- Design agreement does not authorize dependencies, commit, delivery, deployment, or destructive actions.
