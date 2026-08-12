---
name: change-review
description: Independently review frozen source or an approved change for integration, maintainability, security, compatibility, and failure risks; report only verified findings.
---

# Change Review

Return user-owned findings to the root; any resulting checkpoint remains in Default mode and follows `../requirements-design/references/user-interaction.md`.

Review intent fidelity and failure risk independently from implementation narration.

## Responsibility contract

- Consumes: frozen source/change scope, applicable contracts, approved digest and changed-file accounting when a change exists, owner decisions, and available raw evidence.
- Owns: independent blue/red findings, verification of each finding, classification, severity, and repair disposition.
- Stops: on an incomplete frozen brief, verified blocker, architectural conflict, or three failed repair rounds.
- Hands off: ambiguity/scope to requirements, cause to debugging, design defects to architecture, evidence gaps to verification, and a clean result to delivery when requested.

## Procedure

1. Freeze the reviewed source/scope and applicable contract. For an approved change: Freeze the approved revision/digest, AC/SC/VO set, base/diff, changed-file and generated-artifact accounting, and raw verification evidence.
2. Use a clean brief without implementer conclusions. Keep blue and red records separate.
3. Blue review: trace every requirement and scope ID; inspect integration, errors, lifecycle, compatibility, migration, telemetry, docs, cleanup, and unexplained preference divergence.
4. Red review: attack malformed/boundary inputs, authorization, secrets, unsafe/FFI, cancellation, retries, races, overload, data loss, mixed versions, rollback, platform differences, packaging, and resource cliffs as applicable.
   Authorization/privacy review:
   - Only when the approved task or diff contains an authorization or privacy boundary, read `references/authorization-privacy.md`; otherwise do not load, mention, or apply that checklist.
5. Route only the smallest admitted specialist capability set. Validate active language, version, artifact role, call path, host compatibility, authority, collision, and context cost.
6. Verify each candidate finding in current source and causal path. Preserve applicable independently variable axes or prerequisites; umbrella labels do not replace them. Route admission is not post-change review. Detailed cross-language and evidence-gated review rules live in `references/review-protocol.md`.
7. Record severity, affected IDs, proof, owner, disposition, and repair round. Re-review only affected scope plus relevant regressions.
8. Stop after three failed repair rounds or an architectural conflict.

Read `references/review-protocol.md` for clean briefs, finding discipline, specialist admission, and reopening rules.

## Boundaries

- Names such as DTO, Repository, Service, or Manager are never sufficient evidence.
- Do not load every installed review Skill or let Rust guidance leak into unrelated languages.
- Do not claim security, accessibility, compatibility, or release readiness from a generic code review alone.
