---
name: change-review
description: Independently review current source or final diffs and report verified, consequential findings.
---

# Change Review

Review the actual source and diff, not the implementer's narrative. Review depth follows blast radius and risk; ordinary changes do not require ceremonial blue/red reports.

This Skill may operate alone for an independent read-only review. If the request also authorizes material repair, crosses repositories, needs managed continuity, or assesses high-risk delivery, load `dev-flow` as the coordinating kernel when it is available and not already active; keep this Skill as the finding owner.

## Procedure

1. Establish the objective, repository state, reviewed paths/base, relevant contracts, and raw verification evidence.
2. Inspect intent and scope fidelity, integration paths, errors, lifecycle, compatibility, migrations, telemetry, documentation, cleanup, dependencies, generated surfaces, and user-owned changes as applicable.
3. Adversarially inspect relevant boundary inputs, authorization, secrets, unsafe/FFI, cancellation, retry, race, overload, data loss, mixed versions, rollback, platform, packaging, and resource risks.
4. Load only specialists justified by the active language, version, artifact role, and failure surface.
5. Verify every candidate finding in current source and its causal path. Report severity, proof, consequence, and a bounded repair; omit speculative or style-only noise.
6. If the review exposes a weak or easy-to-fake oracle, route the evidence question to verification and prefer a practical ready test/mutation/counterexample method before a blocked high-cost independent derivation. Use an explicit fallback or reasoned abstention; never report method selection itself as a finding or proof.
7. After repair, re-review the affected scope and relevant regressions. Escalate recurring repair failure to design/debugging rather than repeating a fixed number of reports.

Read `references/review-protocol.md` for large or independent reviews and `references/authorization-privacy.md` only when the change contains that boundary.

## Boundaries

- Names and patterns alone are not findings.
- Generic review does not prove security, accessibility, compatibility, runtime, or release readiness.
- Do not require acceptance IDs, digests, frozen packet artifacts, or separate blue/red documents unless a repository-native process consumes them.
