# Audit, acceptance, and delivery

## Static scan

Run applicable repository-native gates after implementation and before completion:

- format, compile/typecheck, lint, dead/unused code, generated-file consistency;
- dependency, advisory, license, secret, and supply-chain checks;
- language/framework specialist review Skills;
- schema, migration, API, ABI, protocol, packaging, and configuration validation;
- unsafe, concurrency, FFI, performance, accessibility, and platform-specific analyzers.

Treat tool output as evidence to interpret, not automatically valid findings. Use `review-verification-protocol` before reporting code-review findings.

## Blue audit: specification and integration

Use a clean brief containing the approved requirement, design, scope, diff/base, and raw evidence. Verify:

- every acceptance and scope ID is implemented or explicitly excluded;
- protected and out-of-scope behavior remains intact;
- interfaces between tasks/components agree;
- error, cancellation, lifecycle, compatibility, migration, telemetry, docs, and cleanup are complete;
- changed files and generated artifacts are explained;
- implementation does not contradict engineering preferences without a recorded exception.
- each finding is classified as an implementation defect, design defect, evidence gap, scope change, or requirement ambiguity; any `AMB-n` is traced to affected requirements/scope and reopening state.

Do not provide the implementer's self-review or expected conclusions.

## Red audit: adversarial and failure-oriented

Attack the change through applicable lenses:

- malformed, boundary, adversarial, and oversized inputs;
- authorization bypass, tenant confusion, secret exposure, injection, unsafe behavior;
- cancellation, timeout, retry, duplicate delivery, ordering, race, deadlock, leak, overload, and shutdown;
- data loss, partial migration, mixed versions, rollback, stale caches, corrupt files, and crash recovery;
- browser/device/OS/toolchain/architecture differences;
- packaging, signing, loader, permission, installation, upgrade, and production configuration;
- performance cliffs, memory growth, startup regression, and unbounded resource use.

Rank findings by impact and evidence. Verify the causal path and applicability before remediation.

Red review does not decide intended product behavior. When two materially different behaviors remain plausible, record the ambiguity, owner, affected IDs, recommendation, and evidence; require user confirmation for user-owned semantics.

## Finding loop

For each verified finding:

1. Record ID, severity, evidence, affected requirement/scope, and owner.
2. Decide fix-now, design change, defer with explicit acceptance, or reject with proof.
3. Apply the smallest root-cause correction.
4. Run a scoped re-review and affected regression tests.
5. Stop and escalate after three failed repair rounds or an architectural conflict.

Before step 2, classify whether the finding contradicts a clear requirement or exposes an ambiguous requirement. For schema 1.2 material/high-risk ambiguity, reopen approval with the `AMB-n` record instead of applying a speculative fix.

## Acceptance traceability

In `evidence.md`, map:

```text
AC/SC/VO ID -> implementation paths -> command/test/manual evidence -> status -> limitation
```

Requirements are not proven merely because tests pass; tests are not proven merely because code exists. Re-read the final diff and approved artifacts, then run fresh evidence after the last relevant change.

## Claim vocabulary

- `implemented`: code/artifact exists; does not imply tests passed.
- `verified`: named fresh evidence supports the claim in stated environments.
- `accepted`: all required criteria and gates for the agreed delivery profile are satisfied.
- `release-ready`: all required release, compatibility, security, migration, packaging, and rollback gates are satisfied.
- `delivered`: the specifically authorized commit/push/PR/tag/release/deploy action completed and was checked.

Do not collapse these states.

## Delivery authority

Treat each action separately:

- edit local files;
- run local builds/tests;
- create commit;
- fetch/merge/rebase;
- push branch;
- create/update PR;
- tag or publish release;
- migrate data or deploy;
- send external message or change external system.

Only perform actions explicitly authorized by the user or clearly inherent in the requested local implementation. Resolve every independent Git root before commit or publication. Report commit, push, PR, tag, release, and deployment status separately.

## Final report

Lead with the actual outcome, then state:

- implemented scope and important design decisions;
- dependency approvals and exceptions;
- fresh static/test/audit evidence with counts or cells;
- compatibility environments passed, failed, flaky, blocked, not run, or waived;
- residual risks and remaining gates;
- delivery actions actually performed.
