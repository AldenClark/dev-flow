# Independent change review

## Frozen brief

For a source audit, freeze the exact source tree/revision or content digest, audited paths, applicable contracts, explicit exclusions, environment facts, and any evidence already available; change-only inputs remain `not applicable`, not silently invented. For an approved change review, provide the approved requirement revision/digest, AC/SC/VO IDs, architecture/dependency decisions, protected/out-of-scope behavior, base and final diff, changed-file list, and raw verification results. Exclude implementer self-review and expected conclusions in both modes.

## Blue lens

Verify requirement fidelity, complete scope, integration between components, public/data/protocol compatibility, errors and cancellation, ownership/lifecycle/cleanup, migration/rollback, security/privacy, performance/operations, observability, documentation, generated artifacts, and explained preference exceptions.

## Red lens

Select only applicable hypotheses:

- malformed, boundary, oversized, ambiguous, and adversarial input;
- authorization bypass, tenant confusion, secrets, injection, unsafe behavior;
- cancellation, timeout, retry, duplicates, ordering, race, deadlock, leak, overload, shutdown;
- data loss, partial migration, mixed versions, corrupt state, stale cache, crash recovery, rollback;
- browser/device/OS/toolchain/architecture differences;
- signing, packaging, loader, permissions, installation, upgrade, runtime configuration;
- performance cliffs, memory/resource growth, and unbounded work.

## Specialist routing

For each candidate route, record capability ID, provenance/digest/version, active-host compatibility, language/framework/version, artifact role/boundary, tools/permissions/side effects, context cost, source freshness, overlap/collision, structural validation, paired utility, fallback, and admission state.

Use native controls first and select the smallest approved non-colliding route set. `trial` routes require an explicit note. Unassessed, incompatible, stale, conflicting, untrusted, missing, or irrelevant routes never auto-activate. Do not copy manuals or install plugins as review remediation.

## Finding discipline

A reportable finding needs current source location, applicable rule/contract, causal path, concrete impact, reproducible or inspectable evidence, and a scoped correction. Verify names/style/context before reporting. Facts and project style guides outrank reviewer preference.

Classify as implementation defect, design defect, evidence gap, scope change, requirement ambiguity, or non-issue. A late material/high-risk ambiguity reopens affected approval; an implementation defect does not.

Record finding ID, severity, affected AC/SC/VO, evidence, owner, disposition, repair round, and fresh recheck. Use fix-now, design change, explicit defer/acceptance, or rejected-with-proof. Stop after three failed repairs.

For cross-language changes, trace every consumer and generated-artifact causal path. A post-change review names the approved diff, generated artifacts, complete changed-file list, raw verification evidence, each applicable consumer path, ABI, lifecycle, packaging/loading, version coexistence, and rollback; missing prerequisites remain `NOT RUN`.

## Evaluation

Test positive violations, safe counterexamples, and unrelated changes. Measure coverage, restraint/false positives, retention of ordinary defects, actionability, rework, context cost, and unsafe actions—not finding count.

For concurrency findings, require controlled scheduling or bounded repeated evidence, retain protected ordinary behavior tests, and omit unrelated specialist checklists.
