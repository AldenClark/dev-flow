---
name: requirements-design
description: Resolve material requirement ambiguity and bind outcomes, constraints, scope, compatibility, rollback, verification, and approval before consequential changes.
---

# Requirements and Design

Own user-visible semantics and the content-bound approval baseline. The goal is semantic closure, not fewer questions: continue focused interaction until no material ambiguity remains, while making every revision recoverable.

At every user-owned checkpoint, remain in Default mode and follow `references/user-interaction.md`; prefer the native `request_user_input` tool when the effective host surface exposes it.

## Responsibility contract

- Consumes: fresh repository context and the product/UX contract when applicable.
- Owns: user-visible semantics, acceptance, scope, compatibility intent, and content-bound approval.
- Stops: at open material ambiguity, stale approval digest, or missing user disposition.
- Hands off: structure to architecture, external capability to dependency, and a ready baseline to the control plane.

## Procedure

1. Consume fresh repository/context evidence. Preserve a sanitized original request or secure pointer, then write the first complete AI-understood requirement revision before asking.
2. Normalize actor, trigger, preconditions, inputs, trust boundary, output, state transition, failures, cancellation, retry, timeout, recovery, authorization, privacy, compatibility, performance, and operations.
3. Record observable `AC-n` criteria and explicit non-goals. Avoid prescribing implementation unless it is an approved constraint.
4. For every surviving material interpretation, record `AMB-n`: source, at least two evidenced meanings, materiality, owner, affected AC/SC/VO, recommendation, blocked slice, creation revision, and status.
5. Codex owns repository facts; the user owns material semantics. Ask one-to-three decision-changing questions per round, explain outcome impacts and an evidence-backed recommendation, then immediately persist the answer/correction and next requirement revision. Repeat as needed; do not pursue literal zero unknowns or invent questions for a count target.
6. Compare viable product/scope options against repository facts and applicable resolved preferences. Record observable failure behavior, compatibility intent, rollout/rollback outcomes, cleanup expectations, and `VO-n` obligations; link separately owned architecture and dependency decisions when routed.
7. Define direct, indirect, conditional, protected, out-of-scope, and delivery scopes with stable `SC-*` IDs.
8. Requirement Ready means no open material/high-risk ambiguity, observable ACs, explicit non-goals, and visible evidence-backed reversible low-risk assumptions. Bind it and the repository-grounded design to current digests. When late material ambiguity changes the baseline, record an `AMB-n`, stop affected work, return the content-bound packet to `awaiting-approval`, increment the revision, preserve approval history, obtain the user disposition, and create fresh digest-bound Requirement Ready and design approvals.

Read `references/semantic-and-scope.md` for ambiguity ownership, collaboration modes, scope, drift, and approval rules. Read `references/user-interaction.md` before asking a material question or requesting approval.

## Output contract

Produce `requirements.baseline.v1` and `design.record.v1` containing the sanitized source, ordered understanding/correction chain, current truth, revision/digests, AC/AMB/SC/VO, evidence, alternatives, failure/compatibility/rollback/testing intent, approved constraints, linked owner decisions, approval, and reopen triggers.

## Boundaries

- Do not hide material product choices inside implementation tasks.
- Do not select technical architecture, control/data flow, ownership mechanics, or an external capability inside the requirement artifact; route those decisions and bind their returned artifacts as constraints.
- Do not ask the user to rediscover code, manifests, or runtime facts.
- Do not treat approval of design as dependency, delivery, or deployment authority.
