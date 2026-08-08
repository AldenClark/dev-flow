# Dependency decision: <dependency-or-capability>

- Change ID: <change-id>
- Approval status: pending

## Requirement and repository evidence

<Why the capability is needed and what existing code/manifests show.>

## Exact usage

<APIs, features, call sites, runtime/build/test role, and expected usage depth.>

## Options

| Option | Capability fit | Maintenance/security/license | Compatibility | Graph/build/size/performance | Lock-in/rollback |
|---|---|---|---|---|---|
| Standard library/platform | <...> | <...> | <...> | <...> | <...> |
| Existing dependency | <...> | <...> | <...> | <...> | <...> |
| Local implementation | <...> | <...> | <...> | <...> | <...> |
| Candidate A | <...> | <...> | <...> | <...> | <...> |
| Candidate B | <...> | <...> | <...> | <...> | <...> |

## Exact impact

- Manifest/features: <changes>
- Lockfile/transitive graph: <changes>
- Native/build scripts/generated files: <changes>
- CI/platform/toolchain: <changes>
- Validation: <commands and environments>

## Recommendation and rejected alternatives

<Recommended option, rationale, and why other options lose.>

## Rollback

<Removal or replacement path.>

## Approval question

Do you approve adding `<name>` with `<version/features/source policy>` for this change?
