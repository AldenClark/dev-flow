# Change requirements: confidentiality-controls-v1

[Manifest](./manifest.json)

## Requirement source and understanding revisions

- Original input: after accepting the differentiated confidentiality-aware design, the user requested complete implementation plus red/blue adversarial acceptance and drift prevention.
- AI understanding revision 1: implement a lightweight, low-interruption confidentiality control stack that shares one policy across Codex, ChatGPT Work, and ordinary Chat while using only the controls each surface actually supports. Codex receives deterministic local Hook controls; Work and Chat receive portable Skill/instruction guidance and verifiable manual baselines. The implementation must not claim enterprise immutability or endpoint-wide egress prevention.
- Corrections and decisions: the prior design-only packet is the semantic baseline. One hundred percent prevention, a reversible token vault, live customer data, and user-operated tokenization workflows remain rejected. “No drift” means byte/configuration drift is detected at verification time; it does not mean a Pro account or employee-managed endpoint is centrally unmodifiable.
- Current requirement truth: revision 1 is complete and supersedes only the prior packet's implementation exclusion. Its classification, convenience, surface differentiation, and enforcement limits remain authoritative.

## User and product outcome

Security owners can distribute one Dev Flow capability that helps ordinary users and Codex keep secrets and sensitive data out of unnecessary model context without turning routine work into a security ceremony. Success is visible as: safe guidance on every supported ChatGPT surface, deterministic high-confidence secret checks on supported Codex paths, local redaction of sensitive tool output, a self-contained doctor, and a synthetic red/blue test suite that fails on control drift.

## Requirement delta

Before this change the repository contains only a design document and Dev Flow lifecycle Hooks. It has no reusable data-security Skill, DLP engine, DLP Hook adapter, employee instruction templates, surface-aware doctor, or adversarial corpus. After the change these artifacts are packaged in the plugin, registered by governance, covered by repository-native tests, and documented with honest activation and residual-risk boundaries.

## Acceptance criteria

- AC-1: A first-class `company-data-security` Skill gives one C0-C4 policy and the same low-friction treatment order—reference, local compute, pseudonymize, redact/minimize, warn/confirm, block—while selecting different playbooks for Codex, ChatGPT Work, and ordinary Chat.
- AC-2: Codex `UserPromptSubmit` and supported `PreToolUse` paths block high-confidence C4 secret exposure without echoing the secret; safe placeholders and C0-C3 routine content are not blocked by default.
- AC-3: Supported Codex `PostToolUse` paths replace detected secret or direct-identifier output with bounded locally redacted content before the original result is returned to the model, and oversize uninspectable output fails closed without returning raw content.
- AC-4: The local engine detects representative private keys, access tokens, authorization credentials, credentialed URLs, sensitive assignments, encoded high-confidence secrets, and explicit reads/uploads of known credential stores; it pseudonymizes common direct identifiers while preserving repeated-entity relationships within one invocation.
- AC-5: Detection, Hook, doctor, and tests never print, persist, or commit the synthetic raw secrets they inspect. Production/customer/employee credentials and personal data are never used as test fixtures.
- AC-6: ChatGPT Work and ordinary Chat receive distinct instruction templates and Skill paths that favor source minimization, reference-preserving work, local compute, draft-first external actions, and user confirmation. They do not claim a deterministic pre-send Hook.
- AC-7: A doctor command verifies packaged file integrity, Hook registration/schema, capability registration, required templates, and product-surface activation evidence. It labels live Hook trust and live Chat/Work account alignment as manual/not-proven unless separately observed.
- AC-8: Synthetic blue-team tests prove intended allow/redact/block behavior and usability; synthetic red-team tests cover evasion, obfuscation, oversized payloads, credential-file reads, exfiltration-like commands, Hook output leakage, tampering, and unsupported-surface overclaim.
- AC-9: Repository contract checks, plugin validation, maintainer validation, knowledge validation, Python compilation, JSON parsing, secret scan, focused tests, and the full native test suite pass on the final bytes.
- AC-10: Existing Dev Flow lifecycle behavior remains compatible: the DLP Hook is independent, bounded, standard-library-only, fail-safe, and does not activate or mutate Dev Flow packets.
- AC-11: Rollback can disable the DLP handlers without removing lifecycle Hooks, or remove the additive Skill/control files and governance registration without data migration or retained sensitive mappings.
- AC-12: Final acceptance separates repository proof, isolated Hook proof, local installation/trust proof, and live Chat/Work account proof; any unexecuted external gate is reported as `NOT RUN`, never as passed.

## Non-functional requirements

- Security/privacy: do not invent cryptography; use only standard hash/HMAC primitives for non-reversible labels, never as encryption. Never store original findings, full Hook payloads, or sensitive mappings.
- Usability: pass through ordinary public/internal content; block only high-confidence C4 or explicit credential-store/exfiltration paths. Explanations tell the user how Codex can continue safely without requiring manual token commands.
- Reliability: deterministic results for the same input and configured local pseudonym salt; bounded recursion, base64 decoding, input size, output size, runtime, and error messages.
- Compatibility: Python 3 standard library only; preserve current plugin manifest, lifecycle Hook behavior, CLI contracts, and supported Hook JSON protocol.
- Operability: one command returns machine-readable doctor status and a nonzero exit code for required drift; optional/manual checks remain distinguishable from failures.
- Maintainability: one engine owns classification/redaction; Hook and CLI adapters do not duplicate detector rules.

## Compatibility and exclusions

- Compatibility: additive plugin Skill and Hook handlers; existing Dev Flow users not handling secrets should observe no block and no packet change. Supported OpenAI Hook schemas are rechecked against official documentation current on 2026-08-14.
- Excluded behavior: enterprise workspace policy, network/proxy egress filtering, browser-extension interception, endpoint MDM, reversible token vault, automatic modification of ChatGPT account settings, legal classification decisions, scanning unsupported hosted-tool paths, guaranteed detection of novel/low-entropy secrets, installation into the user's plugin cache, Hook trust approval, commit/push/release/deploy, or a 100 percent prevention claim.

## Requirement Ready gate

- Status: ready.
- Evidence: the user explicitly approved the prior cross-surface design and now authorized implementation plus adversarial acceptance. Repository discovery found a compatible plugin Skill/Hook/eval architecture. Current official Hook and Skill documentation establishes the supported local enforcement boundary.
- Remaining decisions: none for repository implementation. Plugin installation/trust and live ChatGPT account configuration remain later delivery gates outside current authority.

## Requirement baseline

- Revision: 1.
- Digest: recorded by the content-bound CLI when this packet enters approved state.
- Baseline content: this complete `requirements.md` file.
- Reopen conditions: a change to C4 blocking thresholds, introduction of reversible mappings/cryptography/dependencies, central account enforcement, endpoint egress control, live data testing, Hook protocol drift, or expanded delivery authority.

## Ambiguity ledger

| ID | Source and interpretations | Evidence | Materiality and owner | Affected IDs | Recommendation | Status and resolution |
|---|---|---|---|---|---|---|
| AMB-1 | “No drift” could mean centrally unmodifiable enforcement or detectable configuration divergence. | Pro/manual-account constraint and product-specific Hook boundary from the accepted design. | High-risk; user semantics already established. | AC-7, AC-12 | Implement deterministic doctor/contract drift detection and explicitly reject immutability claims. | Resolved by prior user principle and current implementation request. |
| AMB-2 | “Red/blue confrontation” could imply real secrets/external exfiltration or synthetic, isolated attack cases. | AC-5 and repository security policy prohibit real credentials. | High-risk; Codex-owned safe execution. | AC-5, AC-8 | Use generated synthetic values and mocked Hook payloads only. | Resolved: synthetic isolated testing is sufficient and safer. |
| AMB-3 | Tracked governed authority could be a semantic summary or byte-identical to the packet baseline. | `bind-knowledge` rejected summary bytes under the quality authority contract. | Material; Codex-owned evidence architecture. | SC-D5, VO-6, VO-8 | Use one byte-identical packet/tracked authority baseline with the required manifest backlink. | Resolved by repository contract evidence; revision 2 adopts identical bytes. |

## Confirmation record

- 2026-08-14: user accepted the practical, convenience-preserving, differentiated cross-product design.
- 2026-08-14: user authorized implementation and requested red/blue adversarial acceptance with drift control.
