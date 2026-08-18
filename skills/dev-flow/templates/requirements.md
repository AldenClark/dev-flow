# Change requirements: <change-id>

> Legacy packet compatibility template. Direct and managed 2.0 work uses repository-native requirement sources or `templates/workstream/requirements.md`.

## Requirement source and understanding revisions

- Original input: <sanitized user text, issue, design package, or durable secure pointer>
- AI understanding revision 1: <complete actors, triggers, inputs, states, normal/failure/retry/cancel/recovery, permissions/privacy, compatibility, operations, acceptance, non-goals, and assumptions>
- Corrections and decisions: <ordered user interactions with affected AC/SC/VO IDs; persist semantic disposition, not secrets or unnecessary raw personal data>
- Current requirement truth: <latest complete revision and why it supersedes earlier interpretations>

## User and product outcome

<Actor or user, context, problem, desired outcome, current pain point, and how success is observed.>

## Requirement delta

<Describe the observable difference between current and desired behavior.>

## Acceptance criteria

- AC-1: <observable criterion with actor, trigger, result, and failure behavior>

## Non-functional requirements

- <performance, security, privacy, accessibility, operability, reliability, or maintainability requirement>

## Compatibility and exclusions

- Compatibility: <directions, versions, platforms, data, protocol, or none with rationale>
- Excluded behavior: <explicit non-goal>

## Requirement Ready gate

- Status: <ready or blocked>
- Evidence: <repository evidence, resolved material decisions, and user confirmation when required>
- Remaining decisions: <none or exact blocker and affected IDs>

## Requirement baseline

- Revision: <positive requirement revision>
- Digest: <sha256 digest recorded by the content-bound CLI at Requirement Ready>
- Baseline content: <full requirements.md, or the Requirement and design section for a traced packet>
- Reopen conditions: <material late ambiguity, requirement correction, or audit finding that changes affected semantics>

## Ambiguity ledger

| ID | Source and interpretations | Evidence | Materiality and owner | Affected IDs | Recommendation | Status and resolution |
|---|---|---|---|---|---|---|
| <AMB-n or state that no ambiguity was found> | <where ambiguity arose and at least two plausible meanings> | <repository evidence or missing evidence> | <low, material, or high-risk; Codex or user> | <AC, SC, or VO IDs> | <recommended decision and tradeoff> | <open or authorized resolution with actor and evidence> |

## Confirmation record

- <timestamp or ordered event>: <user-confirmed requirement, correction, or unresolved decision>
