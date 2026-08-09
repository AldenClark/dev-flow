# Default-mode user interaction

## Invariant and ownership

Dev Flow always remains in Default mode. Never switch to Plan mode to make a question tool available.

For a material, user-owned, bounded, non-secret choice, invoke the host-exposed `request_user_input` tool when it is available. Codex App Server and its client own the resulting `item/tool/requestUserInput` request, `threadId`/`turnId`/`itemId`, `isBlocking`, `isOther`, `isSecret`, response correlation, `serverRequest/resolved`, rendering, and lifecycle cleanup. A Skill never constructs raw protocol frames, calls App Server directly, or guesses lifecycle identifiers.

Detect capability from the effective tool surface for the current turn. Do not infer availability from an installed version, feature flag name, remembered session, or plugin inventory. Do not enable an experimental feature or modify global Codex configuration on the user's behalf.

## Route the interaction

| Need | Route | Failure behavior |
|---|---|---|
| One to three bounded decisions whose answers change behavior, contract, dependency, compatibility, scope, risk, acceptance, or authority | Native `request_user_input` when exposed | If the tool is unavailable or invocation fails before presentation, stay in Default mode and ask at most one focused non-enumerated question when the host permits; otherwise report the blocker |
| Open-ended context, explanation, artifact review, or a choice that cannot be represented faithfully by the tool schema | Normal conversation | Ask one focused question; do not force false choices |
| Command, file-change, destructive, or external-action authorization | The host's native approval surface | Do not replace an approval with an ordinary question or infer authority from discussion |
| Secret or credential | A host-approved secure input surface, including native `request_user_input` only when its effective tool schema exposes protected secret input | If none exists, do not request the value in ordinary conversation or non-secret structured choices |
| Repository/runtime fact Codex can inspect | No user question | Investigate and record evidence |

The current host tool schema controls exact field and option limits. Prefer one consolidated batch of no more than three high-value questions. Each question has a short stable ID/header, one decision, mutually exclusive options when applicable, a recommended option first with its impact, and a free-form path only when it can change the decision usefully.

## Answers and traceability

Before invocation, record the affected `AMB-n`, `AC-n`, `SC-*`, `VO-n`, dependency, waiver, or delivery boundary, current requirement revision/digest, and which work is blocked. After a response, accept exactly one presented non-empty option, or exactly one non-empty free-form value only when the host enabled Other for that question. Reject unknown question IDs, empty answers, multiple/conflicting values, values outside the options when Other is disabled, and answers for a stale revision. Then record the user's actual wording or selected option, actor, time, scope, and downstream tasks released.

Do not collapse lifecycle outcomes. Tool absence or invocation failure before presentation permits at most one host-compatible fallback; that fallback is one focused plain-text question, never a textual multiple-choice list. User cancellation/dismissal, client interruption, request cleanup, omission, an empty or malformed response, and a stale/late response keep the decision unresolved and must not trigger an immediate re-prompt. Retry only after new user intent or an explicit retry request, and correlate the accepted answer to the current decision and requirement revision. None of these outcomes select the recommendation. Continue only independent reversible work already authorized; otherwise report the exact blocker.

App Server currently marks `item/tool/requestUserInput` experimental. Treat its transport fields as observed host behavior, not a stable plugin-owned API. Recheck this reference when the effective tool schema, lifecycle contract, or feature maturity changes.
