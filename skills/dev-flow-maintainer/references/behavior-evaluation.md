# Behavior-qualified suite evolution

Use this reference when promoting a capability, changing task-facing guidance, or interpreting local dogfood. It keeps deterministic contracts useful without treating them as a proxy for user results.

## Promotion comparison

Start from an observed failure or decision defect while the needed guidance is absent or insufficient. For the smallest representative fixture, predeclare:

- the decision or next action expected to change;
- a direct trigger and adjacent negative trigger;
- fixed candidate/baseline bytes, environment, black-box outcome, and negative control;
- the affected owner and a bounded claim about outcome, repair burden, or context burden; and
- a stopping rule.

Compare final outcome first, then repair/rework and context burden only when they are actually observable. Promote only when the marginal value is stable across the predeclared comparison and the negative control remains sensitive. A green schema, structural validator, route catalog, coverage report, or activation check is useful hard-boundary evidence, but never evidence of behavior improvement or productivity. Leave an unavailable comparison as `NOT RUN` or a trial; do not average it into a quality score.

## Dogfood slices

Each slice has one observable result and ends with exactly one bounded disposition:

- `proved-and-stopped` after its oracle resolves the result;
- `reopened-with-owner` when a material regression or repair needs the affected product, design, testing, or compatibility owner; or
- `externally-blocked` when the required environment or authority is unavailable.

Record only the bounded, aggregate-safe fields accepted by `scripts/analyze_dogfood.py`; never copy task text, identifiers, paths, private history, or free-form notes. A regression or repair claim requires a black-box oracle and an affected owner. Structural signals may accompany the slice but cannot make that claim. Close the slice at its disposition; a material new risk starts a new slice instead of extending the old one.

## Evaluation boundary

Deterministic tests own compatibility, schema, routing, safety, and sensitivity. The affected professional/module owner owns the product result and its repair. A separately authorized live comparison may support only its stated claim and retains first attempts; repetition or population/productivity research belongs to a separately scoped Bench study.
