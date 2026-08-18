# Flow Activation Coverage

Dev Flow tests whether representative work enters the intended branches and avoids unnecessary ones. It does not measure developer productivity, business effect, overall model quality, or the value of a Skill by counting its use.

`flow-metrics` is retained as a compatibility name for this activation test only.

## Active coverage contract

The shipped catalog is `evals/flow-activation-cases.json`. Run it through the public command:

```bash
python3 skills/dev-flow/scripts/dev-flow.py flow-metrics
```

For a semantic or isolated pilot, execute the task outside the evaluator in a fresh repository, preserve its first attempt, and describe only the observed activation in a small manifest:

```json
{
  "schema_version": "flow.activation.observations.v1",
  "cases": [{
    "id": "SEMANTIC-U1-CLARIFICATION",
    "observed": ["requirements-design", "focused-material-clarification", "default-mode-stop", "no-repository-mutation"],
    "evidence": ["isolated first response and repository diff inspected"],
    "unmet_prerequisites": [],
    "authority_violations": []
  }]
}
```

Then evaluate every catalog case through the same public command:

```bash
python3 skills/dev-flow/scripts/dev-flow.py flow-metrics \
  --lane semantic --observations /absolute/path/to/first-attempt-observations.json
```

The default semantic catalog requires an observation for every shipped case. For a predeclared affected subset, pass a smaller catalog with `--catalog`; missing observations within that selected catalog still fail instead of being inferred. The runner does not invoke or rank a model, copy credentials, or spend a model budget. Model execution remains an explicitly authorized release/research action; `flow-metrics` only checks the resulting branch evidence.

The result reports:

- each case as `matched` or `mismatched`;
- the expected and observed branch when they differ;
- missing activation, unexpected activation, or an unmet prerequisite;
- `effect_measurement: false` and `aggregate_score: null`.

The matched count is test accounting, not a quality percentage or release score. Never aggregate Skill, method, model, review, agent, question, or document counts into an effectiveness claim.

## Required branch families

Keep pairwise and boundary cases for:

1. intent: research, diagnosis, design, change, review, and delivery;
2. continuity: direct work and managed work with only the two core documents;
3. requirement understanding: U1 confirmation stop, confirmed continuation, ambiguous-defect upgrade, and established-bug/mechanical/read-only skips;
4. overlays: security/privacy, migration/data, external systems, release, irreversible action, and UI/product without automatic mode escalation;
5. specialist routing: applicable effective Skills, plugin-prefixed Skill names, and qualified fallback when a route is absent;
6. methods: high-leverage activation and ordinary-work quietness;
7. review: material/explicit activation and generic-label restraint;
8. child routing: P0-P2 Luna only for closed directed work, Terra for ordinary judgment, Sol for open/consequential work, and root-only decisions;
9. verification, knowledge, delivery authority, and native-adapter boundaries.

Add a case when a real activation omission or over-activation is observed. Prefer the smallest case that distinguishes the boundary; do not create a Cartesian matrix.

## Three evidence layers

1. Deterministic routing executes the public commands and negative controls in normal CI.
2. Semantic fixtures combine a natural-language request with a small repository shape and assert expected/forbidden activation against a preserved first-attempt observation manifest. Run these when model-facing instructions or triggers change.
3. High-fidelity isolated pilots use fresh repositories and a temporary plugin home when release confidence depends on actual Codex interpretation. Preserve the first attempt and record only expected versus observed activation, prerequisites, and evidence limits.

Semantic and high-fidelity cases are not effect experiments. They do not compare developer speed, defect rates, token economics, or one model's general quality. A pilot can show that a branch did or did not activate under its exact setup; it cannot establish a population performance claim.

## Release use

R1 always runs deterministic activation coverage. R4 model-semantic changes additionally run the affected semantic fixtures and a bounded set of isolated first-attempt pilots when the changed trigger cannot be proved deterministically. Predeclare affected branch families and expected/forbidden activation; do not require repeated trials merely to produce a score.

A result may block publication only when a required branch is missing, a forbidden branch activates, authority is exceeded, or the fixture/prerequisite is invalid. Repository tests, platform checks, security controls, artifact provenance, installation, and publication authority remain separate evidence.

## Unsupported 1.x evaluation residue

The repository still contains the 1.x paired-evaluation runner, schemas, development bank, and frozen acceptance bank as internal historical residue. They are not a supported 2.0 compatibility or research interface, not `flow-metrics`, and not a release gate. They may be removed without a migration promise.

Dev Flow 2.0 never uses their historical metric or threshold fields to rank people, optimize process activation counts, or decide releases. Flow Activation Coverage is the only active routing-evaluation contract.
