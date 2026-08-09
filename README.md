# Dev Flow

[![CI](https://github.com/AldenClark/dev-flow/actions/workflows/ci.yml/badge.svg)](https://github.com/AldenClark/dev-flow/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Dev Flow 是一套面向 Codex 的中立、可组合、证据驱动工程工作台。它把仓库上下文、分层工程 Profile、需求与设计、实施、验证、审查和交付就绪度连接为可追溯流程，同时避免把某个人的 Rust、前端或库偏好写进公共内核。

> English: a lightweight, repository-first and evidence-driven Codex workflow for high-quality software changes.

## 核心能力

- 在需求和方案前扫描真实代码、运行时事实与 Git 边界；
- 按真实 Git 根和待修改路径解析本地规范、嵌套指令、Skills、机器配置与 CI，并把有效规则映射到实现和证据；
- 以 `execute`、`checkpointed`、`co-design` 三种协作模式控制需求、设计、漂移与验收检查点；
- 把输入中的多义性记录为结构化 `AMB-n`，区分“Codex 应从仓库查明的事实”和“必须由用户定稿的需求语义”；
- 用需求修订号与 SHA-256 摘要绑定 Requirement Ready/设计批准，后续语义变化或审计疑义会使旧批准失效；
- 将 UI 工作分为 `none`、`preserve`、`material`，只对重大产品/UI 变化强制 UX Ready，避免无差别设计仪式；
- 明确记录需求、验收标准、设计、改动范围、进度、决策、测试和审计；
- 按微小修改、日常需求、Bug 修复、大型功能、重构、迁移、安全与性能任务调整流程重量；
- 按 Rust 后端、Web、Apple/Android/Windows 客户端、FFI、CLI/TUI 等项目形态组织验证；
- 新依赖必须先比较候选方案、影响与维护成本，并取得明确批准；
- 只把边界清晰的独立工作交给子代理，由根代理负责综合、复核和最终验收；
- 管控浏览器、模拟器、设备、虚拟机、容器和服务等测试资源；
- 用蓝队审计、红队审计和新鲜验证证据阻止未经证实的完成声明。
- 以 12 个职责单一的 Skills 支持直接调用和端到端组合，避免加载无关工程手册；
- 解析 public baseline、个人、团队、项目、组件与任务六层 Profile，并输出带来源哈希、冲突和例外的有效快照；
- 以 T0-T3 Engineering Context Readiness 检查当前任务真正需要的上下文，而不是按文件存在性评分；
- 以 EQAC 优先使用编译器、类型检查、lint、测试、CI 等原生控制，再按当前宿主准入最小化路由专业 Skills；
- 缺少个人 Profile、`AGENTS.md` 或某个具名 Skill 不会单独构成阻断，也不会触发自动安装。
- 所有用户交互始终留在 Default mode；适合的封闭选择优先调用宿主原生 `request_user_input`，由 App Server 承载 `item/tool/requestUserInput`，不会为提问切换 Plan mode 或自行拼装协议帧。

## 运行要求

- Codex CLI `0.147.0` 或更高版本；
- Python `3.11` 或更高版本，仅使用标准库；
- Git；
- Codex 配置启用 `multi_agent`、`multi_agent_v2` 和 `hooks`。

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

发布与插件清单版本一致的标签后，可直接添加仓库内的 marketplace 并安装固定到该标签的插件。当前已发布稳定标签为 `v0.2.0`；源码中的下一版本能力需待对应标签发布后再从 marketplace 安装：

```bash
codex plugin marketplace add https://github.com/AldenClark/dev-flow.git
codex plugin add dev-flow@dev-flow
```

从源码检出进行开发时，先运行：

```bash
python3 skills/dev-flow/scripts/dev-flow.py check --plugin-root "$PWD"
python3 skills/dev-flow/scripts/dev-flow.py preflight --tool-surface-confirmed
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

## 使用方式

在 Codex 中调用 `$dev-flow`，并描述目标、允许的交付范围以及兼容性要求。主流程会先使用 `$repo-context` 建立仓库事实、ECR/EQAC 和有效 Profile，再只路由当前任务需要的能力。也可以直接调用 `$requirements-design`、`$architecture-decisions`、`$dependency-decisions`、`$systematic-debugging`、`$verification`、`$change-review` 或其他聚焦 Skill。

只有在创建、调整、解释、推广、退役或审计 Profile/质量策略时才调用 `$manage-engineering-profiles`；普通代码任务只消费解析结果。`$dev-flow-maintainer` 仅用于显式维护本插件。

Profile 与上下文命令均使用 Python 标准库：

```bash
python3 skills/dev-flow/scripts/dev-flow.py resolve-profiles \
  --root "$PWD" --output .codex/dev-flow/<change-id>/effective-preferences.json

python3 skills/dev-flow/scripts/dev-flow.py assess-context \
  --root "$PWD" --task-type routine --packet .codex/dev-flow/<change-id>

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
  --collaboration-profile co-design --ui-impact material
```

新工作包使用向后兼容的 schema 1.2，并继续验证旧 schema 1.0/1.1。`checkpointed`/`co-design` 在批准前记录 Requirement Ready；schema 1.2 会把批准绑定到当前需求修订与摘要，`material` UI 还记录 UX Ready：

```bash
python3 skills/dev-flow/scripts/dev-flow.py record-approval \
  .codex/dev-flow/console-redesign requirements \
  --id REQ-READY --by user --note "requirements approved"

python3 skills/dev-flow/scripts/dev-flow.py record-approval \
  .codex/dev-flow/console-redesign ux \
  --id UX-READY --by user --note "product and UX direction approved"
```

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

非微型任务会在目标仓库建立：

```text
.codex/dev-flow/<change-id>/
├── packet.json
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

真正的微小变更沿用同一机器状态和目录边界，但把人类可读记录压缩到 `trace.md`。

## 仓库内容与运行时数据

| 公开上传 | 不应上传 |
|---|---|
| 插件清单、Skills、hooks、角色配置 | `.codex/dev-flow/` 工作包和运行产物 |
| 工程偏好、治理规则和参考案例 | 本地日志、截图、trace、dump 和临时文件 |
| 确定性测试、契约和 CI 配置 | `.codex/plugin-data/`、环境变量和密钥 |
| LICENSE、CHANGELOG、贡献与安全说明 | 虚拟环境、缓存、覆盖率和构建产物 |

工作包可能包含命令、路径、日志和测试产物，因此默认只保存在使用者项目的本地 `.codex/dev-flow/` 中，不属于插件源码。提交 Issue 或 PR 前应移除凭据、个人数据和不必要的运行时内容。

Hooks 只在仓库显式激活 `.codex/dev-flow/current` 时工作；它们不包含 MCP 服务、不发起网络请求、不读取凭据。子代理运行标记写入 `PLUGIN_DATA`，只保存不可逆的数据包标识哈希和时间戳，并在成功结束后清理。

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
python3 -m compileall -q hooks skills evals
```

CI 在 Linux、macOS 和 Windows 上覆盖 Python 3.11 与当前 Python 3.14。实时模型行为评测与确定性仓库检查分离，避免把不可复现的模型结果伪装成静态门禁。

## 版本与兼容性

仓库使用 [Semantic Versioning](https://semver.org/)：

- `MAJOR`：Skill 名称、工作包、CLI 或 hook 契约的不兼容变化；
- `MINOR`：向后兼容的新流程、命令、策略或能力；
- `PATCH`：兼容的修复、文档和规则校正。

源码与 Git tag 使用稳定版本（例如当前源码 `1.0.0`）；仅本地 Codex 开发重装时才临时追加 `+codex.<cachebuster>`，不把缓存破坏后缀发布为正式版本。源码版本不代表对应标签已经发布，发布状态以 Git tag/release 为准。变更记录见 [CHANGELOG.md](CHANGELOG.md)。

## 参与和安全

提交修改前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。安全问题请遵循 [SECURITY.md](SECURITY.md)，不要在公开 Issue 中提交漏洞细节、凭据或敏感运行数据。

## License

MIT，详见 [LICENSE](LICENSE)。
