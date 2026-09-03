---
name: requirements-design
description: Use when product behavior, scope, contract, or recovery meaning has competing interpretations; not for established mechanical work.
---

# Requirements and Design

Own product meaning and scope. The goal is enough shared understanding to make the next implementation slice correct, not a complete requirements database or approval system.

This Skill may operate alone for a bounded requirements result. If the result leads to material repository mutation, cross-boundary design, managed continuity, or high-risk delivery, load `dev-flow` as the coordinating kernel when it is available and not already active; keep this Skill as the semantic owner.

A public-contract or data-lifecycle design that spans compatibility, rollout, recovery, privacy, or deletion boundaries is cross-boundary even when the user requests design only and no repository mutation. Load `dev-flow` before technical design in that case.

## First action

Start with one representative actor, trigger, and observable result from the user's request and current behavior. Pair it with one boundary, failure, recovery, permission, or compatibility example that could make the same words mean something else. A known defect with a proven expected behavior can proceed from that behavior; a new capability with two credible outcomes cannot.

## Procedure

1. Read current repository, product, issue, test, and relevant external evidence before asking questions. Resolve repository facts yourself.
2. Classify understanding depth: U1 semantic creation/change, U2 structural adjustment, U3 defect correction, U4 mechanical edit, or U5 read-only work. Read `references/semantic-and-scope.md` for the classifier.
3. Build a technology-neutral model of the actor, problem/goal, trigger, scenarios, observable outcome/state, failures/recovery, compatibility, protected behavior, in/out scope, acceptance behavior, facts, user decisions, bounded assumptions, and material unknowns that actually apply. Use examples, counterexamples, a small state model, decision table, or event timeline only when it removes a real ambiguity.
4. Use a bounded discovery method when complex rules, states, journeys, trust boundaries, or mixed versions need it. Produce the resulting business meaning, not a methodology transcript.
5. Ask only when surviving interpretations materially change behavior, contract, scope, irreversible consequence, or external authority. Group one to three decision-changing questions and explain the recommendation.
6. For U1, after material questions are resolved, publish the complete requirement-understanding result, explicitly state that technical design and implementation have not started, and end the turn for user confirmation. A correction requires a complete revised result and another stop. Proceed only after explicit confirmation or an explicit waiver in the request. Confirmation changes the gate state, not the class: an already-confirmed U1 remains U1 and must not be relabeled U2 to bypass the stop.
7. For U2, stop only when product/compatibility/operational semantics can change. For U3, state expected and protected behavior and proceed without the confirmation stop when evidence establishes them; upgrade to U1 when they remain open. U4 and U5 never acquire a confirmation ceremony merely because Dev Flow is active.
8. When repository mutation is explicitly in scope, write confirmed material semantics, examples/anti-examples, protected behavior, and unresolved user choices back to the existing product or contract owner so technical design can read them. If mutation is not authorized, return the proposed owner and exact update in chat without editing the repository. If no owner exists, ask `repository-knowledge` to choose the smallest discoverable owner; do not silently convert a read-only design request into documentation work. A change record is justified only when reliable continuation crosses sessions, owners, or independent slices and existing owners cannot carry the navigation.
9. Define verification intent as observable behavior. Leave exact technical oracles to `verification` and structural choices to their owning specialists.

Always stay in Default mode. Read `references/user-interaction.md` before a material question or U1 confirmation checkpoint.

## Quality, handoff, and stopping

The result is sufficient when two implementers would preserve the same main result, protected behavior, material failure/recovery, and non-goals. Hand technical design a concise behavior understanding plus the canonical owner and remaining user decisions; hand user-flow uncertainty to `product-ux-discovery`.

Stop and ask only when surviving interpretations change behavior, scope, irreversible consequences, or external authority. Do not ask for repository facts, manufacture a requirements file for an established defect, or keep refining once remaining ambiguity has no material effect. New evidence that changes meaning replaces the prior understanding with one coherent revision rather than a revision ceremony.

## Boundaries

- Do not require AC/SC/VO identifiers, digests, approval records, or packet revisions unless the repository's own regulated process requires them.
- Do not ask the user to resolve repository facts.
- Do not start technical design or product-code mutation before required U1 confirmation.
- Do not force a question, requirements file, or confirmation stop for an established defect or mechanical edit.
- Do not create a stub requirements file merely to inventory unknown product semantics.
- Do not write requirements or product documentation during a read-only or design-only request unless repository mutation is explicitly included.
- Design agreement does not authorize dependencies, commit, delivery, deployment, or destructive actions.
