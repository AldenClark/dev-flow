# Security, privacy, safety, and supply-chain methods

These families are related but not interchangeable:

- security asks how an adversary can violate confidentiality, integrity, availability, identity, or privilege;
- privacy asks how data processing can harm people through linkage, disclosure, unawareness, retention, or non-compliance;
- safety asks how control actions and interactions can cause unacceptable loss, including without component failure;
- supply-chain assurance asks whether source, dependency, builder, and artifact provenance is trustworthy and reproducible.

## Security stack

Start with assets, actors, flows, trust boundaries, and `use-misuse-abuse-case`. Apply STRIDE per boundary/element. Use an attack tree when a consequential adversary goal needs path decomposition. Map each credible threat to prevention, detection, response, residual assumption, and failure-sensitive evidence.

Use SSDF/SAMM as control organization, not a security score. Fuzzers, scanners, and sanitizers cover specific classes; none proves the system secure. Cryptography, authentication, authorization, secrets, and unsafe/FFI boundaries require qualified/native controls and cannot be invented by the method layer.

## Privacy stack

1. Build `data-lineage-provenance`: sources, transformations, stores, recipients, retention, access, deletion.
2. Build `ontology-identity-ledger` when linkage/equivalence crosses identifiers or time.
3. Apply LINDDUN to the actual flow.
4. Map harms and mitigations to minimization, purpose, consent/awareness, access, retention/deletion, and evidence.

Do not label the output “legal compliance.” Missing policy/legal/product decisions stay owner gates.

## Safety selector

| Failure question | Method |
|---|---|
| How can a component fail and effects propagate? | FMEA |
| What combinations can cause a top loss? | Fault tree |
| What happens under no/more/less/reverse/early/late/other-than deviations? | HAZOP-style guidewords |
| Which unsafe control actions/interactions can cause loss even without failure? | STPA |
| How do we argue a consequential safety claim from evidence and assumptions? | GSN assurance case |

For every safety artifact, define the system boundary, losses, domain owner, hazards, controls, assumptions, and external/regulatory gates. Formal-looking diagrams without domain expertise are worse than an explicit evidence gap.

## STPA recipe

1. Define unacceptable losses and system-level hazards.
2. Draw controllers, controlled processes, control actions, process models, and feedback.
3. For each control action ask: not provided, provided incorrectly, wrong timing/order, stopped too soon/applied too long.
4. Develop causal scenarios including flawed feedback/model, communication, timing, environment, and organizational control.
5. Convert safety constraints into design invariants, monitoring, tests, operating procedures, and assurance claims.

## Assurance case guardrails

A GSN-style argument must expose scope/context, assumptions, strategies, evidence, and defeaters. Every leaf is supported or unresolved. Evidence freshness and independence matter more than diagram completeness. A structured argument cannot turn weak evidence into strong assurance.

## Supply-chain stack

Inventory exact dependencies, source references, generators, builders, artifacts, manifests/locks, and ownership. Select an achievable SLSA/provenance target; verify attestations/hashes where available; record opaque stages and rollback. SBOM/provenance proves origin/integrity properties, not source correctness, compatibility, or runtime safety.
