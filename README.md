# Dev Flow

[![CI](https://github.com/AldenClark/dev-flow/actions/workflows/ci.yml/badge.svg)](https://github.com/AldenClark/dev-flow/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Dev Flow 是一套面向 Codex 的中立、可组合、证据驱动工程工作台。它把需求澄清、仓库上下文、分层工程 Profile、设计、实施、验证、知识沉淀、审查和交付就绪度连接为可恢复、可追溯流程，同时避免把某个人的 Rust、前端或库偏好写进公共内核。

> English: a lightweight, repository-first and evidence-driven Codex workflow for high-quality software changes.

## 核心能力

- 在需求和方案前扫描真实代码、运行时事实与 Git 边界；
- 按真实 Git 根和有效工作目录解析 Codex 指令链，按任务路径选择证据、Profiles、原生控制与 CI；
- 所有持久改动都执行一个不可被条件路由删除的质量内核：仓库事实、需求真相、设计、语义连续性、黑白盒测试、根级质疑和知识处置；
- 内置 117 种方法、38 个风险模型和确定性 `select-methods`：从当前阶段、风险与 identity/interaction/temporal/oracle/hazard/agent-control 等失败信号选择有界的 starter/deep/formal 方法栈，并明确负向触发、缺失前提、回退与 `NOT RUN`；
- 以 `execute`、`checkpointed`、`co-design` 三种协作强度控制需求、设计与用户检查点；持久工作默认 `checkpointed`，只有已明确且无实质歧义的范围才显式使用 `execute`；
- 保存原始或脱敏需求来源、AI 理解修订、用户纠正和结构化 `AMB-n`，区分“Codex 应从仓库查明的事实”和“必须由用户定稿的需求语义”；
- 用需求修订号、需求摘要和设计摘要绑定批准；后续语义、设计或上下文变化会使相关批准与证据失效；
- 在恢复、用户修正、前提/阶段变化、切片和委派边界、重复失败、验证前与最终声明前重载精简检查点，解决上下文压缩后的遗忘，而不是按时间填表；
- 将 UI 工作分为 `none`、`preserve`、`material`，只对重大产品/UI 变化强制 UX Ready，避免无差别设计仪式；
- 明确记录需求、验收标准、设计、改动范围、进度、决策、测试和审计，并把“当前项目真相”“单次变更历史”“本地运行恢复证据”分开管理；
- 按微小修改、日常需求、Bug 修复、大型功能、重构、迁移、安全与性能任务调整流程重量；
- 使用 `direct`（无工作包）、`traced`（三个核心状态文件）和 `governed`（完整治理记录）三级工作模式；
- 按 Rust 后端、Web、Apple/Android/Windows 客户端、FFI、CLI/TUI 等项目形态组织验证；
- 新依赖必须先比较候选方案、影响与维护成本，并取得明确批准；
- 只把边界清晰的独立工作交给子代理，通常同时运行 1–2 个；以确定性的 P0-P6/PX 画像按任务宽度、推理深度与风险选择子代理模型/effort，根代理按 deadline、resource lease 和 disposition 完成综合、复核与最终验收；
- 管控浏览器、模拟器、设备、虚拟机、容器和服务等测试资源；
- 在需求、设计、实施、验证和最终 diff 上执行基本蓝/红质疑；对治理风险再路由独立深度审查；
- 通过 `$company-data-security` 为 Codex、ChatGPT Work 和普通 Chat 提供同一 C0-C4 数据处理原则，并在受支持的 Codex 本地 Prompt/工具路径上增加高置信 Secret 检查和输出脱敏；
- 保留当前职责分离的 Skill 拓扑作为兼容接口，但数量不是质量目标；只加载适用 owner 与专业技术 Skill，质量内核始终生效；
- 解析 public baseline、个人、团队、项目、组件与任务六层 Profile，并输出带来源哈希、冲突和例外的有效快照；
- 以 T0-T3 Engineering Context Readiness 检查当前任务真正需要的上下文，而不是按文件存在性评分；
- 以 EQAC 优先使用编译器、类型检查、lint、测试、CI 等原生控制，再按当前宿主准入最小化路由专业 Skills；
- 缺少个人 Profile、`AGENTS.md` 或某个具名 Skill 不会单独构成阻断，也不会触发自动安装。
- 所有用户交互始终留在 Default mode；适合的封闭选择优先调用宿主原生 `request_user_input`，由 App Server 承载 `item/tool/requestUserInput`，不会为提问切换 Plan mode 或自行拼装协议帧。

## 运行要求

- 支持当前 Codex CLI 的基础单代理工作流；委派与 hooks 能力在使用前单独检测；
- Python `3.11` 或更高版本，仅使用标准库；
- Git；
- 如需多代理与 hooks，Codex 配置启用 `multi_agent`、`multi_agent_v2` 和 `hooks`。

推荐配置：

```toml
[features]
multi_agent = true
multi_agent_v2 = true
hooks = true

[agents]
max_concurrent_threads_per_session = 3
```

## 安装

发布与插件清单版本一致的标签后，可直接添加仓库内的 marketplace 并安装固定到该标签的插件。当前已发布稳定标签为 `v1.1.2`；只有对应标签已推送后，才应从 marketplace 安装该版本：

```bash
codex plugin marketplace add AldenClark/dev-flow --ref v1.1.2
codex plugin add dev-flow@dev-flow
```

从源码检出进行开发时，先运行：

```bash
python3 skills/dev-flow/scripts/dev-flow.py check --plugin-root "$PWD"
python3 skills/dev-flow/scripts/dev-flow.py preflight
```

再安装随附的角色配置：

```bash
python3 skills/dev-flow/scripts/dev-flow.py install-runtime
```

安装器不会静默覆盖已有配置：同内容文件会标记为 `unchanged`；不同内容文件会阻止整次安装。如确实要替换，请显式使用 `--force`，安装器会先在目标目录的 `.dev-flow-backups/` 下备份原文件。

```bash
python3 skills/dev-flow/scripts/dev-flow.py install-runtime --force
```

安全卸载只删除仍与插件分发版本完全一致的配置；已被用户修改的文件会保留并报告冲突：

```bash
python3 skills/dev-flow/scripts/dev-flow.py uninstall-runtime
```

安装或更新 hooks 后，请在 Codex 中使用 `/hooks` 检查并明确授权。Codex 会跳过尚未信任的新建或已变化的非托管 hook 定义。

### 机密数据安全 V1

源码检查只证明插件包本身。先运行：

```bash
python3 skills/company-data-security/scripts/doctor.py --plugin-root "$PWD"
python3 -m unittest evals.test_data_security -v
```

doctor 会检查受保护文件摘要、三个 DLP Hook 事件、Skill 元数据、能力注册和三类表面模板。Hook 信任、Codex 新任务实际加载、ChatGPT Work 指令和普通 Chat 指令属于现场证据；未提供时会保持 `not_observed`，不会伪装成通过。

三份可复制的指令基线位于：

- `skills/company-data-security/assets/codex-agents-baseline.md`
- `skills/company-data-security/assets/chatgpt-work-instructions.md`
- `skills/company-data-security/assets/ordinary-chat-instructions.md`

该 V1 不替代企业策略、端点/网络出口 DLP、最小权限配置、MCP/连接器管理或事故响应。详见 `docs/confidentiality-aware-ai-work-v1.md`。

## 使用方式

在 Codex 中调用 `$dev-flow`，并描述目标、允许的交付范围以及兼容性要求。主流程会先使用 `$repo-context` 建立仓库事实、ECR/EQAC 和有效 Profile，再只路由当前任务需要的能力。也可以直接调用 `$requirements-design`、`$architecture-decisions`、`$dependency-decisions`、`$systematic-debugging`、`$verification`、`$change-review` 或其他聚焦 Skill。涉及凭据、个人/客户/生产数据、内部材料、连接器或敏感外部动作时，可显式调用 `$company-data-security`；它也允许按描述隐式触发。

只有在创建、调整、解释、推广、退役或审计 Profile/质量策略时才调用 `$manage-engineering-profiles`；普通代码任务只消费解析结果。`$dev-flow-maintainer` 仅用于显式维护本插件。

核心顺序是：控制面绑定权限和不可省略的质量内核 → `repo-context` 建立事实与专业能力上下文 → `requirements-design` 保存并澄清持久改动的需求真相 → 按需进入 UX/诊断/架构/依赖 owner → 按可验证切片实施并维护恢复检查点 → `verification` 用独立推导的黑盒/白盒证据证明 → 仅在治理风险下独立 `change-review` → 仅在明确交付意图下进入 `delivery-readiness`。验证和审查可以暴露上游缺口，但不能在自己的输出中替代需求、诊断或架构决策。

完成 `repo-context` 后，AI 会使用方法论层，而不要求用户先知道 Alloy、TLA+、LINDDUN、STPA、semantic mutation 或其他方法名：

```bash
python3 skills/dev-flow/scripts/dev-flow.py validate-methods
python3 skills/dev-flow/scripts/dev-flow.py select-methods \
  --phase design --task-type large-feature \
  --risk concurrency --signal temporal-progress \
  --available repository-facts --available requirement-baseline \
  --available state-model --depth deep
```

受治理工作包会自动写入初始选择，但该记录只是 discovery 时的初筛，不能通过设计门禁。设计、验证和审计阶段分别使用 `record-methods <packet> --phase design|verification|review ...` 写入新鲜的 `method-selection.json`/`.md`；记录与方法库、需求/设计摘要、当前风险和 owner 产物绑定，缺失、初步或过期选择会阻断对应状态转换。

输出沿“观察事实 → 失败假设 → 方法 → owner 产物 → 证据义务”解释选择，并受风险归一化、阶段、深度、负向规则、前提和 context cap 约束。方法选择是指导，不是证明或授权；完整研究、方法家庭和扩展治理见 [`docs/methodology-pool.md`](docs/methodology-pool.md)。

委派前，根代理必须为一个明确 workload 调用 `route-agent`。角色只规定权限；模型与推理强度由任务画像在 spawn 时决定，角色 TOML 不固定型号：

```bash
python3 skills/dev-flow/scripts/dev-flow.py route-agent \
  --role dev-flow-explorer --workload broad-mapping \
  --signal large-context --signal oracle-challenge
```

返回 JSON 包含 default/policy/selected profile、`requested_model`、`requested_reasoning_effort`、`fork_turns` 和升级原因。P3 是 B/high 的有界深度，P4 是 F/medium 的任务宽度；两者同时需要时选择 P5。P6 只由明确的关键验收、不可逆或数据丢失信号触发；PX 只能显式指定并确认例外。运行时不能满足请求时必须记录 fallback 与实际可观察配置，不能静默假设请求已经生效。完整矩阵、任务路由和 receipt 契约见 [`multi-agent-v2-orchestration.md`](skills/dev-flow/references/multi-agent-v2-orchestration.md)。

## Source 与运行时边界

仓库内检查只证明当前 source bytes；Codex 任务实际使用的是任务启动时已安装的插件快照。除非 exact source 已经通过受控安装/升级进入目标 `CODEX_HOME`，并在新任务中按 installed bytes 复验，否则不得把 source 结果表述为当前运行插件已经生效。安装、升级、卸载和覆盖现有运行时都是独立外部变更，必须有明确授权。

schema 2.0 工作包用 `record-iteration` 记录同一原因的 hypothesis/repair 结果。原因必须绑定到包内 `artifacts/` 下的稳定证据文件；同一代中重命名原因、替换证据或删除熔断状态都会失败关闭。第三次连续失败会自动进入 `blocked` 并拒绝第四次；只有记录重新评估和重新打开的上游 owner 后才能恢复：

```bash
python3 skills/dev-flow/scripts/dev-flow.py record-iteration <packet> \
  --kind repair --cause-id <stable-cause> --cause-file <evidence-file-below-artifacts> \
  --outcome failed --note <evidence>
python3 skills/dev-flow/scripts/dev-flow.py record-iteration <packet> \
  --kind repair --cause-id <stable-cause> --cause-file <same-evidence-file> --outcome reassessed \
  --reopened-owner architecture-decisions --note <new-causal-model>
```

Profile 与上下文命令均使用 Python 标准库：

```bash
python3 skills/dev-flow/scripts/dev-flow.py resolve-profiles \
  --root "$PWD" --output .codex/dev-flow/<change-id>/effective-preferences.json

python3 skills/dev-flow/scripts/dev-flow.py assess-context \
  --root "$PWD" --task-type routine --profile-mode team-reproducible

python3 skills/manage-engineering-profiles/scripts/profile-tool.py \
  scaffold --id project.default --layer project --owner team \
  --output .dev-flow/profiles/project.toml

python3 skills/manage-engineering-profiles/scripts/profile-tool.py \
  suppress --fingerprint sha256:<64-hex> --owner <owner> \
  --reason "reviewed for this unchanged task context" \
  --tier T1 --output .dev-flow/suppressions.json
```

Profile 工具默认只输出 review-first 提案；明确审核后才添加 `--write`。它不会自动创建团队规则、安装专业 Skill 或修改依赖。

### 用户确认与结构化输入

Dev Flow 把“为什么要问”和“如何展示问题”分开：只有仓库调查后仍然存在、且会改变行为、契约、依赖、兼容性、范围、风险、验收或权限的用户自有决策，才进入确认流程。对一至三个能够准确表达为封闭选项的非秘密决策，当前 Default-mode 宿主若暴露 `request_user_input`，就调用该原生工具；App Server/客户端负责 `item/tool/requestUserInput` 的线程、轮次、item、阻塞、响应关联、渲染和清理生命周期。

Skill 不直接发送 App Server 帧，也不根据版本号、已安装能力或记忆推断工具可用，更不会自动修改全局 Codex feature 配置。当前 turn 没有暴露该工具、或在展示前调用失败时，流程保持 Default mode；若宿主允许，只退化为一次聚焦的非枚举文字问题，否则明确报告阻断，不把多选框伪装成文字选项。开放式说明继续使用普通对话；命令、文件变更、破坏性或外部动作使用宿主原生批准界面；秘密只通过宿主认可的安全输入通道收集，否则停止请求。

合法回答是一个已展示的非空选项，或在该问题启用 Other 时的一条非空补充；未知问题、空值、多值冲突、未启用 Other 的越界值和过期修订回答都无效。取消、清理、中断、漏答或无效回答保持“未决”，不立即换通道重问，也绝不会自动采用推荐项；只有新的用户意图或明确重试才重新发问。有效回答会回写受影响的 `AMB/AC/SC/VO`、依赖、豁免或交付记录及需求修订/摘要。App Server 当前仍把这项协议标记为 experimental，因此实时原生交互和静态契约验证会分开报告。

CLI 初始化也支持显式分类：

```bash
python3 skills/dev-flow/scripts/dev-flow.py init-packet \
  --root "$PWD" --change-id console-redesign --task-type large-feature \
  --objective "Redesign the primary console workflow" \
  --collaboration-profile co-design --ui-impact material --mutation persistent
```

CLI 会自动选择工作模式，也可用 `--work-mode` 显式指定。`--mutation persistent` 的微小任务也会创建 traced 工作包；`direct` 只用于不修改持久状态的单回合调查或 spike。新工作包使用 schema 2.0 和 append-only `events.jsonl`，并继续读取旧 schema 1.0、1.1、1.2。`checkpointed`/`co-design` 在批准前记录 Requirement Ready；内容绑定会把批准关联到当前需求修订与摘要，`material` UI 还记录 UX Ready：

```bash
python3 skills/dev-flow/scripts/dev-flow.py record-approval \
  .codex/dev-flow/console-redesign requirements \
  --id REQ-READY --by user --note "requirements approved"

python3 skills/dev-flow/scripts/dev-flow.py record-approval \
  .codex/dev-flow/console-redesign ux \
  --id UX-READY --by user --note "product and UX direction approved"
```

Schema 2.0 的依赖批准必须绑定机器可读身份、精确 ref、目标文件、允许操作和最终文件摘要，不能用一个泛化的 `DEP-n` 解锁其他依赖。例如：

```bash
python3 skills/dev-flow/scripts/dev-flow.py record-approval \
  .codex/dev-flow/release-change dependencies \
  --id DEP-1 --by user --note "approve exact action" \
  --dependency-ecosystem github-actions \
  --dependency-name actions/upload-artifact --dependency-version 7.0.1 \
  --dependency-ref 043fb46d1a93c77aae656e7c1c64a875d1fc6a0a \
  --dependency-file .github/workflows/release-candidate.yml \
  --dependency-operation add
```

包管理器调用必须是可解析的单一精确命令，并通过 `--dependency-command 'cargo add name@ref --features=exact'` 连同全部 flags 绑定；add/update/remove 使用同一规则。`.exe`/`.cmd` launcher、Cargo toolchain 与普通嵌套 shell launcher 会被识别，任何位于 verb 前后且无法绑定目标 manifest 的 path/package/workspace selector 都会拒绝。直接写 manifest/lockfile 时，最终审计还要求 `--dependency-result-sha256 PATH=sha256:<hex>` 与实际文件字节一致。GitHub Actions 的 block/flow mapping、YAML 十六进制/Unicode 转义 `uses` 键和值，以及工作流中的具体 Action 引用也使用同一路径、operation 与完整 commit SHA 约束。不能可靠绑定的操作会拒绝，而不会退化为“已有任意依赖审批即可”。

当仓库调查后仍存在会改变行为、契约、安全、兼容性、范围或验收的多义性时，先记录不同解释、责任人、受影响 ID 和建议，再由证据或用户定稿：

```bash
python3 skills/dev-flow/scripts/dev-flow.py record-ambiguity \
  .codex/dev-flow/console-redesign \
  --summary "默认行为是否变化" --source "需求文档" \
  --interpretation "仅显式启用" --interpretation "所有用户默认启用" \
  --materiality material --owner user --affects AC-1 \
  --recommendation "保留现有默认值"

python3 skills/dev-flow/scripts/dev-flow.py resolve-ambiguity \
  .codex/dev-flow/console-redesign --id AMB-1 \
  --status user-confirmed --by user --resolution "保留现有默认值" \
  --evidence "用户在需求检查点确认"
```

实现或审计阶段若发现新的重大需求疑义，受影响工作必须先回到等待确认；旧设计批准被保留为历史，但不能复用：

```bash
python3 skills/dev-flow/scripts/dev-flow.py transition \
  .codex/dev-flow/console-redesign awaiting-approval \
  --ambiguity-id AMB-2 --note "审计发现兼容性语义存在两种解释"
```

日常 `traced` 任务只建立：

```text
.codex/dev-flow/<change-id>/
├── packet.json
├── events.jsonl
├── trace.md
└── artifacts/
```

高风险或显式治理的 `governed` 任务建立：

```text
.codex/dev-flow/<change-id>/
├── packet.json
├── events.jsonl
├── context.md
├── requirements.md
├── design.md
├── execution.md
├── test-matrix.md
├── blue-audit.md
├── red-audit.md
├── evidence.md
├── decisions.md
├── briefs/
├── reports/
└── artifacts/
```

无持久修改的清晰微型调查可使用 `direct`，不创建工作包；任何持久修改至少使用 traced，高风险或显式治理升级为 governed。

### 连续性恢复与项目知识

新质量内核工作包在语义边界保存短恢复入口；它绑定当前需求、设计、工程上下文、活动 `AC/SC/VO`、最近证据、下一动作和停止条件。恢复时先读取它，验证前再冻结一次，避免上下文压缩或委派交接把旧目标带入新字节：

```bash
python3 skills/dev-flow/scripts/dev-flow.py record-checkpoint \
  .codex/dev-flow/console-redesign --trigger slice-end \
  --objective "Finish the validated console navigation slice" \
  --active-id AC-1 --active-id SC-D1 \
  --last-evidence "focused navigation tests passed" \
  --next-action "run module smoke checks" \
  --stop-condition "stop on requirement, design, or context drift" \
  --repository-reconciliation "reviewed the exact slice diff against AC-1 and SC-D1"

python3 skills/dev-flow/scripts/dev-flow.py resume-packet \
  .codex/dev-flow/console-redesign
```

检查点同时绑定每个声明仓库根的身份、Git `HEAD` 与完整工作树摘要。实现中的开放切片允许正常编辑；`resume-packet` 会把这类变化报告为需复核，而不是伪装成已对齐。切片结束、委派、阶段切换和验证前属于封闭边界，之后出现的字节变化会阻断。`HEAD` 改变不能由普通 resume 静默接受：复核精确提交范围后，必须用 `--trigger reconciliation --repository-reconciliation <evidence> --accept-head <root>=<exact-oid>` 明确建立新基线。若 `verifying` 后仅出现已复核的仓库 HEAD/工作树或绑定知识清单漂移，可先退回 `implementing` 修复绑定，再显式 reconciliation 并重新冻结 `pre-verification`；任何其他完整性错误仍会阻断回退。当前保守观察范围是整个声明根；非 Git 根会标记为不可机械观察，而不会虚报连续性。

项目知识按语义分为三层：`docs/project/` 保存当前真相，`docs/changes/<change-id>/` 保存可追溯变更档案，忽略的 `.codex/dev-flow/` 只保存本地恢复状态和原始证据。只有已经实现、重新验证、可跨任务复用且适合公开保留的结论才晋升到当前真相；日志、临时计划、凭据和敏感原文不晋升。

```bash
python3 skills/dev-flow/scripts/dev-flow.py validate-knowledge --root "$PWD"
python3 skills/dev-flow/scripts/dev-flow.py bind-knowledge \
  .codex/dev-flow/console-redesign --impact update \
  --root "$PWD" \
  --manifest docs/changes/console-redesign/manifest.json \
  --rationale "implemented and verified console behavior updates current project truth"
```

结构、模板、晋升与隐私边界见 [docs/knowledge-system.md](docs/knowledge-system.md)。结构校验只检查可机械事实，不给文档质量打分。

多代理完成以“没有仍在运行/待启动的委派任务，且每个任务都已有 reconciled disposition”为准，不要求可复用的终态 thread 从界面中消失。子代理原生 final 是主结果，`reports/` 文件仅在 brief 明确要求时作为持久证据；缺少报告不会阻止退出，也不会单独触发重复派工。`wait_agent` 超时只表示本次观察窗口没有更新。超过 hard deadline 后先检查状态，最多请求一次 interrupt，再记录 terminal 或 `orphan-suspected` 处置。

工作包验收后可显式解除活动指针而不删除证据：

```bash
python3 skills/dev-flow/scripts/dev-flow.py deactivate-packet .codex/dev-flow/<change-id>
```

成功收尾的顺序是：冻结 `pre-verification` 检查点并进入 `verifying`，完成新鲜验证与证据记录，执行 `validate-packet`，通过 `transition ... accepted` 的终态校验，再对匹配的终态工作包执行 `deactivate-packet`，最后才发送成功回复。源码校验不证明当前任务已加载同一插件快照；遇到不受当前运行时支持的 schema 或更新的工作包生产版本时，应保留工作包并升级运行时，而不是降级或改写证据。

## 仓库内容与运行时数据

| 公开上传 | 不应上传 |
|---|---|
| 插件清单、Skills、hooks、角色配置 | `.codex/dev-flow/` 工作包和运行产物 |
| 工程偏好、治理规则和参考案例 | 本地日志、截图、trace、dump 和临时文件 |
| 确定性测试、契约和 CI 配置 | `.codex/plugin-data/`、环境变量和密钥 |
| LICENSE、CHANGELOG、贡献与安全说明 | 虚拟环境、缓存、覆盖率和构建产物 |

工作包可能包含命令、路径、日志和测试产物，因此默认只保存在使用者项目的本地 `.codex/dev-flow/` 中，不属于插件源码。提交 Issue 或 PR 前应移除凭据、个人数据和不必要的运行时内容。

Hooks 只在仓库显式激活 `.codex/dev-flow/current` 时工作；子代理生命周期 Hook 还要求工作包处于活动流程状态，accepted、archived 和 blocked 包不会继续治理后续子代理。Stop Hook 在 assistant 回复之后运行，因此只对 `verifying`/`accepted` 工作包提供只读诊断：运行时不兼容和同版本验证失败都不会返回阻断决策或拉起新的 assistant turn；硬门由回复前的 CLI 验证和生命周期转换承担。Hooks 不包含 MCP 服务、不发起网络请求、不读取凭据。子代理运行标记写入 `PLUGIN_DATA`，只保存不可逆的数据包标识哈希和时间戳，并在停止时清理；marker 存储不可用会给出 `DEV_FLOW_AGENT_MARKER_UNAVAILABLE`，缺少可选报告会给出 `DEV_FLOW_AGENT_REPORT_MISSING`，两者都不会阻断原生生命周期。

## 仓库结构

- `skills/dev-flow/`：薄编排内核、工作包协议、Profile/ECR/EQAC 运行时、CLI 与角色配置；
- `skills/repo-context/`、`requirements-design/`、`product-ux-discovery/`：上下文、语义/范围与产品体验输入；
- `skills/architecture-decisions/`、`dependency-decisions/`、`systematic-debugging/`：技术决策和诊断；
- `skills/verification/`、`change-review/`、`delivery-readiness/`：证据、独立审查与交付就绪；
- `skills/manage-engineering-profiles/`：个人/团队/项目/组件 Profile 和质量策略生命周期；
- `skills/dev-flow-maintainer/`：显式维护 schema、能力准入、路由、迁移和评测；
- `hooks/`：仅对显式激活工作包生效的依赖、委派、进度与完成门禁；
- `evals/`：行为测试、结构契约和代表性项目案例；
- `governance/industry-practices.json`：外部实践到本地策略的采用记录。

## 验证

```bash
python3 -m unittest discover -s evals -v
python3 evals/run_contract_checks.py
python3 skills/dev-flow/scripts/dev-flow.py check --plugin-root "$PWD"
python3 skills/dev-flow-maintainer/scripts/validate-suite.py
python3 -m compileall -q hooks skills evals tools
```

CI 在 Linux、macOS 和 Windows 上覆盖 Python 3.11 与当前 Python 3.14。确定性契约、代表性仓库工作流和原生测试是默认质量门禁；实时模型评测只是模型可见行为发生实质变化后的辅助证据，不能替代代码、平台、安全、审查或发布证据。

确定性门禁通过后，实质性的模型行为变化按受影响开发类别运行至少三轮独立 first attempt。单个 pair 只用于定位案例、grader 或局部行为缺陷，不能单独为实质性变更提供准入证据：

```bash
python3 evals/run_paired_evaluations.py \
  --attested-pilot --category CAT-FFI \
  --executor-draft 'python3 evals/codex_model_adapter.py inventory --model gpt-5.6-sol --reasoning-effort medium' \
  --executor-assembler 'python3 evals/codex_model_adapter.py assembler --model gpt-5.6-sol --reasoning-effort high' \
  --grader 'python3 evals/codex_model_adapter.py grader --model gpt-5.6-sol --reasoning-effort medium' \
  --output /absolute/path/to/eval-output --trials 3
```

`--attested-pilot` 必须用 pair/category 筛选 schema-1.8 development 配置；不存在可执行的无筛选开发广测命令。结果分别报告安全/权限硬门禁、按案例与类别的 outcome、跨轮波动、fidelity/retention/rework 和成本，不能合成一个“总体质量分”。固定案例只支持受控对比；Wilson 区间是运维性描述，即使冻结发布配置继续把下界作为保守门禁，也不代表对所有开发任务的总体置信度。完整冻结验收只用于另行授权和预算的发布对比；详见 [docs/evaluation-suite.md](docs/evaluation-suite.md) 与 [docs/releasing.md](docs/releasing.md)。

## 发布候选与供应链证据

发布流程把 PR CI、模型评测、制品构建、SBOM/provenance、签名标签和最终发布视为不同门禁。确定性源码制品只从指定 Git commit 构建；相同 commit 在同一工具链下重复构建必须得到相同字节，验证器会检查版本、提交、SHA-256、归档根、路径和链接安全：

```bash
git rev-parse HEAD
python3 tools/build_release.py build \
  --root . --output dist --version 1.1.2 --commit FULL_COMMIT_SHA
python3 tools/build_release.py verify \
  --artifact-dir dist --expected-version 1.1.2 --expected-commit FULL_COMMIT_SHA
```

`.github/workflows/release-candidate.yml` 只能手动运行并要求完整 `expected_sha`；它使用固定 SHA 的 Syft、GitHub attestation 和 artifact Actions，生成 SPDX 2.3 JSON、provenance/SBOM attestations、manifest 与 checksums，但没有发布 Release 的权限。新工作流只有进入默认分支后才能 dispatch，不能把 PR 通过误报成 provenance 已生成。

Marketplace 内的插件源使用当前快照相对路径 `.`；因此外层 `codex plugin marketplace add ... --ref <immutable-tag>` 是唯一版本选择，不会在安装时悄悄跳到另一个标签。完整的 gate、验证命令、隔离安装、失败处置与发布/回滚顺序见 [docs/releasing.md](docs/releasing.md)。

## 版本与兼容性

仓库使用 [Semantic Versioning](https://semver.org/)：

- `MAJOR`：Skill 名称、工作包、CLI 或 hook 契约的不兼容变化；
- `MINOR`：向后兼容的新流程、命令、策略或能力；
- `PATCH`：兼容的修复、文档和规则校正。

源码与 Git tag 使用稳定版本（例如当前源码 `1.1.2`）；仅本地 Codex 开发重装时才临时追加 `+codex.<cachebuster>`，不把缓存破坏后缀发布为正式版本。源码版本不代表对应标签已经发布，发布状态以 Git tag/release 为准。RC 标签只证明候选身份，不等于稳定版发布。变更记录见 [CHANGELOG.md](CHANGELOG.md)。

## 参与和安全

提交修改前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。安全问题请遵循 [SECURITY.md](SECURITY.md)，不要在公开 Issue 中提交漏洞细节、凭据或敏感运行数据。

## License

MIT，详见 [LICENSE](LICENSE)。
