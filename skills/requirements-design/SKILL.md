---
name: requirements-design
description: Resolve material requirement ambiguity and bind outcomes, constraints, scope, compatibility, rollback, verification, and approval before consequential changes.
---

# Requirements and Design

Own user-visible semantics and the content-bound approval baseline; do not substitute technical preference for an unresolved product choice.

At every user-owned checkpoint, remain in Default mode and follow `references/user-interaction.md`; prefer the native `request_user_input` tool when the effective host surface exposes it.

## Procedure

1. Consume a fresh `context.snapshot.v1`. Scan unresolved repository facts before asking questions.
2. Normalize actor, trigger, preconditions, inputs, trust boundary, output, state transition, failures, cancellation, retry, timeout, recovery, authorization, privacy, compatibility, performance, and operations.
3. Record observable `AC-n` criteria and explicit non-goals. Avoid prescribing implementation unless it is an approved constraint.
4. For every surviving material interpretation, record `AMB-n`, evidence, materiality, owner, affected IDs, recommendation, and status.
5. Assign repository-resolvable facts to Codex and final material requirement semantics to the user. Ask only questions whose answer changes behavior, architecture, dependency, compatibility, scope, risk, or acceptance.
6. Compare viable designs against repository facts and applicable resolved preferences. Record failures, migration, rollout, rollback, cleanup, and `VO-n` obligations.
7. Define direct, indirect, conditional, protected, out-of-scope, and delivery scopes with stable `SC-*` IDs.
8. Bind Requirement Ready and design approval to the current revision and digest. When late material ambiguity changes the baseline, record an `AMB-n`, stop affected work, return the content-bound packet to `awaiting-approval`, increment the revision, preserve approval history, obtain the user disposition, and create fresh digest-bound Requirement Ready and design approvals.

Read `references/semantic-and-scope.md` for ambiguity ownership, collaboration modes, scope, drift, and approval rules. Read `references/user-interaction.md` before asking a material question or requesting approval.

## Output contract

Produce `requirements.baseline.v1` and `design.record.v1` with revision/digest, AC/AMB/SC/VO mappings, evidence, alternatives, selected design, approval state, dependency decisions, and reopen conditions.

## Boundaries

- Do not hide material product choices inside implementation tasks.
- Do not ask the user to rediscover code, manifests, or runtime facts.
- Do not treat approval of design as dependency, delivery, or deployment authority.
