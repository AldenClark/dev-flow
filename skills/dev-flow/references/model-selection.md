# Task-relative model selection

Use the least sufficient profile for the child's current decision. Model rank is neither a quality guarantee nor permission to reduce verification. Keep one owner when a new child would cost more context or coordination than it saves.

## Profile and workload map

| Profile | Model / effort | Current task | Do not use it for |
|---|---|---|---|
| P0 | GPT-6 Luna low | Exact symbol lookup, fixed build/test command, log filtering | Dynamic UI decisions, causal diagnosis |
| P1 | GPT-6 Luna medium | Narrow research, bounded log classification, specified mechanical edit | Unsettled behavior or ownership |
| P2 | GPT-6 Luna high | Confirmed bounded fix/feature slice, directed mapping with a known oracle | Inventing an unresolved contract |
| P3 | GPT-6 Luna xhigh | Large context or many steps with closed semantics | Complex judgment inferred just from volume |
| P4 | GPT-6.1 Sol medium | Ordinary coding, diagnosis, independent review, cross-component integration, adaptive native verification | A demonstrated deep or compound unresolved decision |
| P5 | GPT-6.1 Sol xhigh | Deep unresolved causes, genuinely conflicting oracles, interacting open contract/high-consequence decisions | Routine carefulness, many files, product importance, repeated builds |
| P6 | GPT-6 Astra xhigh | Deep unresolved reasoning + interacting unknowns + cross-boundary impact; or documented current-Sol failure + deep unresolved reasoning | Risk labels or an ordinary tool/environment failure |
| PX | GPT-6 Astra max | Explicit exceptional evaluation/campaign inside its separately authorized scope | Automatic fallback or everyday engineering |

Choose the workload from the actual child unit, not the parent project's hardest problem. An exact command stays `exact-verification`; observing and adapting a device/UI flow uses `adaptive-verification`. Ordinary review uses `routine-review`; `high-risk-review` retains full security/data/compatibility/rollback controls but starts at P4. Cross-component work with ordinary judgment starts at P4; a closed bounded slice can use P2 or P3 even inside that project.

Examples that commonly fit P4 without reducing checks:

- implementing adapters across established APIs, ownership, and state transitions;
- reviewing a localized security/privacy repair with a known attack regression and negative control;
- repairing a reproducible DLP matcher false positive while preserving real-secret denial;
- diagnosing a bounded concurrency/lifecycle/recovery defect with distinguishable causes;
- checking a compatible dependency update against the affected native protocol path;
- repairing a known fixture, wait, or runner defect with a failure-sensitive oracle;
- navigating and checking an adaptive native UI flow against confirmed requirements;
- reviewing release identity, ordinary integration, or adversarial counterexamples on a stable diff.

Pure execution, copying, formatting, and closed mechanical fixes in those domains can use P0–P2. Credentials, migration, data deletion, FFI, device work, rollback, and release still require their applicable specialist, authority, negative controls, native checks, and unrun-environment limits at every profile.

## Signals describe observed reasoning needs

State the relevant observation and the decision it prevents in the existing child brief. A keyword is not evidence. Do not copy every parent risk or signal into an execution child's route.

- `oracle-challenge`: the success/failure criterion is in question, not merely that a test or negative control will be run.
- `conflicting-evidence`: credible observations support incompatible conclusions, not two logs with different wording.
- `nondeterminism`: ordering or variability obstructs the result, not merely that async code exists.
- `interacting-unknowns`: resolving one unknown changes the valid choices for another, not several independent TODOs.
- `deep-unresolved`: identify concrete competing explanations/constraints, the evidence that leaves them unresolved, and the consequential decision still blocked. No prior lower-model run is required when the complexity is already visible.
- `failed-sol-discrimination`: a documented reasoning/implementation discrimination failure of current GPT-6.1 Sol on this task. Tool access, timeout, fixture, missing device, old-model results, or a failed command alone do not qualify.

Single `oracle-challenge`, `conflicting-evidence`, or `nondeterminism` signals select P4. P5 remains available for:

1. concrete `deep-unresolved` or documented `failed-sol-discrimination`;
2. `conflicting-evidence` + `oracle-challenge` that dispute the same outcome;
3. `ambiguity` + `interacting-unknowns` + `cross-boundary-impact` for an open contract;
4. `ambiguity` + `interacting-unknowns` + `high-risk-acceptance` for an unresolved high-consequence decision.

P6 keeps its existing compound conditions. `closed-scope` or `deterministic-oracle` does not erase a real unresolved condition: reclassify stale signals rather than silently suppressing a contradictory one. Do not cap a truly difficult task at P4 to meet a low-cost quota.

## Overrides, host limits, and follow-up

Prefer the policy result. An explicit `--profile P5` or `P6` above policy requires `--selection-reason` with one concise task-specific reason for the additional depth. This is the AI caller's explanation, not human approval, a budget grant, or proof that the reason is true. Matching-policy profiles and P0–P4 selections need no such flag. Explicit below-policy selections still require `--acknowledge-downgrade`; PX still requires `--acknowledge-exception` and does not gain campaign authority from that flag.

Existing CLI names, profiles, model/effort vectors, output schema, and ordinary automatic routes remain supported. Old unexplained above-policy P5/P6 commands now return `invalid` with a corrective message; add the reason if warranted or use the policy route. Do not retry with invented reasoning signals just to regain the old profile.

Use the full relevant inventory observed on the actual dispatch host, including available Luna and Sol medium choices. A deliberately high-only inventory is not proof that lower profiles are unavailable. A capability-limit suggestion never dispatches automatically or authorizes spending; investigate the inventory, then use an explicitly explained fallback if the host really lacks the selected route. Never silently substitute an unsupported model or effort.

Re-evaluate when the next independently useful brief materially changes: a complex recovery repair does not make its later incremental build P5. Discard resolved uncertainty and choose the new unit's profile. If the host cannot change a running child's model, finish a very short continuation when cheaper than a handoff; route a genuinely new unit before dispatch. Do not spawn solely to lower a label, reload unchanged guidance, or create receipts for unchanged continuations.

## Quality safeguards and evidence limits

The task outcome, sensitive native oracle, first failure, material recovery, specialist controls, and independent review where needed stay fixed when model choice changes. A material reasoning failure reopens the relevant diagnosis and can justify more depth; inspect environment/fixture causes first. Stop repeated unsuccessful attempts and escalate or return the concrete blocker rather than run an endless cheap-model retry loop. Never force a paid low-model trial before selecting P5 when its need is already established.

Treat the 2026-10 calibration as a bounded routing trial: it corrects observed blanket promotions and unexplained overrides, but equivalent model quality and lower task cost have not been experimentally established. The parent owns the outcome and integration. The expected change is fewer high-profile routes for ordinary tasks while complex positive controls retain P5/P6; stop at an accepted native outcome. Reopen if a lower route causes a material correctness/requirement/rework regression, retain the first failure, and restore depth for that decision. No automatic comparative model calls or install/release actions are authorized.

Deterministic tests qualify selection, authority, host checks, and positive/negative routing boundaries only. Live matched-model comparison remains `NOT RUN` unless separately authorized and budgeted; no quality-equivalence or monetary-saving claim follows from static green. The registry and this reference own rollback of calibration; published and installed versions remain separate facts.
