# Dev Flow state contract

`<repo>/.codex/dev-flow/<change-id>/` is ignored recovery/evidence state; tracked knowledge is separate (see `knowledge-system.md`). New packets use capability-tagged schema 2.0. Older or untagged packets keep their original contract; never upgrade them silently.

## Work modes

- `direct`: no packet and no persistent mutation; retain non-mutating micro/spike evidence inline.
- `traced`: `packet.json`, append-only `events.jsonl`, `trace.md`, and optional `artifacts/`.
- `governed`: traced state plus split context, requirements, design, execution, matrix, audits, evidence, decisions, method-selection JSON/Markdown, and child directories.

Use governed mode for explicit governance or security, FFI/ABI, migration, dependency, delivery, public-contract/data, regulated, rollback, or UI. Never silently downgrade.

## Schema 2.0 projection and capabilities

`packet.json` projects lifecycle, authority, classification, AC/SC/VO, baselines, ledgers, continuity, knowledge, and history. The first event freezes capabilities, task/mutation class, roots, collaboration, UI, compatibility, risk, and authority. Contiguous `events.jsonl` projects state/history and non-transition records; CLI mutators append, then atomically replace the projection.

New `skill_version` build tokens are exact additive capabilities:

- `change-set-transition-v1`: each `verifying` transition binds the existing `Change set` ledger/body SHA-256.
- `quality-kernel-v1`: persistent work carries `mutation_intent`, `design_digest`, `continuity_checkpoint`, and `knowledge_manifest`; capability and authority come from an exact metadata-matching creation contract.
- `method-selection-v1`: governed creation records a preliminary design selection; approval, verification, and acceptance require fresh design, verification, and review records bound to registry, risks, requirement/design bytes, events, and owner artifacts.

Tag downgrade with residual capability data/events, incomplete projection, or bound-section drift fails. Unsigned state detects inconsistency, not coordinated rewriting; tamper evidence needs external immutable storage.

## Lifecycle and semantic approval

```text
discovering -> awaiting-approval -> approved -> implementing -> verifying -> accepted -> archived
      |                |              |              |             |
      +--------------> blocked <------+--------------+-------------+
blocked -> discovering | awaiting-approval
verifying -> implementing
implementing | verifying -> awaiting-approval (open material/high-risk AMB-n required)
```

Checkpointed/co-design work records `REQ-READY`; material UI also records `UX-READY`. Approval requires a concrete design approval. Governed requirements hash exact `requirements.md`; traced hashes the `Requirement and design` body. Quality-tagged approval also binds exact `design.md` or that body. A later material correction archives approval, increments revision, clears baselines/checkpoint, and appends an exact `checkpoint-invalidated` tombstone binding reason, the then-open material/high-risk ambiguity, prior checkpoint hash, and old/new revision; fresh readiness/approval is required while recovery remains possible.

Each `AMB-n` records source, two or more surviving interpretations/evidence, materiality, owner, affected AC/SC/VO, recommendation, creation revision, status, and evidence-bearing resolution. Open material/high-risk AMB blocks approval.

## Semantic continuity

Quality-tagged implementing-or-later state requires a schema-1.1 `Continuity checkpoint`, projected into `packet.json` and `checkpoint-recorded`. Its fields are `Trigger`, requirement/design/context/repository baselines, `Repository reconciliation`, active objective/slice, last evidence, next action/stop, and drift review. Projection binds active AC/SC (plus pre-verification VO), ledger/body SHA-256, and time. Verification needs a fresh `pre-verification` checkpoint; later drift invalidates dependent evidence.

Triggers are event semantics:

- **OPEN:** `implementation-start`, `resume`, `user-steering`, `slice-start`, `reconciliation`, `premise-change`. Bytes may evolve; ordinary mutation rehydrates the objective and checks root identity plus Git `HEAD`, not full bytes per tool call.
- **SEALED:** `slice-end`, `delegation`, `phase-transition`, `pre-verification`, `final-claim`. These freeze the full-worktree premise; later deltas cannot inherit its evidence.

`resume-packet` is the recovery entrypoint. OPEN deltas need evidence-bearing reconciliation before a boundary claim; SEALED deltas block. Git `HEAD` change needs explicit reconciliation to the exact root-qualified object ID; resume never adopts it. Repository identity change reopens the premise or needs a new packet.

Observation covers every declared root (including a declared Git subtree and populated submodules); staged, unstaged, and untracked child bytes enter the full digest. SC/path labels do not narrow it. Non-Git roots record `observable=false` and need external byte-stability evidence. Use event/risk boundaries, not timers/tool counts.

## Documentation and knowledge

`trace.md` keeps source/understanding revisions, facts/authority, quality routes, requirement/design, AC/SC/VO, continuity, progress/decisions, test accountability, change set, evidence, basic blue/red challenge, knowledge/commit readiness, and delivery limits.

Governed files split the same chain:

- context/requirements: source, facts, instructions, understood revisions, semantics, ambiguity, outcome, compatibility, exclusions;
- design/execution: grounded alternatives/choice, failure/rollback/tests, scope, dependencies, tasks, checkpoint, progress/drift, knowledge/commit readiness;
- matrix/audits: resources, separate black-/white-box accountability, oracle review, blue/red findings/adjudication;
- evidence/decisions: AC/SC/VO, commands, changed files, promotion, residual gates, approvals, sources, supersession.

Before verifying, `knowledge_manifest` is mandatory: `none` binds only rationale; `add|update|deprecate` binds root, dossier `manifest.json`, and SHA-256. Structural validation must pass. Acceptance also needs terminal dossier status/disposition.

Only root writes core packet state and owns claims. Child briefs/results bind baselines and ownership; terminal child state is not root completion. `current` activates hooks, not history. `deactivate-packet` removes only a matching terminal regular-file pointer and preserves the packet.

## Identifiers and evidence

- `AC-n`: observable acceptance.
- `SC-D/I/C/P/O/Ln`: direct, indirect, conditional, protected, excluded, delivery scope.
- `VO-n`: verification obligation.
- `DEP-n`, `INS-n`, `AMB-n`: dependency, instruction, ambiguity.
- `Tn`, `TM-n`, `BLUE-n`, `RED-n`: task, matrix cell, review finding.

Declared/documented ID sets must match. Command evidence records command, absolute root, relevant environment/version, time, exit, oracle/count, artifact, and final-byte freshness. Preserve first failure. Status is `PASSED`, `FAILED`, `FLAKY`, `BLOCKED`, `NOT RUN`, or `WAIVED`; waiver is not pass.

Schema 2.0 binds each `DEP-n` identity, command/ref, files, operations, and result digests. Matrix suffixes are uppercase; `Required` is `yes`/`no`. Quality verification separately accounts black-/white-box views (or concrete N/A), oracle failure sensitivity, and commit readiness; it grants no delivery authority.

Optional preference/readiness files keep v1 shape. Quality readiness adds a validator-recomputed canonical fingerprint over all governed fields; an old self-reported fingerprint cannot preserve changed tier/outcome/route/coverage. Checkpoints need non-blocked readiness. Accepted state cannot retain blocked/checkpoint readiness or preferences.

Validate after approval, resume/compaction, material implementation/repair waves, pre-verification, and final claim. Use CLI mutators so ledger and projection stay consistent. Before a successful final: `validate-packet`, terminal transition, then matching `deactivate-packet`; preserve newer packets on runtime mismatch, and treat Stop as advisory.
