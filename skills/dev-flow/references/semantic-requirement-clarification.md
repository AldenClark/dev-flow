# Semantic requirement clarification

Use this protocol before Requirement Ready and whenever implementation, tests, or audits expose a possible mismatch in intended behavior. The objective is semantic completeness at decision boundaries, not exhaustive questioning.

## Normalize the input without judging it by length

Classify the available input as one or more of:

- complete product/design package;
- product-manager requirement or issue document;
- short natural-language request;
- bug report with incomplete reproduction or context;
- repository/runtime evidence that conflicts with the stated request.

Input form does not decide readiness. A long specification can contain contradictions; a short bug request can be sufficient after repository investigation. Extract actors, triggers, inputs, outputs, state transitions, failures, compatibility, security/privacy, non-functional needs, acceptance, exclusions, and delivery boundaries. Preserve provenance and distinguish user statements, repository facts, inference, and proposals.

## Investigate before asking

Codex owns discoverable facts: repository instructions, current code paths, tests, configuration, runtime behavior, analogous features, history, manifests, and platform constraints. Do not ask the user to rediscover these.

Ask only when at least two plausible interpretations remain after investigation and the choice can change one or more of:

- observable behavior or acceptance;
- public, persisted-data, protocol, or compatibility contracts;
- security, privacy, authorization, destructive, or external effects;
- architecture, dependency choice, material scope, rollout, rollback, or delivery;
- product/UX direction for material UI.

Consolidate one to three highest-value, user-answerable decisions. Each question states evidence, competing interpretations, affected `AC-n`/`SC-*n`/`VO-n` IDs, recommended option, alternatives and impact, safe default if one exists, and what work is blocked. Question count is not a quality metric.

## Record an ambiguity ledger

Schema 1.2 packets store stable `AMB-n` records with:

- summary and source;
- at least two distinct interpretations;
- available evidence and missing evidence;
- materiality: `low`, `material`, or `high-risk`;
- owner: `codex` for repository-resolvable facts or `user` for final requirement semantics;
- affected acceptance, scope, or verification IDs;
- a recommendation;
- creation revision, status, and evidence-bearing resolution.

All open ambiguity must be disposed before Requirement Ready. Materiality controls who may resolve it, not whether it may remain hidden.

Authorization rules:

- user-owned ambiguity is `user-confirmed` or explicitly `deferred-out-of-scope`, only at an awaiting-approval checkpoint;
- Codex-owned ambiguity is `resolved-by-evidence`;
- a Codex-owned low ambiguity may use a recorded `safe-assumption` or `deferred-out-of-scope` resolution;
- high-risk ambiguity is always user-owned;
- reviewers, workers, and explorers never choose a user-owned product meaning.

Use the CLI so validation and timestamps remain consistent:

```bash
python3 <skill-root>/scripts/dev-flow.py record-ambiguity <packet> \
  --summary <summary> --source <source> \
  --interpretation <meaning-a> --interpretation <meaning-b> \
  --materiality <low|material|high-risk> --owner <codex|user> \
  --affects <AC-or-SC-or-VO-id> --recommendation <recommended-choice>

python3 <skill-root>/scripts/dev-flow.py resolve-ambiguity <packet> \
  --id <AMB-n> --status <authorized-status> --by <actor> \
  --resolution <decision> --evidence <evidence>
```

## Bind approval to requirement content

Schema 1.2 strengthens the existing `REQ-READY` gate; it does not add a second semantic ceremony.

- Start at `requirement_revision: 1`.
- Hash exact `requirements.md` bytes for a complete packet.
- For a micro packet, hash only the `Requirement and design` section body so progress and test evidence can evolve without invalidating requirements.
- `record-approval ... requirements --id REQ-READY` records the current revision and SHA-256 digest.
- Design approval records the same revision and digest.
- Any later requirement-content change invalidates the stale approval.

In unambiguous `execute` work, the explicit implementation request may still authorize the repository-derived requirement under `collaboration-checkpoints.md`; design approval binds the computed digest. A user-owned material ambiguity automatically escalates `execute` to `checkpointed`.

## Reopen instead of burying a late ambiguity

During implementation or verification, first classify a new finding as:

- implementation defect: behavior contradicts an already clear requirement;
- design defect: the requirement is clear but the approved technical/product design cannot satisfy it safely;
- evidence gap: intended behavior is clear but proof is missing;
- scope change: the proposed behavior is neither required nor inside approved conditional scope;
- requirement ambiguity: multiple materially different intended behaviors remain plausible.

Fix implementation defects and evidence gaps within approved scope. Return design defects to Design and Scope Ready, and require scope approval for material expansion. For an open material/high-risk requirement ambiguity, stop only affected work and run:

```bash
python3 <skill-root>/scripts/dev-flow.py transition <packet> awaiting-approval \
  --ambiguity-id <AMB-n> --note <reason>
```

The transition increments the requirement revision, clears the current digest/design approval, preserves prior design approval in history, and requires an authorized ambiguity disposition plus fresh Requirement Ready/design approval. Unaffected discovery or verification may continue when it cannot prejudice the pending decision.

While a schema 1.2 packet is implementing, verifying, or blocked with an open material/high-risk ambiguity, the bundled hook denies product mutations. Packet-only edits remain available so the root can document the ambiguity and complete the reopening/confirmation cycle.

## Evidence and evaluation

Trace each `AMB-n` through requirements, execution, evidence, affected IDs, approval revision, and any audit reopening. Measure late clarification, preventable rework, assumption reversals, clarification usefulness, and first-attempt acceptance. Never optimize for more questions or approvals.

Research basis: [NASA Systems Engineering Handbook appendices](https://www.nasa.gov/reference/system-engineering-handbook-appendix/) on explicit assumptions and baselines; [GitHub Spec Kit agentic SDD](https://github.com/github/spec-kit/blob/main/docs/reference/agentic-sdd.md) on clarification and cross-artifact analysis; [ClarifyGPT](https://doi.org/10.1145/3660810) and [Clarify When Necessary](https://aclanthology.org/2025.findings-naacl.306/) on selective clarification utility; [Ambig-SWE](https://arxiv.org/abs/2502.13069), [CLARITI](https://arxiv.org/abs/2604.14624), and [ClarifyCodeBench](https://arxiv.org/abs/2607.00711) on ambiguity-aware coding-agent evaluation.
