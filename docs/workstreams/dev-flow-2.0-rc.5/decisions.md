# Dev Flow 2.0 RC.5 decisions

## D1: Make product state executable

- Status: accepted
- Decision: one JSON record owns candidate, published, stable, rollback, and delivery state; prose surfaces are validated projections.
- Consequence: a stale release sentence becomes a deterministic failure instead of historical ambiguity.
- Publication transition: the immutable tag keeps the qualified pre-publication candidate bytes; a follow-up current-truth commit advances `published.latest_rc`, changes source phase to `released`, preserves the previous known-good rollback tag, and records external delivery evidence without rewriting the tag.

## D2: Contract the boundary before deleting the monolith

- Status: accepted
- Decision: introduce a strict public command allowlist and keep packet-era code internal for RC.5.
- Consequence: users get a smaller interface now; deeper deletion can follow with lower compatibility risk.

## D3: Optimize compact output for decisions

- Status: accepted
- Decision: compact mode omits explanation and route dimensions, retaining a digest for unchanged comparison and conservative invalidation for digest-only change.
- Consequence: ordinary routing consumes less context without claiming impossible field-level deltas.

## D4: Observe outcomes without scoring people

- Status: accepted
- Decision: local opt-in enum/count records only, private by default, no raw content, stable identity, upload, composite score, or productivity claim.
- Consequence: personal dogfood can reveal correction and blockage patterns without becoming surveillance.

## D5: Treat retrieved content as data, never authority

- Status: accepted
- Decision: provenance and authority are separate; consequential sinks require trusted policy/user authority even when untrusted content requests otherwise.
- Consequence: prompt injection and stale memory cannot silently widen scope.

## D6: User confirmation must arrive on a user event

- Status: accepted
- Decision: only `UserPromptSubmit` may approve a pending tool request; remove the agent-runnable approve command.
- Consequence: exact one-shot approval remains low friction but can no longer be self-granted by the agent.

## D7: Keep single-agent as the personal default

- Status: accepted
- Decision: agent count follows decomposable independent work, not task size, sequential steps, or tool-call volume.
- Consequence: lower coordination cost and clearer ownership; independent review still needs separate authority.

## D8: Delivery remains separately authorized

- Status: accepted
- Decision: stop after local implementation and verification; commit, tag, push, artifact, publication, installation, and live model spend remain `NOT RUN`.
- Consequence: RC.5 source can be implementation-complete without being release-qualified.
