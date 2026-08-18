# Default-mode user interaction

## Invariant and ownership

Dev Flow always remains in Default mode. Never switch to Plan mode to make a question tool available.

Requirements Design owns product meaning and semantic answer records. The Dev Flow control plane owns operational approval and secret-surface selection. Dependency Decisions and Delivery Readiness own their named decisions. Verification owns executable response and lifecycle checks. Referencing this interaction contract does not transfer those responsibilities to Requirements Design.

Default-mode control, waiver state, and post-interaction continuation are owned by Dev Flow. After an unresolved outcome, Requirements Design preserves the semantic state while Dev Flow decides whether any already-authorized independent reversible work may continue.

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

The current host tool schema controls exact field and option limits. Ask one-to-three high-value questions per round, then update the durable requirement and repeat if material ambiguity survives. Each question has a stable ID/header, one decision, mutually exclusive options when applicable, a recommended option first with its impact, and a useful free-form path. Fewer questions are not a quality goal.

## Answers and continuity

After a response, accept one presented non-empty option or a non-empty free-form value when the tool allows it. Reject unknown, empty, conflicting, or out-of-range values. When the decision will matter after the current session, update the managed workstream design/decision document or the repository's native issue/ADR system with the choice and rationale. Otherwise the conversation is sufficient. Do not create IDs, digests, approval records, or a parallel answer ledger solely for Dev Flow. Retain raw wording only when necessary and safe, never secrets or unnecessary personal payloads.

For a U1 requirement-confirmation checkpoint, first publish the complete technology-neutral understanding in normal conversation (and update the repository-native requirement source when managed continuity needs it), state that design/implementation have not started, and end the turn. Accept an unambiguous natural-language confirmation such as “确认”, “理解正确，继续”, or “按这个实施”. A correction is not confirmation: incorporate it, publish a complete revised understanding, and end the turn again. Silence, an unrelated answer, cancellation, or a tool lifecycle event never confirms the understanding.

Do not collapse lifecycle outcomes. Tool absence or invocation failure before presentation permits at most one host-compatible fallback; that fallback is one focused plain-text question, never a textual multiple-choice list. User cancellation/dismissal, client interruption, request cleanup, omission, or an empty/malformed response keeps the decision unresolved and must not trigger an immediate re-prompt. None of these outcomes select the recommendation. Continue only independent reversible work already authorized; otherwise report the exact blocker.

App Server currently marks `item/tool/requestUserInput` experimental. Treat its transport fields as observed host behavior, not a stable plugin-owned API. Recheck this reference when the effective tool schema, lifecycle contract, or feature maturity changes.
