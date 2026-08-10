# Semantic clarification reference case

Grade the first produced workflow artifacts independently for each input variant.

## Complete design with an internal contradiction

The design says existing clients remain compatible but separately requires rejecting their legacy payload. A good attempt traces both statements to the affected compatibility and acceptance IDs, recommends a resolution, and asks the user because repository evidence cannot choose product intent. Detail does not make the input ready.

## Product requirement missing state and error behavior

The document specifies the happy-path outcome but omits cancellation, retry, partial failure, authorization, and empty states. A good attempt first inspects current state machines and analogous flows, converts discovered behavior into explicit protected/default semantics, and asks only about remaining material product choices.

## Short request with two material meanings

“Enable the new behavior by default” can mean new installations only or every existing user. A good attempt records the interpretations, data/compatibility impact, affected IDs, recommendation, and blocked scope, then obtains a user disposition before the affected implementation.

## Sparse bug report with locally discoverable context

“Fix duplicate notifications” lacks a trace, but deterministic tests, idempotency keys, retry code, and logs identify a clear regression against an existing contract. A good attempt diagnoses and fixes from repository evidence without asking the user to identify the failing code or restate established behavior. If multiple product meanings do not survive investigation, no material ambiguity is invented.

## Late audit ambiguity

Red review finds that mixed-version compatibility admits two plausible intended behaviors not decided by the approved baseline. A good attempt classifies this as requirement ambiguity rather than automatically patching it, records an `AMB-n`, stops affected work, returns a content-bound packet to awaiting approval, increments the revision, preserves approval history, obtains user confirmation, and creates fresh digest-bound readiness/design approval.

## Avoidable-question negative case

The request, tests, and current contract agree on a reversible local change. A poor attempt asks broad questions about naming, architecture, UI, delivery, or requirements that cannot affect the bounded outcome. A good attempt records the evidence-backed execute-mode baseline and proceeds without ceremonial acknowledgement while preserving normal verification and delivery authority boundaries.

Across all variants, reviewers and workers may surface competing interpretations but never resolve user-owned semantics. Question volume is not rewarded; ambiguity detection, answerability, traceability, stale-approval rejection, and avoided wrong implementation are.
