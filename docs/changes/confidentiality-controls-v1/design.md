# Change design: confidentiality-controls-v1

[Manifest](./manifest.json)

## Decision

Implement one shared confidentiality policy as a first-class plugin Skill, backed by one standard-library local inspection/redaction engine. Codex gains a thin deterministic Hook adapter for `UserPromptSubmit`, `PreToolUse`, and `PostToolUse`; ChatGPT Work and ordinary Chat use the same Skill semantics plus surface-specific instruction templates and guided self-checks. A doctor and synthetic adversarial suite make repository/config drift visible without pretending employee-managed Pro configuration is immutable.

## Engineering preferences applied

- Instruction mapping: INS-1 preserves low interruption; INS-2 binds the accepted common policy and differentiated adapters; INS-3 controls current Hook/Skill protocol; INS-4 requires governed security quality and no invented cryptography; INS-5 limits delivery to repository changes and isolated verification.
- Applicable instructions: repository evidence first; use language-native Python and explicit failure behavior; add no dependency; do not invent encryption; require enforceable automated security evidence plus contextual review.
- Effective snapshot: engineering-context fingerprint `sha256:e58536aaacb149af1a4394f8543608f3570047200761c90ca49fa46ff3137421`; neutral profile fingerprint `sha256:1675459854660e70296bea197c65a87c48f3bb379a6dbcae2b9ded3961f35d3f`; no conflicts or waivers.
- Language/framework scope: Python 3 standard library for the engine, adapter, doctor, and tests; Markdown/YAML/JSON for portable Skill, instructions, Hook registration, and governance.
- Quality coverage: repository-native unittest/contract/plugin/maintainer/knowledge gates plus qualified blue and adversarial red review.

## Alternatives

| Option | Capability fit | Costs and risks | Decision |
|---|---|---|---|
| Guidance-only Skill | Portable to all surfaces | Cannot stop a supported Codex prompt/tool leak | Rejected as insufficient alone |
| One cross-product mandatory interceptor | Appears uniform | No documented pre-send Hook exists for all Work/Chat flows | Rejected as an overclaim |
| Local proxy/token vault | Stronger possible mediation | New secret store, network/dependency/operations burden, high friction | Rejected for V1 |
| Shared Skill/engine plus product adapters | Common behavior with strongest available per-surface control | Requires explicit degradation and manual proof | Selected |
| Broad entropy scanner that blocks every match | More theoretical coverage | High false-positive and workflow interruption risk | Rejected; high-confidence blocking only |

## Architecture and failure behavior

```text
shared C0-C4 policy + surface playbook
                 |
       company-data-security Skill
          /          |           \
      Codex       Work mode    ordinary Chat
        |             |             |
 local Hook      instructions   instructions
        |          + source       + minimize/
 inspect/redact    scoping         confirm
        |
 bounded result + machine-readable doctor
        |
 synthetic blue/red corpus + repository gates
```

The engine recursively inspects scalar values from bounded JSON/text payloads. High-confidence detector families identify recognizable credential formats, private-key blocks, bearer/authorization values, credentialed URLs, sensitive assignments with non-placeholder values, and bounded base64 encodings that decode to a high-confidence secret. Lower-severity direct identifiers can be replaced with deterministic HMAC labels when a local salt is supplied; the operation is non-reversible and retains no mapping.

The Hook adapter reads one JSON object from stdin and writes one bounded JSON decision to stdout. It never logs the request, finding value, or original tool result. `UserPromptSubmit` blocks high-confidence secrets because that event cannot safely rewrite the submitted prompt. `PreToolUse` denies inline high-confidence secrets and explicit reads/uploads of credential stores. `PostToolUse` replaces detected sensitive output with locally redacted content and stops the original result from continuing; oversized/unparseable security-critical payloads return a bounded safe replacement. Engine failure is fail-closed only on content that otherwise crosses a model boundary; doctor/test commands fail explicitly.

The Hook script resolves the engine under `PLUGIN_ROOT`; no import from user-controlled working-directory paths is allowed. Recursion depth, input bytes, decoded base64 bytes, number of findings, and replacement output are capped. Pattern messages name only the category and safe continuation, not the value.

Work/Chat do not receive a fake Hook adapter. Their templates instruct the model to avoid opening sensitive sources, use references and local computation, minimize selected sources, pseudonymize relationships, draft before external actions, and confirm high-impact disclosure. The doctor proves packaged template bytes and reports live account alignment as manual/not-observed unless supplied an explicit exported/checklist attestation.

## Product and UX contract

- UI impact: none in the plugin repository.
- Users and outcome: employees continue natural-language work; the assistant performs safe referencing/redaction where possible. A block contains a short reason and an immediately usable safe path, such as referring to an environment variable rather than pasting its value.
- Protected flow: C0-C3 routine work remains uninterrupted by default. C4 and explicit credential-store/exfiltration paths are the narrow deterministic stop boundary. External actions remain draft-first/confirm-first on Work/Chat.
- UX Ready: not applicable; templates and Hook messages receive black-box usability checks.

## Requirement baseline and reopening

- Bound revision and digest: requirement revision 1; recorded at approval by the packet CLI.
- Disposed ambiguities: AMB-1 binds “no drift” to detection/proof, not central immutability. AMB-2 binds adversarial validation to synthetic isolated inputs. AMB-3 binds tracked and packet requirement/design authority to identical bytes.
- Reopening behavior: stop affected implementation and return to awaiting approval for changes listed under Requirement baseline reopen conditions.

## Dependency decisions

- DEP-1: no new dependency. Python `re`, `json`, `base64`, `hashlib`, `hmac`, `secrets`, and standard path/CLI modules are sufficient. HMAC is used only for non-reversible correlation labels, not encryption or authentication of an external trust boundary.

## Change scope

- SC-D1: add `skills/company-data-security/` with `SKILL.md`, `agents/openai.yaml`, concise references, templates, and a stdlib engine/doctor CLI.
- SC-D2: add `hooks/data_security_hook.py` and register independent UserPromptSubmit/PreToolUse/PostToolUse handlers in `hooks/hooks.json`.
- SC-D3: add focused engine, Hook, doctor, and adversarial red/blue tests with synthetic fixtures.
- SC-D4: register the new first-class capability in `governance/capability-contracts.json` and update the human-readable capability/lifecycle projection.
- SC-D5: update the accepted design document, `SECURITY.md`, project governance/current truth, and a tracked change dossier with activation, limitations, rollback, and evidence.
- SC-I1: update repository/plugin validation expectations only where they derive from the capability contract; do not add fixed-count assumptions.
- SC-C1: if product Hook schema or plugin trust behavior differs from the 2026-08-14 official documentation, stop activation claims and adapt only after protocol evidence.
- SC-P1: preserve all current Dev Flow packet activation, lifecycle Hook behavior, Skill routing, CLI, manifest compatibility, and tests.
- SC-O1: no dependency, reversible vault, network gateway, endpoint agent, browser extension, enterprise admin policy, live account change, real secret fixture, installation, trust click, external delivery, commit, push, release, or deployment.
- SC-L1: repository edits and local/isolated verification only under current authority.

## Compatibility, rollout, rollback, and cleanup

The change is additive. Existing lifecycle handlers remain separate and retain their matchers. DLP handlers can be disabled by removing only their entries from `hooks/hooks.json`; the shared Skill remains guidance-only. Full source rollback removes the new Skill, adapter, tests, capability registration, and documentation changes. There is no database, migration, external service, credential, or sensitive mapping to clean up.

Recommended rollout after separate authority is: inspect plugin diff and Hook trust prompt; install/update in a disposable Codex profile; run doctor and synthetic self-test; enable shadow/observe validation if the host supports it; pilot high-confidence C4 blocking; manually align Work/Chat instructions; record per-surface evidence. This change itself does not perform those delivery actions.

## Verification obligations

- VO-1: unit-test every detector family, placeholder exclusion, repeated pseudonym relation, recursion/size boundary, and no-raw-value serialization.
- VO-2: black-box all three Hook events using official JSON shapes; prove allow, deny/block, redacted replacement, malformed input, oversized input, and engine-failure behavior.
- VO-3: run synthetic red tests for case/Unicode separation, base64 wrapping, nested structures, credential file access, upload/network commands, false-positive decoys, finding caps, and raw-secret absence from stdout/stderr/evidence.
- VO-4: tamper copied plugin files/Hook registration/templates and prove doctor returns nonzero with bounded drift identifiers; prove an intact copy passes required checks while manual external gates remain `not_observed`.
- VO-5: prove the Skill/Work/Chat templates contain surface-specific controls and explicit unsupported-enforcement language; verify no Work/Chat pre-send Hook claim exists.
- VO-6: run fresh focused tests, contract checks, plugin check, maintainer validation, full unittest suite, compileall, JSON/YAML structural checks, secret scan, `git diff --check`, and knowledge validation.
- VO-7: conduct independent blue review for requirement/integration/usability and red review for bypass/leak/fail-open/overclaim/rollback risks; resolve every blocking finding or record a scoped residual risk.
- VO-8: inspect final Git status/diff and report external installation/trust/account gates separately as `NOT RUN`.

## Testing and implementation strategy

- Implementation slices: (1) shared Skill/policy/templates, (2) engine and unit tests, (3) Hook adapter/protocol tests, (4) doctor/drift tests, (5) governance/docs/dossier, (6) full verification and blue/red closure. Each slice carries its tests and documentation.
- Black-box design: invoke public CLIs and Hook subprocesses exactly as the host does; inspect only exit code and JSON output. Exercise normal, block, redaction, malformed, oversized, unsupported/manual, rollback, and smoke paths.
- White-box design: test rule IDs/severities, placeholder filters, recursive traversal, output caps, path classification, base64 decode caps, pseudonym determinism, no input mutation, and doctor inventory/hash/schema branches.
- Oracle and test-code review: every red case includes a negative control that would pass if the relevant detector/Hook/doctor branch were removed; safe decoys challenge false positives. A leakage oracle scans captured stdout/stderr and generated evidence for the exact synthetic value.
- Specialist controls: repository-native Dev Flow maintainer, verification, and change-review contracts; official OpenAI Hook/Skill documentation; no new external scanner or dependency.

## Approval record

- 2026-08-14 user approval: implement the previously accepted cross-Codex/Work/Chat lightweight design and use red/blue adversarial methods to verify completeness and drift control. Delivery remains limited to repository implementation and local/isolated proof under the authority recorded in `context.md`.
