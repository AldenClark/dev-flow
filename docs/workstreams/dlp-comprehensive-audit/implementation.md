<!-- dev-flow-workstream-contract: v1 -->
# DLP comprehensive audit implementation

## Outcome

Audit and repair DLP false positives, secret leakage, bounds, Hook validation and one-shot approval defects using synthetic native evidence

## Scope and acceptance

- In scope: the bounded detection/redaction engine, credential-path classification, Hook input/output validation, local one-shot approval state, packaging doctor, regression tests and their maintained handling contract.
- Protected behavior: actual credentials remain blocked or fully redacted; exact test-only personal confirmations remain session-bound and one-shot; strict mode has no override; state never persists raw input. Ordinary source expressions and public/template references must not become high-confidence findings.
- Observable completion: synthetic pre-fix failures, repaired engine and Hook journeys, independent review, complete local behavioral tests and suite/knowledge/plugin/security validation pass. Every confirmed consequential finding is repaired and rechecked or has an explicit evidence-backed disposition.

## Slice plan

| Slice | Outcome | Write prefixes | Protected paths | Evidence | Status | Decision |
|---|---|---|---|---|---|---|
| S1 | Correct detection, path boundaries and complete bounded redaction | `skills/company-data-security/scripts/data_security.py`, `evals/` | - | Synthetic false-positive and leak regressions; cap/encoding/overlap controls | complete | Implementation owner: root |
| S2 | Make Hook and local confirmation failures bounded and explicit | `hooks/data_security_hook.py`, `skills/company-data-security/scripts/dlp_approval.py`, `skills/company-data-security/scripts/dlp_policy.py`, `skills/company-data-security/scripts/doctor.py`, `evals/` | - | Malformed-input, expiry, session, concurrency, diagnostic and failure-recovery checks | complete | Disjoint independent audit/repair owners |
| S3 | Review, integrate and maintain the handling contract | `skills/company-data-security/references/`, `docs/`, `CHANGELOG.md`, `evals/` | - | Independent review, complete local suite, maintained baseline and validators | complete | No delivery authorization inferred |
| S4 | Additional adversarial audit requested after the first review closed | `skills/company-data-security/`, `hooks/`, `evals/`, `.github/workflows/ci.yml`, `governance/compatibility-surfaces.json`, `docs/workstreams/dlp-comprehensive-audit/` | - | Seeded composition/property probes, state-failure recovery, CI coverage and confirmed-defect regressions | complete | User requested further bug exploration; no release or installation |
| S5 | Deeper protocol, representation and lifecycle sequence audit | `skills/company-data-security/`, `hooks/`, `evals/`, `docs/workstreams/dlp-comprehensive-audit/` | - | Actual Hook event sequences, supported format/path boundaries, controlled state and I/O failures | complete | Ten confirmed failure families repaired, including S6's full-filename exemption finding |
| S6 | Challenge regression sensitivity and independently recheck final repairs | `skills/company-data-security/references/`, `evals/`, `docs/workstreams/dlp-comprehensive-audit/` | - | Credible seeded faults, counterexamples, final source checks and independent review | complete | Ten failure families closed; six mutations caught; final local suite and independent checks passed |

## Ordering and dependencies

S1 and S2 have disjoint production owners; integrate their Hook/engine boundary before S3. The baseline is refreshed only after owned code changes, then the final target is reviewed and verified. No dependency additions are needed. Keep this plan stable; record findings, first failures, repaired slices and evidence in progress.md.

## Evidence limits

Only synthetic data and temporary state are used. Live credentials, existing approval state, remote services and another repository are outside this audit. Hosted CI, native Windows/Linux runtime, primary plugin installation and live-session reload are separate observations. Commit, push, tag, publish and install require their own user instruction; this request authorizes source repair and verification.
