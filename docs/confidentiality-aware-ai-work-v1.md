# AI 机密数据安全工作机制：差异化能力矩阵与轻量 V1

> 状态：仓库 V1 已实现并通过隔离红蓝与完整回归验收；现场安装、Hook 信任和 ChatGPT 账号配置需分别验收
> 适用产品：Codex、ChatGPT Work、普通 Chat
> 产品能力核对日期：2026-08-14
> 目标：在不显著破坏工作效率的前提下，利用当前可用的指令、Skills、Hooks、权限、插件和本地处理能力，降低机密数据被不必要读取、上传、传播或写入外部系统的概率与范围。

仓库中的对应实现为：

- 跨表面 Skill：`skills/company-data-security/`
- Codex 本地 Hook：`hooks/data_security_hook.py` 与 `hooks/hooks.json`
- 本地检测/脱敏：`skills/company-data-security/scripts/data_security.py`
- 防漂移 doctor：`skills/company-data-security/scripts/doctor.py`
- Codex、Work、普通 Chat 指令模板：`skills/company-data-security/assets/`
- 合成红蓝测试：`evals/test_data_security.py`

这里的“已实现”只指当前仓库字节和隔离测试。插件安装、变更后的 Hook 信任、新任务加载，以及 Work/普通 Chat 的个人或项目指令对齐，都不是仓库测试能够代替的现场证据。

## 1. 定位

这不是“百分之百不可绕过”的传统企业 DLP，也不承诺覆盖终端上的全部进程、网络出口或人为规避。它是一套 **Confidentiality-Aware AI Work（机密数据感知型 AI 工作机制）**：

1. 用户继续用自然语言正常工作，不要求掌握 Tokenization、DLP CLI 或复杂安全配置。
2. AI 优先避免读取真实值；确有需要时，依次考虑引用、本地计算、假名化和脱敏。
3. 能静默纠正的场景不打断用户；只有极高置信度的凭据泄漏或高影响外部动作才阻断或确认。
4. 不同产品表面使用不同控制手段，不把 Codex 的 Hook 能力虚构成 ChatGPT Work 或普通 Chat 的通用能力。
5. 对 ChatGPT Pro 的人工部署现实保持诚实：可以标准化、检查和纠偏，但不能宣称企业级不可绕过。

统一的处置优先级是：

```text
不读取
  → Reference（变量、路径、对象引用）
  → Local Compute（本地筛选、聚合、提取）
  → Pseudonymize（保持关联的假名化）
  → Redact / Minimize（删除或最小化）
  → Warn / Confirm（必要时提醒或确认）
  → Block（仅最后手段）
```

## 2. 产品表面定义

| 主场景 | 本文中的运行形态 | 主要用途 | V1 判断依据 |
|---|---|---|---|
| Codex | 本地 Codex；Codex 云任务 | 代码、仓库、Shell、文件、MCP、技术任务，也可承担非编程工作 | 本地形态拥有最完整的 AGENTS、Hooks、本地脚本和权限控制；云任务不得假设本机 Hook 或辅助进程存在 |
| ChatGPT Work | Work locally；Work cloud | 文档、表格、报告、演示文稿、调研、跨插件工作流和长任务 | 本地形态可使用本地文件、应用和浏览器；云端形态适合持续任务，但不得依赖本机脚本或 Hook |
| 普通 Chat | 网页、桌面和移动端 Chat | 问答、讨论、搜索、头脑风暴、短文稿、文件总结 | 主要依赖个人/项目指令、Skills/Plugins、最小输入和用户/AI 行为；V1 不假设存在确定性的发送前 Hook |

OpenAI 当前将 Chat、Work、Codex 分别定位为对话式工作、产出可审阅成果和开发者工具场景；Work 可使用文件、插件和获批工具，并区分本地和云端工作。参考 [Use ChatGPT](https://learn.chatgpt.com/docs/use-chatgpt) 与 [Get started with ChatGPT Work](https://learn.chatgpt.com/docs/get-started-with-work)。

## 3. 数据分类

分类表达默认处置强度，不替代公司法务、隐私或行业合规分类。发生冲突时，以公司正式制度中更严格的分类为准。

| 级别 | 名称 | 代表性数据 | 默认原则 |
|---|---|---|---|
| C0 | Public | 已公开官网内容、公开仓库、公开产品资料 | 可正常使用，仍避免无关批量采集 |
| C1 | Internal | 一般内部流程、普通会议结论、非敏感内部文档 | 可以使用，但只提供完成任务所需范围 |
| C2 | Confidential | 未公开代码、设计、路线图、合同内容、经营分析、内部域名 | 优先最小化、引用和选定片段；避免整库、整盘或整文件夹上传 |
| C3 | Restricted | 客户数据、生产数据、个人信息、HR/财务敏感数据、受限商业材料 | 优先本地处理和假名化；云端只接收完成任务所必需的脱敏语义 |
| C4 | Secret | 密码、API Key、Access/Refresh Token、Cookie、私钥、带凭据 DSN、恢复码 | 模型不需要知道真实值；使用引用或本地执行。高置信原值进入待发送内容时才考虑阻断 |

同一材料包含多个级别时按最高级别处理，但允许先在本地拆分出低敏、任务相关的派生结果。

## 4. 控制手段图例

| 标记 | 含义 |
|---|---|
| `V1` | 当前产品表面可用，纳入轻量 V1 |
| `条件` | 取决于本地/云端、安装状态、工具能力或用户授权；V1 只能在条件成立时使用 |
| `指导` | 能降低风险，但不构成确定性强制边界 |
| `不依赖` | V1 不以该能力作为这个产品表面的安全前提 |

控制强度分为四类：

- **指导（G）**：指令、Skill、模板和培训，让 AI 更可能选择安全路径。
- **辅助（A）**：本地筛选、假名化、脱敏、引用和安全执行，自动降低暴露量。
- **检查（C）**：Hook、权限提示、连接器动作确认等确定性或半确定性检查。
- **证明（V）**：doctor、自测、版本清单和合成样例，证明人工配置是否对齐。

## 5. 产品表面 × 可用控制手段矩阵

| 控制手段 | Codex | ChatGPT Work | 普通 Chat |
|---|---|---|---|
| 全局持久原则 | `V1/G`：`~/.codex/AGENTS.md`；仓库可叠加项目级规则 | `V1/G`：ChatGPT 个人指令、项目说明；不假设读取仓库 AGENTS | `V1/G`：ChatGPT 个人指令、项目说明 |
| 跨产品安全 Skill | `V1/G`：插件 Skill 可隐式或显式触发 | `V1/G`：插件 Skill 可在 Work 中使用 | `V1/G`：插件 Skill 可在 Chat 中使用 |
| Skill 自动触发可靠性 | `条件/G`：依赖 description 匹配和渐进加载 | `条件/G`：同样依赖匹配，不视为硬门 | `条件/G`：同样依赖匹配，不视为硬门 |
| 用户提示词发送前检查 | `V1/C`：本地 `UserPromptSubmit` 仅拦截高置信 C4 | `不依赖`：当前 V1 不假设 Work 有等价 Hook | `不依赖`：当前 V1 不假设 Chat 有等价 Hook |
| 工具输入检查/改写 | `V1/C`：本地 `PreToolUse`；优先改为引用或安全助手，必要时才拒绝 | `条件`：依赖具体工具、插件和权限提示，不假设 Codex Hook 覆盖 | `条件`：依赖具体插件/工具权限，不假设 Codex Hook 覆盖 |
| 工具输出脱敏 | `V1/A+C`：本地 `PostToolUse` 可兜底扫描模型可见结果 | `条件/A`：由 Skill、插件或本地工作流处理，不承诺统一拦截 | `指导/A`：由 Skill 指导最小化或脱敏，不承诺统一拦截 |
| 本地脚本/辅助程序 | `V1/A`：本地 Codex 可自动调用；云 Codex 不依赖 | `条件/A`：仅 Work locally 且工具可用时使用；Work cloud 不依赖 | `不依赖`：普通 Chat V1 不要求本机辅助程序参与 |
| 文件系统最小权限 | `V1/C`：本地 permission profile/sandbox；云端按云环境能力 | `条件/C`：Work locally 使用桌面权限边界；Work cloud 不使用本机文件边界 | `条件/C`：仅桌面本地工具动作；网页/移动 Chat 不依赖 |
| 网络目的地约束 | `条件/C`：本地权限 profile 或云任务网络设置；V1 不宣称终端全出口 DLP | `条件/C`：依赖运行形态、浏览器/插件权限；无统一 Hook | `条件/C`：依赖 web、插件和浏览器自身权限；无统一 Hook |
| MCP/插件/连接器最小权限 | `V1/C`：MCP 清单、权限和外部动作确认 | `V1/C`：插件/连接器按需安装，读取范围最小，写动作确认 | `V1/C`：插件/连接器按需安装，读取范围最小，写动作确认 |
| 外部写入前确认 | `V1/C`：沿用权限和外部动作审批 | `V1/C`：草稿优先，发送/发布/删除前确认 | `V1/C`：草稿优先，发送/发布/删除前确认 |
| 自动配置验收 | `V1/V`：本地 doctor 可检查文件、Hook、权限和版本 | `条件/V`：本地项可检查；账号/云端项采用引导式自测和人工证明 | `指导/V`：Skill 存在性、自测题和人工清单；不伪造自动合规证明 |

`AGENTS.md` 是 Codex 在工作前读取并按全局到项目层级组合的指令机制；不是普通 Chat 的通用配置文件。参考 [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md)。插件化 Skills 可覆盖 Chat、Work 和 Codex，但采用渐进加载，因此 V1 把它作为跨表面行为层而非强制边界。参考 [Build skills](https://learn.chatgpt.com/docs/build-skills)。

ChatGPT 的全局 Custom Instructions 可覆盖网页、桌面、iOS 和 Android，项目指令则仅作用于对应项目并覆盖全局指令，因此普通 Chat 与 Work 的持久原则需要同时准备全局短版和项目级适配版。参考 [ChatGPT Custom Instructions](https://help.openai.com/en/articles/8096356-chatgpt-custom-instructions) 与 [Projects in ChatGPT](https://help.openai.com/en/articles/10169521-using-projects-in-chatgpt)。

Codex Hooks 可以在 `UserPromptSubmit`、`PreToolUse`、`PostToolUse` 等生命周期点运行确定性脚本，但 hosted tools（例如 WebSearch）不走本地 function-tool Hook，部分特殊工具路径也可能退出默认 Hook 路径，因此 Hook 只作为安全网。参考 [Hooks](https://learn.chatgpt.com/docs/hooks)。

ChatGPT Apps 的动作能力和确认行为取决于具体 App、账号与权限配置；V1 的 draft-first 和写入前确认是组织基线，不等于所有账号都天然处于相同权限模式。参考 [Apps in ChatGPT](https://help.openai.com/en/articles/11487775-connectors-in)。

## 6. 数据类型 × 产品场景处置矩阵

| 数据级别 | Codex | ChatGPT Work | 普通 Chat |
|---|---|---|---|
| C0 Public | 正常使用；仓库/网页来源仍按任务范围读取 | 正常用于文档、表格、演示和调研 | 正常问答、搜索、总结和起草 |
| C1 Internal | 可进入上下文；优先只读相关文件、符号和日志片段 | 使用少量明确来源；避免为了“方便”连接整个文件夹或全部消息 | 可以使用必要文字或文件；不粘贴与问题无关的内部上下文 |
| C2 Confidential | 优先路径/变量/符号引用；局部读取；日志先筛选；外部写入确认 | Work locally 优先处理本地材料；Work cloud 仅选定材料；生成物默认先审阅 | 只提供完成问题所需片段；长材料先分段、摘要或去除身份信息 |
| C3 Restricted | 本地聚合、筛选和假名化后再推理；保持业务状态、错误码和实体关系 | 优先 Work locally；云任务只接收脱敏或聚合结果；连接器限制到指定对象 | 原始数据不是默认输入；先使用脱敏副本、区间、统计量或合成样例 |
| C4 Secret | 不读取真实值；使用 env/path/secret ref；本地执行；高置信误粘贴可由 Hook 阻断 | 不上传、不回显；只描述凭据类型、来源和所需操作；没有 Hook 时依靠 Skill/指令纠正 | 不粘贴原值；只讨论配置方法、变量名、错误现象和轮换步骤；V1 不声称可自动阻断 |

## 7. 普通工作场景差异化矩阵

| 工作场景 | 首选产品表面 | 默认安全路径 | 允许打断用户的条件 |
|---|---|---|---|
| 代码、配置、构建和仓库分析 | Codex | AGENTS → Skill → 相关文件/符号最小读取 → Hook 兜底 → 本地验证 | 高置信 C4、读取明确受限凭据文件、未批准外部写入 |
| 生产日志和故障数据 | Codex 或 Work locally | 本地 grep/解析/聚合 → 保留错误码、时间分布和状态 → 删除身份与凭据 | 无法避免 C4 进入模型，或需要真实生产写操作 |
| 合同、制度、会议纪要和报告 | Work | 选定文档 → 去除签名、账号、联系人 → 保留条款与结论 → 先出草稿 | 需要把 C3 原文发送到新外部主体，或直接发布最终材料 |
| 表格、经营和财务分析 | Work locally 优先 | 本地筛选列、聚合和区间化 → 仅上传所需派生表 → 生成可审阅结果 | 原始受限明细无法最小化且任务又要求云端处理 |
| 客户、HR 和个人信息分析 | Work locally 或 Codex 本地 | 稳定假名化实体 → 保留关联和业务状态 → 删除直接标识符 | 高风险直接标识符无法自动处理，或要执行外部写入/发送 |
| 邮件、日历、IM、云盘和知识库 | Work 或 Chat + 插件 | 限定账号、文件夹、线程和时间窗；只读优先；草稿优先 | 发送、发布、删除、共享范围扩大或新增收件人 |
| 网页搜索和研究 | Chat 或 Work | 搜索公开问题；不把 C2-C4 内容拼进查询；内部事实用抽象描述 | 查询必须包含受限原文或要向第三方网站提交内部文件 |
| 快速问答、写作和头脑风暴 | Chat | 使用抽象背景、占位符和最小片段；必要时显式调用安全 Skill | 用户直接粘贴明显 C4 时提示停止并轮换；V1 不保证技术阻断 |

## 8. 轻量 V1

### 8.1 共享核心：一套规则，不同执行器

V1 只定义一套数据分类和决策树，但生成三种表面适配：

1. **Codex baseline**：10～20 行全局 AGENTS 规则，声明 Reference → Local Compute → Pseudonymize → Redact → Block 的顺序。
2. **ChatGPT baseline**：等价但更短的个人/项目指令，适用于普通 Chat 和 Work，不提不存在的 Hook 或 Shell 能力。
3. **`company-data-security` Plugin Skill**：跨 Chat、Work、Codex 分发，description 明确覆盖 credentials、personal data、customer data、production data、contracts、finance、HR、files、connectors 和 external actions。

Skill 的职责是让 AI 自动判断和处理，不把脱敏步骤转嫁给用户。它必须包含：

- 数据分类和处置优先级；
- 文件、表格、日志、连接器、浏览器和外部动作的差异化方法；
- 语义保留规则：保留业务状态、错误码、关系和统计意义，减少原始身份值；
- 在能力缺失时的降级方式；
- “Ask User 是最后路径”的交互原则；
- 不得把自身描述成强制 DLP 的限制声明。

### 8.2 Codex V1：薄 Hook + 本地辅助

Codex 本地形态增加确定性安全网：

- `UserPromptSubmit`：只对高置信 C4（私钥、明确 Token/Key 格式等）阻断；C1-C3 默认不阻断。
- `PreToolUse`：发现明文凭据、明显受限路径的大范围读取或敏感数据外发时，优先改为引用、局部读取或安全辅助调用；无法安全改写时才拒绝。
- `PostToolUse`：对返回模型的结果执行高置信凭据扫描和基础直接标识符脱敏；不得在 Hook 错误或日志中回显原文。
- 本地辅助能力只做 `scan / minimize / pseudonymize / summarize`，不在 V1 建设完整可逆 Token Vault。
- permission profile/sandbox 使用最窄但可工作的配置；默认避免 full access，MCP 按实际用途逐个启用。

个人规范模式在此基础上增加低打扰确认层：

- `personal` 为默认模式。明确声明为测试数据、且不属于私钥、认证头、带凭据 URL、编码/混淆秘密的高置信值，第一次仍被停止，但提示会同时给出安全保存命令、环境变量引用和五分钟内有效的一次性确认方式。
- Prompt 确认绑定去除确认标记后的完整 Prompt、当前目录、宿主 session 和事件类型；工具确认绑定完整工具输入、工具名、当前目录和宿主 session。内容、目标或 session 变化后必须重新确认。
- 本地确认状态只保存私有权限的范围 HMAC、随机请求元数据、令牌摘要、过期时间和消费状态，不保存 Prompt、工具参数或凭据原值；消费通过原子文件标记防止并发重放。
- `strict` 模式保留原有高置信 C4 全部硬阻止行为，可通过本地 `dlp_approval.py configure --mode strict` 选择。环境中的无效模式值按 strict 处理。
- 每次阻止或确认必须返回“安全继续卡”：原操作状态、数据类别、首选存储位置、交互式保存命令、Agent 引用方式和重试范围。macOS 优先使用 Keychain 且不使用 `-A`，密钥值不进入命令参数或 shell 历史。
- 当前 Codex `PreToolUse` 不支持 Hook 返回原生 `ask`，`UserPromptSubmit` 也不能改写用户消息：返回 `additionalContext` 时原消息仍会进入模型，返回 `decision: block` 则无法在同一事件驱动 Agent 重试。因此工具确认采用 deny → 用户把不含密钥的随机短期标记作为下一条 `UserPromptSubmit` → Hook 在模型处理前消费该标记的确认用途并提供无值继续上下文 → 原调用精确重试。原工具密钥不进入确认消息；本地助手只配置模式，不提供 Agent 可运行的 approve 命令。

Codex permission profiles 可以组合本地文件系统和网络规则，但当前仍标为 Beta，因此 V1 将其视作可配置最小权限能力，不将其描述成稳定的全终端 DLP。参考 [Permissions](https://learn.chatgpt.com/docs/permissions)。

### 8.3 ChatGPT Work V1：来源最小化 + 草稿优先

Work 不依赖 Codex Hook，核心是任务编排中的安全默认值：

- Work locally：涉及本地 C2/C3 文件时优先使用；先本地筛选、聚合或假名化，再让模型生成成果。
- Work cloud：只使用经过选择的文件、插件对象或脱敏派生物；不得假设能调用本机 DLP 脚本。
- 连接器查询必须限制账号、文件夹、对象、线程、时间窗或搜索条件，避免“把所有内容都给我”。
- 写操作采用 draft-first：先生成草稿并展示收件人、目标系统和影响，再发送、发布、删除或扩大共享。
- 任务产物默认进入人工审阅状态，不因为模型生成完毕就自动视为可外发。

### 8.4 普通 Chat V1：低负担指令 + 安全提问习惯

普通 Chat 不能依赖确定性本地拦截，因此目标是减少误输入和后续扩散：

- 个人/项目指令持续提醒使用占位符、少量片段、脱敏副本和公开搜索词。
- 安全 Skill 通过隐式匹配或 `@company-data-security` 显式调用提供处理方法。
- 对已经粘贴的 C1-C3，不频繁中断对话；AI 应停止继续复制和扩散，后续改用假名或摘要。
- 对已经粘贴的 C4，明确建议停止使用该值并按公司流程轮换；不得在回答中再次完整复述。
- 插件默认只读和最小范围；任何发送、发布、删除或权限变化都需要明确确认。

### 8.5 人工安装、自动或半自动验收

由于 ChatGPT Pro 无法形成企业级中央强制，V1 采用分表面验收：

| 表面 | 验收方式 | 能证明什么 | 不能证明什么 |
|---|---|---|---|
| Codex 本地 | `doctor` 检查受保护文件摘要、Hook 注册/协议、Skill 元数据和能力注册；Hook 信任与合成现场自测作为独立人工证据 | 当前插件包在检查时无已知字节/语义漂移；现场项是否已自证 | 用户之后不修改配置；Hook 已被信任；权限/MCP/hosted 或特殊工具都被覆盖 |
| Work locally | 本地安装项检查 + Skill 自测 + 权限模式和插件清单确认 | 本地工具和工作方法可用 | 云端账号设置和所有插件内部数据流都被本机控制 |
| Work cloud | Skill/Plugin 存在性、自测任务、连接器清单和人工确认 | 账号在检查时具备推荐工作流 | 存在统一发送前 Hook 或本机强制执行 |
| 普通 Chat | 个人/项目指令检查、Skill 自测、插件只读/动作确认清单 | 推荐行为路径可被触发 | 用户不会粘贴敏感数据，或所有输入都被技术拦截 |

## 9. V1 交互预算

V1 对用户打断实行明确预算：

- **静默处理**：C1-C3 的最小化、局部读取、假名化、摘要和输出脱敏。
- **一次性提示**：能力不可用、无法安全自动转换、分类高度不确定且选择会显著影响结果。
- **明确确认**：发送、发布、删除、扩大共享范围、变更权限或向新外部系统写入。
- **阻断**：非测试或高风险 C4、凭据存储读取、无效/过期/重放确认、无法检查的输入，或明显凭据将被写入外部目的地。personal 模式下可确认的测试值仍先停止一次。

不得因为检测到普通姓名、内部域名、订单号或单个手机号就默认终止任务。检测器不确定时优先继续采用最小化路径，并把最终判断留给明确的公司数据规则。

## 10. V1 验收标准

- **AC-1 差异化真实**：文档分别说明 Codex、Work、Chat 的可用、条件可用和不可依赖能力；Work 本地/云端及 Codex 本地/云端差异可见。
- **AC-2 数据处置一致**：C0-C4 在三个主场景均有默认处置，且共同遵循 Reference → Local Compute → Pseudonymize → Redact → Warn/Confirm → Block。
- **AC-3 低打扰**：默认只阻断高置信 C4 和高影响外部动作，C1-C3 的常规检测以静默处理为主。
- **AC-4 语义保留**：脱敏测试样例保留业务状态、错误码、实体关系和分析意义，不只验证字符串被删除。
- **AC-5 支持路径有效**：Codex 合成 canary 在声明受支持的 Prompt、工具输入和工具输出路径中被识别；未覆盖 hosted/specialized tools 明确记录为限制。
- **AC-6 普通任务覆盖**：至少覆盖代码、日志、文档、表格、客户/HR 数据、邮件/云盘、网页研究和快速问答。
- **AC-7 人工部署可验收**：每种产品表面都有与其能力相符的配置或自测方法，不伪造跨表面的自动证明。
- **AC-8 可回退**：关闭 Hook 或本地辅助工具后，Codex 仍可依赖 AGENTS + Skill 工作；插件/Skill 缺失时明确降级为个人/项目指令和人工安全习惯。
- **AC-9 确认不变成白名单**：一次授权只能放行完整内容和目标均未变化的一次调用；过期、篡改、跨工具和并发重放均失败，状态文件不含原值。
- **AC-10 安全继续可执行**：阻止/确认提示不回显原值，并给出当前平台可复制的保存方式和只传引用名的 Agent 调用方式。

## 11. 验证计划

V1 实施时使用全部为合成数据的测试集，不使用真实客户、员工或生产数据。

| 测试族 | 关键样例 | 预期结果 |
|---|---|---|
| 高置信 C4 | 合成私钥、典型 Token/Key、带密码 DSN | Codex 支持的 Hook 路径阻断或安全改写；Work/Chat Skill 不复述原值并建议安全处理 |
| 误报约束 | 代码中的 `password` 字段名、文档里的示例占位符、公开测试值 | 不阻断普通工作；必要时只给非中断提示 |
| C3 语义保留 | 合成客户、订单、错误码、时间和状态 | 输出使用稳定假名，保留订单关联、状态和错误分布 |
| 最小读取 | 大型合成日志、表格和文档集合 | 先筛选/聚合，只向模型提供与任务相关的派生结果 |
| 连接器范围 | 合成邮箱/云盘对象和多线程结果 | 查询限制到指定对象；外部写入先生成草稿并确认目标 |
| 产品降级 | 禁用 Hook、本地 helper 或 Skill | 按该表面声明的降级路径继续，不把缺失能力报告为已保护 |
| 绕过与边界 | base64、长输出、压缩内容、WebSearch、特殊工具路径 | 受支持路径按规则处理；不支持路径进入限制清单而不是虚假通过 |
| 一次性确认 | 声明测试的合成 Token、内容篡改、过期、并发消费、严格模式 | personal 精确放行一次；其余情况阻止且不持久化原值 |
| 安全存储建议 | macOS Keychain、环境变量引用、非 macOS 降级 | 保存命令采用交互输入；不生成任意应用访问或明文参数；Agent 只获得引用方式 |

V1 的效率指标先测量再确定阈值，至少记录 Hook 命中率、真实阻断次数、误阻断、用户额外操作、脱敏前后任务可完成性和本地处理延迟。不能用单一“安全分数”替代这些可解释信号。

## 12. 实施与上线顺序

仓库实施已经完成规则/样例、共享 Skill、Codex 薄 Hook、本地 scan/redact/pseudonymize、个人/严格模式、精确一次性确认、安全继续卡、三表面模板、doctor 和合成红蓝测试。V1 没有实现可逆 Token Vault、权限 profile 自动改写、MCP 自动收紧或集中式连接器策略。

现场上线仍按以下顺序执行，并分别留证：

1. 审查将要安装的精确插件字节和 `hooks/hooks.json`。
2. 在隔离 Codex 配置中安装，使用 `/hooks` 信任当前 Hook 摘要，再启动新任务。
3. 运行 doctor 和合成 canary；若任何 required check 失败，不启用阻断。
4. 将 Codex AGENTS、Work、普通 Chat 模板分别人工对齐；doctor 只把这类证明标为 `self_attested`，不升级为强制证明。
5. 小范围试点高置信 C4 阻断和 C3 输出脱敏，记录误报、漏报、额外操作和任务可完成性。
6. 按版本/Hook 协议/模板摘要定期复核；漂移时先停止“已保护”声明，再修复或回退。

每一步都可以独立回退；不得把启用 Skill 的批准解释为启用 Hook、安装辅助程序、收紧权限或部署网络控制的批准。

## 13. V1 非目标和残余风险

V1 明确不包含：

- 100% 防泄漏或对主动规避者不可绕过的保证；
- 企业工作区的中央策略、审计和合规 API 替代品；
- 终端全进程、全浏览器、全网络出口控制；
- 完整可逆 Token Vault、集中密钥托管或生产凭据轮换系统；
- 自动完成法律、隐私和监管分类；
- 对所有编码、加密、压缩和自定义工具外传的阻断；
- 假设 Codex Hook 覆盖 Work、普通 Chat、hosted tools 或全部特殊工具；
- 对已经发送到模型或第三方系统的数据进行“撤回”。
- Codex UI 直接新建任务时的容器级原子性；`UserPromptSubmit` 能证明 Prompt 未转发，但 UI 可能已经留下空任务壳。通过 Agent 工具创建任务时，`PreToolUse` 可在实际创建前停止。

主要残余风险：人工配置可被修改；一次性确认代表用户有意接受一次披露；Hook 事件没有对同一 OS 用户下恶意进程的密码学隔离；完整性基线不是签名且可被有意协同篡改；Skill 可能未触发；普通 Chat 没有统一发送前拦截；云端任务无法依赖本机工具；连接器权限可能过宽；分隔/加密/压缩/低熵或新格式秘密可能漏检；直接标识符可能误报；产品能力会变化。短期精确授权、自测、版本清单、最小权限、合成测试和定期复核只降低这些风险，不消除它们。

## 14. 产品事实来源与复核触发

| 官方来源 | 本文使用的事实 | 复核触发 |
|---|---|---|
| [Use ChatGPT](https://learn.chatgpt.com/docs/use-chatgpt) | Chat、Work、Codex 的用途与工具定位 | 产品模式或导航发生变化 |
| [Get started with ChatGPT Work](https://learn.chatgpt.com/docs/get-started-with-work) | Work 使用文件、插件、工具；本地/云端差异 | Work 本地或云端能力变化 |
| [Custom instructions with AGENTS.md](https://learn.chatgpt.com/docs/agent-configuration/agents-md) | Codex 的全局/项目指令发现与层级 | AGENTS 发现或优先级变化 |
| [Build skills](https://learn.chatgpt.com/docs/build-skills) | Skill/Plugin 跨表面分发与渐进加载 | Skill 安装、触发或表面支持变化 |
| [Hooks](https://learn.chatgpt.com/docs/hooks) | Codex 生命周期 Hook、工具覆盖及限制 | Hook 事件、输出协议或工具覆盖变化 |
| [Permissions](https://learn.chatgpt.com/docs/permissions) | Codex 本地文件/网络 permission profiles 及 Beta 状态 | 权限 profile 稳定性或平台支持变化 |
| [Permission modes](https://learn.chatgpt.com/docs/permission-modes) | 桌面应用与 Codex 的 sandbox/approval 边界 | 桌面权限模式变化 |
| [ChatGPT Custom Instructions](https://help.openai.com/en/articles/8096356-chatgpt-custom-instructions) | 全局 Custom Instructions 的产品表面覆盖 | 个性化设置或适用平台变化 |
| [Projects in ChatGPT](https://help.openai.com/en/articles/10169521-using-projects-in-chatgpt) | 项目指令的作用域及其与全局指令的优先关系 | Projects 指令或共享模型变化 |
| [Apps in ChatGPT](https://help.openai.com/en/articles/11487775-connectors-in) | Apps 的动作能力、权限和确认配置差异 | Apps 命名、动作权限或确认策略变化 |

该能力矩阵必须在以下任一事件发生时重新核对：OpenAI 产品大版本更新；Hook/Skill/Permission 文档变化；公司从 Pro 迁移到 Business/Enterprise；新增关键连接器；引入公司网关或端点 DLP；试点证明某项能力无法满足其声明。
