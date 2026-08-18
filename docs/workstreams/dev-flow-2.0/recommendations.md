# Broader recommendations after 2.0

S12–S20 bring the previously proposed RC/2.1 workflow capabilities into the 2.0 beta baseline. The remaining recommendations are organizational or product-packaging choices that should not become global workflow requirements.

## 1. Remove residual 1.x internals only when it pays for itself

The compatibility decision is resolved as a hard 2.0 cut. Packet, catalog, method-record, and paired-evaluation residue is unsupported internal debt, not a public transition surface. Remove or extract it later only when the maintenance saving exceeds the deletion and regression cost; never make ordinary 2.0 work validate it as a release promise.

## 2. Improve repository-native golden paths

When setup, verification, migration, preview, or release work repeats, invest in repository scripts, hermetic fixtures, CI reuse, preview environments, and self-service platform capabilities. Dev Flow should discover those paths, not encode every organization's operations in prompts.

## 3. Make documentation ownership explicit at team level

Teams should own architecture, contract, runbook, product-rule, and workstream truth, including archive and staleness policy. Keep this in repository conventions and normal review ownership rather than a global Dev Flow manifest.

## 4. Keep external systems optional

Issue trackers may own scheduling and cross-team status while repositories own technical and business truth close to code. Integrations should link stable identities and use the light four-field external-context contract; no external service should be required for local direct work.

## 5. Package organizational compliance separately

Regulated teams may need immutable evidence, approvals, separation of duties, or retention beyond 2.0. Provide explicit repository/organization profiles with policy authority and rationale instead of silently raising every task to the same process.

## 6. Use a program hub only for genuine multi-repository work

For programs such as GLM, one owning repository may keep the cross-repository outcome map, dependencies, integration order, and program progress. Child repositories should own their local requirements, design, implementation, and evidence; link rather than duplicate status.

## 7. Turn repeated corrections into local guidance

When Codex repeats a repository-specific mistake, update the nearest `AGENTS.md`, runbook, test fixture, or focused Skill. Do not pre-encode hypothetical failures globally. Periodically audit the effective instruction hierarchy for conflicts, stale commands, broken links, or harmful scope.

## 8. Decide whether confidentiality stays bundled

The data-security Hook is independent from process control and has a narrower deterministic boundary. Decide from user needs whether it remains bundled or becomes a separately installable confidentiality plugin; do not weaken its detector merely to reduce visible Hook count.

## 9. Review controls as product features

Every new control should name the concrete failure it prevents, ordinary-path cost, false-positive risk, owner, removal condition, and the smallest activation test that distinguishes it. Simplify, automate, specialize, or remove controls that no longer have decision value.
