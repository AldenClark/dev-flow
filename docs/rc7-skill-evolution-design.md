# Dev Flow RC.7 Skill 演进设计

> 状态：已接受的实施前设计基线；对应主 Skill、专业 Skills、路由、方法与候选状态改造已在 RC.7 source-candidate 工作树实现。
> 配套资料：[开发指导主线](./rc7-development-lifecycle.md)、[方法工具箱](./rc7-methodology-system.md) 与 [本地任务回看](./rc7-dogfood-audit.md)。

## 1. 设计结论

RC.7 不新增一个“完整开发流程”Skill。它在 RC.6 的 15 个 Skill 上做两类改造：

1. 把 `dev-flow` 从高密度的流程、路由和控制说明，收敛成一条有判断力的开发主干；
2. 把专业 Skill 从“该领域的程序清单”，增强为真正能提高该环节成果质量的工作指导。

目标结构是：

```text
用户目标与仓库现实
        |
        v
dev-flow：保持方向、选择当前最有价值的动作、综合最终结果
        |
        +-- 当前事实不够 --------> repo-context
        +-- 产品意义不清 --------> requirements-design
        +-- 用户流程/界面不清 ----> product-ux-discovery
        +-- 技术取舍不清 --------> architecture-decisions
        +-- 依赖取舍不清 --------> dependency-decisions
        +-- 因果不清 ------------> systematic-debugging
        +-- 证据不够 ------------> verification
        +-- 测试系统不可信/待建立 -> test-system-engineering
        +-- 最终变化需挑战 ------> change-review
        +-- 知识体系需建立 ------> repository-knowledge
        +-- 偏好资产需管理 ------> manage-engineering-profiles
        +-- 交付动作将发生 ------> delivery-readiness
        +-- 敏感数据边界出现 ----> company-data-security
```

这些箭头不是阶段迁移。一次任务可以从任意位置开始，可以只用一个 Skill，也可以在新证据出现后返回前面的判断。`dev-flow` 不替专业 Skill 做决定，专业 Skill 也不接管整个任务。

## 2. RC.6 当前结构的主要问题

RC.6 的基础并不差。它已经具备仓库优先、按风险缩放、专业 owner、渐进披露、诚实证据、直接/持续工作区分等关键能力。RC.7 要解决的是这些能力目前还没有充分转化成自然、稳定的开发表现。

### 2.1 主 Skill 过于拥挤

当前 `dev-flow/SKILL.md` 同时解释：

- 授权和信任边界；
- 负向触发；
- intent、U1-U5、direct/managed 和 risk overlays；
- `route-task` 的强制调用条件与纠错；
- 工作流文档；
- 质量校准；
- 实施、测试、审查；
- 多代理、独立审查和模型路由；
- 完成声明与知识影响。

这些内容分别合理，聚在入口后却产生三个副作用：

- AI 更容易先执行分类和路由，而不是先理解任务；
- 一些本应是内部启发式的概念变成用户可感知的流程；
- 专业 Skill 看似被调用，真正决定结果的指导仍堆在主 Skill 中。

### 2.2 专业 Skill 的“责任”清楚，“手艺”不足

多数专业 Skill 已经能回答“什么时候用”和“不要做什么”，但对以下问题回答不够：

- 第一个高价值动作是什么；
- 怎样在中途发现理解或方案质量不足；
- 怎样反复打磨而不机械增加轮次；
- 什么样的结果才算真正解决了该领域问题；
- 什么情况下应该停止、退回或换一种方法。

因此它们更像路由终点，不完全像能带着 AI 把事情做好的专业工作法。

### 2.3 路由模型仍有隐性的流水线倾向

当前固定路由通常把 `repo-context` 和 `verification` 放入大量任务，再按风险增加其他 Skill。这对确定性测试很好，但真实任务中容易形成“先加载一组角色”的思维。

RC.7 应改成：先识别**当前阻碍下一步质量的具体问题**，再加载能改变这个决定或证据的最小 owner。专业 Skill 完成局部责任后回到任务，而不是把工作交给下一站。

### 2.4 方法能力分布不均

当前 117 个方法中，`architecture-decisions` 名义上拥有 38 个，`verification` 拥有 28 个，其他 owner 明显更少。这不一定表示功能错误，但说明方法组织仍沿用较宽的阶段归属。

RC.7 应让方法按“它解决什么困难”进入专业 Skill。方法 ID 可以保持兼容，owner 和参考入口则逐步校正。一个 Skill 不需要因为名义上拥有几十个方法而在普通任务中理解整个方法库。

### 2.5 “实施和编码质量”没有单独 owner

当前相关指导分散在：

- `dev-flow` 的 coherent slice；
- `architecture-decisions` 的中性工程策略；
- `verification` 和 `change-review`；
- 宿主提供的语言、框架和专项 Skill。

这可能是实际缺口，但目前证据不足以直接增加第 16 个 Skill。RC.7 先增强现有组合，再用真实任务确认是否仍反复出现无人负责的实现质量问题。

## 3. Skill 套件的目标分工

### 3.1 `dev-flow` 只拥有五件事

主 Skill 的长期责任收敛为：

1. **保持结果方向**：持续对齐用户最终应观察到的变化和受保护行为；
2. **选择下一步**：根据当前最大未知、后果、波及和可逆性，选择最有判别力的动作；
3. **组合专业能力**：只在专业 owner 能实质改变决定或证据时加载；
4. **保持变化完整**：让代码、测试、受影响知识和最终 diff 围绕同一个完整切片；
5. **综合完成结论**：把实现、证据、限制、未运行环境和交付边界重新合成一个诚实结论。

以下内容不再由主入口详细承担：

- U1-U5 的完整分类说明；
- 方法候选、前置条件和选择程序；
- P0-P6 模型细节；
- workstream 字段和结构合同；
- 测试类型、审查攻击面、交付制品的详细清单；
- 各专业领域的完整风险枚举。

这些信息保留在相应专业 Skill、按需 reference 或确定性工具里。

### 3.2 专业 Skill 各自拥有一个质量问题

专业 Skill 不是流程阶段，而是问题 owner：

| Skill | 它真正拥有的质量问题 | 不拥有 |
|---|---|---|
| `repo-context` | 当前决定依赖哪些真实仓库事实 | 产品意义和技术取舍 |
| `requirements-design` | 要解决什么、行为应该是什么意思 | 实现结构和测试命令 |
| `product-ux-discovery` | 用户怎样理解、操作、失败和恢复 | 后端架构和视觉偏好替用户决策 |
| `architecture-decisions` | 边界、所有权、状态和演进怎样安排 | 产品语义和依赖批准 |
| `dependency-decisions` | 外部能力是否值得引入、怎样退出 | 用依赖替代架构思考 |
| `systematic-debugging` | 哪个最早原因造成了现象 | 未经授权的修复和顺便重构 |
| `verification` | 哪些证据足以推翻错误实现 | 测试框架本身的完整治理 |
| `test-system-engineering` | 测试系统能否稳定地产生可信反馈 | 把绿色 runner 当作产品正确性 |
| `change-review` | 最终变化中有哪些可验证的后果性缺陷 | 用风格偏好制造 finding |
| `repository-knowledge` | 哪些长期知识放在哪里才可发现、可维护 | 每次任务的普通文档更新 |
| `manage-engineering-profiles` | 明确偏好如何被保存、解释和治理 | 从代码频率猜测个人或团队政策 |
| `delivery-readiness` | 某个具体交付动作是否已具备身份、证据和恢复条件 | 自动获得交付授权 |
| `company-data-security` | 数据怎样以最小暴露完成任务 | 接管普通工程生命周期 |
| `dev-flow-maintainer` | Skill 套件本身怎样演进并证明边际价值 | 普通项目开发 |

### 3.3 主 Skill 与专业 Skill 的协作协议

协作不依赖状态机，只遵循四条自然规则：

- **一个当前主问题，一个主要 owner。** 可以有辅助 Skill，但不要同时把所有邻近 Skill 加入上下文。
- **owner 产出可直接用于下一步的结果。** 例如需求 Skill 产出行为理解，架构 Skill 产出选择和边界，验证 Skill 产出可反驳声明的证据。
- **专业结果回到主任务。** 不把用户交给一条 Skill 链，也不要求 handoff 文档。
- **冲突按事实所有权解决。** 产品意义归需求/产品，仓库现状归源码与 `repo-context`，技术取舍归架构，证据结论归验证，外部动作归授权和交付 owner。

## 4. `dev-flow` 主 Skill 的具体改造

### 4.1 新入口应围绕自然开发循环

主入口建议只保留下面的认知骨架：

```text
看清现实 -> 对准结果 -> 选择下一步 -> 做出完整变化 -> 证明它 -> 留下有用知识
```

它不是六步检查表。入口应告诉 AI：

- 从任何位置进入；
- 新事实可以随时让工作回到理解或设计；
- 简单任务可以在一次连续动作中完成；
- 复杂任务才需要反复循环和持续文档。

### 4.2 用“何时慢下来”替代任务等级

主 Skill 不必首先输出 U1-U5、风险等级或过程模式。它只需在以下情况放慢并调用专业能力：

- 两种以上产品解释仍然成立；
- 当前方案跨越公共合同、持久数据、并发、外部系统或所有权边界；
- 错误后果高、难以及时发现或难以恢复；
- 新抽象、依赖或机制的独立价值说不清；
- 失败或测试结果反驳了当前模型；
- 工作需要跨会话、跨人或多个独立切片持续推进。

现有 U1-U5 可以暂时保留在兼容 CLI 和需求 reference 中，但不再作为主入口的用户可见组织方式。真正需要停下来确认的是“仍存在会改变产品结果的用户决策”，不是命中了某个分类代码。

### 4.3 `route-task` 从强制仪式改成诊断工具

建议目标行为：

- 普通开发由主 Skill 直接选择 owner，不为证明路由而运行 CLI；
- 当 owner 冲突、方法候选复杂、兼容路由需要观察或维护者正在调试激活行为时，`route-task` 提供确定性诊断；
- CLI 输出不成为任务状态、批准、完成证据或继续工作的前置许可；
- 兼容期保留现有字段和命令，先取消运行时强制，再根据使用数据决定是否收缩公共表面。

这项变化必须通过“该加载的仍能加载、简单任务更安静、无 CLI 时质量不下降”来验证，而不是只改文案。

本地任务回看进一步要求路由按**语义目标摊销**：owner 已经确定后，普通续接、工具中断、上下文压缩或需求细化不触发重复路由。只有意图、权限、平台、范围、主要风险或证据计划发生材料变化时才重新判断。重点样本中可识别到 48 次 `route-task`，虽然一部分属于 Dev Flow 自身维护，但其他长任务也出现重复调用，因此“静默直达”应成为行为测试，而不是文案愿望。

### 4.4 direct/managed 只表达连续性

保留 direct/managed 的实际价值，但不让它们变成两套流程：

- `direct`：上下文、代码和当前对话足以可靠完成；仍更新本次变化触及的现有产品、设计、测试或运行文档；
- `managed`：任务需要跨会话/人/独立切片恢复，因此依照仓库现有约定维护最小实施/进度真相或 change record，并链接各环节的长期 owner。

选择依据只有“是否需要可靠续接”，而不是任务看起来是否重要。新增、明显行为变化、跨边界设计和新项目必须更新它们实际改变的产品、设计、架构、测试或运行 owner，但只有现有 owner 无法支撑跨会话/人/切片续接时才增加中心导航。不要求 requirements、design、ADR、test matrix 各自成为独立文件；机械任务不因为 Dev Flow 激活而创建文档。

### 4.5 工程偏好怎样进入主线

RC.7 应在主入口或一个很短的共享 reference 中保留稳定偏好：

- 先从仓库证据和现有约定生长方案；
- 优先最小而完整的结果，不堆半成品层；
- 先证明变化轴，再抽象；
- 让非法状态更难表达，在不可信边界完成解析；
- 行为变化与大范围重构尽量分离；
- 测试从可能发生的错误和用户结果出发；
- 最终 diff 必须重新对齐目标、范围、知识和证据；
- 本地、CI、模拟器、设备、安装、部署、生产证据永不互相冒充。

个人偏好由已确认 profile 补充；主 Skill 只消费有效结果，不自行推断或持久化偏好。

这里必须区分承载者：宿主系统和仓库指令拥有所有任务都适用的授权、用户修改保护和证据诚实；Dev Flow 主 Skill 只在激活时强化它们。静默路径可以没有 Dev Flow 路由与文档，却不能没有明确的宿主/仓库合同。行为 eval 要分别覆盖主 Skill 已加载和未加载的情况，证明 RC.7 不削弱现有边界，也不把宿主能力冒充为 Dev Flow 自己提供的能力。

### 4.6 入口内容建议

新的 `SKILL.md` 可以收敛为七个短部分：

1. 目的和默认取向；
2. 自然开发循环；
3. 何时调用哪个专业 owner；
4. 何时增加深度或持续性；
5. 实施与验证的共同原则；
6. 环节文档接力、知识回写与完成综合；
7. 授权、用户修改和证据环境等少数硬边界。

模型路由、独立审查、方法系统、workstream、信任边界分别由链接清楚的按需 reference 承担。

### 4.7 模型与多代理从“等级规则”改成工作分配判断

主 Skill 只保留决定是否委派的原则，不暴露完整 P0-P6 表：

- 没有独立工作面时由当前代理完成；出现能带来净进度、专业性或干净上下文价值的独立单元时主动委派；
- 只有子任务可以独立产出有用结果，或者确实需要干净上下文时才委派；
- 需求理解、方案形成、实施和验收高度互相依赖时保持在同一主线；
- 机械、封闭且有确定 oracle 的工作可以使用快速模型；
- 需要普通探索、因果分析和技术取舍的工作使用均衡模型；
- 开放、跨边界或高后果的语义、架构和验收判断使用更强模型与更深思考；
- 文件数量、token 数和工具调用量本身不决定模型等级；
- root 必须检查真实源码、diff 和测试，不能把子代理摘要当作集成证据。

具体模型名、effort、可用并发和路由参数属于宿主能力与按需 orchestration reference。这样模型更新时不需要重写开发哲学，主入口也不会因为一张模型表变得陈旧。独立审查仍需真实的独立上下文，但不需要用户为 spawn 单独授权；同一上下文换一个“reviewer”标签仍然不产生独立性。

RC.7 明确废除“delegation authority”这一层：root 启动子代理、子代理在继承边界内继续启动子代理、以及为材料变化启动独立 reviewer，都是可直接执行的内部工作分配，不向用户请求许可。需要单独授权的是子代理拟执行的 commit/push/发布/部署/安装/外部通信/敏感访问/破坏性操作或真实范围扩张，而不是派发本身。宿主没有独立上下文或任务不可拆分时如实降级，不能写成“用户未授权 reviewer”。

子代理派发仍满足三项运行约束：派发前定义独立有用的工作产品和 oracle；root/parent 预先知道怎样把结果并回主线；已无后果性未知时停止继续派发。审查不以固定轮数或 P0/P1/P2 全部归零为目标，剩余内容只是命名、措辞或个人偏好时结束。

现有 `route-agent` 与 P0-P6 模型/effort 分工整体保留，不新建代理 Skill。RC.7 只调整授权语义、嵌套委派和宿主适配：P0-P6 自动选择且不弹用户确认；PX 与另行计费的批量模型试验仍由异常预算规则管理；`--independent-review-authorized` 不再决定是否能派发，可作为兼容输入短期保留但不得让缺省路径降级。

## 5. 专业 Skill 的共同改造原则

每个专业 Skill 不必使用同一模板，但都应让另一个 Codex 实例容易回答七个问题：

1. 模型怎样从用户语言、仓库事实或中途新证据及时发现这个困难？
2. 我现在遇到的具体困难是否属于它？
3. 最值得先做的动作是什么？
4. 怎样发现当前结果仍然肤浅或错误？
5. 有哪些方法能在特定困难下加深工作？
6. 什么结果可以直接帮助下一步开发？
7. 什么时候应该停止、退回主任务或交给另一个 owner？

“输出”不等于文档。它可以是：确认后的行为语义、一个被淘汰的方案、一个状态模型、一个最小复现、修改后的测试、一次真实渲染观察、一条具体 finding，或者一份未来确实需要的 ADR。

所有专业 Skill 还应采用以下写法：

- 正向触发写成可观察的问题，不写“复杂任务”；
- 负向触发保护普通工作不被过度激活；
- 区分“分类后路由可表达”和“分类前问题可被自然识别”，不能用前者冒充后者；
- 需要隐式发现的 owner 同时覆盖入口 metadata、主流程/`repo-context` 识别、中途 rebind 和行为 eval；显式 owner 则使用一致的 implicit-off metadata 与负向案例；
- 采用[证据触发的 owner 发现机制](rc7-specialist-discovery-audit.md#rc7-solution-evidence-triggered-owner-discovery)：主入口只常驻少量可观察问题，专业正文按需加载；不把 15 个 Skill 的完整说明塞回静态上下文；
- 将 candidate discovery、admission 和 application effect 分开判断，允许 `none`，通常只保留一个主 owner 和至多一个真正相邻的候选；
- 在初始意图、仓库事实、语义确认、首次矛盾/假绿、材料边界扩张和完成声明前进行有界检查；目标与证据未变时保持 sticky，不因续接或上下文压缩反复加载；
- 把 Skill metadata 当作不可信的操作输入：发现不能自动产生信任、安装、权限或交付授权；
- 默认给高自由度，仅对安全、权限、迁移和脆弱操作给精确顺序；
- 常见失败和停止条件比完整步骤清单更重要；
- 方法通过困境进入，不通过方法目录进入；
- 详细模式和例子放 reference，入口不复制百科。

## 6. 各专业 Skill 的深化方案

### 6.1 `repo-context`：从仓库清点变成决策所需事实

保留 Git 根、指令、工作树、调用路径和原生控制，但把重心从“返回 context 信息”改成：**找出会改变下一步决定的最少事实**。

增强方向：

- 起手先明确当前要支持哪个决定，避免无目标遍历；
- 同时追踪正常路径、错误路径、消费者和现有测试，而不仅是目标文件；
- 对旧项目优先寻找附近类比和权威来源，对新项目优先确认 toolchain、入口、运行和测试反馈；
- 输出区分事实、可信推断、尚未观察和真正属于用户的选择；
- 比较任务必须说明两边各自的身份、权威和差异，不能用类比替代目标事实。

应避免：为普通任务生成 context ledger、全仓库地图或 Skill 候选清单。

### 6.2 `requirements-design`：成为需求理解与反复澄清的核心

这是 RC.7 的重点改造对象。目标不是生成完整需求文档，而是让 AI 在编码前获得足以做对下一步的产品理解。

建议工作法：

1. 从现有行为、用户表述和真实例子建立初始理解；
2. 找出至少一个代表性场景、一个边界/失败场景和必要的保护行为；
3. 用反例、状态变化或时间顺序挑战仍含混的词；
4. 区分仓库可以回答的事实与必须由用户决定的产品语义；
5. 只对会改变行为、范围、不可逆后果或外部权限的分歧提问；
6. 新增或明显行为变化在进入技术设计前，给出一份完整但自然语言化的理解供确认；
7. 新证据推翻理解时，重新给出完整修订，不维护修订编号仪式。

质量判断不看字段是否齐全，而看：

- 两个实现者是否会据此做出相同的用户行为；
- 失败、恢复、权限和兼容是否仍有会改变实现的空白；
- 验收行为能否从产品意义自然推出；
- 明确的非目标是否足以抑制范围漂移。

方法入口：具体例子/反例、EARS、决策表、状态模型、事件时间线、story mapping、event modeling。方法结果融入理解，不单独生成方法报告。

### 6.3 `product-ux-discovery`：从状态检查走向真实任务体验

增强为三个相互反馈的视角：

- **任务视角**：用户从什么入口、为了什么目标、怎样完成或恢复；
- **系统状态视角**：加载、空、错误、权限、离线、部分成功、取消、重试、撤销怎样被理解；
- **体验质量视角**：信息层级、反馈、可达性、响应式和平台习惯是否支持这个任务。

工作深度由未知决定：一句流程说明、状态表、线框、交互原型或真实渲染都只是解决不同未知的工具。对材料 UI 改动，应在实现后观察成品，而不是以设计稿完成替代产品完成。

增加按需方法：认知走查、启发式评估、结构化设计 critique、真实数据/极端内容检查和必要的可用性测试。审美偏好不能替代明确的产品目标和设计真相。

### 6.4 `architecture-decisions`：从架构清单走向可证伪的技术选择

保留最小充分架构和语言原生原则，进一步强调设计是对具体驱动的响应。

每个材料决定先回答：

- 哪个现有约束或变化驱动了它；
- 当前仓库约定能否满足；
- 更小、更局部的方案为什么不够；
- 错误、资源、取消、兼容、观测和恢复怎样工作；
- 哪个 spike、测量、合同测试或消融能够推翻选择；
- 什么新事实出现时应该重看决定。

新增重点：

- 对新抽象使用 AHA 和设计消融，避免为想象中的变化轴设计；
- 对输入边界使用 Parse, Don't Validate 和强类型建模；
- 对旧代码删除使用实际调用/消费者证据，而不是只凭“看起来没用”；
- 将跨边界决定与局部编码选择分开，局部选择不要求 ADR；
- 对高风险方案在实施前获得一项能区分备选的证据，而不是反复润色设计文档。

方法参考应拆成普通架构、数据/状态、并发/资源、兼容/迁移、FFI、性能和形式化保证等按需入口，减少当前单 owner 承载过多方法的上下文负担。

### 6.5 `dependency-decisions`：补全引入后的真实成本

现有结构较成熟，重点增加：

- 从能力缺口而不是库名开始；
- 只评估实际会启用的 API、features、平台和传递依赖；
- 说明所有权、升级节奏、故障模式、供应链和退出路径；
- 对旧项目检查与现有依赖/平台能力的重复；
- 对新项目避免因为搭骨架而提前选定大量长期依赖；
- 引入后用真实消费者构建/运行证明集成，而不只证明包管理器成功。

### 6.6 `systematic-debugging`：加强因果纪律和边界追踪

现有 Skill 已经接近目标，主要增强：

- 明确“现象位置”和“最早错误状态”之间的追踪；
- 将代码、配置、数据、工具链、环境和测试 oracle 都视为候选原因；
- 通过单变量实验、最小复现、二分、delta debugging 或故障注入区分假设；
- instrumentation 只为区分当前假设服务，完成后删除无长期价值的临时机制；
- 修复必须恢复被破坏的不变量，不能只让当前样例通过；
- 连续实验没有增加因果信息时，回到模型和复现，不继续叠补丁。

### 6.7 `verification`：从运行测试升级为声明—风险—oracle 设计

这是 RC.7 的另一个重点。它应明确拥有：

- 从用户可观察行为推导黑盒测试；
- 从实际改动的分支、状态、边界、资源和失败路径推导白盒测试；
- 根据输入空间和风险选择 property、model、fuzz、differential、metamorphic、exploratory 或 mutation；
- 证明关键 oracle 对目标缺陷敏感；
- 区分单元、组件、集成、端到端、兼容、非功能和真实环境证据；
- 把每个完成声明限制在真正观察过的 bytes、环境和方向。

对于新增或明显改动，不要求机械拥有所有测试类型，但必须同时完成黑盒产品结果推导和白盒实现风险推导，并解释它们落在哪些单元、组件、集成、端到端或专项测试上。覆盖判断至少审视需求/行为、风险/恢复、结构/状态、输入组合/事件顺序、环境/兼容和 oracle 灵敏度六个维度。

测试深度使用风险预算：核心行为、材料失败/恢复、已改结构和高后果风险默认覆盖；常见组合与受影响平台按风险扩展；低概率低后果且成本很高的极边缘场景默认停止，只有用户明确要求广泛探索时继续。安全、隐私、资金、数据损坏或不可恢复后果即使罕见也不归入可忽略边缘。

覆盖率是缺口探测器而非终点。line/branch/condition、requirements traceability、state/transition、input-space、environment matrix 和 mutation score 各自只回答一部分问题。AI 应在新增测试不再覆盖新的材料义务、暴露新的可信故障或杀死有价值 mutant 时停止，而不是为了数字继续堆用例。

对于项目级工作，应能设计测试层次、运行通道和环境矩阵，而不是只列本次命令。

`verification` 的增强重点是教 AI 怎样实际把覆盖做深：先从用户结果推导黑盒场景，再从最终实现的分支、状态、边界、错误与资源路径补白盒风险；按问题选择单元、组件、集成、合同、端到端和平台层，不用 mock 冒充跨边界证据；用 coverage diff 找空白，用 changed-code mutation 或 seeded fault 检查断言力量，用 property/model/fuzz 扩展输入空间，用 decision/state 与受约束 t-way 扩展规则组合，用 differential/metamorphic/invariant 解决 oracle 困难。

完成前重新看最终 diff 和实际运行环境，补的是材料盲区，不是表格字段。`test-system-engineering` 负责发现测试有没有被 runner 正确发现、选择和隔离，`change-review` 从遗漏和自证角度挑战测试；这些都是实际测试改进，不产生新的流程文档或固定轮次。

输出通常是测试代码、命令结果和诚实限制；只有多环境、高后果或跨版本协调时才需要书面矩阵。

### 6.8 `test-system-engineering`：从排查假绿扩展到建立完整测试体系

RC.6 主要关注 discovery、selection、sensitivity、isolation、interpretation 和 representativeness。RC.7 保留这六项，并增加建设模式：

- 为新项目建立最小测试骨架和首个可失败的真实 oracle；
- 为旧项目盘点现有层次、缺口、重复、慢点和不可信反馈；
- 定义 Focused、PR、Nightly、Release 等反馈通道各自保护什么；
- 设计 fixture、时间、随机性、网络、数据库、设备和进程隔离；
- 建立测试数据与生产数据的安全边界；
- 用风险/行为地图指导覆盖，而不是追求单一覆盖率；
- 维护需求/风险/结构/状态/组合/环境的覆盖视图和已接受缺口，避免只用 line coverage；
- 在组合空间过大时使用带约束的 pairwise/t-wise 或 variable-strength 组合覆盖，高风险因子提高强度，普通因子保持较低强度；
- 将 mutation 限于 changed code、关键逻辑和经过筛选的 operator，避免无价值 mutant 消耗预算；
- 对 AI 生成的测试独立检查需求—测试—实现一致性，使用预修复失败、seeded fault、differential/metamorphic/property oracle 或独立 reviewer 防止自证；
- 检查 runner、分片、重试、缓存和跳过是否掩盖失败；
- 让新增测试体系能被仓库原生命令和 CI 维护；
- 为新项目建立“快速单元/组件反馈 + 一个真实边界黑盒切片 + 项目原生入口 + 最小 CI 通道”的可持续起点；为旧项目优先修复现有层次和通道，不平行建设万能 runner；
- 用实际测试和运行结果说明哪些核心行为/风险已经覆盖、哪些仍受环境限制；不能把 `NOT RUN`、环境替代或绿色 runner 写成已经覆盖。

它仍不负责宣布产品正确。`verification` 决定声明需要什么证据，`test-system-engineering` 证明产生这些证据的系统是否可信。

项目级测试策略应成为 `repository-knowledge` 管理的长期文档 owner：记录测试层次、Focused/PR/Nightly/Release 或项目原生通道、环境与资源、fixture/数据隔离、覆盖目标、边缘场景升级条件和已知缺口。测试系统 Skill 负责内容专业性，知识 Skill 负责可发现性、唯一所有权和持续维护。

### 6.9 `change-review`：增加简化与可维护性审查

在正确性、集成和对抗性审查之外，增加一个“简化”视角：

- 是否存在为未来假设建立的抽象、配置、扩展点或兼容层；
- 是否把一个概念拆散到过多层或文件；
- 是否重复解析、验证或状态转换；
- 是否有更直接、语言原生且符合仓库惯例的表达；
- 测试是否锁定实现细节而不是行为；
- 注释和文档是在保存原因，还是补救难懂代码。

审查不固定轮次。一个具体 finding 被修复后重新检查受影响区域；如果问题根源是需求或架构，返回 owner，而不是继续做第三轮同类审查。

设计消融可以成为这里的实用工具：当某个新机制价值不清时，比较移除后是否损失需求能力、证据或可维护性。它不是审查的核心，也不适用于没有可隔离结构的变化。

### 6.10 `repository-knowledge`：让知识沉淀贯穿但不打断开发

不新增文档或“生命周期知识”Skill；在现有 `repository-knowledge` 的 audit/plan/map/bootstrap/check 基础上增强。主 `dev-flow` Skill 只声明文档接力原则和何时需要本 owner，具体知识拓扑、文件安排、唯一所有者、读者路径、freshness 与检查全部由这里负责。

当前 RC.6 还存在一个比 Skill 内容更靠前的缺陷：**这个 owner 未必会被发现**。源码审计确认，Skill 和插件元数据使显式“审计/建立知识体系”可被识别，但主 Skill 把 knowledge-system maintenance 写成 explicit-only；`route-task` 不接受 `knowledge` 或 `repository-knowledge` need，`--knowledge-impact current-truth` 也只记录处置而不路由；现有 deterministic/semantic eval 没有一个案例要求该 Skill 在隐含知识拓扑问题出现时被调用。因此 RC.7 不能仅增强 Skill 正文，必须同时修复 [professional-Skill discovery audit](rc7-specialist-discovery-audit.md) 记录的发现链。

增强方向：

- 当材料任务需要跨会话/人/独立切片续接，且现有长期 owner 不足以承载当前进度导航时，建立最小 change record 连接需求、UX、技术设计、实施、测试、验收和运行结果，但不复制各长期 owner 的全文；
- 定义环节进入时应读取的前序真相，以及离开时应回写的产品/合同、架构、ADR、测试策略、runbook 或 changelog；
- 普通任务若只是更新一个已有 owner，直接更新，不激活完整知识 Skill；
- 当找不到权威位置、事实重复冲突、跨会话续接需要但找不到现有导航 owner，或需要为新/旧项目建立知识拓扑时才调用本 Skill；
- 新项目在首次产生可持续的非代码知识时建立可发现的项目原生入口；小型库可使用 README，多个长期知识域需要导航时再建立 `docs/`/`docs/index.md` 或等价结构。产品/合同、架构、测试策略、进行中变化和运行知识在第一次产生真实内容时创建，不预建空文件；
- 旧项目先识别现有权威和读者路径，通过链接、合并和触及式修复改善；没有可靠入口时建立 `docs/` 或项目原生等价入口，而不是继续依赖聊天知识；
- 建立阶段交接检查：下一环节能否找到语义、决定、限制和未决问题，长期事实是否已回到唯一 owner，旧结论是否 superseded，文档是否链接真实源码/测试/命令；
- 评估知识是否缩短下一次定位、减少错误假设或保存不可从代码恢复的理由。

发现规则以“是否需要知识拓扑决定”为边界，而不是以“是否改文档”为边界。新项目没有可发现入口、材料任务将依赖聊天交接、长期事实没有唯一 owner、维护文档重复/冲突/失效，或项目级测试策略/架构/runbook 的长期位置未定时，应发现并调用 `repository-knowledge`。已有 owner 清楚且只需触及式更新、机械文档修改或生成资料刷新时，不加载完整 Skill。

发现链需要同时落在主 Skill 的短判断、`repo-context` 的观察式 handoff、`repository-knowledge` 的正负触发描述、agent metadata、capability contract 和行为 eval。公共路由增加 canonical `--need knowledge` 与 Skill-name alias，用于诊断和确定性测试；它不是普通任务的新强制步骤，`--knowledge-impact` 也不因记录 current truth 就自动拉起专业 Skill。真正的正向 oracle 是 Skill 改变了权威 owner/读者路径，并让后继任务找到和使用它；仅在调用记录里出现 Skill 名不算通过。

知识检查只机器验证链接、schema、生成一致性、索引可达性和引用完整性等确定事实，不以文件存在或章节齐全证明知识质量。文档的质量 oracle 是下一环节或种好的后继任务能否据此采取正确行动。

### 6.11 `manage-engineering-profiles`：把个人取向可靠地送入开发

管理 Skill 继续只负责显式 profile 操作，但 RC.7 需要补上“消费侧”设计：

- `repo-context` 发现有效的仓库/组件规则；
- `dev-flow` 使用已解析的有效偏好决定工作方式；
- 专业 Skill 在自己的领域解释偏好，例如抽象、依赖、测试、注释或 Git 粒度；
- `manage-engineering-profiles` 只在用户明确创建、修改、解释、冲突处理、晋升或退休偏好时激活。

个人偏好必须来源于明确表达和确认，不能由历史频率自动推断。偏好也不能削弱项目 `must`、安全边界或真实证据要求。

RC.7 可以优先支持这类可观察偏好：最小充分设计、语言原生、功能切片、测试深度、文档沉淀位置、子代理使用、提交粒度、审查强度和对过度抽象的容忍度。

### 6.12 `delivery-readiness`：把 Git 集成与真实交付说清楚

保持 commit、push、tag、release、deploy、migration 等动作授权分离。增强两个部分：

- **Git 集成质量**：在已获授权时，提交围绕一个可理解、可验证、可回滚的功能变化；避免把多个无关变化混进一个提交，也不强制全局 commit 规范；
- **真实世界闭环**：精确绑定源码、制品、目标、兼容、观察、停止和恢复，执行后验证外部结果。

Skill 只对即将发生的具体动作加载相应细节。普通实现完成不需要提前完成整套发布清单。

### 6.13 `company-data-security`：保持成熟边界，减少与主流程重复

该 Skill 已有清晰的数据分级、最小暴露和产品表面区分。RC.7 主要做整合性调整：

- 在主 Skill 只保留“敏感数据出现时调用 owner”的短提示；
- 避免在其他 Skill 重复数据分级和工具限制；
- 为需求、测试 fixture、日志、外部 connector 和发布证据提供短链接；
- 保持它是跨切面保护，不把每个内部仓库任务都升级为数据治理工作。

### 6.14 `dev-flow-maintainer`：从结构合规转向真实行为改进

保留显式触发和兼容/发布责任，增强 Skill 改造的准入标准：

- 先观察没有该指导时的真实失败；
- 明确准备修正哪个决定或行为；
- 同时设计应触发和不应触发的任务；
- 对比修改前后最终成果、返工、上下文和过程负担；
- 只有稳定的边际价值才进入入口或新增 Skill；
- 一条规则持续增加成本而无结果收益时删除或下沉；
- deterministic eval 保护结构和安全边界，behavior eval 检查真实工作质量，二者不互相冒充。

本地 dogfood 还要求维护者观察长任务是否收口：每个切片必须有一个主要可观察结果和终止条件；结束时明确完成、外部阻塞或因材料新风险而重开。任务长度、文档数量、代理数量和绿色检查数都不能独立证明收口。

## 7. 是否新增“实施与编码质量”Skill

RC.7 初期不新增。先用三层组合覆盖：

1. `dev-flow` 负责完整切片、范围和完成综合；
2. `architecture-decisions` 的工程策略负责抽象、类型、错误、资源、边界和语言原生取向；
3. 宿主语言/框架 Skill、`verification` 和 `change-review` 负责专项实现与反馈。

只有同时满足下面条件，才考虑 `implementation-quality` 之类的新 Skill：

- 至少一组重复真实任务暴露同类实现质量失败；
- 这些失败无法自然归属现有 owner，或放入现有 Skill 会显著稀释其触发边界；
- 新 Skill 有清晰直接请求、独立结果和强负向触发；
- 在代表性正向任务中明显改善代码结果；
- 在机械修改、已知缺陷和专项语言任务中不会误触发或增加明显负担；
- 它提供的不是通用“写好代码”提醒，而是一套独立可执行的工作法。

候选 Skill 不应拥有整个实现阶段，也不能成为所有编码任务的必经入口。

## 8. 方法库与专业 Skill 的重新连接

方法卡按专业问题分发，不把完整清单塞入 Skill：

| 困难 | 首要 owner | 方法示例 |
|---|---|---|
| 语义歧义、规则交互 | `requirements-design` | 具体例子、EARS、决策表、状态模型 |
| 任务流与体验未知 | `product-ux-discovery` | journey、认知走查、启发式评估、原型测试 |
| 架构取舍、复杂度价值不清 | `architecture-decisions` | ADR、spike、ATAM、AHA、设计消融 |
| 因果不清、修复反复失败 | `systematic-debugging` | 最小复现、delta debugging、故障注入 |
| oracle 或覆盖策略不清 | `verification` | property、model、metamorphic、differential、mutation |
| 测试系统可能假绿 | `test-system-engineering` | 负向控制、semantic mutation、fixture isolation |
| 最终变化可能过度设计 | `change-review` | 简化审查、设计消融、独立反例 |
| 交付与恢复不清 | `delivery-readiness` | compatibility、replay/rollback、canary、provenance |

重构方法 owner 时保留稳定 ID 和查询兼容。先改变 reference 导航与实际使用，再决定是否需要 schema 迁移，避免方法治理先于用户价值。

## 9. 新项目与旧项目的差异化行为

### 新项目

主线优先获得一个 walking skeleton：可运行入口、一个真实端到端行为、首个可信测试和最小知识入口。新项目的可持续非代码知识在第一次产生真实内容时进入 README 或其他项目原生入口；多个长期知识域需要导航时再建立 `docs/`/`docs/index.md` 或等价结构，不用空文件预演未来环节。需求与 UX 先聚焦首个用户结果；架构只决定当前骨架必须稳定的边界；依赖尽量延迟到能力需要明确时。

随着真实切片出现，再逐步形成：

- 产品/合同真相；
- 组件和边界导航；
- 测试层次、覆盖义务与反馈通道；
- 材料 ADR；
- 跨会话/多切片变化在确有续接需要时的进行中导航；
- 运行和恢复方式。

目录可以先建立，内容文件按真实环节出现；不预建空模板来表示“流程完整”。

### 旧项目

主线先识别已有权威、调用路径、兼容消费者、测试能力和文档习惯。专业 Skill 优先延续可用约定，并在当前变化触及的地方修正漂移。

旧项目尤其需要：

- characterization 和消费者证据；
- 行为变化与结构重构分离；
- 对已有抽象先理解原因再删除；
- 兼容与迁移方向清楚；
- 让新增测试进入现有 runner/CI，而不是平行建设新体系；
- 通过索引和链接改善知识发现，而不是整体搬家。

## 10. 项目与主 Skill 同名的处置

当前仓库、产品/插件 ID 和主 Skill canonical name 都使用 `dev-flow`。它会让“Dev Flow”在讨论中同时指套件和入口 Skill，也让安装身份看起来重复；但本次任务回看没有发现由同名直接造成的误路由、安装失败或错误行为。

RC.7 因此不改项目名，也不立即改 canonical Skill 名：

- 产品和插件继续叫 **Dev Flow**；
- 人类可读界面把主 Skill 称为 **Dev Flow · Repository Engineering**；
- 设计和维护文档用“Dev Flow 套件”指产品，用“repository-engineering kernel（canonical `dev-flow`）”指主 Skill；
- Skill 描述改成动作和边界导向，避免用产品名自我解释；
- 行为 eval 观察真实任务是否仍因命名产生误激活、错误预期或审计归因困难。

本次不选择另外三种方案：项目改名会影响仓库、插件、文档、安装和发布身份，却没有解决开发行为的证据；新增别名 Skill 会扩大激活面和上下文；静默改 canonical name 会破坏显式调用、CLI 路径和已发布资料。若 RC.7 仍观察到实际命名故障，再把 canonical Skill 改名作为下一次有迁移说明和兼容期的独立决策，而不是夹带在内容重写中。

## 11. 实施顺序

RC.7 的实施主线仍然是：先改造主 `dev-flow` Skill，再系统增强现有专业 Skill，最后收敛路由、方法、评估和产品状态。历史任务回看只用于确定薄弱点、优先级、负向案例和验收样本，不按历史任务原型重组产品架构或实施路线。

### 第一组：主 `dev-flow` Skill 与静态上下文

- 将主入口收敛为开发主线、专业 owner 导航、文档接力原则、完成综合和少数硬边界；
- 把详细路由、方法、模型、workstream 和专业程序下沉到按需 reference/owner；
- 将 ordinary static path 从当前 `14082` 字节降到现有 `13500` 预警线以下，目标争取不高于 `12500`，同时保持普通缺陷、材料新增和安全负向案例不回归；
- 当前构成为主 `SKILL.md` `8998`、`repo-context` `2591`、`verification` `2493` 字节；若后两者保持约 `5100`，主入口应压到约 `7400` 以内。新增文档与测试细节进入按需 reference，不能挤回普通静态路径；
- 同时保护始终可见的 Skill description 预算：当前总量 `1979` 字符，`1995` 为预警线，`2128` 为硬上限。发现改善必须同时证明 catalog 实际可见、held-out owner recall 提高且邻近负例不过路由，不能用加长 metadata 替代效果；
- 同步调整主 Skill 的 `agents/openai.yaml` 和插件提示，不让旧入口继续传播 RC.6 的重流程行为。
- 将仓库根 `AGENTS.md` 纳入同一迁移组：删除“独立 reviewer 需另行授权”的现行矛盾，改为有独立价值、可拆分即可派发，同时保留所有真实动作和范围边界；用回归检查防止旧授权文案残留在任一入口。
- 第一组只建立全部专业 owner 共用的 discovery contract/matrix 基础设施和主 Skill 的短发现/重绑定脊柱：可观察正向信号、邻近负向信号、首次识别点、中途重新绑定点、确定性表达和结果 oracle；[专业 Skill 发现审计](rc7-specialist-discovery-audit.md) 是基线，不只修复 `repository-knowledge`。
- 每个 owner 的 `Use when...` 意图/症状、邻近排除条件、Skill 正文、metadata、contract、route fixture 和正负测试在它所属的第二至第六组原子更新，不在第一组提前改完触发面却留下旧程序。额外案例和仓库信号进入 contract/eval，不靠加长主入口或非标准 metadata。当前 15 个内置 Skill 不引入向量检索；只有观测到 catalog 截断/遗漏或 held-out recall 随规模下降时，才单独评估 body-aware retrieve-and-rerank。
- 更新多代理 reference、capability contract、`route-agent`/`route-task` 输出和行为测试：普通与嵌套派发不需要用户授权，独立审查缺省可直接派发；已纳入的 owner 只能在用户已经授予且所有祖先 envelope 仍保留的边界内分配工作，Skill 激活、owner 身份或子代理请求都不能新增仓库/路径/依赖/语义/外部/破坏性权限。只有宿主能力不足、资源冲突或拆分无净收益才不派发。模型/effort 仍由 P0-P6 自动选择，嵌套负向测试必须证明 owner 不能扩权。

### 第二组：需求、UX 与文档知识链

- 深化 `repo-context`、`requirements-design` 和 `product-ux-discovery` 的第一动作、反例、状态和停止条件；
- 在现有 `repository-knowledge` 基础上增加环节文档接力、长期 owner 回写、有续接需要时的最小进度导航、新旧项目原生文档入口策略和后继任务可用性检查；
- 主 Skill 只保留短原则和激活条件，不复制知识拓扑与文件矩阵；
- 验证材料新增能把需求、UX 和未决问题交给技术设计，而机械任务不会生成空文档。

### 第三组：技术设计、依赖、调试与编码质量

- 深化 `architecture-decisions`、`dependency-decisions` 和 `systematic-debugging`；
- 将抽象、类型、错误、资源、并发、兼容和因果停止条件落实为实际指导；
- 加入设计消融、AHA、边界解析和可证伪方案，但不把任一方法提升为编码核心；
- 用实际代码结果验证现有组合是否足够，再决定是否需要新的 implementation owner。

### 第四组：测试、验证与验收

- 深化 `verification`、`test-system-engineering` 和 `change-review`；
- 建立需求/风险/结构/状态/组合/环境/oracle 的覆盖模型，以及核心、扩展、极边缘三层预算；
- 加入 changed-code mutation、约束 pairwise/t-wise、property/model/fuzz、独立 oracle 和 AI 生成测试审计；
- 强化单元、黑盒、白盒、项目级反馈通道和真实环境证据，同时在低价值边缘空间达到饱和后停止。
- 把上述覆盖方法写进 `verification`/`test-system-engineering` 的实际指导和例子：怎样从黑盒/白盒找用例、怎样选测试层、怎样用 coverage/mutation/property/model/fuzz/t-way/differential/metamorphic 扩大覆盖，以及怎样识别 runner 假绿；新项目和旧项目分别验证可持续骨架与原生体系加固。

### 第五组：偏好、安全、交付与运行回流

- 打通 `manage-engineering-profiles` 的确认值消费；
- 收敛 `company-data-security` 的跨 Skill 重复；
- 深化 `delivery-readiness` 的功能点式 Git 集成、身份、授权、观察和回滚；
- 让运行故障、用户反馈和验收缺口回流到产品、设计、测试和长期知识 owner。

### 第六组：路由、方法、评估与兼容收敛

- 深化 `dev-flow-maintainer` 的候选提升决策、dogfood 切片收口和证据限定；正负测试必须证明 schema/结构/覆盖绿色不能冒充行为或生产率改善，而真实行为回归/修复会被送回受影响 owner 并有界收口；
- 逐项同步 capability contracts、Skill 描述、路由 fixture、方法导航和兼容测试；这些表面随对应 Skill 组一起更新，不能留到最后才修，但最终在本组做全局收敛；
- 对全部专业 Skill 运行 discovery matrix：每个 owner 至少一组确定性正向/邻近负向案例；需要隐式发现的 owner 还要有自然语言/仓库证据 semantic case，显式 owner 要有 ordinary-work quiet case；
- 修复方法效果 fixture 的悬空引用、方法/oracle 不一致和 `route-agent --risk` 帮助问题；
- 用历史 dogfood 提炼的代表性案例检查改进，不让它们反过来主导实施结构；
- 保持 `dev-flow.product-state.v1` 的整体形状，先将 validator 的 source/workspace workstream 最小要求改为 `implementation.md` + `progress.md` 与可选维护性引用，并删除无条件的 RC.6 `HC7` 进度投影或把它限定在真正拥有该表的 legacy RC.6 合同；验证 source/workspace 均只有两份文件的 RC.7 source-candidate 通过、两份任一缺失必须失败、RC.6 五文件加历史投影超集仍通过。现有 marker 驱动的 `check-workstream` 保留给 legacy/显式 opt-in v1 workstream，RC.7 不创建空 requirements/design/decisions，也不伪造 marker。然后以一个原子 candidate-transition bundle 同步 `.codex-plugin/plugin.json`、`governance/product-state.json`、`README.md`、`docs/releasing.md`、`CHANGELOG.md` 和 RC.7 `progress.md`：RC.7 delivery 重置为 incomplete/not-observed，latest published 仍为 RC.6，rollback 仍指向真实最新已发布标签。负向测试拒绝继承 RC.6 交付证据、manifest/version 漂移、rollback 漂移和投影陈旧，然后再对精确真实树验证。完成 integrated candidate 验证后，另行授权的 live-model 比较仍只决定相应效果声明，未运行时保持 `NOT RUN`。

各组都必须同时更新其主动发现表面、合同和受影响测试，使中间结果可验证，但这只是避免半成品的工程纪律，不是另一条“按任务原型垂直切片”的总路线。精确改动和当前进度由 [RC.7 implementation](./workstreams/dev-flow-2.0-rc.7/implementation.md) 维护；[代表性行为评估参考](./workstreams/dev-flow-2.0-rc.7/acceptance.md) 用于挑战受影响的行为声明，不是实施编排器或发布门禁。

## 12. 文件级改造地图

这张表用于约束 RC.7 实施范围，避免“重写 Skill”最后演变成再次增加一套平行体系。

| 现有表面 | RC.7 处理方向 |
|---|---|
| `AGENTS.md` | 将独立审查派发从额外授权中移除；保留动作/范围授权、用户修改保护和证据边界 |
| `skills/dev-flow/SKILL.md` | 重写为薄主干；移出 visible 分类、强制 route、完整风险/模型/方法细节 |
| `.codex-plugin/plugin.json` | 与主入口同时更新人类可读描述和默认 prompt，不保留 RC.6 工作流暗示 |
| `skills/dev-flow/references/core-lifecycle.md` | 改写为自然循环、连续性选择、重看信号和完成综合，不保留阶段式生命周期 |
| `skills/dev-flow/references/quality-calibration.md` | 拆减为“何时加深、何时回看”的判断；能力失败、模型路由、方法、独立审查分别指向专门 reference；删除 unauthorized delegation 作为派发降级理由 |
| `skills/dev-flow/references/methodology-system.md` | 从选择程序说明转为问题触发的工具导航；保留兼容 CLI 说明但不主导普通工作 |
| `skills/dev-flow/references/orchestration.md` 与 `multi-agent-v2-orchestration.md` | 保留运行时细节；按独立价值、闭合度、后果和 oracle 重新解释路由；删除 reviewer 授权 gate 和“已纳入 owner 可扩大祖先 envelope”漏洞 |
| `skills/dev-flow/scripts/dev_flow.py`、`route_incremental.py` 与 supported wrapper | 更新 `route-task`/`route-agent` 的输出、帮助、兼容输入和嵌套权限语义；`--independent-review-authorized` 短期可解析，但不得进入 review basis、改变 dispatch/`route-agent` 或产生授权降级 |
| Dev Flow agent profiles 与 `skills/dev-flow/agents/openai.yaml` | 与主入口同步派发条件、模型/effort 路由和非扩权返回边界 |
| 各专业 `SKILL.md` | 补强第一动作、质量挑战、有效结果、停止/回退；入口仍保持短小 |
| 各专业 `references/` | 按真实工作模式拆分深层指导和例子，不复制方法百科 |
| `skills/repository-knowledge/` | 在现有 topology/audit/plan/map/bootstrap/check 上增加阶段文档接力、长期 owner 回写、按真实续接需要建立的最小 change record、新旧项目入口与可用性检查；不新增平行文档 Skill |
| `skills/verification/` 与 `skills/test-system-engineering/` | 增加六维覆盖模型、三级测试预算、changed-code mutation、约束组合覆盖、AI 测试 oracle 审计和边缘场景停止条件 |
| `governance/capability-contracts.json` | 更新 owner、handoff 和负向触发；不新增生命周期状态 |
| `governance/methodology-pool.json` | 初期保持 117 个 ID 兼容；在行为验证后再校正 owner、卡片和候选方法 |
| `evals/skill-routing-cases.json` | 从固定 Skill 集合预期，逐步转向“必要 owner 出现、无关 owner 不出现、任务仍完成”的行为边界 |
| dispatch/activation fixtures 与 tests | 同步 `evals/agent-dispatch-routing-cases.json`、flow-activation cases、`test_agent_dispatch.py`、`test_flow_activation.py` 和受影响的 `test_dev_flow_v2.py`；证明无授权 gate、嵌套不扩权和 quiet 路径 |
| semantic/behavior evals | 增加需求澄清、过度设计、测试敏感度、知识价值和简单任务静默案例 |
| `evals/method-marginal-utility-cases.json` 及其 fixture | 修复悬空引用和方法/oracle 对应关系；在可执行成对 runner 中区分 gain、no-gain、regression 与 inconclusive |
| 现有 deterministic/behavior eval catalogs 与 runners | 把各组受影响的代表性 case、负向控制、精确环境和声明边界分配给现有 owner；不新建通用 RC.7 验收 runner 或发布门禁 |
| `governance/product-state.json` 与 validator | 保持 `dev-flow.product-state.v1`；先让 source/workspace workstream 最少只需 `implementation.md` 和 `progress.md`，其他维护性引用可选，将无条件 `HC7` 投影限定到 legacy RC.6，且 RC.6 五文件作为超集继续有效；旧 marker 驱动的 `check-workstream` 只约束 legacy/显式 opt-in v1 workstream，RC.7 保持未标记。正负/兼容测试通过后，以 manifest、product-state、README、releasing、CHANGELOG、progress 同步的 source-candidate bundle 切换指针 |
| `skills/dev-flow-maintainer/` | 深化 promotion、dogfood 切片收口和证据限定；结构/schema/覆盖证据不得冒充行为改善 |
| README、`docs/releasing.md`、`CHANGELOG.md` | 同步公共授权语义和 candidate 投影，不让 RC.6 reviewer waiver 或交付证据变成 RC.7 现行规则 |
| context budget tests | ordinary static path 必须先降到 `13500` 以下，并以不高于 `12500` 为优化目标；Skill descriptions 当前 `1979`，优先低于 `1995` 预警并严格不超 `2128`；只有核心行为、owner recall/邻近负例和安全案例不回归时才接受降载 |
| 1.x packet 模板与残余 CLI | 继续保持不被 2.0/RC.7 正常路径激活；是否物理删除另行做兼容决策 |

实施时优先修改已有 owner，不创建 `rc7/` 运行时目录、第二套路由器、Skill handoff schema、方法执行记录或新的阶段文档模板。

## 13. 兼容与迁移策略

RC.7 可以改变指导语义，但不应无意中破坏已公开的安装和命令表面：

- 15 个现有 Skill 名称先保持稳定；
- 主 Skill 的人类可读标签改为“Dev Flow · Repository Engineering”，canonical `dev-flow` 在 RC.7 保持稳定；
- `dev-flow.py` 继续是受支持 CLI 入口；
- `route-task`、U 分类、method ID 和现有 JSON 字段先兼容保留，但不再要求普通任务依赖它们；
- 先通过文案、reference 和行为路由完成软迁移，再根据真实调用与测试决定弃用；
- `agents/openai.yaml` 描述变化需要同时验证正向和负向自动激活；
- `.codex-plugin/plugin.json` 的描述和默认 prompt 与主 Skill 行为在同一集成修改组更新；
- 当前 product-state validator 固定要求五份 workstream 文档；RC.7 保持 v1 schema，先迁移为最小 `implementation.md`/`progress.md` 加可选维护性引用的合同并更新正负/旧版兼容测试，不能用空文件满足校验；旧 marker/check-workstream 行为保留给 legacy 或显式 opt-in 工作流，然后才切换 RC.7 产品指针；
- 删除或重命名公共字段、命令、Skill 前单独做兼容决策和发布说明；
- RC.7 草案文档不自动成为生效策略，只有 Skill、路由、测试和产品状态一起更新后才可以声称落地。

## 14. 怎样验证优化确实有效

### 14.1 结果质量

比较 RC.6 与候选版是否：

- 更准确理解用户真正要的行为；
- 更早发现会改变方案的未知；
- 更少引入无价值抽象、层、依赖和文档；
- 更容易形成完整端到端切片；
- 测试更可能在实现错误时失败；
- 最终结论更准确区分环境和未运行项；
- 下一次任务能从沉淀知识中更快找到真相。
- 每个实际发生的材料环节都有可发现的结果，下一环节能从仓库文档而非聊天记忆继续工作。
- 测试覆盖能说明材料需求、风险、结构、状态/组合、环境和 oracle 缺口，而不是只报告一个百分比。

### 14.2 激活质量

验证：

- 当前宿主确实暴露了 Skill，且 catalog 截断、遗漏和同名碰撞可观察；
- 正确 owner 能从显式请求、隐含/长文本信号和中途新证据进入有界 candidate set；
- candidate 只有在正向问题存在、邻近负向边界不存在且能产生边际价值时才被加载；
- owner 在第一次材料决定前及时出现，普通续接保持稳定，材料新证据才触发 rebind；
- 被加载的 Skill 实际改变决定、产物、oracle、下一动作或声明边界，不能用 Skill 名出现代替效果；
- 机械任务不会加载一串专业 Skill；
- 需求、UX、架构、测试系统和交付边界不会彼此越权；
- 专业 Skill 完成局部工作后能自然返回主任务；
- 没有 `route-task` 时普通行为仍然稳定；
- 同一语义目标不会因普通续接、上下文压缩或非材料细化重复路由；
- 不可信、未暴露或碰撞 metadata 不能借发现过程获得权限或替换 canonical owner。

### 14.3 过程成本

关注总交互、上下文、停顿次数、生成文档、返工、模型/代理使用和完成时间。成本不是越低越好，但每一项新增成本都应对应可观察的质量收益。

长任务还要观察切片是否以可证明结果收口、文档是否改变下一动作、子代理发现是否真正进入最终决定，以及审查是否能在只剩非后果性意见时停止。

上下文成本单独设门：ordinary static path 从当前 `14082` 降至 `13500` 以下才解除预警，目标不高于 `12500`；始终可见的 Skill descriptions 从当前 `1979` 字符出发，优先低于 `1995` 预警并严格不超 `2128`。任何字节或字符调整都必须同时通过普通缺陷、材料新增、文档接力、测试覆盖、owner recall/邻近负例和安全案例，不能用删除关键指导或加长 metadata 换取单一数字。

### 14.4 负向案例

至少包含：

- 拼写和确定性机械修改；
- 有清楚 oracle 的局部 bug；
- 只读 Git/文件事实查询；
- 项目已有明确产品和设计真相的实现；
- 只需更新现有文档的一处行为变化；
- 用户未授权 commit 或外部动作、但存在有净收益子代理工作的任务；应直接委派，同时仍拒绝未授权动作。

这些案例用于证明 RC.7 没有重新制造流程负担或权限扩张。

### 14.5 评价边界

- deterministic tests 验证 schema、链接、命令、兼容和安全硬边界；
- behavior eval 验证真实成果，不奖励固定标题、方法名或过程措辞；
- discovery eval 分别报告 availability、candidate recall、admission、timing/rebind、application effect、cost/restraint 与 trust，不合并成掩盖 owner 差异的总分；
- 每个隐式 owner 覆盖显式正向、隐含/嵌入式正向、邻近负向和中途出现四类案例；显式 owner 覆盖显式正向、普通工作 quiet 和对抗式隐含负向；
- 描述调优与 held-out 代表性行为示例使用分离样本；确定性案例随受影响改动运行，另行授权的 live semantic observation 保存选定声明的第一次尝试，重复试验留给 Bench；
- paired comparison 在相同任务、模型和资源条件下比较边际价值；
- 模型试验需要单独预算和授权；本设计本身不声称已经得到模型效果证明。
- 对受影响的代表性行为示例，绑定 candidate bytes、精确 fixture、黑盒/白盒 oracle、目标故障、负向控制、环境和 claim limit；需要比较时再绑定 baseline。不以激活、固定措辞或 aggregate score 替代效果。
- 边缘场景扩张需要用户明确要求或高后果风险依据；低概率低后果空间达到预算后应停止并记录重开触发。

## 15. RC.7 完成后的理想体验

对一个小缺陷，AI 读相关代码和测试，复现、修复、验证、检查 diff，然后结束；用户几乎感觉不到流程存在。

对一个模糊新增，AI 先用仓库事实、例子和反例把产品结果说清，在真正材料的选择上请求确认；随后比较最小技术方案，做端到端切片，从黑盒和白盒两面建立证据，并只留下未来还会使用的知识。

对一个高后果跨边界变化，AI 会自然增加状态/兼容模型、专业方法、恢复设计、测试系统检查、独立视角和目标环境证据，但这些工作都能说明自己正在减少哪个未知或风险。

这就是 RC.7 的判断标准：**流程始终存在于开发质量中，而不是存在于流程产物中。**
