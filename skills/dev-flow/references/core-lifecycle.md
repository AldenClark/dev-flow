# Core lifecycle

Every change follows the same evidence chain; task playbooks scale its depth.

## 0. Authority and preflight

- Determine whether the request is read-only, design-first, implementation, monitoring, or delivery.
- Confirm Codex 0.147.0+, Multi-Agent V2, required tools, writable roots, repository instructions, and active Git roots.
- Select an initial collaboration profile and classify visible UI impact; refine both after discovery.
- Record destructive, external, costly, credential, release, and dependency approval boundaries.
- Create the compact or complete trace packet before the first product, project, manifest, lockfile, configuration, or documentation edit. For a non-trivial read-only audit, create it before broad findings work.

Exit when the tool/authority surface and durable packet identity are known. Do not treat implementation authority as commit, push, PR, release, deployment, or dependency approval.

## 1. Instruction and convention discovery

- Follow `repository-instructions-and-conventions.md` for every real Git root and prospective touched path.
- Record the effective `INS-n` ledger, scope, precedence, conflicts, downstream effects, and verification evidence.
- Load only applicable repository and installed Skills; preserve their approval and authority boundaries.

Exit at Instruction Ready: every touched scope has an effective rule set, material conflicts are resolved or blocking, and material rules map to requirements, design, tasks, tests, audits, or evidence.

## 2. Repository-first discovery

- Inspect manifests, dependency graph, project layout, toolchains, CI, tests, nearby implementations, public contracts, runtime configuration, and recent relevant changes.
- Establish the smallest causal and ownership boundary before scanning broadly.
- Record evidence with paths and commands; distinguish facts from inference.
- Write repository facts, current behavior, and unknowns while scanning; do not reconstruct them from memory after implementation.

Exit when the current architecture and likely impact surface can be explained from repository evidence.

## 3. Current behavior

- For bugs, reproduce or gather direct logs/traces before proposing a fix.
- For features, trace the current user or system flow and identify the missing behavior.
- For migrations/refactors, establish a clean baseline and inventory consumers, data, protocols, generated artifacts, and operational dependencies.

Exit when current and desired behavior can be compared concretely. If reproduction is impossible, state what evidence is missing and design observability rather than guessing.

## 4. Product, UX, requirement, and confirmation

- For user-facing work, classify UI impact and follow `frontend-product-and-ux-discovery.md`; do not impose UI ceremony on `none` work.
- Convert the request into actors, triggers, inputs, outputs, state changes, failures, compatibility, non-functional requirements, and acceptance criteria.
- Follow `semantic-requirement-clarification.md`: normalize any input form, investigate repository-resolvable facts, and record competing interpretations as `AMB-n` rather than silently selecting one.
- Ask only material questions that repository evidence cannot answer safely; the user is the final owner of material requirement semantics.
- Follow `collaboration-checkpoints.md`; present discoveries and recommended decisions in small batches.
- Persist each confirmed correction and material decision in requirements, decisions, and packet approval history.

Exit at Requirement Ready when every open ambiguity has an authorized disposition, affected IDs are traceable, and the current requirement revision/digest is recorded. Material UI also requires UX Ready before production implementation.

## 5. Classification and design

- Select task playbook, project profiles, risk modifiers, and delivery profile.
- Compare viable alternatives against the repository and engineering preferences.
- Define direct, indirect, conditional, protected, out-of-scope, and delivery scope.
- Define compatibility, migration, rollback, telemetry, and verification obligations.

Exit at Design and Scope Ready after user approval of material choices, complete scope, verification obligations, and dependency cards.

## 6. Task graph and delegation

- Decompose by dependency and ownership boundary, not arbitrary file counts.
- Give each task a verifiable outcome, inputs, owned files or symbols, non-goals, required checks, and stop conditions.
- Give each task the exact applicable `INS-n` rules and product/UX constraints.
- Schedule only independent read work in parallel. Serialize overlapping writes and shared mutable environments.

Exit when every acceptance criterion and risk has an owner and verification obligation.

## 7. Implementation loop

For each ready task:

1. Reconfirm the task brief and current repository state.
2. Implement the smallest coherent slice.
3. Run the narrowest meaningful check.
4. Inspect the diff for scope drift, unintended generated changes, secrets, and dependency changes.
5. Update progress, decisions, evidence, and blocked edges.
6. Replan downstream tasks when a discovered fact invalidates an assumption.

Classify late findings as implementation defects, evidence gaps, or requirement ambiguities. Reopen schema 1.2 approval for an open material/high-risk ambiguity before affected work continues; do not let implementation momentum define the requirement.

Stop for user input when a change crosses approval, dependency, destructive, external, or material scope boundaries.
No code slice is closed until its execution event, scope mapping, and verification result are durable in the packet.

## 8. Static, dynamic, and adversarial verification

- Run format, compile/typecheck, lint, dependency/security/static analysis, and generated-code checks applicable to the project.
- Execute the test matrix in controlled waves from cheap/local to expensive/remote.
- Use a separate blue audit for contract/scope and a red audit for failure, abuse, compatibility, concurrency, data loss, and rollback risks.
- Keep blue/red briefs and findings in separate documents so the adversarial review is not anchored by implementer conclusions.
- Require both audits to classify semantic findings; reviewers identify ambiguity and affected IDs but never resolve user-owned meaning.
- Trace the final diff against the instruction ledger and, for UI work, verify rendered behavior and the approved product/UX contract.
- Verify findings before remediation; rerun the affected slice and relevant regression gates.

Exit when evidence matches the accepted risk level or remaining gates are explicitly reported.

## 9. Acceptance and delivery

- Trace each acceptance criterion to fresh command, test, inspection, screenshot, trace, or runtime evidence.
- Re-read the approved design and change scope; account for every changed file.
- Report residual risks, flaky or blocked cells, and `NOT RUN` environments.
- Commit, push, open PR, tag, release, deploy, or message externally only when separately authorized.
- Validate the packet before acceptance, then archive it only after recording the accepted state and delivery outcome.

## Research basis

- OpenSpec: explore the codebase before proposing a change.
- GitHub Spec Kit: constitution, clarification, task derivation, and cross-artifact analysis.
- Superpowers: systematic root-cause debugging and fresh verification before completion.
- OpenAI model guidance: lean instructions, explicit autonomy, exact tool/output contracts, bounded concurrency, retries, and stopping conditions.
