---
name: dev-flow
description: Orchestrate repository diagnosis, change, audit and verification with risk-based evidence and Skill routing.
---

# Dev Flow

Use this thin control plane to preserve authority, conventions, compatibility, and evidence while loading focused Skills.

For multi-owner work, read `references/core-lifecycle.md`; packets and evaluations only record or test it.

## Responsibility contract

- Consumes: the user objective and authority plus focused owner artifacts.
- Owns: work mode, route order, lifecycle, integration, drift, and the exact final claim state.
- Stops: at missing authority, material semantic/scope drift, or an unapproved dependency/delivery action.
- Hands off: first to `repo-context`, then only to applicable owners in lifecycle order.

## Classify and start

1. Resolve the real Git root, effective Codex instruction chain, worktree state, task scope, risks, and mutation/delivery authority.
2. Run `route-task` and use its smallest work mode:
   - `direct`: clear micro/spike work; no packet; keep the decision and fresh check inline.
   - `traced`: ordinary non-trivial work; `packet.json`, append-only `events.jsonl`, and `trace.md` only.
   - `governed`: security/migration/release/dependency/public-contract/persisted-data risks, material UI semantics, or an explicit governance request; use the full packet.
3. Create state only when the selected mode requires it. Read `references/artifact-schemas.md` before packet work; new writes use schema 2.0 and old schemas remain readable.

## Establish context

Route `repo-context` for facts and compact readiness. Use full detail only to diagnose readiness; use team/CI profile modes when evidence must reproduce without personal profiles. Missing optional profiles, instructions, or specialist Skills never expand authority or block by name.

## Execute

For multi-slice or governed work, read `references/orchestration.md`. Otherwise:

Bugfixes reproduce the causal failure and, when practical, prove a focused regression fails before the fix; keep direct, protected, and out-of-scope behavior explicit.

1. Confirm current behavior, acceptance, protected behavior, scope, and the narrow verification oracle.
2. Activate focused owners only as needed: requirements/UX, architecture/dependency decisions, debugging, verification, review, or delivery readiness.
3. Implement the smallest coherent slice, run its narrow check, inspect drift and user-owned changes, and update persistent state when present.
4. Reopen only the affected requirement or scope when evidence changes it. Never treat momentum as authority.

Independent review is conditional on explicit review, governed risk, material UI impact, or security/migration/release/rollback work. Delivery readiness is conditional on explicit delivery intent or release/rollback work; it is not an ordinary mutation tax.

Single-agent execution is the baseline. Before delegation, follow `references/multi-agent-v2-orchestration.md`; reconcile every delegated task without duplicating work because of a wait timeout.

At user-owned checkpoints, remain in Default mode and follow `../requirements-design/references/user-interaction.md`. Requirements owns product meaning; dependency and delivery own named decisions; the control plane owns operational approval, secret routing, and waiver state. Never infer authority.

## Close

Run repository-native fresh checks through `verification`. Use `change-review` only when routed; verify findings before repair. Use `delivery-readiness` only when routed. Claim implemented, verified, accepted, release-ready, or delivered only when evidence proves that exact state; keep failures, flakes, blocks, waivers, and unrun gates distinct.

Never commit, push, create a PR, tag, release, deploy, install, or message externally without separate authority.
