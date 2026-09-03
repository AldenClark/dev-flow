# Dev Flow 方法论池与专业推理层

本文件解释 Dev Flow 为什么以及怎样选择方法。机器可读真相位于 [`governance/methodology-pool.json`](../governance/methodology-pool.json)，详细操作卡按需位于 [`skills/dev-flow/references/`](../skills/dev-flow/references/)；这里不复制 117 张完整方法卡，避免文档和选择器分叉。

> Dev Flow 2.0：方法池是新颖/高不确定问题的有界研究工具。高杠杆失败机理会通过 task-facing `route-task` 主动匹配，但结果不要求落盘，也不参与 direct/managed 生命周期门禁。下文的 `record-methods`、AC/SC/VO 和 packet 绑定属于 1.x 历史兼容说明。

## 目标与边界

方法论层解决的是“面对这个已观察到的失败机理，AI 应该怎样专业地推理、产出什么、用什么证据检验”的问题。它不取代：

- `requirements-design` 对产品/需求语义的所有权；
- `architecture-decisions` 对类型、边界、状态、并发、兼容和资源设计的所有权；
- `verification` 对测试推导、执行环境和证据的所有权；
- `change-review` 对独立发现与分级的所有权；
- `dependency-decisions` 与 `delivery-readiness` 对依赖和交付授权的所有权。

“所有可能的方法”没有可验证的封闭边界。本池采用可治理定义：只纳入能够对应软件、系统、UX、运营或 AI Agent 实施失败类，并能给出正向触发、负向触发、前提、步骤、产物、证据、局限和回退的方法。当前版本广泛覆盖完整生命周期，但不宣称穷尽全部人类管理理论、行业标准或受监管认证程序。

## 我们从业界成果中吸收了什么

### 1. 需求不是一句自然语言，而是可追踪的语义基线

[ISO/IEC/IEEE 29148](https://www.iso.org/standard/72089.html) 与 [NASA Systems Engineering Handbook](https://www.nasa.gov/reference/systems-engineering-handbook/) 强调需求的完整性、可验证性、追踪和生命周期控制。Dev Flow 把它适配为需求修订/摘要、歧义责任、AC/SC/VO 与重开规则；再用 Specification by Example、决策表、状态模型、质量属性场景和身份账本补足自然语言最常见的缺口。

### 2. 架构质量来自权衡与反例，不来自架构名词

[SEI ATAM](https://www.sei.cmu.edu/library/the-architecture-tradeoff-analysis-method/) 将业务驱动、质量场景、敏感点和权衡点连接起来。Dev Flow 不强制完整工作坊，而是按风险选择轻量质量场景/替代方案表或深度 ATAM；把结论继续映射到可执行验证，而不是给架构打总分。

DDD 的 [Bounded Context](https://martinfowler.com/bliki/BoundedContext.html) 用于处理同一概念跨上下文不同模型的问题；它与 ontology/identity ledger、数据血缘、context map 组合，而不被泛化为“所有代码都做 DDD”。

### 3. 形式方法必须匹配失败机理

- [Alloy](https://alloytools.org/faq/what_kind_of_analysis_does_the_alloy_analyzer_do.html)：有限作用域内的集合、关系、身份、权限和配置反例；
- [TLA+](https://lamport.azurewebsites.net/tla/book-01-11-10.pdf)：状态转换、并发/分布式交错、安全性、活性与公平性；
- [Event-B/Rodin](https://wiki.event-b.org/)：从抽象事件系统到更具体系统的逐步精化与证明义务；
- [seL4 refinement proofs](https://sel4.systems/Verification/proofs.html)：抽象规范、实现和精化映射之间的高保证案例；
- Petri/process model：并发工作流、同步、资源 token、可达性和死锁；
- theorem proving：稳定且高后果的数学/程序性质。

选择器不会因为“任务很大”就上形式方法。关系、时序、精化、证明分别有明确的 failure signal、`formal` 深度、前提与回退；没有模型检查器、证明能力、领域所有者或 code mapping 时只能报告缺口。

### 4. 测试先解决 oracle problem，再选择工具

[Oracle Problem survey](https://discovery.ucl.ac.uk/id/eprint/1471263/) 说明了为什么“测试跑过”不等于能判断正确。Dev Flow 先独立推导黑盒和白盒义务，再从以下手段中按 oracle 条件选择：

- 等价类、边界值、决策表、状态转换；
- [NIST ACTS](https://csrc.nist.gov/projects/automated-combinatorial-testing-for-software) 的 t-way 组合测试；
- [QuickCheck](https://www.cse.chalmers.se/~rjmh/QuickCheck/manual.html) 一类 property-based testing；
- model-based、metamorphic、differential、characterization/golden master；
- contract/consumer-driven testing；
- mutation 与 [semantic mutation](https://eprints.whiterose.ac.uk/id/eprint/196292/)；
- fuzzing、static analysis/sanitizers、symbolic execution；
- 并发 history/linearizability、故障注入/chaos、性能/load/stress/soak；
- accessibility、usability、compatibility matrix、migration replay/rollback。

mutation score、coverage、test count 和 green status 都不是质量目标。关键测试必须说明它怎样在目标缺陷存在时失败。

### 5. 安全、隐私和安全性不是同一张清单

[NIST SSDF](https://csrc.nist.gov/pubs/sp/800/218/final)、[Microsoft STRIDE](https://www.microsoft.com/en-us/securityengineering/sdl/threatmodeling) 与 [OWASP SAMM](https://owasp.org/2020/02/11/SAMM-v2) 提供安全开发和威胁分析框架；[LINDDUN](https://www.nist.gov/privacy-framework/linddun-privacy-threat-modeling-framework) 处理隐私链接、识别、披露、无感知等威胁；[MIT STPA](https://psas.scripts.mit.edu/home/books-and-handbooks/) 处理控制互动导致的系统性损失；[GSN](https://scsc.uk/gsn-standard) 把高后果声明、论证、证据、假设和反驳项显式化；[SLSA](https://slsa.dev/spec/v1.2/about) 处理供应链来源和构建 provenance。

方法池分别保留这些 failure model，避免把扫描器当完整安全保证、把数据地图当法律合规、把 FMEA 当 STPA、或把 assurance case 图形当证据。

### 6. 实施与迁移需要共存、回滚和公共行为保护

TDD/ATDD/BDD、typestate/smart types、coherent vertical slice、formal inspection 是常用实现手段；[Parallel Change](https://martinfowler.com/bliki/ParallelChange.html)、[Evolutionary Database Design](https://martinfowler.com/articles/evodb.html) 与 [Contract Test](https://martinfowler.com/bliki/ContractTest.html) 用于非原子公共契约/数据迁移。

[Cleanroom Software Engineering](https://doi.org/10.1109/MS.1987.231413) 与 N-version programming 被保留为高成本 specialist 方法，并明确其负向触发和 common-mode failure：前者不能被简化为“不运行代码”，后者也不能假设多数投票能抵抗共享规格、工具和概念错误。

### 7. 交付与运营证据必须与实施证据分离

[DORA Continuous Delivery](https://dora.dev/capabilities/continuous-delivery/)、[Google SRE Workbook](https://sre.google/workbook/part-I-foundations/)、[Principles of Chaos Engineering](https://principlesofchaos.org/)、[OpenTelemetry Specification](https://opentelemetry.io/docs/specs/otel/) 和 [USE Method](https://www.brendangregg.com/usemethod.html) 被适配为 small batch/CI、canary、blue-green/shadow、SLO/error budget、observability、game day 和 postmortem。

没有真实部署授权、cohort、telemetry、回滚和生产观察时，选择器只提供计划/回退，现场证据保持 `NOT RUN`。

### 8. AI Agent 需要自己的质量方法

[OpenAI harness engineering](https://openai.com/index/harness-engineering/) 与 [Anthropic context engineering](https://www.anthropic.com/engineering/effective-context-engineering-for-ai-agents) 强调 agent 可见的仓库知识、工具反馈和长任务上下文；[OpenAI coding-eval analysis](https://openai.com/index/separating-signal-from-noise-coding-evaluations/)、[Anthropic agent evals](https://www.anthropic.com/engineering/demystifying-evals-for-ai-agents) 与 [METR controlled study](https://metr.org/Early_2025_AI_Experienced_OS_Devs_Study-paper.pdf) 提醒我们关注 case/grader 健康、模型/工具身份、首轮行为、随机方差和真实开发者结果，而不是把单一 benchmark/速度结论当通用真理。

因此基础池加入 repository legibility/context engineering、deterministic harness/agent-computer interface、authority/tool boundary、semantic checkpoint/action ledger、agent eval design、identity pinning、case-health/contamination 与 multiple first attempts。

在此基础上，1.1.0 把 AI 编程与通用 Agent 的专业推理组织为九组风险主题，并进一步细分为 14 个可观察 failure model，避免 broad Agent signal 把 specialist 方法一起触发：

1. **自主性过度**：用 minimum-effective autonomy 和 human-agent function allocation 比较脚本、workflow、单 Agent、evaluator loop、多 Agent；稳定流程不因“AI 能做”就升级自治。
2. **部分可观测与开环漂移**：用 belief-state/active information、receding horizon、behavior tree 或 HTN，把已知/未知/陈旧事实、下一次高信息量观察、执行 horizon 和重规划条件显式化。
3. **补丁过拟合**：用 CEGIS 式 counterexample-guided repair，让独立反例持续约束候选修复；不允许通过削弱测试让补丁通过。
4. **运行安全与时间性质**：用 Simplex/runtime-assurance shield、temporal runtime verification，在外部 effect 前独立约束行为，并把顺序、期限、最终处置、retry/cancel/compensation 写成可观测性质。
5. **非原子外部副作用**：用 saga/compensating actions、幂等键、append-only action ledger 和 reconciliation 管理部分提交；明确 compensation 不等于 rollback。
6. **不可信上下文与记忆**：用 instruction/data provenance taint 和 agent-memory lifecycle governance 管理来源、优先级、scope、freshness、poisoning、correction、retention 与 deletion。
7. **多 Agent 协调**：先用 task dependency/communication cost 选择拓扑和 exclusive ownership；只有动态异构分配确有必要时才进入 contract-net specialist。
8. **过程级评测**：用 trajectory/intervention evaluation 同时观察最终状态、动作轨迹、授权、副作用、恢复与 teardown；通过受控干预区分 prompt/context/tool/environment/model/infra 失败。
9. **统计与仿真有效性**：multiple first attempts 要预声明配对/随机化、分析单位、停止/重试规则和基础设施错误；conformal risk control 只有在 held-out calibration 和分布假设成立时才给覆盖/选择性声明；digital twin 明确 reality gap，不能冒充真实现场验收。

新增方法的主要研究锚点包括 [Agentless](https://arxiv.org/abs/2407.01489)、[Building effective agents](https://www.anthropic.com/engineering/building-effective-agents)、[UALA](https://arxiv.org/abs/2401.14016)、[CodePlan](https://arxiv.org/abs/2309.12499)、[CEGIS](https://digicoll.lib.berkeley.edu/record/134841)、[Simplex runtime assurance](https://arxiv.org/abs/2102.12981)、[Runtime Verification](https://arxiv.org/abs/1707.05555)、[Sagas](https://www.cs.princeton.edu/research/techreps/598)、[NIST agent hijacking](https://www.nist.gov/news-events/news/2025/01/technical-blog-strengthening-ai-agent-hijacking-evaluations)、[indirect prompt injection](https://arxiv.org/abs/2302.12173)、[Human-AI Interaction Guidelines](https://www.microsoft.com/en-us/research/publication/guidelines-for-human-ai-interaction/)、[HTN planning](https://arxiv.org/abs/1403.7426)、[Behavior Trees](https://arxiv.org/abs/2203.13083)、[Conformal Language Modeling](https://arxiv.org/abs/2306.10193)、[SWE-agent ACI](https://arxiv.org/abs/2405.15793) 以及业界多 Agent 与评测基础设施研究。完整、稳定 ID 和适配边界以 registry 为准。

### 9. 方案设计与方案审计必须把方法选择变成可验证流程

1.1.1 增加了六类过去覆盖不足、但对复杂系统方案很实用的方法：ISO/IEC/IEEE 42010 风格的多视图一致性、Reflexion Model 风格的实现—架构符合性、OMG BPMN 协作流程、ISO/IEC 25012 数据质量场景与对账、SEI CBAM 成本收益架构决策，以及跨语言 ABI/所有权契约。它们只在对应 failure signal 出现时进入工作集，不能由 `large-feature` 或 `architecture` 宽标签单独触发。

方法本身仍不构成执行证据。新受治理包在创建时自动生成初步设计选择，并在设计批准、进入验证、最终接受前分别要求新鲜的 design、verification、review 记录；每条记录绑定方法库摘要、需求/设计字节、规范化风险、前提、owner 和计划产物。独立/旧工作仍可只使用 `method.selection.v1`，不会被可变字段静默升级。

## 方法池结构

当前机器池包含：

| 层 | 内容 | 选择方式 |
|---|---|---|
| Foundation | 注册表按内部适用位置保留的基础纪律 | 由当前专业 owner 按实际问题选择，不是阶段门禁 |
| Automatic | 由风险模型和阶段触发的专业方法 | `starter` 或 `deep` |
| Specialist | 形式化、高保证、高成本或需专家的方法 | 仅 `formal` 且显式 signal/前提满足 |
| Source registry | 标准、原始方法、权威手册、研究与优秀实践 | 所有方法至少一个来源 |
| Risk models | 观察、加权阈值、失败假设、方法栈、证据义务、升级规则 | 确定性匹配 |
| Negative rules | 低风险 routine 禁止形式方法；无现场权限禁止 live/production experiment | 先于前提和 context cap |

当前池含 117 个方法、73 个来源和 38 个确定性风险模型（其中 14 个为 AI coding/general-agent 专项模型，6 个为 1.1.1 的方案设计/审计与 FFI 补强模型）。方法家庭包括 foundation、discovery、requirements、architecture、formal、security、privacy、safety、supply-chain、implementation、debugging、testing、assurance、delivery、operations、AI-agent。每个条目的完整字段由 `validate-methods` 失败关闭。

## 风险到方法的推理算法

```text
仓库与运行时事实
  -> 当前任务位置（内部 phase 字段）、task type、canonical risks
  -> 失败信号（identity / interaction / temporal / oracle / hazard / rollout ...）
  -> 加权风险模型阈值
  -> “可能怎样失败”的具体假设
  -> phase + depth + negative trigger + prerequisite + context cap 过滤
  -> 现有 owner 的有界方法和产物
  -> failure-sensitive evidence
  -> claim / limitation / NOT RUN
```

Signal 权重高于通用 risk/task type，避免“architecture/large-feature”这种宽标签自动触发 Alloy/TLA+/theorem proving。低风险 routine 的全局负向规则会压制形式化 specialist；显式 high-consequence/safety/regulatory signal 可以解除该抑制。缺失 prerequisite 会进入 `blocked_methods` 并提供 fallback，而不是从输出中消失。

## 内部适用位置

下表是方法注册表的兼容分类，用于专业 owner 判断某个方法是否适合当前问题；它不是要求用户或 AI 依次通关的阶段流水线。

| 阶段 | Foundation | 典型 failure signal |
|---|---|---|
| Discovery | repository-evidence-first | uncertain user need, unclear identity, hidden boundary |
| Requirements | semantic-baseline | ambiguity, identity, state, quality attribute, misuse |
| Design | decision-record | interaction, state space, temporal progress, tradeoff, hazard |
| Implementation | coherent-vertical-slice | compatibility coexistence, invalid state, oracle feedback |
| Diagnosis | hypothesis-led-debugging | unknown cause, noisy reproduction, failure propagation |
| Verification | black-white-oracle-accounting | weak oracle, configuration, concurrency, performance, accessibility |
| Review | clean-context-blue-red | common-mode error, false assurance, integration/security failure |
| Acceptance | acceptance-traceability | claim/evidence gap, regulated assurance, residual external gate |
| Delivery | rollout-readiness | rollout, coexistence, abort, rollback, authority |
| Operations | observability-use | saturation, SLO, recovery, incident learning |

风险、前提、架构或 oracle 发生实质变化时才重新考虑。不要因为已经写了某份模型就把方法永久留在任务中。

## CLI

验证方法池：

```bash
python3 skills/dev-flow/scripts/dev-flow.py validate-methods
```

检查某个任务会激活哪些专业 owner 和有界方法：

```bash
python3 skills/dev-flow/scripts/dev-flow.py route-task \
  --intent change --risk concurrency --risk weak-tests \
  --method-signal temporal-progress --method-signal weak-oracle \
  --method-prerequisite requirement-baseline \
  --method-prerequisite test-oracle --compact
```

`--method-prerequisite` 必须有当前证据，不是愿望清单。输出只用于解释当前路由、被阻塞的方法与 fallback；不要求落盘。`select-methods` 和 `record-methods` 是已退出公共 CLI 的 1.x 内部兼容能力，只能在历史实现与历史记录中解释，不能作为当前操作命令。

2.0 `route-task` 是普通任务的集成入口：它接受八个稳定 canonical signals，并把 `concurrency-ordering`、`distributed-state`、`migration-rollback` 等常见说法归一化；当调用方只给出 concurrency、migration、security/privacy、persisted-data 等风险而没有 signal 时，派生最小基础 signal。`data-loss` 作为 task-facing 风险别名映射到 `persisted-data`。canonical signal、方法 ID 和低层 `method.selection.v1` 不变。

Task-facing 投影分别限制 ready 与 blocked：最多给出三个可执行 guidance 和两个直接相关的缺前提 fallback；blocked 不占 ready 名额。若 change/implementation 阶段没有匹配方法，但 signal 明确属于 requirements、diagnosis、design 或 verification owner，route 会选择相邻 owner phase，而不是返回空的 implementation 结果。宽 security 不会单独引出隐私方法，persistent-agent-memory 需要 agentic system 与 memory-store 证据，多 Agent 方法需要真实 delegation signal。若仍没有可执行或直接相关的 blocked 方法，结果明确为 `no-actionable-match` 并回退到 owner Skill，而不是用一个无关名称假装覆盖。

独立 `select-methods` 仍可做显式维护研究；旧 packet 的 `record-methods` 和风险翻译继续作为兼容接口。

## 扩展治理

新增或修改方法时：

1. 先证明一个现有方法栈无法覆盖的 failure class 或显著不同的前提/产物。
2. 优先更新方法卡或风险模型；不要为了方法名新增 top-level Skill。
3. 绑定 primary/authoritative source，记录本地适配和不适用条件。
4. 为正向、负向、缺前提、低风险排除、context cap、owner 和证据添加确定性用例。
5. 保持 stable method/source/risk-model IDs；schema 变更必须兼容或经过显式迁移。
6. 只有 deterministic contract 无法观察重要模型行为时，才增加可选 live model eval。

该层的质量标准不是“方法越多越好”，而是能否用最少的方法暴露当前最可能且最昂贵的错误，并诚实地说明还没有证明什么。
