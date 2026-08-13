# Quality-policy records

Use `kind = "quality-policy"` to express an owned outcome, not a second formatter/linter configuration and not a mandatory vendor Skill name.

Required fields include key, strength, outcome, selectors, rationale, exception policy, review trigger, and at least one of:

- `required_evidence`: stable evidence classes such as compiler/typecheck, selected lint, contract test, security scan, compatibility matrix, manual accessibility run, or code-owner review;
- `required_capabilities`: neutral IDs such as `quality.rust.correctness`, `quality.security.review`, or `quality.ffi.review`;
- `fallbacks`: qualified manual owner, alternate native control, or explicit bounded procedure.

Example:

```toml
[[preferences]]
key = "quality.auth-change"
kind = "quality-policy"
strength = "must"
outcome = "Authentication changes prove authorization isolation and secret-safe failure behavior."
applies_when = ["risk=security", "component=auth"]
required_evidence = ["authorization-matrix", "secret-log-review"]
required_capabilities = ["quality.security.review"]
fallbacks = ["qualified-security-owner-review"]
rationale = "Generic unit tests do not cover cross-tenant or log-leak risks."
exception_policy = "security-owner-waiver"
review_trigger = "auth-boundary-or-policy-change"
```

Team/project/component layers may require outcomes. Personal layers may prefer a route but cannot weaken required native evidence or shared policy. A personal Skill or personal admission may support an interactive local task; it does not satisfy a shared quality policy unless a team/project authority explicitly binds the capability or supplies a qualified shared fallback. Exact Skill paths, versions, digests, host compatibility, permissions, context footprint, collision, and admission state remain in local capability admission/effective snapshots.

Resolve selectors against path-specific phase, role, boundary, language/framework/version, path, component, and risk facts. Derive the neutral capability outcome before selecting the minimal admitted route. Coverage is satisfied by an appropriate native control, owned rule, authority-compatible admitted capability, qualified fallback, or explicit waiver. Missing one named Skill is never sufficient reason to block or install it; `not-observed` is not proof that a plugin is globally uninstalled.
