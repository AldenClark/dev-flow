---
name: change-review
description: Independently review a frozen requirement/design/scope and final change through specification, integration, maintainability, and adversarial failure lenses. Use for code review, pre-acceptance review, migration/security/FFI audits, or verified finding adjudication; require current call-path evidence and do not report style preferences or specialist output as defects without applicability and impact proof.
---

# Change Review

Return user-owned findings to the root; any resulting checkpoint remains in Default mode and follows `../requirements-design/references/user-interaction.md`.

Review intent fidelity and failure risk independently from implementation narration.

## Procedure

1. Freeze the approved revision/digest, AC/SC/VO set, base/diff, changed-file accounting, and raw verification evidence.
2. Use a clean brief without implementer conclusions. Keep blue and red records separate.
3. Blue review: trace every requirement and scope ID; inspect integration, errors, lifecycle, compatibility, migration, telemetry, docs, cleanup, and unexplained preference divergence.
4. Red review: attack malformed/boundary inputs, authorization, secrets, unsafe/FFI, cancellation, retries, races, overload, data loss, mixed versions, rollback, platform differences, packaging, and resource cliffs as applicable.
5. Route only the smallest admitted specialist capability set. Validate active language, version, artifact role, call path, host compatibility, authority, collision, and context cost.
6. Verify each candidate finding in current source and causal path. Distinguish defect, design defect, evidence gap, scope change, requirement ambiguity, and non-issue.
7. Record severity, affected IDs, proof, owner, disposition, and repair round. Re-review only affected scope plus relevant regressions.
8. Stop after three failed repair rounds or an architectural conflict.

Read `references/review-protocol.md` for clean briefs, finding discipline, specialist admission, and reopening rules.

## Boundaries

- Names such as DTO, Repository, Service, or Manager are never sufficient evidence.
- Do not load every installed review Skill or let Rust guidance leak into unrelated languages.
- Do not claim security, accessibility, compatibility, or release readiness from a generic code review alone.
