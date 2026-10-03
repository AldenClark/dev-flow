# Dev Flow 2.0 正式版：累计审计、设计与实施总方案

本文件是正式版优化工作的单一设计与审计汇总入口，先保存此前会话结论，再在同一文件中更新核查、红蓝对抗与最终实施方案。它是**待实施方案，不是已实现能力、发布许可或发布就绪证明**。产品当前状态仍由 `governance/product-state.json` 管理；代码、原生测试、宿主观察和交付制品分别拥有其工程事实。

基线：2026-10-03；源码 `7d3fc25118c23b433519b00b88f52b4be73da0a7`；开始时工作区干净。当前源版本/已发布 RC 为 2.0.0-rc.9，stable 为 1.1.2；RC.9 的部分验证是 waived，不可升级为 PASS。后续源码、宿主能力或官方模型文档变化时，应重新核查受影响部分。

状态：v5，已批准设计基线；六轮审计/红蓝工作已整合，最后定向复核未发现新的实质方案缺口。方案审查完成；用户随后授权实施至正式发布和本机更新，当前状态见 [stable progress](../dev-flow-2.0-stable/progress.md)。下文审计终态保留为历史，不能替代后续实施/资格证据。审计编号只是本文件内的定位标记，不是新增产品协议或强制工作流字段。

## 1. 用户目标、授权与非目标

目标：深入找出定义不清、逻辑冲突、路径不顺、与 GPT-6/6.1 及近期研究不匹配的设计，形成能实施、能反驳、能验收的正式版方案。先持久化既有结果，审计期间持续修订；开展多轮审计和红蓝对抗。

已确认的方向：增强实际工程能力和深度，不扩张 Bench 或 Skill 推荐目录；合理减少过时强约束，不为了凑优化点改动；主动澄清真实需求，持续对齐，及时纠正旧假设；普通磁盘不足等宿主问题按普通环境故障处理，不为单次事故建立专用大体系。

本轮授权：读取仓库、相关既有审计和公开研究，运行安全的诊断/测试，修改本总方案及必要的导航链接，委派只读审计。本轮不修改产品实现，不提交、推送、打标、发布、安装、部署、修改宿主配置、清理缓存、发起付费模型实验或保存个人画像。后续实施/交付需要对应授权。

“完美”转化为可检查的目标：所有已发现的实质性问题有证据和处置，关键设计经独立反例挑战，剩余未知被明确报告。不承诺穷尽全部缺陷，也不把审计轮数当质量证据。

## 2. 证据与归属

- **源码确认**：给出当前 owner/符号和矛盾或失败路径；不是运行时行为证明。
- **本地复现**：记录命令、输入、实际输出和环境；不外推 hosted、平台、安装或生产。
- **历史观察**：先前会话/发布记录支持的问题线索；不是本轮重新执行结果。
- **设计风险**：有合理失败机制，但尚未观察到失败；不得写作现存已证实 bug。
- **NOT RUN / not_observed / WAIVED**：保持原义。诊断无法观察不等于没有问题。

本文件拥有本次优化建议与实施次序；实施后，正式语义分别写回 Skills、references、registry、源码、测试和发布说明等原有 owner，本文件保留决策与结果链接，不成为并行运行时真相库。现有 workstream 的 `implementation.md` 不在本轮重写；本计划尚未激活为新的实施 workstream。

## 3. 前几轮审计结论的保全

### 3.1 实际任务的启示（历史观察，非成功率研究）

先前任务审计按 session 元数据、真实用户消息、实际调用和终态区分真正使用与注入内容；有界样本涉及 Aegir、PushGo、Loshu、Dev Flow 等任务。不能从文件数量、工具次数或关键词频率推导生产率、失败率或因果收益。

- Aegir：设计图库与静态交付不等于原生交互/VPN 完成；配置来源、编辑权、运行选择等语义容易在长任务中错位。应持续保留用户约束，并用行为例子验收。
- PushGo：独立嵌套仓库与平台证据必须分开；最小根因修复有价值，反复扩张边缘验证会增加用户负担。原生测试系统失败、签名/设备阻塞不能被编译通过掩盖。
- Loshu：Simulator/隔离 review host 的结果不能冒充真实使用；磁盘不足与手动解锁属于环境条件，不构成模型能力缺陷。
- Dev Flow：RC.9 历史上存在旧模型断言导致首次失败、随后修正，以及升级后运行会话仍引用旧 Hook 路径的观察。安装成功与当前会话生效应分开。

### 3.2 累计问题清单（本轮继续核验）

| 标记 | 现象与证据入口 | 性质 | 最小处置与反例 |
|---|---|---|---|
| F01 | `tools/validate_product_state.py:261,293,381-382` 的 candidate/base/install/stable 规则仍依赖 RC 和旧 stable 假设；`evals/test_product_state.py:95-103` 的投影 fixture 复制旧描述 | 本轮源码再确认 | 建立 RC→正式候选→正式发布→下一开发态的真实迁移测试；错误 tag/manifest/工作流投影必须拒绝 |
| F02 | `skills/dev-flow-maintainer/SKILL.md` 要求每类 3 cases×3 attempts，与 maintenance-contract、`docs/releasing.md` 的薄验证/Bench 分离冲突；contract checks 保留旧话术 | 前轮源码确认 | 发布契约唯一归属；RC 直接受影响 case 首次尝试，stable 五条旅程；重复比较只属获授权 Bench |
| F03 | `skills/requirements-design/agents/openai.yaml` 的 U1 默认提示要求无条件停顿，而正文允许语义已定后继续 | 前轮源码确认 | 提示与正文同义；已确认实施不再停，仍存实质用户选择才问 |
| F04 | `workstream_contract.py` 将 Git status 失败归为非 Git，N/A/exit 0；Git 调用缺乏已有安全运行边界 | 前轮源码确认 | 明确非仓库、执行失败、超时、脏状态；错误不可绿色降级；受控 Git 环境和超时 |
| F05 | `agent_dispatch.py` 对宿主库存中未知 effort 拒绝整个列表，即使请求的 medium 可用 | 前轮源码确认 | 宽容解析库存并保留诊断，严格匹配实际选中模型/effort；未知项不自动可用 |
| F06 | `runtime_doctor.py` 的注册数量/传入目录 manifest 不证明当前加载；activation 已诚实标记 not_observed，但运行恢复不足 | 历史故障+诊断边界 | 区分 installed/registered/effective/current-session；仅宿主实际证明才提升；安全新会话恢复指引，不自动删缓存 |
| F07 | `governance/industry-practices.json` 保留最多 3 子任务/单层/不能自主派发等，和多代理正文冲突 | 前轮源码确认 | 更新活跃投影；按任务独立性、宿主资源、用户预算、集成积压选择；保留权限交集 |
| F08 | `dev_flow.py` preflight 固定 6 ceiling、3 soft、每次 +1；`agent_dispatch.py` 把总工作单元限制 1..8 | 前轮 CLI 复现 | 区分总任务数与同时运行数；可分批处理 >8 单元；软默认可调，宿主硬上限不可突破 |
| F09 | preflight 的旧 CLI 版本/feature flag 可能覆盖真实能力观察 | 前轮源码确认 | 分离 CLI 兼容诊断与当前宿主可用能力；未知不能正向推断 |
| F10 | `governance/methodology-pool.json:205` long-running-semantic-checkpoint 自动要求 digests + ledger；:104 semantic-baseline 的显式方法选择仍输出 ambiguity ledger/stable acceptance IDs | checkpoint 前轮公开路由复现；foundation 本轮 maintainer selector 复现 | 普通任务使用既有 owner + 简短 checkpoint；相关活跃方法投影一并校准，只为真实事务恢复/原生消费者保留限定机制 |
| F11 | “最多 3 个方法”的执行建议容易被当普遍硬上限；路由 3 ready/2 blocked 是有用的上下文预算 | 设计风险，未证明实际漏检 | 保留默认呈现预算，允许明确盲点触发例外；不扩大默认方法倾倒 |
| F12 | 需求澄清之后，代码、测试、子任务仍可能依据旧假设继续；各 owner 有分散规则但缺少一致的行为闭环 | 历史案例+设计缺口 | 需求修订应失效受影响设计/测试/任务输出；不只是更新摘要，不全量重置 |
| F13 | `evals/test_product_state.py:208-212,509-523,563-577` 混合当前 product-state 和硬编码 RC.8/RC.7，当前基线已有 3 项失败 | 本轮两次运行确认 | 历史场景使用完整独立固定 fixture；当前仓库检查验证真实投影关系；迁移期望另设手写 oracle，不能全部从被测实现反推 |
| F14 | `evals/test_release_artifacts.py:198-205` 要求示例 attestation 的 RC.8 等于当前 manifest RC.9；:185 同时把所有源版本锁定 RC 格式 | 本轮全套测试确认首项失败；后项源码确认 | 区分安全示例、真实当前 attestation 与历史证据；示例测试其 schema/无实证含义，真实 attestation 才做身份绑定；不把示例版本机械改新来伪造 live 证明 |
| F15 | `requirements-design/references/user-interaction.md:11-19`、`governance/user-interaction-contract.json:8,28`、`evals/run_contract_checks.py:679-696` 将曝光/available 绑定固定同步工具，未充分建模 mode/purpose/schema/lifecycle | 本轮独立审计+主代理源码复核；当前宿主 schema 反例，未观察非法调用 | 先判定 eligible，再选择真实同步/异步/对话能力；Plan-only 在 Default 不调用，optional-only 不承接必需决定，审批不得借普通问答完成 |
| F16 | `docs/index.md` 的 RC.8 导航仍称 local source candidate/not a release，与 product-state/CHANGELOG 的 RC.9 已发布事实冲突，并缺 RC.9 入口 | 本轮源码确认，低风险导航漂移 | 导航按历史/当前归属链接，不在多个索引复制“当前版本”事实；保留历史 workstream，不批量重写历史 |
| F17 | `tools/validate_product_state.py:307-327` 将 source-candidate 与“不能有tag成功”绑定，将 stable 与“所有安装等交付项成功”绑定；`docs/releasing.md:107` 延后到发布/安装都成功才写真相 | 最终红队内存负例+主代理源码核验 | 分离发布身份事实、逐项交付事实、结构有效性和动作资格；如实表达部分成功/失败，不能靠虚填 passed 或延迟写真相获得 valid |

### 3.3 明确保留的约束

权限边界、脏工作区保护、秘密与不可信输入边界、独立审查、原生证据分层、子任务权限交集、资源单一所有者、失效结果检查必须保留。两次没有改善的辅助修补后重新判断 simplify/replace/defer/block 是收敛机制，不是“两次尝试就放弃任务”。没有证据要求移除依赖决策、所有方法上限或所有确认行为。

现有模型路由允许显式更高 profile，不要求先用 Sol 失败再上 Astra；不制造这一不存在的问题。默认单代理对紧耦合任务合理；多代理不是质量保险。

独立扩展审计同时排除了几类误报：明确标为 unsupported 的 packet 模板不是当前工作要求；尚未证明跨平台故障的 CI 路径覆盖疑点不列 bug；含合成敏感样例的工具输出被 Hook 替换，不足以证明误报。`check-workstream --check-worktree` 对所有 dirty 路径报告 ambiguous 而不推断作者是保守行为，不应为了通过检查扩 scope、忽略路径或改用户文件。有可信起始观察/原生任务 diff 才能区分既有和新增改动；没有则保留不确定性。F04 修复不得损坏这条保护。

### 3.4 基础出发点审计：不是只修旧规则的一致性

当前 Dev Flow 已声明薄协调、原生反馈、按需方法和任务相关路由；不能把它描绘成完整瀑布或固定多代理流水线，再以“升级”之名重复已有设计。真正需要修正的是残留的相反规则，以及把有用启发式提升为普遍真理的倾向。新模型提高自治能力，是重新检验约束成本的理由，不是取消权限/安全约束的理由。

| 基础问题与当前证据 | 处置与拟定原则 | 为什么不选另一极端 | 可反驳验收 |
|---|---|---|---|
| **质量来自流程服从，还是结果与反馈？** core-lifecycle/quality-calibration 已强调原生结果，但 F02/F10 等活跃投影仍奖励重复步骤和制品 | **保留主方向、退役残留**：流程是解决具体不确定性的工具；每项约束必须能解释保护了什么结果/边界。方法名、文件数、调用数不是质量代理 | 完全无结构会丢约束、跳验收；通用细密脚本又会挤占模型判断 | 同一有界结果允许不同合法路径；缺关键证据仍失败，少写方法文档不应失败 |
| **需求必须完整后才能碰技术吗？** requirements-design 首段说足够完成下一 slice，step 6 却要求 U1 在技术设计前 publish complete understanding，末尾又笼统禁止未决选择下技术设计 | **修订**：先明确下一重要决策所需的语义；允许在现有授权内只读查证、比较技术可行性和明确可逆的隔离试探。暂停的是依赖未决用户选择的承诺/实现，不是所有技术学习 | 不能用“技术试探”偷偷替用户选择产品行为、改生产数据或引入依赖；也不能要求用户先回答可由技术证据消除的问题 | 一个产品选择未定时，可查已有 API 能力并提交差异；不能实施任选分支。用户明确要求先审阅时仍停止依赖工作 |
| **模型/effort 能排成普遍强弱阶梯吗？** agent_dispatch 的 ORDERED_PROFILES 用于 policy minimum、downgrade 和缺能力建议；P3 Luna xhigh 与 P4 Sol medium 是不同模型/预算向量 | **校准而非重建**：保留公开 profile 和当前策略顺序，但明确它是任务相关的路由政策，不是实测质量全序。尊重显式 profile、真实 host 和任务反例；“更高”不保证更正确或更省 | 无本地比较证据，不重写算法成复杂学习路由；也不要求先失败若干次才能选择适合的模型 | 输出区分 policy requirement、host availability 与 observed outcome；固定 profile 上仍用任务 oracle，不能凭等级宣称通过 |
| **每次路由调用本身是否创造价值？** quality-calibration 要求每次实际派发前运行 route-agent；决策结果不持久化已是正确边界 | **有条件简化提案**：同一回合中，policy 内容、宿主能力观察、role/workload/risk/signal/显式参数完全不变时，可复用已校验建议；派发时仍检查真实容量、权限和目标，不将建议当 reservation | 不建立缓存服务、长期 dispatch receipt 或新的路由状态；跨会话、内容/输入变化、能力错误立即失效。未证明显著成本收益，不以此作为 stable 必需新能力 | 改一个输入或 host 观察后不得复用；同输入复用不跳实际 slot/授权检查。若规则比重复调用更复杂，直接不实施此优化 |
| **能力缺失是否必然禁止其他路径？** quality-calibration:81 将 named capability 缺失扩展为 Web/browser/MCP/app/dynamic 等所有替代发现禁令；相邻规则已经正确限制证据声明 | **收窄绝对禁令**：按用户授权的结果、数据、动作和工具限制判断。一般任务允许已授权、同范围、已曝光且可用的只读替代；保持原能力 BLOCKED/NOT RUN，不冒称同等 specialist 覆盖 | 工具存在不是权限，通用任务也不是上传源码、访问无关账户、安装插件、产生开销或绕过 exact-tool 限定的许可。外部检索不得携带私有内容；不靠外部页面获得权限 | 泛化请求可用允许的官方资料检索并注明覆盖变窄；明确 local-only/exact-tool 请求仍不能调用 Web/无关 MCP；缺独立审查不得用同上下文冒充 |
| **任何指导修订都必须先观察 unguided failure 吗？** maintainer step 2 将 changing guidance 与 promoting Skill 绑定；behavior-evaluation 要求稳定边际收益 | **按声明分层**：正确性/兼容/冲突修复可由机制、源码反例和确定性验证成立；新行为指导先作为有界试用；“改善行为/生产率”及 first-class promotion 才要求相应真实比较证据 | 不要求为了修一处自相矛盾先付费跑模型；也不以静态 green 或论文结果证明行为收益。发布资格仍按实际受影响旅程执行 | 未发生事故也可修复已证明可达的错误路径；试用不能标为收益已证实；没有对比仍不得宣传稳定边际改善 |
| **上下文越多、方法越全、代理越多是否更好？** 方法池、仓库指引、并发策略有真实价值，但研究显示收益依任务结构；现有 specialist-first/abstain 应保留 | **按决策价值选择**：只加载能改变当前判断的上下文/方法；保留少数关键约束与原始来源。并行用于真正独立任务，集成积压也是预算；纠正时让依赖旧理解的输出失效 | 不删除所有 Skills/记忆/审查；不自动把会话教训升为个人长期规则；不把 context 压缩变成删除安全边界 | 无关 Skill 不加载，关键一次性约束在续跑后仍被遵守；多代理输出必须可整合且检查 freshness，数量不计收益 |
| **“证据驱动”是否意味着全都成功才能写真相？** F17 显示发布身份和资格耦合；F04 显示观察失败可能被降为 N/A | **分离事实与资格**：先诚实记录发生了什么、哪里未知，再判该动作是否可开始/已完成；只失效受影响证据。恢复依据故障类型和新事实，不依据固定重试仪式 | 结构 valid 不能替代授权、资格或交付完成；放宽记录真实失败不等于放宽安全门槛；仍保留两次无改善辅助修补后的收敛处置 | 部分成功/失败可合法保存但动作仍 blocked；环境错误不能变产品 PASS；未变化的权限阻塞不得反复重试 |

这些决定改变的是“何时需要约束、它证明什么”，不是简单地“规则全部变少”。核心定位为：**模型负责推理和执行路径，Dev Flow 负责用户意图/授权的连续性、正确能力边界、可反驳反馈与诚实交付**。将所有判断硬编码成通用流程、建立中央任务/需求数据库、自动学习路由或把跨栈知识再复制一遍均被拒绝；当前问题没有证明它们比薄 owner 协作更好。

基础方向实施采用两级处置：完整理解措辞、替代路径授权边界、维护证据分层必须在 A 中完成语义统一并加反例；路由复用只作为可删的局部优化，在证明实现简单且有实际重复成本时考虑，不阻塞 stable。没有请求新的付费对照研究；未观测行为收益保持未知。

## 4. 目标设计：薄协调层、可纠正的需求、可信的证据

### 4.1 工作闭环

用户意图 → 当前理解和已知约束 → 最小有用动作 → 原生反馈 → 只修订受影响的理解/方案 → 用户可观察的结果。

这不是新增状态机或每步文档要求。小任务直接完成；长任务使用已有产品/设计 owner，必要时补一份简短进展。模型决定合理执行路径，Dev Flow 保持意图、约束、授权和证据的一致性。

### 4.2 主动提问，不滥问、不猜授权

| 情况 | 动作 | 负例 |
|---|---|---|
| 可查的仓库、运行时事实 | 自行验证 | 不问用户当前 CLI 支持什么 |
| 多个解释会改变产品结果、恢复或外部权限 | 提一个高价值问题，必要时分轮追问 | 不把 silence/默认选项当确认 |
| 语义已定、低风险可逆实现细节 | 说明必要假设并继续 | 不因 U1 标签再次要求批准 |
| 调研/设计请求 | 给方案和差异 | 不自行实施产品代码 |
| 未决选择不影响独立可逆工作 | 继续该部分，暂停依赖部分 | 不以并行工作为借口实施待决分支 |

实际宿主工具 schema 和上层限制优先。同步/异步工具不可凭名称假定能力；问答工具不是操作审批工具，取消、空响应和打断不选中推荐项。

交互适配顺序：确认问题是否应问 → 检查当前 mode、允许用途、参数 schema 和回答生命周期 → 选择符合条件的宿主能力或正常对话。工具列在目录但限制为 Plan-only 时，在 Default 不调用也不切模式；optional-only 工具仅可提出能改善结果的非阻断问题。异步工具返回不等于用户已答，未决分支不执行，独立可逆工作可继续。若没有合适工具，必需的产品选择以正常对话结束当前回合；不反复逼问。审批沿真实宿主与用户授权边界处理，不凭工具名称推断“任何权限都能问”；不可获取的权限如实阻塞。

### 4.3 持续对齐与纠正传播

保留最小的“当前理解”：用户确认的目标/不可丢失约束、当前事实、可逆假设、未决选择。记录在既有 owner；不新增需求数据库、全局 action ledger、强制 IDs、摘要哈希或个人长期记忆。

触发重新对齐的是改变设计的事实、用户纠正、跨会话交接、重要实施切片和结束验收，不是固定每 N 次调用问用户一次。恢复上下文时重读当前 owner 和相关原始约束，必要时重新核查可漂移事实。

纠正处理：定位哪条旧假设失效 → 找依赖它的设计、代码、测试、子任务和外部动作 → 暂停/更新受影响的后续工作 → 保留未受影响结果 → 用用户行为例子重新验证。已经执行的外部动作不会因 steering 自动撤销，工具也不会自动取消；报告事实并按实际权限处理补救。

完整性标准还包括：技术受阻时不把产品目标换成容易实现的替代品；压缩/交接后仍能区分用户明确约束、仓库事实、模型假设和已否定方案。沿用已有 target-revision/增量失效机制（如适用），不要求每个任务产生 revision 协议。反馈要证明效果来自目标请求和目标制品，而非背景流量、旧缓存或 mock。Rust/FFI 关注所有权与取消/回调生命周期，Apple/Android 关注实际入口/状态/恢复；这些交给已有专业 owner，不新增一套语言或平台 Skill。

### 4.4 自适应模型、并行与方法

按任务结构、证据不确定性、实际宿主能力、成本和收益路由；模型名不是可用性证明。能力库存可包含未来字段，但被选择的组合必须受支持。对没有观察的更高能力保持 not_observed，不静默替换。

并行宽度是同时活动的资源预算，不是总工作项数量。有效宽度取宿主可用额度、用户约束、路径/资源独立性及集成能力的共同限制；宿主未暴露容量时保守逐步派发，不猜默认无限。共享写路径串行化或隔离；子任务可嵌套但不能放宽祖先边界；普通顺序工作仍用单代理。

方法选择保留小规模按需投影；已有方法足够就不增加。需要额外方法时说明它能排除哪个实质盲点；解除形式配额不等于无限测试、无限代理或无预算探索。

### 4.5 证据与恢复

检查失败必须表示失败或不可观察，不得伪装“不适用”。原生环境/调用失败是 test-system/environment 问题，不能计为产品 PASS，也不能没有依据归咎模型。

安装库存、插件注册、选中路径、当前会话实际加载分别报告。若没有宿主提供的有效身份观察，提供安全诊断/重开会话建议并保留 not_observed，不制造“已加载”信号、不改用户配置、不清缓存。

正式版状态以真实源候选、发布版本、stable、workspace base、rollback 和逐项交付事实建模；版本值变化不会自动提升交付状态。历史 RC 与回滚 tag 保留，不能因为进入 stable 就重解释或删除历史。

### 4.6 正式版状态判定表（拟采用，实施前锁定到测试）

现有 schema 字段足以表达主要身份与逐项事实，但现有 validator 将身份和资格错误耦合，必须同时修正；不新增泛用发布状态引擎。`source-candidate` 应表示“尚未公开发布的源候选”，允许正式 semver 或 RC，不能禁止如实记录已完成的 tag；`released` 继续表示已发布 RC，`stable` 表示已公开发布正式版，二者都不意味着所有资格/安装门槛成功。`published.latest_rc` 保留 RC 历史，不能在正式版发布时冒充 stable。

| 情景 | source | published 记录 | workspace.base_published | 默认安装说明 | rollback |
|---|---|---|---|---|---|
| 当前基线 | RC.9 / released | latest_rc=RC.9；stable=1.1.2 | RC.9 | 保留现有 RC.9 用户指引 | RC.8，保留既有事实 |
| 2.0 正式候选未发布 | 2.0.0 / source-candidate | 不提前修改 published | RC.9 | 仍指向已发布 RC.9，候选只能明确标注本地/隔离路径 | RC.9 是上一发布版本，不声称因而经过完整资格验证 |
| 2.0 正式发布完成 | 2.0.0 / stable | latest_rc 仍 RC.9；stable=2.0.0 | 2.0.0 | 默认稳定渠道 2.0.0，RC 指引显式 opt-in | 保留明确选择的上一可用版本；此迁移预期 RC.9 |
| 下一轮开发候选（示例） | 2.0.1-rc.1 / source-candidate | latest_rc 仍 RC.9；stable=2.0.0 | 2.0.0 | 稳定默认仍 2.0.0 | 2.0.0 |
| 下一 RC 发布（示例） | 2.0.1-rc.1 / released | latest_rc=2.0.1-rc.1；stable=2.0.0 | 2.0.1-rc.1 | 稳定默认 2.0.0；RC opt-in 指向新 RC | 2.0.0 |

基线表示当前事实，其余是拟定产品行为，不是本轮执行计划。候选版本须高于现有发布记录中最高 semver（不能只比较 latest_rc）；stable 不含 prerelease，latest_rc 必须是 RC。工作区基线必须是实际承接的已发布版本，不能永远绑定 latest_rc。回滚目标必须已发布且比候选旧，并具有适用的兼容边界；不承诺 1.x 状态可无损回滚到/从 2.0。上述 RC.9 回退只承诺待验证的插件版本切换，不是数据/宿主状态逆变换。

交付状态不批量复制：候选的新 commit、CI、artifact、review 等按其具体证据更新；公开 tag/publication 在事实发生前不能 passed，发生后也不能因后续步骤失败而隐去。正式版所需验证仍不可由 RC waive 继承。更改源文件、提示、Hook、依赖或实际加载内容后，只失效被影响的观察；发布资格必须最终绑定同一不可变候选。`workspace_head` 应说明是否相同，不把“刚检出已发布 tag 尚无修改”当永久无效状态；此处拟将严格 divergence 调整为观察，不再当发布身份完整性错误，实施时需同步原有测试和消费者。

负例：未来 stable tag、伪造 publication、错 manifest、stable 字段填写 RC、候选低于 stable、错 channel 安装说明、缺失 tag、旧版本证据套新版本均拒绝；无 Git 的发行包仍可检查结构，但 tag 事实保持 not_observed。缺少/重复当前 changelog 标题直接报明确投影错误，避免悄悄扫描全历史后产生误导归因。

Git 身份检查必须同步修改，而不只放宽字段：当前 `tools/validate_product_state.py:478-515` 只解析 latest_rc/rollback，且 HEAD 与 latest_rc 比较。拟补充 `stable_tag` 和 `workspace_base_tag` 的真实观察，HEAD 与 **workspace.base_published 对应 commit** 比较；stable/基线 tag 在实际 Git 仓库中缺失必须报错。无 Git 包、Git 命令失败/超时与确实缺 tag 分开表达，复用受控只读 Git 边界，不能将观测故障伪装成不存在仓库。

输出兼容：既有 `published_version` / `observations.published_tag` 暂保留“latest RC”含义并明确标注 legacy，新增明确的 latest-RC/stable/workspace-base 观察字段；不能静默把旧字段切成 stable。对 `workspace_head` 保留旧观察兼容或显式版本化，新增按 base 计算的字段作为当前判断来源；先查所有 consumer 再定最终 schema 变化。测试分别固定 `stable=2.0.0/latest_rc=RC.9`、缺失 stable tag、HEAD 恰好匹配 stable base、HEAD 已推进、无 Git 发行包、Git 异常，不借 fixture 复用 validator 决策。

安装事实分义：`delivery.isolated_install` 维持**发布后固定公开版本的隔离安装**含义；候选阶段不得为它填 passed。资格旅程所需的“候选隔离加载”记录在既有验证结果中（具体路径/内容身份/宿主），不冒充公开 tag 安装。这两个事实需要各自授权和证据；候选资格完成不表示已安装公开版本。tag/publication/公开安装执行与最终状态写回分开记录实际结果，不以候选资格提前提升 stable。

部分失败是正式状态设计的必测路径：

| 已观察到的结果 | 应保存的事实 | 结构与资格结论 | 下一步边界 |
|---|---|---|---|
| tag 成功、publication 失败 | source 仍 candidate；tag=passed、publication=failed；published 仍旧版本 | 一致的结构可以 valid，但该次发布操作失败、交付未完成；不能凭 valid 重试 | 保留原失败，核实原因/远端实际状态；后续重试须仍在明确授权内，不删/重打不可变 tag |
| publication 成功、公开安装失败 | 立即更新 source=stable（或 released RC）及 published；publication=passed、isolated_install=failed | 结构可以 valid，交付资格/完成结论 blocked；不能隐瞒已经发布 | 修安装或提出明确回退处置；不自动删除 Release、不把已发布改回未发布 |
| publication 响应丢失、是否发生未知 | 该步骤 blocked，并在现有进展中说明“事实待确认”；不写 passed，也不宣布没有发布 | 保留明确的不确定性；暂停重试和依赖动作 | 只读核实 exact tag/release/artifact，避免重复副作用；若权限/服务不可用则真实阻塞 |

validator 默认 `status=valid` / exit 0 仅表示记录自洽；新增可机读的动作门槛缺口/交付完成度输出，不得仅凭状态字段自动证明 hosted/旅程/远端事实。具体字段兼容在 B3 一次确定，不新增持久化证据账本。发布前 action gate 检查届时应已满足的 commit、原生回归/资格、CI、制品等；不能要求 publication 或发布后安装在发布前就 passed。发布后 completion gate 才要求发布与公开安装实际成功。所有 stable 必需门槛仍强制，历史 waiver 不可变 PASS。

此解耦必须与 `delivery-readiness`、`docs/releasing.md`、结构/动作门槛 tests 同片实施：结构合法的 failed/blocked 记录不能使发布动作获准或完成判断通过；未公开发布的 candidate 若填写 publication=passed、已公开发布却仍装作 candidate，均应报身份矛盾。CI 当前只是运行结构 validator，candidate workflow 没有发布权限，builder 只验证 commit/manifest/制品；保留这些边界，不把它们的 green 解释为发布许可。状态文字/校验器不可能替代对实际外部动作的观察。

### 4.7 宿主适配与接口兼容

F05 的宽容范围仅是**格式有效但当前产品不认识的库存项**：保留原字段或给出不支持项诊断，不让它污染已知请求；畸形类型/空值仍拒绝。选中的 model+effort 仍须同时通过产品支持表与实际宿主证据，不能“库存存在 ultra”就允许选择 ultra，也不能用 API 的 max 替换宿主 effort。保持 P0–P6/PX 及 Luna/Sol/Astra 分工，不做无证据的大迁移。

F08/F09 首选修改已有输入/输出语义，不新增调度器。`parallel_units` 明确为待处理独立单元总数，正整数不等于并发配额；若要删除已有 JSON 字段，应先查实际消费者。过渡期保留可兼容字段并明确 advisory/unknown 或提供已批准的 schema 版本迁移，不悄悄改字段类型。旧 CLI flag/version 只决定该 CLI 的兼容结果；调用方提供的 effective capability 标注为 caller-reported，不能由 CLI 自称已实际调用验证。当前宿主能力、CLI 兼容、配置上限、剩余 slot 分开报告；缺失任一信息不推出无限容量或全局不能工作。

F06 先补说明和来源分类：explicit supplied path、environment path、registry observation、effective host observation 分开。没有可用宿主接口时不建设虚构 probe；保持未知并建议用户在新会话验证。诊断仅读取允许的 manifest/registry，不执行目标仓库代码或加载未知插件；安全自测只在受信的当前执行根进行。

## 5. 研究适用性（前轮阅读与本轮来源复核）

| 来源 | 采用的有限结论 | 不应推导的结论 |
|---|---|---|
| [OpenAI：Rethinking skills and prompts for GPT-6 Astra](https://developers.openai.com/blog/rethinking-skills-and-prompts-for-gpt-6-astra) | 重新评估过度解释、提问、测试及旧模型脚手架；描述应前置关键触发 | 更强模型可以跳过授权、安全或验收 |
| [OpenAI：latest model](https://developers.openai.com/api/docs/guides/latest-model) | 模型建议需要随官方资料和实际宿主更新 | API 模型/effort 等于此宿主可派发组合 |
| [OpenAI：long-horizon Codex](https://developers.openai.com/blog/run-long-horizon-tasks-with-codex) | 持久目标和反馈有价值 | 所有任务都应建立重型外部状态系统 |
| [PROUR](https://arxiv.org/html/2609.32255v1) | 区分问用户、验证世界和行动 | 模拟事务/Qwen 实验等于本仓库 GPT-6.1 实际收益 |
| [Clarification Is Not Correction](https://arxiv.org/html/2609.25337v1) | 承认纠正不等于清除旧假设，需要行为验证 | 强制 ledger 或复杂多假设系统必定有效 |
| [Lost in Compaction](https://arxiv.org/html/2608.11242v1) | 压缩后次要约束可能丢失，应保留并验证关键约束 | 单探针/人工注入实验给出所有宿主的确定失效率 |
| [ClarEval](https://arxiv.org/html/2603.00187v1) | 缺目标、前提、术语意义时定向澄清 | oracle-assisted 改善等于自主判断已解决 |
| [AGENTS.md evaluation](https://arxiv.org/html/2602.11988v3) | 过量上下文可能增加成本，须筛选内容 | 删除全部仓库指引；跨语言泛化确定成立 |
| [SkillsBench](https://arxiv.org/html/2602.12670v4) | Skills 收益依任务/配置，有负收益案例 | 全部 Skills 都有益或都无用 |
| [Scaling agent systems](https://arxiv.org/html/2512.08296v3) | 协作收益依任务结构 | 更多代理必然更强，或永远单代理最优 |
| [Anthropic harness design](https://www.anthropic.com/engineering/harness-design-long-running-apps) | 模型进步后应删掉不再有用的 harness | 工程经验等于受控因果实验 |
| [XRepoSkill](https://arxiv.org/html/2609.36807v1) | 选择性、验证过的经验提炼值得参考 | 跨语言补充案例足以证明 Apple/Android 全栈泛化 |
| [OpenAI：steering](https://developers.openai.com/api/docs/guides/steering) | 纠正影响后续执行，不自动撤销早先动作/取消工具 | Dev Flow 已拥有宿主未暴露的取消、回滚或传输能力 |
| [OpenAI：subagents](https://learn.chatgpt.com/docs/agent-configuration/subagents) | 独立读密集任务适合并行，写密集任务需考虑冲突；权限/能力仍受宿主约束 | 放宽产品建议就能突破宿主 slot 或越权 |

研究是提出可检验改进的依据，不是本地效果证明。本次不创建付费对比实验，也不把联网资料当权限或指令。

本轮在 2026-10-03 再次打开官方模型页、模型/Skill 指南、steering、subagents、长期任务实践及论文摘要核对版本和关键结论；PROUR/Clarification/compaction 等实验范围与局限沿用前轮正文阅读。官方建议中针对 Astra 的敏感性不能未经实验改写成 Sol 6.1 的确定缺陷。研究版本和来源日期是证据范围，不是“最新即最好”的质量排名。

## 6. 拟实施批次与验收

### 批次 A：语义一致性和旧规则冲突

范围：F02、F03、F07、F10、F11、F12、F15、F16，以及 §3.4 中必须处理的基础语义；Skills/references、agents 默认提示、治理 registry 与对应 contract tests 同步。首先修复不同入口说法矛盾，再补纠正传播的精简行为规则。删除重复规则，保留一个 owner 与必要投影。

验收：明确需求直接继续；实质选择才问；旧假设纠正后受影响测试/子任务重检；无关任务无强制文件/ledger；路由输出不能重新注入被删除的要求。反例覆盖取消/空回答、已执行外部动作、过期子结果、无需提问的 bugfix。不得通过删除真实边界断言来“修绿”。

### 批次 B：执行、能力观察与状态迁移

范围：F01、F04、F05、F06、F08、F09、F13、F14、F17；本地 CLI 与 tests。先隔离已有 fixture 漂移再验证状态演进。选择受控 Git helper 的最小复用，不做通用框架。状态演进遵循 §4.6，接口兼容遵循 §4.7。

验收：真实非 Git 才 N/A；Git 非零/超时/异常不可通过；未知库存与已知可用项共存可路由；请求未知能力仍拒绝；9 个任务可分批而不要求 9 个并发；实际宿主能力与过时 flag 不混淆；当前会话无证据时不得 loaded=true；stable 全生命周期正负例通过且历史状态仍有效。

### 批次 C：有界正式版资格验证

只在 A/B 实施并获后续授权后执行：累计需求语义复核、独立整合审查、完整确定性回归，以及 `docs/releasing.md` 定义的五条真实功能旅程：普通 bugfix、重大语义改动、诊断/修复边界、无关 MCP 任务、延续任务不扩权。已有真实失败例融入这些旅程，不新增固定 case 配额。

每条旅程预先写清用户结果、受保护行为、环境、可反驳 oracle、停止点；记录首个失败并区分实现、harness、宿主和未知。没有授权/环境则 NOT RUN；不以历史 waive 顶替 stable 证据。若正式发布需额外 hosted/platform/artifact/install 证据，分别采集，不从本地结果推断。

旅程必须加载待资格认定候选的实际内容，而非开发目录或主 profile 中旧缓存；记录宿主、实际路径/内容身份和可观察结果，不强制新增通用 attestation schema。实际身份无法确认时，行为观察可以保留，但不能算该候选的资格。只改版本号不能令旅程自动有效；相关内容改变后重跑受影响旅程。此处使用已有旅程/证据载体，不修改用户主安装，隔离运行也需后续对应授权。

重大语义旅程应使用有原生可运行结果的最小应用，把以下阶段纳入同一条真实交互，不增加固定 case 配额：

1. 用户明确要求先审阅理解：应提出尚存的实质选择，并停止依赖它的设计/代码；没有实质选择也尊重“先审阅”要求。
2. 用户随后明确确认并授权实施：不因仍是 U1 再次停顿，应实施并运行原生结果检查。需要观察真实动作；`--understanding-confirmed` 的 CLI 输出不证明模型做到了。
3. 用户纠正一个早期假设：替换相关数据/代码/测试期望；若该旅程有真实受影响子任务，更新/取消并检查晚到输出，不能接受旧结果覆盖新语义。无子任务时这部分仅 deterministic fixture，不虚称活体协作已验证。
4. 在真实支持的续跑边界恢复：保留一条只出现一次的保护约束和已否定方案，再执行用户场景与反例。宿主无法观察/强制 compaction 时只能称 continuation，不称 compaction 保真验证。

负控制应使旧行为失败：明确确认后仍停顿、只改文案但旧数据语义未改、以旧测试 green 冒充新需求通过、将过期子结果当当前结果、已完成副作用被虚称撤销。现有 `evals/flow-activation-semantic-cases.json` 的 `SEMANTIC-U1-CONFIRMATION` 本身要求 stop，必须保留作该分支正例，不能单独证明上述继续和纠偏行为。无需为了验证而操作真实外部系统；副作用恢复用安全替身，并标明证据层。

### 实施责任与可独立交付切片

| 切片 | 唯一主要 owner 与同步消费者 | 必须先看到的失败/反例 | 完成与停止条件 |
|---|---|---|---|
| A1 需求/交互一致性 | `requirements-design`；dev-flow core-lifecycle、codex-native-adapters、agents YAML、user-interaction-contract；`evals/test_dev_flow_v2.py` 与 contract checks | 已确认 U1 不应再次停；exposed-but-forbidden 不应调用 | owner/投影一致且 deterministic 正负例通过；真实行为等 C 验证，不宣传效率收益 |
| A2 持续纠偏/原生反馈 | dev-flow；requirements-design、architecture-decisions、verification、change-review 的必要短交接 | 只改需求摘要但旧实现/测试/子结果仍有效 | 只更新受影响规则，现有 native-feedback 负控保留；不创建语义数据库 |
| A3 方法与并发旧规则 | methodology-pool、industry-practices 及各 reference 的现有 owner；route-task 投影、methodology tests | 普通诊断被投影 digest/ledger；治理禁止现有合法嵌套 | 触发范围正确，安全边界不变；方法展示 3/2 默认预算保留 |
| A4 发布规则与导航 | `docs/releasing.md` 的发布合同；maintainer entry/reference、industry-practices、contract checks、docs/index | 3×3 与薄发布冲突；索引指错当前状态 | 发布层与研究层分离；不重写历史发布记录 |
| A5 基础取向校准 | requirements-design、quality-calibration、maintainer/behavior-evaluation；ActiveGuidanceTests、相应语义旅程 | 未决产品选择误阻断只读查证；能力缺失误禁已授权路径；正确性修复误需收益试验 | §3.4 的双向边界均有正负例；保留 exact-tool/local-only、权限和证据限制。模型策略仅校准声明；路由复用可不实施 |
| B0 基线测试隔离 | `evals/test_product_state.py`、`evals/test_release_artifacts.py` | 本轮 4 个失败及独立错误投影负例 | 不动态抄被测选择规则、不伪造示例 attestation；保留历史固定场景 |
| B1 Git/运行时诊断 | `workstream_contract.py`、`runtime_doctor.py`；`evals/test_rc4_convergence.py`、`evals/test_runtime_doctor.py` | Git 128/timeout 不能 N/A； supplied root 不能等于 live identity | 有结构化失败和来源；安全边界/dirty保护不退化 |
| B2 能力和容量 | `agent_dispatch.py`、`dev_flow.py` preflight；profiles、routing cases、`evals/test_agent_dispatch.py`、preflight tests | valid medium+unknown ultra；9项分批；mode/CLI/effective冲突 | 兼容输出、选中组合严格、无静默fallback；无实际调度/性能收益宣称 |
| B3 stable 状态演进 | product-state validator；README/releasing/governance/manifest/workstream/workflow projections、相关 tests | §4.6 独立状态表以及 stable+旧 RC 安装的假绿 | 全迁移正负例、历史兼容，状态没有凭文案升级；不触发发布 |
| C 最终候选资格 | releasing/evaluation 既有 owner；最终候选与隔离宿主 | A/B 中真实语义回归与错误加载身份 | 五旅程和最终完整回归；不具备证据则明确阻塞，不移除门槛 |

次序：A1/A2/A5 优先确定语义，A3/A4 同步规则；B0 是 B3 的前置，B1/B2 可在不共享写路径/资源时独立实施；A/B 整合后再 C。每片先窄测再受影响集成，最后完整回归，不要求每片重复完整套件。额外代理只用于真正独立或干净上下文审查。

回退与停止：设计/提示效果退化时回退该片改动、恢复此前 owner/投影并重跑相关反例；不恢复已确认逻辑缺陷、不静默重启旧 packet 要求。schema 变更先识别消费者并走显式兼容决策；无充分需要就保持现有 schema。新依赖/平台/私人记录/模型开销/发布安装等超出本方案授权边界时单独请求，不靠“必须完成 stable”扩权。

完成定义：每个计划项都有代码/规则 owner、原生验证和处置；重大未决缺陷为零；未执行的环境与交付动作单列；本地实施完成、正式版资格、发布、安装、当前会话加载分别结论。

## 7. 多轮审计与红蓝对抗记录

执行方式：基线源码核验及扩展扫描 → 独立红队挑战总方案和遗漏 → 蓝队提出最小修订 → 主代理核查并更新 → 独立复查修订后的稳定目标。各轮应报告新证据、已驳回误报、真实新增问题和剩余不确定性，不以“零发现”保证完美。

本节保留本轮累计过程。未经核查的候选问题不计入已确认清单。总方案变更后，仅受影响结论需要重审；整份产品还未实现，所以设计审查关闭不能标为代码缺陷已修复。

### 第一轮：基线核验与扩展扫描（已完成）

2026-10-03，主代理重新读取相关源码：F01–F05、F08–F10 的关键路径仍存在。只读 CLI 再现 F05：请求已支持的 `gpt-6.1-sol:medium`，库存同时包含 `gpt-6.1-sol:ultra`，整个请求 exit 2；再现 F08：`parallel-units=9` exit 2。这不是实际多代理容量或性能测试。

首次测试结果原样保留：`python3 -m unittest evals.test_agent_dispatch evals.test_product_state evals.test_runtime_doctor` 执行 48 项，3 failures。随后单独运行 `evals.test_product_state`，21 项同样 3 failures，排除组合顺序是必要原因：

- `test_repository_product_state_is_valid`：实际 RC.9，断言 RC.8。
- `test_development_workspace_cannot_be_identical_to_its_published_base`：fixture 引入 RC.9 状态但只创建 RC.8/7/6 标签，先触发缺少 RC.9 标签。
- `test_candidate_does_not_inherit_historical_review_claim`：当前 source=RC.9，fixture 附加的是 RC.8/7 标题，未形成预期当前版本边界；历史审查声明被纳入 fallback 范围。归为 fixture 漂移；缺少当前标题时 validator 的严格策略另行设计，不为迁就 fixture 放松它。

`python3 tools/validate_product_state.py` 当前返回 valid（仅结构一致性）；repository-knowledge check passed；`git diff --check` passed。现有测试绿色与本方案正确之间没有蕴含关系；这 3 项失败也没有被本轮文档修改修复。

扩展完整本地回归：`python3 -m unittest discover -s evals -p 'test_*.py'` 共 646 项，4 failures、1 skipped，耗时约 66 秒。前三项同上，第四项是 `test_release_identity_and_lifecycle_claims_match_exercised_evidence` 的 RC.8 示例版本与 RC.9 manifest 冲突（F14）。这是本机 Python 的确定性诊断，不是 hosted/Linux/Windows 或正式版资格；未加 CI 的 ResourceWarning-as-error 参数，不标为完整等价 CI 运行。

`evals/run_contract_checks.py`（39 contracts）、maintainer `validate-suite.py`（15 Skills/32 dispatch cases）、`validate-knowledge`、plugin `check`、Python compileall 均通过；data-security doctor 返回 `valid_with_manual_gates`（required failures=0、5 manual gates）。这些检查没有证明实际当前会话 Hook 已加载。F04 额外受控 mock：Git 返回 128/permission denied，`workstream_contract.check(..., check_worktree=True)` 实际返回 exit 0 / not-applicable / root-is-not-a-git-worktree，复现错误分类。

唯一 skip 是 `test_real_windows_job_closes_a_successful_parents_descendant`，原因 `hosted Windows Job Object integration`；本机结果不包含 Windows Job Object 实机证据。

### 第二轮：独立红队挑战 v0（已整合）

独立、无实现者会话上下文的红队发现 2 项 P2 方案缺口，没有 P1：

- 正式版迁移缺独立期望。红队临时 fixture 可让 `source=stable 2.0.0` 与旧 RC 默认安装同时 validator=valid。主代理核实 validator/fixture 因果链，加入 §4.6 小型状态表和独立正负例；设计已处置，产品修复未实施。
- U1 样例明示 stop，无法证明确认后继续/纠正传播。主代理核对 semantic case 与静态测试，加入同旅程多轮行为检查和最终加载身份要求；行为验证仍 NOT RUN。

红队驳回“宽容库存必然放行未知 selected”“嵌套必然扩权”“默认三方法必然漏检”等过强结论。另修正 F01 错写的测试路径，不计为新产品缺陷。只读扩展审计增加 F15，主代理增加 F13/F14 基线失败和 F16 导航漂移。

### 第三轮：蓝队最小可实施性修订（已整合）

蓝队核对了新增状态表和宿主适配，确认无需通用状态引擎，并提出两处必须落到实施的细节：

- 候选隔离加载与 `delivery.isolated_install`（公开固定版本安装）不可共用含义；已在 §4.6 明确分离。
- stable/base 的 Git 分支也必须修，不能仅解除 latest_rc 字段约束；已补 Git 观察、legacy 输出兼容和缺 stable tag/HEAD=base 的独立负例。
- F10 同类残留还包括 `semantic-baseline`。主代理运行 `python3 skills/dev-flow-maintainer/scripts/select-methods.py --phase requirements --intent design --available repository-facts`，确实输出 ambiguity ledger 和 stable acceptance IDs；并入 A3。此复现属于显式 maintainer 方法入口，不宣称每个普通 route-task 都会触发；旧公共 `select-methods` 命令正确返回 unsupported，不恢复它。

主代理直接复核了对应源码和消费者，补充了 A/B/C 的 owner、测试入口、前置关系、回退与停止条件。蓝队建议属于方案修订，不表示已实现或测试通过。

### 第四轮：干净上下文复查 v2（已整合）

复查冻结的 v2（268 行），新增 1 项 P2：部分交付成功/失败无有效表达路径，归入 F17。红队用内存 mock 验证 tag 成功/publication 失败被 candidate 规则拒绝，publication 成功/isolated_install 失败被 stable 规则拒绝；主代理核对源判断与 CI、builder、candidate workflow 消费边界，增加 §4.6 部分失败表以及结构/资格/前后动作门槛分离。没有宣称该缺陷已在产品中修复。

该轮对库存、并行、交互 eligibility、行为旅程与其余实施切片未再发现实质缺口；这不是全产品无缺陷保证。用户随后明确追加基础设计取向审计，下一轮不再局限于修补既有规则。

### 第五轮：基础出发点与设计取向（已整合）

独立代理按“如果面向当前模型重新设计，哪些约束仍成立”审查，主代理同时核对原 owner，并将保留、修订、退役和有条件优化分开写入 §3.4。新增的是设计取舍，不把它们全部伪装成已复现 bug；F02/F10 等重复发现仍用原编号。

特别追溯了能力替代禁令的来源：`docs/workstreams/dev-flow-2.0-rc.3/decisions.md` D5 原本针对不可用 scanner 的重复权限失败；RC.5 requirements 第 8 条防止虚构身份/无关 MCP。`benchmarks/cases/dev-flow-cases.json` 的三个相关用例分别明确禁止发现、禁止特定无关工具、限定 exact 工具。主代理逐一读取确认，它们不能证明普通已授权任务也必须由用户预选工具。因此拟收窄规则，但三个原负例一律保留，新增同范围合法替代正例；没有改变 benchmark runner 或执行模型试验。

同时核实：requirements 首段已正确写“下一 slice 足够理解”，冲突只在 complete/blanket boundary；profile 排序已经是代码中的 policy，因此主要修正其解读而非凭论文重排等级；maintainer 的 observed-unguided-failure 适合新能力收益声明，却不应阻止源契约正确性修复。路由复用尚无成本观测，故降为非阻断可选项，避免用“自适应”引入新缓存/编排框架。

### 第六轮：基础调整与部分失败的最终定向红队（已完成）

前轮独立红队重新检查 v4 的 §3.4、§4.2、§4.6、A5 及三个能力负例，限定范围未发现新的实质问题。F17 的**设计缺口**已关闭：身份/事实/结构/发布前门槛/发布后完成度均有明确归属，并包含响应未知的安全恢复。新基础规则允许查证和比较技术事实，但没有放行依赖未决用户选择的承诺或实施，也未弱化 exact-tool/local-only、权限和证据限制。

这次是同一审查者的修订复核，不宣称又一次无历史上下文全产品审计。审查期间核心章节保持不变，变化仅为标题和审计记录。停止继续加轮的原因是已知实质缺口均有处置、定向反例未发现新缺口；不是保证不存在未知问题。

### 本轮文件交付与验证终态

- 只新增本文件，给 `docs/index.md` 增加一个导航链接；HEAD 仍为开头所列基线。产品代码、治理状态、旧 workstream 实施/进展、安装和宿主配置均未修改；没有 commit/push/tag/publish。
- 最终文档检查：`validate-knowledge --root /Users/ethan/Repo/dev-flow` valid；repository-knowledge check passed（0 errors/0 warnings）；tracked diff whitespace 检查无问题；新文件的 no-index whitespace 检查无诊断（exit 1 表示新文件有差异）。一次未给 `--root` 的知识校验调用 exit 2，补齐必需参数后通过，不归为产品失败。
- `check-workstream --root /Users/ethan/Repo/dev-flow --path docs/workstreams/dev-flow-2.0` 返回 not-applicable：该目录未声明 managed marker，不能称 workstream PASS。实施阶段选择/启用 managed owner 后再按其契约检查。
- 本地工程基线仍为 646 tests、4 failures、1 skipped；其余 deterministic validators 的具体结果见第一轮。未因后续只改文档重复全套回归，也未把未修失败标绿。
- 尚待实施决定：B3 的具体兼容输出字段需在盘点消费者后锁定；可选路由复用可舍弃。尚待实证：提示/交互/纠偏的真实模型行为、实际候选加载、hosted/platform、制品和公开安装；不能从设计审查推导这些通过。

## 8. 下一位实施者的入口

先读本文件的最终状态、问题表、批次与剩余边界，再核对当前 Git 与 `governance/product-state.json`，然后读取各批次所列原有 owner。不要从历史 RC workstream 的完成字样推导 stable 就绪。用户确认实施后，在既有或明确选择的实施 workstream 中保持稳定 `implementation.md` 和更新中的 `progress.md`；本文件的单文件审计要求不意味着新建一套通用进展系统。
