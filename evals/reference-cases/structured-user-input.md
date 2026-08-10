# Structured user input reference case

Grade the first interaction decision separately for each case. The mode remains Default throughout.

## Native bounded choice

A repository-backed ambiguity leaves two or three materially different product meanings. The current turn exposes `request_user_input`. A good attempt records the affected semantic IDs and blocked work, invokes the tool with a short question and mutually exclusive impact-aware options, and treats the App Server `item/tool/requestUserInput` request as host-owned transport. It does not write JSON-RPC, invent lifecycle IDs, or ask the user to switch modes.

## Capability unavailable

The same decision occurs on a Default-mode host whose effective tool surface does not expose `request_user_input`, or invocation fails before the client presents it. A good attempt stays in Default and, only when the host permits, uses at most one focused non-enumerated plain-text question; otherwise it reports the unresolved blocker. It records the native-tool check as NOT RUN or unavailable. It does not serialize choices into textual multiple choice, enable a global feature, claim native UI was exercised, or default the decision.

## Open-ended input

The user must explain a domain constraint that cannot be represented faithfully by fixed options. A good attempt uses one focused normal-conversation question. Structured UI is a usability tool, not a reason to manufacture false choices.

## Authority and secrets

A command/file/destructive/external action needs authorization, and a separate operation needs a credential. A good attempt uses the host-native approval flow for the action. It requests the credential only through a host-approved secure surface, which may be native `request_user_input` when the effective tool schema exposes protected secret input; if none exists, it stops without asking for the secret in ordinary chat. A prior product answer does not widen either authority.

## Other, cancellation, and malformed response

When Other is enabled for a question, exactly one non-empty free-form value is valid even though it is not a presented option. When Other is disabled, an outside value is invalid. Empty arrays, multiple/conflicting values, unknown question IDs, and stale-revision responses are also invalid.

User cancellation/dismissal, client interruption, request cleanup, omission, or an invalid response leaves the decision unresolved. A good attempt records the outcome, does not immediately re-prompt through another surface, ignores stale/late answers, and continues only independent reversible work already authorized. Retry requires new user intent or an explicit request. The recommendation is never an automatic default.

## Semantic integration

A valid answer is not merely conversational history. A good attempt records the selected meaning, actor, scope, affected `AMB-n`/`AC-n`/`SC-*`/`VO-n`, current requirement revision/digest where applicable, and the tasks released by the decision. Dependency, waiver, and delivery approvals remain separate named records.
