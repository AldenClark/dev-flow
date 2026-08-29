# Dev Flow 2.0 RC.4 decisions

## D1: RC.4 hardens convergence and operations

- Status: accepted for implementation
- Context: RC.3 improved correctness and transition semantics, while post-release tasks concentrated overhead in repeated routing, auxiliary repair, resource contention, and test-system uncertainty.
- Decision: prioritize executable convergence and operational coordination. Add no methodology family by default.
- Alternatives: expand the methodology pool; create a general task orchestrator.
- Consequences: RC.4 stays focused on observed failures and retains ordinary-task quietness.

## D2: Route comparison is caller-supplied and stateless

- Status: accepted for implementation
- Context: unchanged routes were repeated, but ambient cache ownership cannot be resolved portably and persisted task state would recreate 1.x behavior.
- Decision: add an exhaustive normalized route basis and optional prior-route comparison to `route-task`. The basis includes every input that can change route output, a router-semantics version, and digests rather than raw values for free-form repository facts. The caller retains any prior output; Dev Flow writes no cache and performs no history discovery.
- Alternatives: guidance-only suppression; repository route files; host-global automatic cache.
- Consequences: compatible callers can obtain deterministic delta/unchanged results without making route persistence mandatory. A first call or incompatible prior route still performs a full route.
- Recheck trigger: a supported host exposes a privacy-safe, task-scoped ephemeral state primitive with demonstrated consumers.

## D3: Managed truth uses a narrow Markdown contract

- Status: accepted for implementation
- Context: managed completion claims can contradict slice, blocker, convergence, and evidence-limit prose; free-form semantic truth cannot be proven by a parser.
- Decision: opt RC.4 workstreams into a versioned Markdown heading/table contract and add a read-only `check-workstream` command. Check structural consistency and Git path accounting only; always state that semantic correctness and evidence freshness need separate proof.
- Alternatives: no checker; a JSON task database; frontmatter as the sole source of truth.
- Consequences: humans retain readable repository continuity, obvious contradictions fail deterministically, and no hidden runtime state is introduced.

## D4: Convergence checkpoints persist only when material

- Status: accepted for implementation
- Context: recording every attempt creates ceremony, but an unresolved two-strike checkpoint must survive interruption.
- Decision: direct work keeps the counter in active reasoning. Managed work records only the current material auxiliary checkpoint and its disposition in `progress.md`; resolved historical attempts are not accumulated.
- Alternatives: a full attempt ledger; prose-only guidance; automatic third-retry circuit breaker with hidden state.
- Consequences: the terminal condition remains visible without turning the workstream into an activity log.

## D5: Resource leases are volatile single-host capabilities

- Status: accepted for implementation
- Context: concurrent tasks collided over simulators, ports, build caches, containers, and disk. The version owner approved a narrow lease exception.
- Decision: implement opt-in acquire/inspect/renew/release around an allowlisted resource key in a validated user-scoped runtime directory. Serialize every state transition with a held, non-blocking OS file lock whose ownership is released by descriptor close or process death; do not reclaim a live lock by wall-clock TTL. Use lease TTL, opaque identities, generation checks, token-bound renewal/release, and no daemon or network. Environment-selected temp roots and unsupported/network filesystems or lock primitives fail closed or remain `NOT RUN` until their guarantees are established.
- Alternatives: prose coordination; repository lockfiles; process killing; distributed lock service.
- Consequences: cooperating tasks can coordinate safely. Non-cooperating tools and remote hosts remain outside the guarantee; lease ownership never authorizes cleanup or termination.
- Recheck trigger: supported-platform tests disprove lock exclusivity, crash release, atomic replacement, or cleanup safety. RC.4 re-opened this decision when adversarial review proved that TTL unlink could create two live guard owners; the OS-lock design supersedes that unsafe premise.

## D6: Resource preflight measures; policy supplies thresholds

- Status: accepted for implementation
- Context: disk and evidence growth were handled reactively, while a universal free-space threshold would be wrong across repositories and hosts.
- Decision: make the helper report observed capacity and evaluate only caller/repository-supplied reserve and growth budgets. It never deletes artifacts.
- Alternatives: fixed global threshold; automatic cleanup; documentation only.
- Consequences: resource risk becomes proactive without inventing policy or destructive authority.

## D7: Test-system integrity has a separate specialist owner

- Status: accepted for implementation
- Context: verification owns product claims, but long test tasks exposed distinct discovery, selector, harness, fixture, runner, flake, and false-green failure modes.
- Decision: add `test-system-engineering` with strict positive/negative triggers. It owns harness validity and hands product evidence back to `verification`.
- Alternatives: enlarge `verification` indefinitely; add test methods only; activate the specialist for every code change.
- Consequences: weak-test failures get a focused procedure while ordinary feature testing stays quiet. Admission must account for the currently saturated Skill-description budget and near-saturated ordinary static-context budget; RC.4 may raise the description cap only by the measured new specialist description, while top-level ordinary guidance must remain within the existing static-byte cap by moving detail to on-demand references.

## D8: Dirty-worktree ownership is declared and reconciled, not inferred

- Status: accepted for implementation
- Context: Git reveals paths but not authorship, and user-owned changes must not be reverted or attributed to the active slice.
- Decision: managed slices declare simple repository-relative write/read/protected prefixes. `check-workstream` and final review compare current paths with declarations but never infer who authored an ambiguous change.
- Alternatives: automatic stash/reset; unrestricted shared-tree mutation; per-file workflow database.
- Consequences: overlap becomes visible and safe, while true enforcement still uses disjoint worktrees or host controls.

## D9: Task-history recovery stays adapter-level

- Status: accepted for implementation
- Context: task APIs can fail or hang, and Dev Flow cannot repair host interfaces or justify ambient history access.
- Decision: strengthen first-failure preservation, changed-fact single retry, repository/context fallback, and claim limitations in the native adapter and semantic cases. Add no task-history store or crawler.
- Alternatives: automatic repeated reads; local transcript cache; omit history-dependent work silently.
- Consequences: failure is bounded and honest without expanding data collection.

## D10: Dogfood observes convergence without scoring people

- Status: accepted for implementation
- Context: RC.4 needs evidence about route deltas, non-progress, resource conflicts, checker contradictions, and test-system activation, but task contents and productivity scores create privacy and Goodhart risks.
- Decision: extend the sanitized observation schema additively and emit only bounded counts/funnels and failure categories.
- Alternatives: raw task mining; one composite quality score; no post-release observation.
- Consequences: the release can be evaluated against its actual goals without storing sensitive content.

## D11: RC.4 uses additive expand/contract compatibility

- Status: accepted for implementation
- Context: route and Skill behavior are public to model callers, RC.3 is the current installation, and RC.2 remains the rollback tag.
- Decision: first add optional commands/fields and dual-compatible templates, then migrate Dev Flow's own guidance/evals, observe old and new paths, and remove no RC.3 contract in RC.4.
- Alternatives: breaking cutover; permanently duplicate two routing systems.
- Consequences: rollback remains practical and every new projection has a repository consumer and removal/recheck condition.

## D12: Final semantic qualification remains three complete attempts

- Status: accepted for implementation
- Context: RC.3's three full attempts consumed 9,092,076 tokens, and auxiliary evaluator repair itself delayed the primary release condition.
- Decision: keep three independent first attempts for the complete final catalog. Bound spend by finishing deterministic/focused semantic work, dry-run runner/observer/catalog contracts, freezing the candidate once, and prohibiting content retries or auxiliary evaluator repair during qualification. A failed infrastructure attempt preserves evidence and requires an explicit new-candidate decision; it is not locally tuned until green.
- Alternatives: one full attempt plus repeated subset; one attempt per case; repeated full qualification during development; score or repair model outputs during execution.
- Consequences: RC.4 does not weaken variance coverage while addressing waste before the expensive gate. The full model/token budget remains separately authorized and may be substantial.

## D13: RC.3 waivers do not roll forward silently

- Status: accepted for implementation
- Context: delegation renewed-authority wording and reference-repository comparison were explicitly waived for RC.3.
- Decision: make both explicit RC.4 semantic cases and require `PASSED`, a new owner `WAIVED` decision, or release blocking.
- Alternatives: inherit the waiver; treat literal wording alone as the oracle.
- Consequences: RC.4 closes known risk while grading the intended authority and evidence semantics rather than phrase matching alone.

## D14: Semantic runtime identity and final release identity are separate evidence bindings

- Status: accepted for implementation
- Context: recording qualification results changes repository documentation bytes after model execution, while rerunning the model after every evidence-only record creates an impossible self-reference. The current runner hashes the entire candidate tree, so RC.4 must not claim this separation without implementing and testing it.
- Decision: add a bounded semantic-runtime identity over the exact plugin inputs that can affect isolated execution—manifest, hooks, Skills/references/scripts/assets, and runtime governance. Separately bind a qualification-execution identity over the runner's transitive repository-local dependency closure, complete catalog and fixture inputs, observer/scoring contracts, Codex executable digest, model/reasoning settings, and environment policy. Evidence-only workstream/release records may change afterward only through a checked allowlist; both identities must remain byte-identical. Final deterministic, artifact, manifest, and install evidence binds to the final release commit.
- Alternatives: keep stale progress in the tagged candidate; attach untracked evidence only; rerun model qualification after writing its own result; treat all documentation as behavior input.
- Consequences: model evidence and final artifact evidence have explicit non-overlapping freshness claims. Any runtime-reachable plugin input or qualification dependency outside its admitted closure, any non-allowlisted post-R4 change, or any bound identity change invalidates R4 and requires a new candidate.

## D15: Qualification is campaign-budgeted and identity-aware

- Status: accepted for implementation
- Context: RC.4 repeatedly repaired qualification infrastructure after partial or failed R4 executions. Per-run ceilings did not bound cumulative campaign spend, and an unchanged candidate could be rerun even when no new semantic or qualification identity existed to justify new evidence.
- Decision: every live transition execution must reserve its entire per-run allowance from one external campaign ledger before the first model call. Allocations are cumulative and never released. A new run is rejected when both semantic-runtime and qualification-execution identities are unchanged; prior evidence must be reused. Changed identity invalidates only the affected evidence and does not itself authorize more spend. Interrupt and failure paths terminate the process tree, preserve bounded partial evidence and known usage, and close the run without retry. After two auxiliary repairs without primary qualification progress, further execution requires an explicit version-owner disposition: simplify, defer, or grant a bounded candidate-specific exception.
- Alternatives: reset the budget for every output directory; infer remaining budget from evidence directories; rerun after every edit; drop the three-attempt default globally.
- Consequences: campaign spend is enforced across candidates and interruptions, while evidence invalidation remains proportional to semantic and execution identity. A release-specific owner exception is recorded as `WAIVED`, never relabeled as a passed three-attempt gate, and cannot establish stable-release or population-effectiveness claims.
