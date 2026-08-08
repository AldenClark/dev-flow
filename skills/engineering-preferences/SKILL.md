---
name: engineering-preferences
description: Apply the project's Rust and frontend engineering preferences when scanning an existing repository, designing architecture, selecting or comparing dependencies, scaffolding a new project, writing or reviewing code, planning tests, designing Rust-to-Swift or Rust-to-Kotlin FFI, or choosing performance and security techniques. Use alongside dev-flow whenever a software task involves technical choices.
---

# Engineering Preferences

Use this Skill as a decision filter, not as permission to rewrite unrelated code. Establish repository facts first, preserve compatible existing conventions for scoped work, and identify migrations explicitly.

## Required sequence

1. Read `references/engineering-constitution.md` for every architecture, implementation, review, or dependency decision.
2. Read `references/language-idiom-overrides.md` for every code-writing or refactoring task and load only the language sections that apply.
3. Read `references/dependency-governance.md` before recommending, adding, replacing, enabling, or vendoring any dependency, external tool, plugin, generator, runtime, or service.
4. Read `references/preference-registry.json` as the machine-readable policy and conflict source of truth. Load only matching policy IDs/domains.
5. Read `references/dependency-preferences.yaml` only for expanded domain detail. It is subordinate to the registry; use targeted search rather than loading the entire file.
6. Read `references/engineering-preferences.md` for the human-readable catalog and baseline. It is not a second policy authority.
7. Read `references/skill-routing.md` and load the relevant specialist Skills before writing or reviewing code.

## Authority order

Apply decisions in this order:

1. The user's explicit instruction in the current task.
2. Safety, correctness, contractual obligations, and observed repository/runtime facts.
3. The approved requirement, design, change scope, and compatibility policy.
4. The engineering constitution and preferences in this Skill.
5. Relevant specialist Skills and current primary documentation.
6. Generic model defaults.

When two valid preferences conflict, present the concrete tradeoff and ask the user. Do not silently select a materially different architecture.

If an expanded reference conflicts with `preference-registry.json`, apply the registry and record the mismatch for maintenance. Current user instructions still outrank the registry.

## Non-negotiable dependency gate

Do not edit manifests, lockfiles, tool configuration, generated dependency metadata, vendored code, or service definitions to introduce a new dependency before explicit user approval. Produce the decision packet defined in `references/dependency-governance.md` and stop at the approval boundary while continuing any useful dependency-free analysis.

Examples and dependency suggestions inside a specialist Skill are advisory. They never constitute approval and never override the project's selected stack.

## Output contract

When this Skill materially affects a decision, state concisely:

- the applicable engineering preference;
- the repository evidence and constraint;
- the selected option or unresolved alternatives;
- any exception from the preference and why;
- whether dependency approval is required.

For a final diff, run the sibling flow's `audit-preferences` command. Treat gates as blockers and warnings/advisories as review prompts; verify context before reporting a violation.
