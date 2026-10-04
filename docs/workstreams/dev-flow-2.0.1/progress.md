# Dev Flow 2.0.1 DLP patch progress

<!-- dev-flow-workstream-contract: v1 -->

- State: active
- Current slice: S2
- Terminal condition: scoped fix verified, pushed source identity observed and primary Dev Flow 2.0.1 installation verified.

## Current truth

- Source candidate implementation: `2.0.1` is implemented. Published stable remains `v2.0.0`; primary installation update is pending.

Delivery state: commit=not-run; hosted_ci=waived; cross_platform=not-run; independent_review=not-run; tag=not-run; artifact=not-run; publication=not-run; isolated_install=not-run.

## Evidence

- Pre-fix regression: all five Swift-expression/patch controls fail with `credential_store_path`.
- Repaired engine controls pass; replay of the original 15,843-byte Loshu patch and its original tool wrapper allows both, without executing the patch. Real sensitive-file controls remain blocked.
- First DLP module run after the code change: 43 tests, two doctor failures due to the changed protected-file digest. The maintained control baseline was updated for the exact changed engine bytes.
- Final focused DLP module: 44 tests passed (final engine includes command-field relative-path controls). Product-state validation, strict workstream checks, packaged-plugin validation, data-security doctor, changed-file Python compilation and diff whitespace checks pass. Same-context diff review found and covered bare relative filenames in shell arguments; standard-library command-field tokenization retains that protection. Full regression and hosted CI explicitly skipped; Linux/Windows, independent review, public tag/release, artifacts and isolated installation are NOT RUN.

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | Focused repair tests and original patch controls pass | implementation | passed | 44 affected tests; original patch and wrapper allowed; real sensitive paths denied |
| HC2 | Version/projections and changed files validate | implementation | passed | Product-state, strict workstream, Python compilation and diff checks pass |
| HC3 | Commit, remote identity and primary installation observed | qualification | open | Delivery pending |
| HC4 | Complete regression | qualification | waived | User explicitly requested only scoped repair verification |
