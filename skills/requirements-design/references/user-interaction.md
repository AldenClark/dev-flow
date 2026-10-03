# Default-mode user interaction

## Invariant and ownership

Dev Flow always remains in Default mode. Never switch to Plan mode to make a question tool available.

Requirements Design owns product meaning and semantic answer records. The Dev Flow control plane owns operational approval and secret-surface selection. Dependency Decisions and Delivery Readiness own their named decisions. Verification owns executable response and lifecycle checks. Referencing this interaction contract does not transfer those responsibilities to Requirements Design.

Default-mode control, waiver state, and post-interaction continuation are owned by Dev Flow. After an unresolved outcome, Requirements Design preserves the semantic state while Dev Flow decides whether any already-authorized independent reversible work may continue.

First decide whether the question is required, optional, an approval, or secret input. Then check the effective current-turn tool instructions: current mode, permitted purpose, parameter schema, and response lifecycle must all fit. An exposed Plan-only tool is ineligible in Default mode, and an optional-only tool cannot carry a required decision or an approval. Never switch modes to obtain eligibility. Select the exact eligible synchronous or asynchronous surface; `request_user_input` and `request_user_input_async` are examples only when actually exposed and permitted, not APIs this Skill provides.

For the observed `request_user_input` transport, Codex App Server and its client own `item/tool/requestUserInput`, `threadId`/`turnId`/`itemId`, `isBlocking`, `isOther`, `isSecret`, response correlation, `serverRequest/resolved`, rendering, and lifecycle cleanup. These fields do not prove that a different tool supports blocking, secret input, or the same transport. A Skill never constructs raw protocol frames, calls App Server directly, or guesses lifecycle identifiers.

Detect capability from the effective tool surface for the current turn. Do not infer availability from an installed version, feature flag name, remembered session, or plugin inventory. Do not enable an experimental feature or modify global Codex configuration on the user's behalf.

## Route the interaction

| Need | Route | Failure behavior |
|---|---|---|
| One to three bounded non-secret product decisions whose answers materially change behavior, contract, dependency, compatibility, scope, risk, or acceptance | An eligible synchronous or asynchronous question surface | If none is eligible or invocation fails before presentation, end the turn with one focused non-enumerated question when the host permits; otherwise report the blocker |
| Optional clarification that can improve the result but need not block it | An eligible optional question surface or normal conversation | Follow the host's unanswered-question rule with a bounded visible assumption; do not turn an optional tool into a required approval |
| Open-ended context, explanation, artifact review, or a choice that cannot be represented faithfully by the tool schema | Normal conversation | Ask one focused question; do not force false choices |
| Command, file-change, destructive, or external-action authorization | The actual host approval surface and existing explicit user authority | Do not replace a host approval with an ordinary question; if required authority cannot be obtained, report it as blocked |
| Secret or credential | A host-approved secure input surface only when its effective schema and instructions expose protected input | If none exists, do not request the value in ordinary conversation or non-secret structured choices |
| Repository/runtime fact Codex can inspect | No user question | Investigate and record evidence |

The current host tool schema controls exact field and option limits. Ask one-to-three high-value questions per round within those limits, then update the durable requirement and repeat if material ambiguity survives. For structured questions, use only supported fields and correlation: one decision, mutually exclusive options when applicable, a recommended option first with its impact, and a useful free-form path when supported. Fewer questions are not a quality goal.

## Answers and continuity

After a response, accept one presented non-empty option or a non-empty free-form value when the tool allows it. Reject unknown, empty, conflicting, or out-of-range values. When the decision will matter after the current session, update the managed workstream design/decision document or the repository's native issue/ADR system with the choice and rationale. Otherwise the conversation is sufficient. Do not create IDs, digests, approval records, or a parallel answer ledger solely for Dev Flow. Retain raw wording only when necessary and safe, never secrets or unnecessary personal payloads.

For a U1 checkpoint justified by a surviving material choice or explicit review-first request, publish the technology-neutral understanding needed for the next coherent slice in normal conversation (and the existing repository-native owner when durable continuity needs it) and state which dependent work is paused. Use an eligible question surface when it faithfully supports the decision; a normal conversational checkpoint ends the turn. Accept an unambiguous natural-language confirmation such as “确认”, “理解正确，继续”, or “按这个实施”. A correction replaces the affected understanding and its consumers; stop again only if a material choice remains. Silence, an unrelated answer, cancellation, or a tool lifecycle event never resolves a required choice. When meaning is settled, publish the understanding and continue authorized work without this checkpoint.

Asynchronous invocation or successful dispatch is not an answer. While its request is pending, pause dependent commitments and implementation; continue only independent reversible work already authorized. Validate the eventual answer and its correlation to the current question/meaning before using it, including after steering or interruption. Never manufacture lifecycle IDs, polling, cancellation, blocking, or secret capabilities from a tool name. An optional unanswered question follows the host's optional-question rule; it cannot silently resolve a required choice.

Do not collapse lifecycle outcomes. Tool absence or invocation failure before presentation permits at most one host-compatible fallback; that fallback is one focused plain-text question, never a textual multiple-choice list. User cancellation/dismissal, client interruption, request cleanup, omission, or an empty/malformed response keeps the decision unresolved and must not trigger an immediate re-prompt. None of these outcomes select the recommendation. Continue only independent reversible work already authorized; otherwise report the exact blocker.

App Server currently marks `item/tool/requestUserInput` experimental. Treat its transport fields as observed host behavior, not a stable plugin-owned API. Recheck this reference when the effective tool schema, lifecycle contract, or feature maturity changes.
