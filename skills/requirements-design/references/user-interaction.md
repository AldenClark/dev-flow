# Default-mode user interaction

## Invariant and ownership

Dev Flow always remains in Default mode. Never switch to Plan mode to make a question tool available.

Requirements Design owns product meaning. Dev Flow owns operational approval, secret-surface selection, and post-interaction continuation; Dependency Decisions, Delivery Readiness, and Verification retain their named responsibilities.

First decide whether the question is required, optional, an approval, or secret input. Then check the effective current-turn tool instructions: current mode, permitted purpose, parameter schema, and response lifecycle must all fit. An exposed Plan-only tool is ineligible in Default mode, and an optional-only tool cannot carry a required decision or an approval. Never switch modes to obtain eligibility. Select the exact eligible synchronous or asynchronous surface; `request_user_input` and `request_user_input_async` are examples only when actually exposed and permitted, not APIs this Skill provides.

The host owns question rendering, response correlation, and lifecycle cleanup. Use the exposed native question API; never construct raw protocol frames, call App Server directly, or guess lifecycle identifiers. One transport's fields do not establish another tool's blocking or secret-input capabilities.

Detect capability from the effective tool surface for the current turn. Do not infer availability from an installed version, feature flag name, remembered session, or plugin inventory. Do not enable an experimental feature or modify global Codex configuration on the user's behalf.

## Route the interaction

| Need | Route | Failure behavior |
|---|---|---|
| One to three bounded non-secret product decisions whose answers materially change behavior, contract, dependency, compatibility, scope, risk, or acceptance | An eligible synchronous or asynchronous question surface | If none is eligible or invocation fails before presentation, end the turn with a focused question with meaningful plain-text options when the host permits; otherwise report the blocker |
| Optional clarification that can improve the result but need not block it | An eligible optional question surface or normal conversation | Follow the host's unanswered-question rule with a bounded visible assumption; do not turn an optional tool into a required approval |
| Open-ended context, explanation, artifact review, or a choice that cannot be represented faithfully by the tool schema | Normal conversation | Ask one focused question; do not force false choices |
| Command, file-change, destructive, or external-action authorization | The actual host approval surface and existing explicit user authority | Do not replace a host approval with an ordinary question; if required authority cannot be obtained, report it as blocked |
| Secret or credential | A host-approved secure input surface only when its effective schema and instructions expose protected input | If none exists, do not request the value in ordinary conversation or non-secret structured choices |
| Repository/runtime fact Codex can inspect | No user question | Investigate and record evidence |

The current host tool schema controls field and option limits. Once a material product choice is clear, ask one to three decision-changing questions through an eligible native surface; do not first complete a repository survey or design every branch. Give meaningful options with a recommendation and consequences, allowing additions, compatible combinations, or “not sure”. Use supported free-form input or conversation when a single-select schema cannot express the answer. Resolve technical facts yourself and ask only about choices the user owns.

## Answers and continuity

Use an answer only when it belongs to the current question and expresses a usable choice. Interpret supported free-form or conversational combinations by their meaning; “not sure” leaves uncertainty. Record the accepted subset in the existing owner only when durable; conversation otherwise suffices. Do not create an answer ledger.

An unresolved material business choice pauses only dependent commitments. Before an important new feature's first implementation, confirm the overall result, scope, and major technical trade-offs with user-visible consequences, or reuse an explicit waiver or prior acceptance of the same scope. Implementation details belong in that readback only when they change the decision. Natural language such as “确认整体方案，按此实施” can accept the presented whole; a local option answer, silence, cancellation, tool lifecycle event or caller-filled CLI flag cannot. Acceptance grants authority for the named scope; the recommendation must still be proportionate to its benefit. Reopen only changed material decisions. If the host requires a conversational checkpoint, end the turn with it.

Asynchronous dispatch is not an answer. While a required choice is pending, continue only independent reversible work already authorized; check the eventual answer still applies after steering or interruption. An optional unanswered question follows the host's optional-question rule and cannot resolve a required choice.

Tool absence or failure before presentation permits one host-compatible fallback question in conversation. Cancellation, dismissal, interruption, cleanup, or an empty or malformed answer leaves a required choice unresolved and does not trigger immediate re-prompting or acceptance of the recommendation. Continue independent authorized work or report the blocker.
