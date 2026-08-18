# Repository discovery

Use this reference for nested roots, cross-repository work, unclear runtime paths, conflicting instructions, or weak source quality. Stop when the facts needed for the current decision are established.

## Roots and authority

- Resolve the actual Git root for each affected path and treat nested repositories independently.
- Treat workspace folders as navigation containers until Git evidence proves otherwise.
- Preserve unrelated user-owned changes and inspect overlapping dirty paths before editing.
- Keep mutation, dependency, destructive, external, credential, and delivery authority separate.

## Instructions and facts

Read the effective instruction chain from repository root to affected path, including an applicable override. Note source, scope, precedence, conflict, and broken references only to the detail needed for the task. Do not hash or persist the chain for ordinary work.

Inspect applicable manifests, lockfiles, toolchains, generated contracts, package topology, CI/scripts, entry points, callers, data/control flow, state, persistence, errors, cancellation, shutdown, telemetry, public contracts, compatibility, migration, packaging, and deployment configuration. Prefer an existing working analogue over invented architecture.

Distinguish:

- `observed`: directly supported by current source, tool output, or runtime evidence;
- `inferred`: a reasonable conclusion that still needs qualification;
- `owner-input-required`: a product, policy, or authority decision;
- `unknown`: evidence is absent or inaccessible.

## Skills and source quality

Use native repository controls first. Inspect a specialist Skill only when its subject is present. Avoid broad machine scans, plugin installation, or loading every available reference. A same-name collision matters only if the task needs that Skill; then bind the chosen source by its visible path/version for the current task.

Use the effective current-turn Skill catalog as the availability source. Match only affected evidence such as Rust/unsafe/Tokio, FFI/ABI, Swift concurrency/SwiftUI, React/frontend rendering, Java/Spring, SQL/schema/migration, security/privacy, accessibility, packaging/signing, or browser/device/runtime work. A capability registry supplies neutral outcomes and fallbacks, not proof of installation or an activation command.

Reject placeholder instructions, stale commands, unscoped language rules in mixed repositories, personal preferences presented as team policy, and prose that claims enforcement without a real control.

## Output

Return a compact fact base: roots, effective instructions, current behavior, affected call/data/artifact boundaries, native commands, important facts versus inferences, unresolved owner decisions, evidence limitations, and recheck triggers. Use a repository document only when these facts are durable design context for managed work; no context snapshot, catalog, or fingerprint is required.
