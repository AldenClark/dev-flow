# Dev Flow 2.0 RC.4 design

## Design position

RC.4 converts a small set of RC.3 behavioral rules into executable, failure-sensitive controls while preserving the 2.0 architecture:

- Git and repository workstreams own durable business continuity;
- source, tests, runtime observations, and artifact identity own engineering evidence;
- host permissions and explicit user authority own destructive, external, delivery, and delegation actions;
- Dev Flow routing and method selection remain advisory, bounded, and non-persisted by default.

The design introduces four executable primitives—route comparison, workstream consistency checking, volatile resource leases, and resource preflight—plus a focused test-system specialist. None is a general lifecycle engine.

## Current architecture and impact graph

The primary current call path is:

```text
user/task facts
  -> skills/dev-flow/SKILL.md
  -> skills/dev-flow/scripts/dev_flow.py route-task
     -> engineering_context capability registry
     -> methodology_system bounded selection
  -> owner Skills and references
  -> repository-native tests/review/delivery
  -> eval catalogs, transition runner, observer, dogfood analyzer
```

RC.4 changes propagate through these owned edges:

| Changed node | Direct consumers | Required protection/evidence |
|---|---|---|
| Route basis/comparison | `route-task`, Skill guidance, activation/transition tests, compact/full callers | old invocation field-equivalence; malformed/RC.3 prior route behavior; unchanged and material-delta cases |
| Workstream contract/checker | templates, `init-workstream`, managed orchestration, current workstreams | legacy workstream readability; seeded contradiction matrix; no semantic-proof claim |
| Convergence checkpoint | quality calibration, progress template, checker, semantic cases | exactly-two trigger; changed-fact reset rules; forbidden third tweak |
| Resource lease/preflight | Dev Flow CLI, verification/resource guidance, platform tests | atomic conflict, token ownership, expiry/renewal, privacy, unsupported-platform behavior |
| Test-system specialist | Skill inventory, capability contracts/registry, route need normalization, evaluation | strict negative trigger; handoff to verification; negative controls |
| Dirty-worktree ownership | implementation/progress templates, checker, orchestration/review | no authorship inference, no revert/stage, prefix/path validation |
| History fallback | native adapters, semantic cases | first failure preserved; unchanged no-retry; changed-fact one retry |
| Dogfood v2 | analyzer, schema fixtures, docs/release policy | v1 acceptance; bounded enums/counts; no content or scoring |
| R4 qualification/identity | runner, observer, releasing docs/tests | three complete attempts once; semantic-runtime, qualification-execution, and final-release identity gates |

Static tracing cannot prove external model callers or runtime-only consumers. RC.4 therefore preserves every old default path and adds focused compatibility fixtures before changing guidance.

## Architecture boundaries

### Routing plane

`route-task` continues to compute the complete current route. RC.4 adds a canonical, content-minimized `route_basis` projection containing every normalized input that can change any route output:

```json
{
  "schema_version": "dev-flow.route-basis.v1",
  "router_semantics": "route-task-rc4-v1",
  "intent": "change",
  "legacy_task_type": null,
  "work_mode_inputs": ["multi-slice"],
  "requirement": {"class": "defect-correction", "confirmation": "not-required"},
  "needs": ["verification"],
  "risks": ["weak-tests"],
  "scope_signals": [],
  "repository_facts_sha256": "sha256:...",
  "effective_skills": [],
  "method": {"signals": ["oracle-challenge"], "prerequisites": ["test-oracle"], "depth": "deep"},
  "review_signals": [],
  "knowledge_impacts": []
}
```

The field-to-input contract is exhaustive:

| Basis field | Public inputs covered |
|---|---|
| router identity | basis schema and router-semantics version |
| intent/task shape | normalized `--intent` or legacy `--task-type`; retain legacy task type because it can affect work mode, mutation, and method selection |
| requirement | `--requirement-class`, `--understanding-confirmed`, `--waive-understanding-confirmation`, `--ambiguity`, and material UI/trade-off signals |
| continuity | requested `--work-mode` plus multi-session, multi-slice, cross-module, coordination, material-tradeoff, and durable-plan flags |
| scope/owners | `--mutation`, `--ui-impact`, `--profile-operation`, `--suite-maintenance`, normalized `--unknown`, and explicit `--overlay` values |
| capabilities | normalized `--need` and `--risk` values |
| repository readiness | a digest of sorted normalized `--repo-fact` values and sorted `--effective-skill` names |
| method | normalized/derived method signals, supplied prerequisites, and resolved depth |
| review | `--material-exposure` and `--independent-review-authorized` |
| knowledge | normalized `--knowledge-impact` values |

The basis is derived after public value normalization. It excludes prompt text, file contents, task/user identity, timestamps, `--compact`, argument order, alias spelling, and the prior-route path. Free-form repository facts can contain bounded prose in current RC.3 output, so the basis stores only their aggregate digest; a caller-retained full prior route remains as sensitive as its original route output and must stay ephemeral.

An optional `--previous-route PATH` reads one bounded regular JSON file containing an RC.4 route result. The path is caller-owned and may be a host temporary file. Dev Flow does not create, discover, update, or delete it.

When supplied, the result adds:

```json
{
  "recalibration": {
    "status": "unchanged",
    "changed_dimensions": [],
    "invalidated_decisions": [],
    "next_action": "continue-without-reloading"
  }
}
```

For a change it reports sorted changed dimensions and only these invalidation classes: `requirement-understanding`, `work-mode`, `routes`, `risk-overlays`, `specialist-readiness`, `method-selection`, `independent-review`, and `knowledge-disposition`. The full current route remains present so old consumers do not need a merge algorithm. `incompatible-prior-route` performs a full route and states why reuse was unavailable.

Input handling follows existing hardened file boundaries: size bound, regular file, no symlink traversal where supported, JSON object, known schema, and fail-closed malformed input. A comparison failure never makes the current route unavailable.

### Managed continuity plane

Opted-in workstreams contain this marker in both owned files:

```markdown
<!-- dev-flow-workstream-contract: v1 -->
```

`implementation.md` owns the stable slice plan:

```markdown
| Slice | Outcome | Write prefixes | Protected paths | Evidence | Status | Decision |
|---|---|---|---|---|---|---|
| S1 | ... | `skills/dev-flow/` | `README.md` | focused tests | ready | - |
```

Allowed slice statuses are `pending`, `ready`, `in-progress`, `blocked`, `complete`, and `deferred`. `deferred` requires a non-placeholder decision reference.

`progress.md` owns only current truth:

```markdown
- State: active
- Current slice: S1
- Terminal condition: ...

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | ... | implementation | open | - |

| Mechanism | Non-progress repairs | Primary progress | Disposition | Authority/decision |
|---|---:|---|---|---|
| grader | 2 | unchanged | pending | - |
```

Allowed gates are `implementation` and `qualification`. Hard-condition statuses are `open`, `passed`, `failed`, `flaky`, `blocked`, `not-run`, and `waived`, case-insensitively normalized to the public evidence vocabulary. `waived` requires an owner decision reference and never becomes `passed`.

Allowed progress states are `planning`, `active`, `blocked`, `implementation-complete`, `release-qualified`, and `closed`. `implementation-complete` requires all required slices complete/deferred and all implementation gates passed/waived. `release-qualified` and RC.4's terminal `closed` require both gate classes. A qualification gate may remain `not-run` before qualification without contradicting `active` or `implementation-complete`.

The Markdown contract is intentionally a strict subset: one required table header, one physical line per row, no escaped/multiline cells, no `|` inside values, normalized UTF-8 text, and explicit `-` for an empty optional path/decision cell. Ambiguous syntax fails with a line location rather than being interpreted heuristically.

The `check-workstream` command accepts `--root` and `--path`, performs no mutation, and emits structured findings with locations. It verifies:

1. both markers and required headings/tables agree;
2. IDs are unique and statuses valid;
3. at most one slice is `in-progress`;
4. `Current slice` names the unique in-progress slice, or a ready/blocked slice when none is in progress;
5. terminal states have no incomplete in-scope slice or unresolved hard condition for the state's applicable gate classes;
6. deferred/waived items have decisions;
7. two non-progress repairs do not retain `pending` or authorize another same-mechanism attempt;
8. declared prefixes are normalized repository-relative paths without `..`, absolute paths, shell syntax, or root-wide catch-alls;
9. current changed paths outside the accumulated completed-plus-active slice prefixes are either declared protected/user-owned or reported as ambiguous, while guidance retains the narrower active-slice mutation boundary; and
10. the result contains `claim_limit: structural-consistency-only`.

The checker does not parse arbitrary prose, infer whether a test is meaningful, prove evidence freshness, assign authorship, or authorize status changes. Existing unmarked workstreams return `not-applicable` unless `--strict` is explicitly requested.

### Convergence plane

The convergence state machine is:

```text
working
  -- auxiliary repair, primary advanced --> working (counter reset)
  -- auxiliary repair, primary unchanged --> nonprogress-1
nonprogress-1
  -- auxiliary repair, primary advanced --> working (counter reset)
  -- auxiliary repair, primary unchanged --> decision-required
decision-required
  -- simplify/replace/narrow/defer/block --> resolved
  -- indispensable + explicit continuation authority --> working
  -- another tweak with pending disposition --> forbidden
```

The implementation does not attempt to observe arbitrary agent activity. Enforcement has two owners:

- active Skill guidance and semantic cases own direct-task behavior;
- the opted-in workstream contract/checker owns restartable managed-task contradictions.

This is deliberately narrower than an automatic circuit breaker: Dev Flow cannot know primary progress without a task-specific oracle.

### Resource coordination plane

The new standard-library module is owned by `skills/dev-flow/scripts/resource_coordination.py` and exposed through two CLI commands.

`resource-lease` supports:

```text
resource-lease acquire --kind KIND --resource VALUE --ttl-seconds N [--owner OPAQUE]
resource-lease inspect --kind KIND --resource VALUE
resource-lease renew --kind KIND --resource VALUE --token TOKEN --ttl-seconds N
resource-lease release --kind KIND --resource VALUE --token TOKEN
```

Design rules:

- allowlisted kind plus normalized resource value is hashed into a filename; raw values are not stored;
- the runtime root is explicit or derived from the platform temporary directory, then resolved, checked not to be the repository/current directory/root, created with restrictive user permissions, and rejected when ownership or same-filesystem transition assumptions cannot be established;
- every acquire/renew/release/expiry transition holds a non-blocking OS file lock on one stable, private guard inode until the transition completes; descriptor close and process death release ownership, and a contender never reclaims a live holder by timestamp;
- stored lease data is bounded JSON: schema, resource kind, resource digest, owner digest, token digest, generation, created/renewed/expiry times, and creating PID when available;
- raw tokens are returned once and never stored; comparison uses a constant-time digest check;
- renew and release require the token and current unexpired ownership;
- replacement and tombstoning occur only within the validated runtime filesystem; expired recovery is serialized and reports `expired-recovered`; corrupt, permission-unsafe, cross-filesystem, network/unknown-filesystem, or Windows sharing/deletion failure states fail closed;
- no command kills a process, removes the underlying resource, or interprets lease ownership as mutation authority;
- unsupported safe atomicity returns `unavailable` and the caller uses isolation/wait/block fallback.

Lease TTL uses bounded CLI ranges; the transition lock has no wall-clock ownership TTL. Wall-clock rollback, a live holder paused beyond the old guard interval, process death before metadata publication, crash residue, concurrent renew/release/expiry, corrupt files, permission changes, and token mismatch are explicit tests. PID is diagnostic only and never sufficient to steal an unexpired lease. The guarantee is coordination among cooperating same-user processes on tested local filesystems and lock implementations, not a security, fairness, or network-filesystem guarantee.

`resource-preflight` supports:

```text
resource-preflight --path PATH [--estimated-growth-bytes N] [--reserve-bytes N] [--require-writable]
```

It reports filesystem identity, free/total bytes, supplied budgets, and `observed`, `passed`, `blocked`, or `unavailable`. `passed` requires supplied budgets and `free - estimated_growth >= reserve`. `--require-writable` uses a securely created zero-content probe in the exact target directory and verifies cleanup; an undeleted probe is an explicit failure. Disk usage does not prove quotas, future contention, or remote-volume availability. The command never deletes user artifacts or chooses a cleanup target.

### Test-system ownership plane

The new built-in Skill is:

```text
skills/test-system-engineering/
  SKILL.md
  agents/openai.yaml
  references/test-system-integrity.md
```

Its procedure is organized around six proof obligations:

1. **Discovery** — prove the intended tests are collected/enumerated.
2. **Selection** — prove filters, shards, tags, schemes, and paths include the intended target and exclude a protected negative.
3. **Sensitivity** — use a safe negative control or mutation to prove the gate fails when the claim is false.
4. **Isolation** — prove fixtures, environment, clocks, caches, ports, devices, and cleanup do not leak between runs.
5. **Interpretation** — distinguish runner success, test success, skipped/not-run, flaky, timeout, and infrastructure failure.
6. **Representativeness** — state which platform, configuration, account, data, and integration boundary were actually observed.

`governance/capability-contracts.json` registers the owner. The neutral capability registry adds `quality.test-system.integrity` with selector `risk=weak-tests`, the new route name, and an explicit manual fallback. Existing `quality.verification.tests` remains unchanged.

The route adds canonical need `test-system` and alias `test-system-engineering`. An explicit need routes the Skill directly. Merely having tests or requesting verification does not. `risk=weak-tests` can expose the specialist in capability activation when it is effective on the current host.

Capability admission is budgeted. The current suite has four description characters and 188 ordinary static bytes of headroom. S1 freezes those baselines. S5 may raise the aggregate description cap only by the measured description of the admitted Skill plus a small explicit margin; S2/S3 must keep the existing 18,000-byte ordinary static cap by moving detailed contracts to on-demand references instead of growing top-level Skills. Budget changes and negative activation cases are reviewed together.

The handoff contract is:

```text
test-system-engineering
  -> discovery/selection/sensitivity/isolation verdict
  -> verification
  -> product claim and evidence status
```

### Dirty-worktree and history plane

Path ownership uses normalized repository-relative prefixes because Git cannot prove authorship and glob semantics would add avoidable ambiguity. The active slice may write only its declared prefixes. For path accounting in an uncommitted managed worktree, the allowed accumulated set is the union of completed-slice and active-slice write prefixes. Protected paths include user-owned pre-existing changes and adjacent areas that must not be reformatted or regenerated.

`check-workstream` obtains current changed paths from Git only when `--check-worktree` is supplied. Non-Git roots return `not-applicable`; submodules and multiple roots remain explicit separate invocations. The command reports outside-accumulated-prefix paths but never stages, restores, cleans, or rewrites them. It cannot prove which slice authored a path or whether a completed slice was later modified; final-diff review and evidence freshness retain that responsibility.

Task-history behavior remains in `codex-native-adapters.md`. The retry guard is semantic because host read operations are not owned by this repository. New transition cases provide a first failure, unchanged follow-up, changed task identity/connection fact, one retry, and repository-only fallback. No host API wrapper is introduced.

### Dogfood and evaluation plane

The analyzer accepts both `dev-flow.dogfood.observations.v1` and additive `v2`. V2 observations may contain:

```json
{
  "route": {"initial": 1, "material_transitions": 2, "delta_routes": 2, "unchanged_routes": 0},
  "convergence": {"checkpoint_required": true, "checkpoint_resolved": true, "third_tweak": false},
  "resource": {"preflight": "passed", "lease": "conflict"},
  "workstream": {"check": "failed", "contradictions": ["open-hard-condition"]},
  "test_system": {"eligible": true, "activated": true, "negative_control": "failed-as-expected"}
}
```

Every enum and count is bounded; unknown keys and content-like strings fail validation. Reports aggregate by task shape and failure category without a total score.

R4 retains three independent first attempts for the complete catalog. RC.4 reduces wasted executions by requiring, before any model spend:

1. deterministic catalog/schema/runner/observer/identity tests pass;
2. a non-spending dry run closes case selection, process, mutation, output, and token-budget contracts;
3. focused semantic development cases are complete and no source repair remains planned;
4. candidate, complete catalog, runner, observer, model, environment, and total budget are frozen; and
5. execution performs no content retry, post-hoc rescoring, or auxiliary evaluator tuning.

One full qualification run contains all three complete attempts. Live execution additionally reserves its full run allowance from one campaign ledger outside the candidate tree. The ledger is cumulative across output directories and candidate identities; allocations are never returned after failure or interruption. An infrastructure failure preserves its first evidence and triggers a candidate/runner decision before any new full run. If semantic-runtime and qualification-execution identities are both unchanged, another run is rejected and the prior evidence is reused. An identity change invalidates only the affected claim and does not automatically renew budget authority.

After two auxiliary repairs without primary qualification progress, execution stops at a version-owner disposition. The owner may require simplification or deferral, or may grant a bounded release-specific exception based on preserved historical attempts, exact-candidate partial evidence, deterministic gates, and independent review. Such an exception is recorded as `WAIVED`; it is not a three-attempt pass and cannot support stable-release or broad-effectiveness claims.

Model evidence binds to a new bounded semantic-runtime identity covering `.codex-plugin/plugin.json`, `hooks/`, `skills/`, and runtime `governance/`. A separate qualification-execution identity covers the runner's transitive repository-local imports and launched helper inputs, the complete catalog and repository fixtures, observer/scoring contracts, Codex executable digest, model/reasoning settings, and environment policy. Closure validation rejects a runtime-reachable plugin input or qualification dependency outside its admitted set; hashing only top-level runner/catalog/observer files is insufficient. After R4, only designated evidence/release records may change; their changed-path allowlist and both unchanged identities are required. Final deterministic/artifact/install evidence binds to the final release commit.

## State-transition oracles

| Transition/forbidden edge | Black-box oracle | White-box oracle | Negative control |
|---|---|---|---|
| unchanged follow-up skips reload | no new route action in semantic case; comparison says `unchanged` | canonical bases equal; no invalidation class | change one material risk and require `changed` |
| material delta recalibrates once | exactly one delta action and correct updated owner/overlay | changed-dimension mapping is exhaustive | change formatting/order only and require unchanged |
| second auxiliary non-progress requires decision | semantic case stops; checker rejects pending checkpoint | transition table reaches `decision-required` | primary-progress event resets count |
| completion with open hard condition is forbidden | checker nonzero and structured finding | terminal-state invariant fails | close condition with evidence reference and accept |
| resource conflict prevents ownership claim | one acquire succeeds, competitor conflicts | atomic record and token digest have one owner | wrong token cannot renew/release |
| test-system false green is rejected | specialist reports invalid gate | discovery/sensitivity obligation missing | intentionally broken selector/assertion must be caught |
| undeclared dirty path remains unattributed | checker reports ambiguity and does not mutate | prefix reconciliation finds unmatched path | declared protected path is retained but not attributed |
| unchanged history failure is not retried | semantic case uses fallback | retry guard lacks changed fact | corrected identity allows exactly one retry |

## Compatibility expand/contract

### Phase A: expand

- Freeze RC.3 public route, workstream generation, analyzer v1, and qualification behavior in compatibility fixtures.
- Add optional route-basis/comparison fields and new commands; default invocations remain field-compatible except for documented additive top-level fields.
- Add opted-in v1 workstream marker/checker; unmarked workstreams remain untouched.
- Add dogfood v2 while continuing to accept v1.
- Add the new Skill and need without removing `verification` behavior.

### Phase B: migrate first-party consumers

- Update Dev Flow guidance to retain one active route basis and use comparison only at material transitions.
- Update workstream templates and this RC.4 workstream to the checked contract.
- Update transition cases, large-task simulations, maintainer validation, release docs, and plugin inventory.
- Dogfood the new specialist and resource helpers on isolated fixtures before any live shared resource.

### Phase C: observe and freeze

- Prove both legacy/default and RC.4 paths in the compatibility matrix.
- Run the three-attempt complete-catalog final R4 once on the frozen semantic-runtime and qualification-execution identities.
- Do not remove an RC.3 path or require migration in RC.4. A later release may consider making the workstream contract default only after false-positive/negative evidence and explicit compatibility review.

### Rollback

- Reinstall `v2.0.0-rc.3` or `v2.0.0-rc.2`.
- RC.4 workstream Markdown remains readable as ordinary Markdown.
- Remove expired host-local lease files through the RC.4 release command before rollback when available; otherwise wait for TTL and remove only the verified user-scoped runtime directory entries. Lease files do not govern RC.3 behavior.
- Route basis, dogfood observations, and live lease tokens are not repository migrations.

## Failure and recovery matrix

| Failure | Safe continuation | Claim limit |
|---|---|---|
| prior route missing/incompatible/malformed | compute full current route and report comparison unavailable | no unchanged/delta claim |
| unmarked/legacy workstream | return not-applicable unless strict migration check requested | no managed consistency claim |
| Markdown ambiguity | fail with exact location; human resolves current truth | checker cannot choose semantics |
| lease store unavailable/unsafe | isolate, serialize, wait, or block | no exclusive resource claim |
| lease owner crashes | wait for expiry; token holder may release; bounded stale recovery | TTL window may delay reuse |
| wall clock behaves unexpectedly | fail closed on invalid expiry ordering | availability reduced; no unsafe steal |
| runtime root or filesystem guarantees are unproved | use an explicitly validated local root or serialize/isolate without a lease | resource exclusivity `NOT RUN` |
| Windows sharing prevents guard/lease replacement or cleanup | preserve state, report unavailable, and do not retry unchanged | availability reduced; no ownership/cleanup claim |
| resource budget absent | report observations only | no capacity pass |
| preflight insufficient | reduce scope, reclaim owned artifacts with authority, choose another volume, or block | planned high-growth step not run |
| test discovery/sensitivity unproved | repair harness or narrow product claim | green exit is not evidence |
| Git path authorship ambiguous | stop overlapping mutation or isolate | no attribution/completion claim |
| task-history host read fails unchanged | use current truth or block history-dependent synthesis | missing historical comparison |
| independent reviewer unavailable/unauthorized | same-context blue/red review | `common-mode-risk`; independent gate unmet |
| model budget absent | deterministic gates continue | R4 `NOT RUN`; release unqualified |

## Security and privacy

- All new JSON/file inputs are bounded, validated, regular-file checked, and treated as untrusted.
- Route bases and dogfood observations exclude prompt/task/source content by schema; free-form route facts are represented only by an aggregate equality digest in the basis.
- Resource values and owners are stored as digests; lease tokens are capability secrets and are never persisted raw.
- Runtime directories use restrictive user permissions and explicit filenames under a narrow root.
- No new command performs cleanup of the underlying resource or broad filesystem deletion.
- Workstream checking is read-only. Git inspection never stages, restores, or cleans.
- The design makes no claim against malicious local processes with the same OS account; leases coordinate cooperating tasks.

The privacy inventory is:

| Surface | Minimum data | Storage/retention | Output/access | Deletion/failure |
|---|---|---|---|---|
| route basis | categorical routing inputs, skill/method identifiers, aggregate repository-fact digest | caller-retained only; no Dev Flow cache | current caller; prior full route retains its original sensitivity | caller deletes temporary file; malformed/sensitive persistence is a limitation |
| lease | resource/owner/token digests, generation, bounded times, optional PID | restrictive host-local runtime root until release/expiry | token holder gets raw token once; inspect is redacted | token release or serialized expiry recovery; failure preserves state |
| preflight | explicit path, filesystem/capacity numbers, caller budgets | command result only | current caller | zero-content probe removed; failed removal is reported |
| workstream | repository paths, decisions, gates, evidence limits | normal repository history | repository readers | normal repository lifecycle; no raw logs or secrets |
| dogfood | bounded enums/counts and opaque case ID | authorized sanitized observation/report | maintainer/user | reject content-like fields; retain per repository policy |
| task history | named host task results needed for synthesis | in-memory unless a durable decision is reconciled into current docs | current task only | no transcript cache; failed reads leave no new residue |

Authorization review retains five explicit groups for lease/resource behavior: caller/token path; missing, stale, confused, and cross-user ownership; stable redacted errors; malformed input/retry/expiry/rollback limits; and causal proof/remediation for every finding. The lease is not cross-tenant authorization, and same-user tampering remains outside its security claim.

Primary runtime facts supporting this boundary are Python's documented [race-free temporary creation and platform/environment-selected temp roots](https://docs.python.org/3/library/tempfile.html), [atomic successful same-filesystem replacement](https://docs.python.org/3/library/os.html#os.replace), Windows-specific sharing/deletion behavior in the same tempfile contract, and [`shutil.disk_usage`'s measurement-only contract](https://docs.python.org/3/library/shutil.html#shutil.disk_usage). Supported-platform tests remain authoritative over the design inference.

## Alternatives rejected

- **Guidance-only RC.4:** RC.3 already contains much of the prose and real tasks still drifted; deterministic controls are needed at checkable boundaries.
- **Persistent task/session database:** duplicates repository continuity, creates privacy/lifecycle obligations, and recreates 1.x ceremony.
- **Automatic host-global route cache:** lacks a portable trustworthy task identity and risks cross-task contamination.
- **Repository lockfiles for live resources:** leak host runtime state into Git roots and do not coordinate unrelated repositories.
- **A daemon or distributed lock service:** disproportionate operational and dependency cost for a plugin RC.
- **Automatic cleanup/process termination:** lease ownership is not destructive authority and underlying ownership cannot be inferred safely.
- **Merge test-system responsibility into verification:** hides the separate failure mechanism and makes activation too broad.
- **Machine-only workstream state:** weakens human readability and creates duplicate truth.
- **Stratified final R4:** rejected for RC.4 because global Skill/runtime changes can affect every semantic case and one attempt outside a subset is weaker variance evidence. RC.4 instead removes repeated pre-freeze/full-run waste and retains three complete final attempts.
- **Raise or remove context budgets without measurement:** rejected; a new specialist must pay an explicit measured description cost, and ordinary top-level guidance remains under the existing static cap.

## Recheck triggers

Re-open this design if implementation shows:

- normalized route comparison cannot preserve existing compact/full consumers;
- Markdown contract parsing has material false positives/negatives on representative workstreams;
- safe atomic leases cannot be implemented on a supported platform with standard-library primitives;
- a resource class needs cross-host or destructive coordination;
- test-system activation cannot remain distinct from ordinary verification;
- current Git facts cannot support bounded path reconciliation without persisted authorship state;
- dogfood v2 requires content-bearing fields;
- the semantic-runtime or qualification-execution identity omits a reachable input or cannot distinguish evidence-only changes safely;
- three complete final attempts remain unaffordable after an explicit budget decision; or
- any new dependency, persistent repository state, external action, or broader authority becomes necessary.

## Open decisions

- None. Recheck triggers return material changes to requirements/design before implementation continues.
