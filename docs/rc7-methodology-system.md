# Dev Flow RC.7 方法工具箱草案

> 状态：已接受的 RC.7 方法基线；117 个稳定方法 ID 保持兼容，问题驱动、饱和停止、设计消融和测试覆盖技术已落实到主 Skill 与专业 owners。新增候选仍按真实边际价值逐项晋升，不因 RC.7 一次性注册。
> 配套资料：[`rc7-development-lifecycle.md`](./rc7-development-lifecycle.md) 描述 RC.7 的开发指导主线。
> Skill 改造方案：[`rc7-skill-evolution-design.md`](./rc7-skill-evolution-design.md) 描述方法怎样进入主 Skill 与专业 owner。

## 1. 方法库不再承担流程控制

现有 117 个方法曾经围绕风险模型、选择记录和生命周期门禁建设。它们提供了丰富的工程技术，但也很容易让 AI 把“选择了方法”当成“已经提高了质量”。

RC.7 对方法库的重新定位是：

> 方法是 AI 在某个具体问题上缺少抓手时使用的思考动作，不是每个任务都要经过的选择程序。

因此：

- 普通任务可以一个方法名都不出现；
- 方法由当前问题触发，不由阶段编号或笼统风险标签触发；
- 一次只拿起少量真正有判别力的方法；
- 方法应直接改变理解、方案、代码或证据，不生产独立执行报告；
- 没有带来新信息时立即停止；
- 方法卡应教会 AI 怎样做，而不是要求它声明“已采用”。

## 2. AI 什么时候需要一个方法

不必先跑全库选择器。遇到下面的实际困难时，再寻找对应方法：

| 当前困难 | 可以寻找的帮助 |
|---|---|
| 需求一句话有多种解释 | 具体例子、EARS、决策表、状态模型、事件时间线 |
| 不知道用户真正要解决什么 | outcome map、journey、story mapping、用户研究 |
| 多个方案都说得通 | ADR、ATAM、spike、成本收益、quality attribute scenario |
| 设计开始变复杂但价值说不清 | AHA、YAGNI、Least Power、设计消融 |
| 既有代码作用不清，不敢安全修改 | repository evidence、impact graph、characterization、Chesterton's Fence |
| 缺陷反复试错 | 最小复现、根因追踪、单一假设、delta debugging、fault injection |
| 测试不知道该断言什么 | acceptance traceability、metamorphic、differential、model/property testing |
| 测试绿色但可能没有灵敏度 | mutation、semantic mutation、负向控制、独立推导 |
| 状态/组合空间太大 | decision/state、t-way、property/model/fuzz |
| 变化有高后果专业风险 | STRIDE、LINDDUN、FMEA/STPA、MC/DC、TLA+、ABI contract |
| 多代理或长任务开始漂移 | semantic checkpoint、receding horizon、ownership topology、trajectory eval |
| 要发布或迁移到真实环境 | rollout readiness、compatibility、replay/rollback、provenance、canary |

方法的名字不是重点。AI 如果已经掌握并正确执行了同一思考动作，不需要为了可见性再调用或复述方法。

## 3. 一张有用的方法卡应该长什么样

方法卡保持很短，只回答五件事：

1. **什么时候有帮助**：描述可以观察到的困境，而不是“复杂任务”。
2. **怎样做**：三到五个足以开始的动作。
3. **它想暴露什么**：歧义、错误假设、无价值结构、弱 oracle 等。
4. **什么时候不用或停止**：避免方法扩大范围或变成仪式。
5. **一个真实例子**：展示方法怎样改变决定、代码或测试。

复杂理论、标准细节和模板放在按需 reference；确定性操作放脚本。主卡不需要 phase、task type、enforcement、intensity、output、fallback 等一大组治理字段才能发挥作用。

## 4. 方法怎样融入开发，而不打断开发

### 4.1 在动作中使用，而不是先开方法会议

例如，需求不清时直接拿两个反例与用户核对；不需要先输出“已选择 specification-by-example”。测试没有 oracle 时直接寻找不变量或第二实现；不需要生成方法 selection sidecar。

### 4.2 优先选择能最快减少当前未知的方法

一个方法已经给出明确答案，就回到开发主线。只有新答案暴露了另一个具体问题，才继续使用第二种方法。

### 4.3 组合互补视角，不堆叠同类方法

常见的有效组合是：

- 一个产品视角 + 一个实现视角；
- 一个正向构造方法 + 一个反向挑战方法；
- 一个测试生成方法 + 一个 oracle 灵敏度方法；
- 一个设计方法 + 一个简化方法。

连续使用多个作用相近的需求框架、架构框架或测试设计方法，通常只会增加文字。

### 4.4 保留项目原生做法

如果仓库已经使用 RFC、EARS、C4、BDD、property tests 或某套运行手册，优先沿用。Dev Flow 方法库负责补缺口，不建立第二套平行语言。

### 4.5 在方法饱和时停止

方法的停止条件与适用条件同样重要。当前未知已经被消除、关键方案已经被区分、oracle 已经能抓住目标错误，或继续使用同类方法只产生措辞和偏好差异时，应立即回到开发主线。

本地 dogfood 中，方法在适用样本里曾改变技术决定、测试 oracle 和完成声明，但大量审查与方法轮次也曾在后期只继续消除低优先级意见。因此 RC.7 不采用固定轮数、方法覆盖率或 finding 清零目标。方法价值必须能落到一个改变的决定、被简化的设计、增强的证据或被避免的错误上；否则记为未观察到效果，而不是默认有效。

## 5. 现有 117 个方法：作为工具完整保留

下面保留当前稳定 ID，方便兼容和后续重写卡片。分类只是导航，不表示固定使用顺序。

### 理解事实与工作方向

`repository-evidence-first`、`semantic-baseline`、`decision-record`、`coherent-vertical-slice`、`hypothesis-led-debugging`、`black-white-oracle-accounting`、`clean-context-blue-red`、`acceptance-traceability`、`rollout-readiness`、`observability-use`

### 发现与需求

`stakeholder-outcome-map`、`user-research-prototype`、`journey-service-blueprint`、`assumption-mapping-premortem`、`domain-storytelling-event-storming`、`ubiquitous-language-glossary`、`ontology-identity-ledger`、`specification-by-example`、`decision-table`、`state-transition-model`、`quality-attribute-scenario`、`use-misuse-abuse-case`、`invariant-design-by-contract`、`traceability-v-model`

### 技术设计与架构

`change-impact-graph`、`feature-interaction-analysis`、`bounded-context-context-map`、`atam-lightweight`、`architecture-fitness-function`、`architecture-spike-prototype`、`data-lineage-provenance`、`information-hiding-modularity`、`saga-compensating-actions`、`behavior-tree-reactive-execution`、`architecture-viewpoint-consistency`、`architecture-reflexion-conformance`、`bpmn-collaboration-process-model`、`data-quality-scenario-reconciliation`、`cost-benefit-architecture-analysis`、`cross-language-abi-contract`

### 实现与演进

`test-driven-development`、`atdd-bdd`、`typestate-and-smart-types`、`parallel-change-expand-contract`、`branch-abstraction-feature-flag`、`strangler-migration`、`cleanroom-development`、`n-version-programming`、`formal-inspection-pairing`

### 调试

`reproduction-minimization`、`delta-debugging-bisection`、`fault-injection-diagnosis`、`counterexample-guided-repair`

### 测试

`equivalence-boundary-testing`、`combinatorial-tway-testing`、`property-based-testing`、`model-based-testing`、`metamorphic-testing`、`differential-testing`、`characterization-golden-master`、`contract-consumer-testing`、`mutation-testing`、`semantic-mutation-testing`、`fuzz-testing`、`static-analysis-sanitizers`、`symbolic-execution`、`concurrency-linearizability-testing`、`fault-injection-chaos`、`performance-load-stress-soak`、`accessibility-conformance-testing`、`moderated-usability-testing`、`compatibility-matrix`、`migration-replay-rollback`

### Agent 工作

`repository-legibility-context-engineering`、`deterministic-agent-harness`、`agent-evaluation-design`、`multiple-first-attempts`、`model-tool-identity-pinning`、`eval-contamination-case-health`、`authority-tool-boundary`、`long-running-semantic-checkpoint`、`minimum-effective-autonomy`、`belief-state-active-information`、`receding-horizon-execution`、`agent-trajectory-intervention-evaluation`、`human-agent-function-allocation`、`agent-memory-lifecycle-governance`、`multi-agent-topology-ownership`

### 形式化和专业保证

`alloy-relational-model`、`tla-temporal-model`、`event-b-refinement`、`refinement-mapping-simulation`、`petri-net-process-model`、`theorem-proving`、`hierarchical-task-network-planning`、`conformal-risk-control-selective-action`、`contract-net-task-allocation`

### 安全、隐私、Safety 和 Assurance

`stride-threat-model`、`attack-tree`、`ssdf-secure-development`、`instruction-data-provenance-taint`、`linddun-privacy-model`、`fmea-fta`、`stpa-control-analysis`、`hazop-guidewords`、`runtime-assurance-safety-shield`、`gsn-assurance-case`、`n-version-independent-derivation`、`temporal-runtime-verification`、`digital-twin-agent-simulation`

### 交付、运行和供应链

`trunk-ci-small-batch`、`canary-progressive-delivery`、`blue-green-shadow-traffic`、`slo-error-budget`、`game-day-runbook`、`blameless-postmortem-cast`、`slsa-sbom-provenance`

## 6. 当前库真正缺少的帮助

联网研究后，缺口主要集中在需求表达、UX 评估、代码简化、探索式测试和文档工程。下面是值得试用的候选，不代表全部立即注册。

### 需求与产品塑形

- **EARS**：当自然语言把触发、状态和异常混在一起时，用少量结构化句式消除歧义。
- **User Story Mapping**：当团队按技术层拆任务而丢失用户旅程时，按活动和任务切出首个端到端版本。
- **Event Modeling**：当业务事件、命令、视图和异步状态难以对齐时，用时间线还原信息流。

Impact Mapping、Opportunity Solution Tree、Double Diamond、Design Sprint 和 Example Mapping 与现有 discovery/requirements 方法高度相近，先作为变体和示例，不增加选择项。

### UX 质量

- **Heuristic Evaluation**：低成本检查可见性、一致性、控制、错误预防和识别负担。
- **Cognitive Walkthrough**：沿一个具体任务检查新用户是否知道目标、看见动作、理解操作和反馈。
- **Structured Design Critique**：围绕目标和约束组织观察、问题、风险和建议，而不是审美投票。
- **HEART Goal–Signal–Metric**：把体验目标连接到真实使用信号，避免代理指标取代用户结果。

Atomic Design 更适合作为 UI/design-system 的参考语言，不急于成为独立方法。

### 技术设计与代码质量

- **Design Ablation**：价值不明的抽象、层、依赖或机制可以被移除/替换后比较能力和复杂度。
- **AHA**：相似代码的稳定共同点尚未出现时，允许局部重复，推迟错误抽象。
- **Principle of Least Power**：在多种机制都能满足需求时，选择表达能力和权限最小的一个。
- **Parse, Don't Validate**：在不可信边界把原始输入一次变成可信类型，减少内部重复验证和非法状态。

YAGNI 和 Chesterton's Fence 分别作为新增结构和删除既有结构时的提醒，不需要独立卡片。

### 测试和质量探索

- **Session-Based Test Management**：用风险导向 charter、时间盒和 debrief 让探索式测试可复盘，而不是随意点击。
- **Risk-Based Testing**：测试空间超过预算时，根据后果、可能性、变化和可检测性分配测试深度。
- **Coverage Obligation Mapping**：把需求/行为、风险/恢复、结构/状态、组合/顺序、环境/兼容和 oracle 灵敏度映射到测试，显式暴露未覆盖义务。
- **Changed-Code Mutation**：只在本次变化和关键逻辑上播种经过筛选的 fault，检验测试是否真的能抓住错误，避免全库 mutant 爆炸。
- **Variable-Strength Combinatorial Testing**：用带约束的 pairwise/t-wise 压缩输入组合，对高风险因子提高交互强度，而不是穷举整个笛卡尔积。
- **Oracle Triangulation for AI Tests**：让需求/合同、实现结构、独立参考或 seeded fault 至少两个来源交叉约束 AI 生成测试，防止代码与测试共同犯错。
- **MC/DC**：只为安全/任务关键布尔决策证明各条件的独立影响，不推广为普通覆盖目标。

Google test sizes、Definition of Done 等更适合作为测试策略和项目约定的参考，不是方法卡。

### 知识工程

- **Docs as Code**：当知识确实需要维护时，让它与代码同行评审、链接检查和演进。
- **Living Change Record**：材料变化用一份持续演进的导航记录连接需求、UX、设计、实施、测试和验收，同时把长期事实回写唯一 owner。
- **Decision Log / ADR**：只为影响结构、关键质量属性或难以回退的选择保存上下文、备选、取舍、后果和 supersede 关系。

Diátaxis 可以帮助组织教程、how-to、reference 和 explanation，但属于信息架构参考。Spec-Driven Development 是多种能力的组合路径，也不需要再建一张方法卡。

## 7. 几个候选方法怎样实际使用

### 7.1 设计消融

适用信号：方案出现额外抽象、缓存、状态机、并行、Agent、依赖或扩展点，但无法说明它带来的独立价值。

做法：固定必须保留的场景和检查，移除或旁路一个成分，比较行为、复杂度、失败面和资源。如果能力没有下降，就简化；如果下降，记录该成分真正承担的责任。

停止：没有对应结构、变量无法隔离或比较 oracle 不可靠。消融不是所有编码任务的核心。

### 7.2 AHA

适用信号：两段代码长得相似，但业务含义、变化方向或约束还不稳定。

做法：保持局部代码清楚，观察它们怎样分别变化；只有稳定共同点出现，并且抽象能减少耦合时才合并。若共享的是必须统一的安全/协议规则，则不应无限等待。

### 7.3 Parse, Don't Validate

适用信号：字符串、JSON、配置或数据库值进入系统后被多次检查，内部函数仍然接受未经证明的原始形态。

做法：定义可信内部类型，在边界完成解析、规范化和错误分类，内部 API 接受可信值。它不能取代持续变化的授权和业务状态检查。

### 7.4 SBTM

适用信号：复杂 UI、状态或未知风险无法仅靠预写脚本覆盖。

做法：用一个清楚的测试 charter 开始，限时探索，记录覆盖、发现、问题和阻塞，结束后 debrief；把稳定发现转成缺陷、回归测试或下一轮 charter。

### 7.5 MC/DC

适用信号：安全/任务关键决策需要证明每个原子条件能独立改变结果。

做法：为每个条件找到只改变该条件且改变决策结果的用例对。普通业务代码不需要为了形式覆盖付出这种成本。

### 7.6 Coverage Obligation Mapping

适用信号：测试很多或覆盖率很高，但无法回答哪些产品行为、失败恢复、状态、组合、平台或 oracle 仍然没有证据。

做法：从确认后的需求和最终 diff 独立列出材料义务，按行为、风险、结构、组合、环境和灵敏度六类连接到具体测试或明确缺口。它可以是一段 change record 或小表，不要求项目永久维护大型 traceability matrix。

停止：所有材料义务已有合适 oracle，剩余仅为低概率低后果空间，并写明触发重新打开的条件。

### 7.7 Changed-Code Mutation

适用信号：关键测试可能只执行代码但没有有效断言，或者 AI 同时生成代码和测试，存在共同自证风险。

做法：只对 changed code、关键分支和高风险规则使用高价值 mutation operator；限制每行/每次变化的 mutant 数量，过滤等价或无行动价值 mutant。存活 mutant 先判断是否揭示真实 oracle 缺口，再决定补测试。

停止：目标错误已能被现有测试杀死，或剩余 mutant 只要求锁定实现细节、产生等价行为或成本超过风险收益。

### 7.8 Variable-Strength Combinatorial Testing

适用信号：参数、配置、权限、平台或状态组合太多，逐一穷举不可行，但交互缺陷是可信风险。

做法：先建带约束的因子和值模型，普通区域从 pairwise 开始；对安全、兼容、状态恢复等高风险因子提高到更高 t-way 强度。加入已知故障组合和代表性事件顺序，不把生成器输出直接当作有效 oracle。

停止：选定强度已覆盖材料交互，历史/风险没有支持更高阶组合；极边缘扩张只有在用户明确要求或后果足够高时继续。

### 7.9 Oracle Triangulation for AI Tests

适用信号：同一个 AI 根据同一份代码同时写实现和测试，或评测 fixture 可能把未说明的实现细节当成正确答案。

做法：让测试至少受到两个相对独立来源约束，例如需求/合同与白盒风险、旧/新实现 differential、property/metamorphic relation、seeded fault、真实数据样例或独立 reviewer。检查需求、测试、参考实现是否彼此一致，并保存第一个反例。

停止：关键 oracle 已对目标 fault 敏感且没有材料来源冲突。代理或 reviewer 数量不是独立性的替代品。

## 8. 方法库怎样继续学习，而不是一次性扩张

新增方法采用经验驱动循环：

```text
真实任务反复失败
  -> 识别缺少的思考动作
  -> 在任务中手工试用方法
  -> 观察它是否改变决定或证据
  -> 写成简洁候选卡
  -> 用相似任务和负向任务测试
  -> 有稳定边际价值才进入正式库
```

因此，上面的候选不应一次性全部写入 `governance/methodology-pool.json`。优先从真实 RC.7 dogfood 中选择最常见、最有价值的缺口。

评估方法时看这些结果：

- 是否更早发现了材料歧义或风险；
- 是否淘汰了错误方案；
- 是否简化了实现；
- 是否使测试更能抓住缺陷；
- 是否帮助后续任务；
- 是否误触发并拖慢了普通任务。

方法调用次数、selection 覆盖率和报告完整度都不是成功指标。

## 9. 方法系统在 RC.7 中的实现方向

- 当前稳定 ID 和注册表先保持兼容。
- `select-methods` 可以保留为高风险或卡住时的辅助检索，不再承担生命周期证明。
- 不恢复 packet sidecar、累计方法记录或方法 gate。
- 方法参考按需求、设计、实现、调试、测试、Agent、专业风险和交付分区，专题 Skill 只读取当前相关部分。
- 方法卡逐步改成“适用困境—动作—暴露问题—停止—例子”的短格式。
- 核心 Dev Flow Skill 不展示方法总表，不要求模型解释它为什么没选某方法。
- 用真实任务的行为 eval 检验方法是否被正确拿起、正确跳过和及时停止。
- 在 eval 中加入“方法饱和”案例：一个方法已解决当前未知后，继续叠加相似方法应被判为过程回归。

## 10. 三个使用例子

### 明确的本地缺陷

先复现并追踪根因，补一个能在旧实现上失败的测试，做最小修复并验证。AI 可能实际使用了最小复现和 TDD，但无需输出方法清单，也无需需求或设计文档。

### 模糊的新功能

先用具体例子澄清用户结果；多状态时补一个小状态模型；比较现有约定和局部方案；按端到端切片实现；从产品结果和内部边界两个方向设计测试。只有会影响多个切片的语义和技术决定进入项目知识。

### 开始过度设计的方案

当设计出现新框架、抽象层和通用扩展点时，用 AHA 检查抽象时机，再对其中一个组件做消融。如果移除后当前场景和质量不变，就删除或推迟。这里方法直接减少代码，而不是增加方法文档。

## 11. 研究来源

- [Anthropic Skill authoring best practices](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices)
- [Agent Skills specification](https://agentskills.io/specification)
- [Superpowers：writing skills and behavior eval](https://github.com/obra/superpowers/blob/main/skills/writing-skills/SKILL.md)
- [BMAD：independent planning tools and intent-sized paths](https://docs.bmad-method.org/plan/choose-a-planning-path/)
- [Kiro Specs best practices](https://kiro.dev/docs/specs/best-practices/)
- [GitHub Spec Kit Lean workflow](https://github.com/github/spec-kit/blob/main/presets/lean/README.md)
- [EARS](https://alistairmavin.com/ears/)
- [User Story Mapping](https://jpattonassociates.com/story-mapping/)
- [Event Modeling](https://eventmodeling.org/)
- [HEART framework](https://research.google/pubs/measuring-the-user-experience-on-a-large-scale-user-centered-metrics-for-web-applications/)
- [W3C Principle of Least Power](https://www.w3.org/2001/tag/doc/leastPower.html)
- [AHA Programming](https://kentcdodds.com/blog/aha-programming)
- [Parse, Don't Validate](https://lexi-lambda.github.io/blog/2019/11/05/parse-don-t-validate/)
- [Session-Based Test Management](https://www.satisfice.com/download/session-based-test-management)
- [NASA MC/DC tutorial](https://ntrs.nasa.gov/archive/nasa/casi.ntrs.nasa.gov/20010057789.pdf)
- [Microsoft Azure Well-Architected：Architecture Decision Records](https://learn.microsoft.com/en-us/azure/well-architected/architect-role/architecture-decision-record)
- [NIST ACTS：Combinatorial Methods for Trust and Assurance](https://csrc.nist.gov/Projects/Automated-Combinatorial-Testing-for-Software/)
- [Google Research：Practical Mutation Testing at Scale](https://research.google/pubs/practical-mutation-testing-at-scale-a-view-from-google/)
- [OpenAI：Separating signal from noise in coding evaluations](https://openai.com/index/separating-signal-from-noise-coding-evaluations/)
- [OpenAI：How evals drive the next chapter in AI](https://openai.com/index/evals-drive-next-chapter-of-ai/)

方法库的价值不在于覆盖整个生命周期，而在于 AI 遇到一个具体难题时，能迅速找到一种经过验证的好做法，然后继续开发。
