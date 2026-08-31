# Dev Flow

Dev Flow 是一个面向 Codex 的仓库优先开发流程。2.0 的目标不是建立第二套工作流引擎，而是用最少的流程成本保持三件事：长期业务工作不漂移、技术结论有原生工程证据、高后果动作保留明确安全边界。

当前源码候选身份为 `2.0.0-rc.5`。它收敛个人 AI 编程辅助的公共命令面、路由上下文、产品状态、只读诊断、隐私友好成效观测和不可信上下文边界。`v2.0.0-rc.4` 是最近已发布且可固定安装的标签，RC.5 的回滚目标为 `v2.0.0-rc.4`；此前 RC.5 候选的 R4 失败已保留，当前 MCP-aware 修复仍需要受影响语义 smoke、轻量方法论静态审查、一次最终本地回归、托管兼容、制品、安装、tag 和发布证据。完整重复 R4 保留给稳定版或单独授权的评估。`v1.1.2` 是最后一个 1.x 稳定标签。2.0 采用破坏性切换，不承诺从 1.x 升级、迁移状态或回滚兼容。

## 2.0 核心模型

```text
仓库业务连续性             原生工程证据              最小安全边界
---------------------     ---------------------     ---------------------
设计与取舍                 代码、配置与 Git           凭据/敏感数据
实施切片                   测试、构建与 CI            广泛破坏
当前进度                   运行时与制品               外部交付与不可逆动作
重要决策                   审查与可观测性             用户的精确授权
```

三类信息互不替代：进度文档不能证明测试通过，本地测试不能证明生产部署，Hook 也不能替用户批准业务语义或外部动作。

## 任务入口

2.0 不再让一个 `task_type` 同时承担规模、意图、风险和流程深度。入口按四个独立维度判断：

- `intent`：`research`、`diagnose`、`design`、`change`、`review`、`delivery`；
- `continuity`：`direct` 或 `managed`；
- `risk overlays`：security、migration、external system、release、irreversible、UI 等；
- `knowledge impact`：`none`、`current-truth`、`change-record`，managed 另有 workstream 连续性文档。

Intent 只选择能力所有者，不是新的生命周期。2.0 调用方只应使用 intent；源码中残留的 `--task-type` 解析不属于公共兼容承诺。

`research` 用于收集、核对和比较事实，不判断目标是否存在缺陷；`review` 用于审计、代码审查、安全审查和其他需要验证发现的只读判断。`review` 默认不修改仓库；“审查并修复”使用 `change --need review`。2.0 不把旧 audit/task-type 别名定义为受支持接口。

仓库修改和外部动作的授权仍在路由之前单独确认。`--mutation` 只描述是否修改仓库；它不代表 push、发布、部署、迁移执行或其他外部动作的权限。

## 需求理解边界

进入技术设计前，按“还需要决定多少业务语义”而不是按任务名称分类：

- U1：新增或改变产品行为、公共契约、权限、数据生命周期、用户流程、集成或迁移语义；
- U2：行为保持不变的结构、依赖、配置或性能调整；
- U3：预期行为已由请求或仓库证据建立的缺陷修复；
- U4：拼写、格式、精确替换或生成同步等机械修改；
- U5：研究、审查和交付评估等只读工作，包括对候选设计的审查。

U1 先调查仓库并解决可自行确认的事实，再输出完整、技术中立的需求理解，明确目标、场景、状态/失败/恢复、范围、保护行为、验收示例、事实/假设/未知和知识影响；随后停在 Default mode 等待用户明确确认。纠正意见会生成一份完整修订结果并再次停止。U2-U5 不因启用了 Dev Flow 而自动获得确认仪式；预期行为仍不明确的 bug 才从 U3 升为 U1。确认业务理解不等于授权依赖、提交、发布、部署或不可逆动作。

## Direct 与 Managed

`direct` 是默认模式，适用于普通修改、有限 bugfix、小功能、小重构、依赖维护、只读审计和一个连贯切片内能完成的专项工作。它不创建 Dev Flow 文件或状态，只要求：

1. 核对真实 Git 根、有效指令、当前行为和用户已有改动；
2. 做一次不落盘的质量校准：结果、事实/假设、影响边界、最小切片和原生验证；
3. 只澄清会改变业务结果、范围、不可逆后果或外部权限的实质歧义；
4. 实现最小连贯变更，先运行聚焦检查，再运行受影响的更广检查；
5. 审阅最终 diff，并如实区分 `PASSED`、`FAILED`、`FLAKY`、`BLOCKED`、`NOT RUN` 和 `WAIVED`。

Direct 不创建 Dev Flow 状态或连续性文档。它优先更新既有架构、产品规则、契约、runbook、用户或运维事实；只有重要行为或理由无法由代码、测试、issue、changelog、ADR 或既有文档保留时，才增加一份轻量 change record。仓库无约定时使用 `docs/change-notes/<slug>.md`，不写命令、hash、agent 活动或逐文件流水。

`managed` 只由连续性和协调需要触发：跨会话、多个可独立交付切片、跨模块/仓库/团队、重大设计取舍，或者用户明确要求长期计划、设计和交接。大功能、大重构和实质迁移默认使用 managed。

风险不会自动把 direct 升级为 managed。一个单文件安全修复可以保持 direct，同时叠加安全控制；一个低风险但持续数月的产品重写应使用 managed。

可用 CLI 查看确定性路由：

```bash
python3 skills/dev-flow/scripts/dev-flow.py route-task \
  --intent change --knowledge-impact current-truth

python3 skills/dev-flow/scripts/dev-flow.py route-task \
  --intent change --multi-session --multi-slice

python3 skills/dev-flow/scripts/dev-flow.py route-task \
  --intent review --risk security
```

## 仓库内业务文档

长期业务工作的文档必须进入拥有该变更的仓库，遵循仓库现有约定。没有约定时使用：

```text
docs/workstreams/<slug>/
├── implementation.md
├── progress.md
├── requirements.md     # 复杂或跨团队业务语义需要独立长期来源时创建
├── design.md           # 只有真实设计取舍时创建
└── decisions.md        # 只有长期决策且仓库无 ADR 位置时创建
```

- `implementation.md`：范围、验收表现、按结果拆分的切片、依赖顺序、影响边界和原生完成证据；不是文件清单或工具调用日志。
- `progress.md`：当前状态、已完成结果、当前切片、下一切片、阻塞和证据限制；只在设计/范围变化、切片完成、阻塞、交接或收尾时更新。
- `requirements.md`：只有复杂或跨团队业务语义无法由原始请求、issue 或既有产品文档长期承载时才创建。
- `design.md`：业务结果、非目标、当前事实、取舍、选定方案、失败/兼容/发布与回滚；只有真实设计不确定性时才写。
- `decisions.md`：上下文、选择、替代方案、后果和状态；优先复用仓库已有 ADR 约定。

初始化命令只创建普通 Git 文档，不创建 `.codex`、packet、manifest、digest、ID 或 current pointer：

```bash
python3 skills/dev-flow/scripts/dev-flow.py init-workstream \
  --root . \
  --slug customer-platform \
  --objective "Deliver the customer platform in reviewable slices"
```

默认只创建 `implementation.md` 和 `progress.md`。需要独立业务语义来源时增加 `--with-requirements`；存在真实设计取舍时增加 `--with-design`；仓库没有 ADR 约定且确有长期决策时增加 `--with-decisions`。

代码、Git、测试、CI、运行时和制品继续拥有技术事实。文档只保留未来维护者真正需要的业务意图、取舍、切片和当前状态；命令输出、bulk 日志、模型 transcript、临时路径和重复 source schema 不进入业务文档。

## 仓库知识与文档体系

`repository-knowledge` 用于显式审计、设计、初始化、重构或检查一整套仓库知识体系，而不是替代普通任务中的就近文档更新。它同时面向人和 agent，区分：

- AGENTS.md 中始终可见的精简路由、命令和边界；
- README 或 `docs/index.md` 中稳定的人类可读组件/知识索引；
- 架构、契约、ADR、runbook、fork 和 workstream 等唯一知识所有者；
- 按任务生成、可替换的代码/仓库地图；
- 由 manifest、测试、lint 和 CI 强制的事实。

配套脚本只读扫描单仓库、manifest 定义的 monorepo，以及包含多个独立 Git 根的开发目录；默认排除构建缓存、依赖 checkout、vendor、评测夹具和生成制品：

```bash
python3 skills/repository-knowledge/scripts/repository_knowledge.py scan --root . --format markdown
python3 skills/repository-knowledge/scripts/repository_knowledge.py plan --root . --format markdown
python3 skills/repository-knowledge/scripts/repository_knowledge.py map --root . --task "修改频道密码兼容逻辑" --format markdown
python3 skills/repository-knowledge/scripts/repository_knowledge.py check --root . --format markdown
```

目录中出现多个 Git 根只证明它是 multi-repository workspace；在建立共享 catalog、跨仓库架构或 program AGENTS.md 前，仍需确认该目录是否拥有正式的产品/项目边界。`bootstrap` 由 Skill 根据经确认的 plan 生成可审阅 diff，扫描脚本不会自动覆盖现有文档或把推断提升为项目政策。

## 风险 Overlay

Overlay 与 direct/managed 正交，只增加暴露风险需要的控制：

| Overlay | 典型触发 | 增量控制 |
|---|---|---|
| Security/privacy | 身份、权限、凭据、不可信输入、隐私/监管数据 | 信任边界、滥用路径、安全测试、敏感数据处理、重大暴露的独立审查 |
| Migration/data | 持久 schema/data、切换、删除、兼容 | 盘点、双向兼容、可恢复执行、观察、restore/rollback、演练 |
| External system | 协议、外部写、分布式状态 | 契约、幂等、超时/重试、对账、sandbox 与真实系统证据分离 |
| Release/delivery | package、签名、部署、发布 | exact target/artifact、provenance、rollback、动作级授权和结果复核 |
| Irreversible | 广泛删除或不可恢复后果 | 精确目标、备份/恢复证据、动作前即时确认 |
| UI/product | 实质工作流或 IA 变化 | 产品意图、完整状态、无障碍、受影响 viewport/device 的渲染证据 |

Overlay 不自动要求 packet、固定文档、独立代理或一整套最大门禁。

## 质量校准与高级能力

2.0 保留一条不产生制品的质量主干。每个任务开始时回答：完成结果是什么、哪些是事实和假设、可能影响哪些业务/信任/数据/兼容/依赖/运维/UI/交付边界、最小连贯切片是什么、什么原生证据最敏感。范围/设计变化、新依赖或外部边界、第一次意外失败、同一症状连续两次错误假设、交付或不可逆动作出现时重新校准。

高级能力在信号出现时介入，而不是常驻主流程：

- 实际委派子代理前使用 `route-agent`，把角色、workload、风险和推理信号映射为 P0-P6 的模型、reasoning effort 和 fork 请求；路由结果不落盘、不生成回执。
- 迁移/混合版本数据、FFI/ABI/unsafe、并发/非确定性、安全/隐私/权限、公共 API/协议、不可逆/数据丢失、冲突证据或连续失败时，主动使用对应专业 Skill；当方法或 oracle 仍不明确时通过 `route-task` 做一次 bounded 方法匹配，只应用能改变决策的 1–3 个步骤，不保存选择记录，也不为取得方法名称而扩张研究。
- 独立审查只用于重大安全/数据/兼容/回滚暴露、重要取舍、冲突证据、共享盲点或仓库明确要求的职责分离。

需要确定性查看高级分支时可使用紧凑输出，避免把完整解释性 envelope 带入模型上下文：

```bash
python3 skills/dev-flow/scripts/dev-flow.py route-task \
  --intent review --risk ffi \
  --method-signal multi-version-coexistence \
  --method-prerequisite repository-facts \
  --compact
```

只读审查本身已经是独立审查所有者，不会仅因同一风险递归创建“审查审查者”。方法选择只运行一次并返回最多三个直接相关的方法、步骤或缺失前提/fallback；不会要求模型读取完整方法池。

`route-task` 在 `review` 意图、显式 `--need review` 或 `--material-exposure` 时加载 `change-review`。仅出现 security、migration、release 或 irreversible 标签不会自动产生独立审查；overlay 本身仍保留对应的领域控制和验证。

核心原则是先使用最简单且足够的能力，再按具体信号增加模型深度、方法或独立上下文。

实施范围同样采用按需收敛：实现/修复默认 `closed`，诊断/评审默认 `bounded`，只有明确要求广泛探索时才进入 `open`。读代码、运行受影响测试和深入推理不会自动授予更宽的写入、依赖、仓库、委派或交付权限；新发现的问题先归类为必要缺陷、必要前置、可选机会或无关项，再决定是否进入当前实现。

方法论不会以“选中了几个方法”作为质量指标。高价值验证、测试、评审和审计场景需要形成一次明确处置：执行已就绪方法、对受阻方法执行 fallback 并保留限制，或因 owner Skill 的原生程序已足够而合理弃用。真正的落地必须改变测试/oracle、反例、状态或兼容模型、评审攻击面、证据矩阵或最终 claim 限制。

子任务模型以闭合度和后果而不是工作量或价格单独决定：P0-P2 分别使用 Luna low/medium/high 处理精确、机械或已确认且有确定性 oracle 的工作；P3-P4 使用 Terra medium/high 处理普通探索、因果分析和常规取舍；P5-P6 使用 Sol high/xhigh 处理开放的跨组件契约和高后果审查/验收；PX Sol max 仅用于显式评估并确认的例外。根上下文不会仅为使用廉价模型而创建子代理。

## 专业 Skills

Dev Flow 主 Skill 只负责模式、风险和最小路由。按真实决策加载聚焦 Skill：

- `repo-context`：真实仓库根、指令、行为、边界和原生控制；
- `requirements-design`：实质业务语义、范围、兼容和设计；
- `product-ux-discovery`：实质 UI/产品工作流、状态和无障碍；
- `systematic-debugging`：复现、竞争假设、最早原因和回归 oracle；
- `architecture-decisions`：边界、所有权、状态、并发、FFI、兼容和性能取舍；
- `dependency-decisions`：新增、更新、移除和供应链影响；
- `verification`：风险驱动的原生验证与诚实证据状态；
- `test-system-engineering`：测试发现、选择、敏感性、隔离、runner 解释和代表性完整性；
- `change-review`：基于当前 source/diff 的独立 finding 验证；
- `delivery-readiness`：动作级交付身份、证据、回滚和授权；
- `company-data-security`：跨 Codex/ChatGPT/普通聊天的敏感数据控制；
- `manage-engineering-profiles`：显式管理偏好/指令资产；
- `repository-knowledge`：显式审计、建立、重构和检查面向人及 agent 的仓库知识体系；
- `dev-flow-maintainer`：显式维护 Dev Flow 自身。

方法池在普通工作中不启用；遇到上述高杠杆风险或方法不确定性时主动做 bounded、非持久化选择。它不参与生命周期门禁。

## Multi-Agent

单代理是默认。只有隔离并行或独立视角的净收益高于协调成本时才委派。每次实际委派先调用 `route-agent` 并使用返回的模型、reasoning effort 与 fork 请求；如果路由后的上下文和协调成本高于独立收益，就留在 root 执行。brief 只需要：目标/结果、相关上下文、写入路径或只读边界、允许的验证/资源、停止条件、返回内容。

不再要求 packet ID、AC/SC/VO、fingerprint、profile 回执、lease epoch、生成报告或 checkpoint。root 按当前 Git diff 集成结果，并重跑受影响检查。

## Hooks 与安全

2.0 不注册 Dev Flow 流程 Hook。普通搜索、编辑、测试、包管理、Bash、代理生命周期、Stop、交付授权和 legacy packet 状态由宿主安全模型、用户指令、Skills 与原生工程系统处理，不再由不完整的命令字符串分类器重复拦截。

`data_security_hook.py` 仍作为独立安全能力，在支持的 prompt/tool 输入输出面阻止或脱敏高置信凭据。个人模式下，可确认的测试凭据先被拒绝；工具输入只有在用户随后提交 session-bound 的一次性随机标记后才可原样重试一次。本地辅助程序不提供 approve 命令。当前 `UserPromptSubmit` 协议不能改写提示，因此工具确认回合只允许随机标记进入模型，原工具密钥不进入该消息；这仍是防误泄露护栏，不是对同一 OS 用户下恶意进程的密码学隔离。它不判断任务流程、需求状态、依赖合理性、测试充分性或用户语义。

## 只读诊断与可选成效观测

统一 doctor 只盘点源码/发布身份、Git、显式提供的安装与加载根、Hook 打包状态、本地缓存规模和可选 outcome 文件；它不清理缓存、不读取凭据，也不会把“已打包”写成“当前账户已激活”：

```bash
python3 skills/dev-flow/scripts/dev-flow.py doctor --plugin-root .
```

个人 dogfood 可显式记录只含枚举和计数的本地 outcome。默认文件为已忽略的 `.codex/dev-flow/outcomes-v1.jsonl`，Unix 上要求 `0600`；它拒绝 Prompt、标题、路径、人员、会话、自由文本和未知字段，也不生成生产力或综合评分：

```bash
python3 skills/dev-flow/scripts/dev-flow.py outcomes record \
  --condition dev-flow --task-shape bounded \
  --outcome completed --verification passed
python3 skills/dev-flow/scripts/dev-flow.py outcomes summary
```

## 2.0 破坏性切换

2.0 不提供 1.x packet、状态、命令、安装布局或工作流的兼容承诺，也不提供自动迁移、升级或回滚路径。旧 `.codex/dev-flow/current` 不得阻断 2.0 的搜索、修改、测试、委派或最终回复；需要保留的历史文件由使用者自行归档。源码中暂时仍存在的旧 reader、validator 或 CLI 只属于未公开内部遗留，不是 2.0 公共接口，可在后续版本直接删除。

## 安装

固定安装当前发布的 RC.4 标签：

```bash
codex plugin marketplace add AldenClark/dev-flow --ref v2.0.0-rc.4
codex plugin add dev-flow@dev-flow
```

正式稳定版发布前，生产性使用仍应显式固定 RC 标签；不要把分支 HEAD 或未打标签的源码当作已发布版本。

## 验证

本地完整验证：

```bash
python3 -W error::ResourceWarning -m unittest discover -s evals -v
python3 evals/run_contract_checks.py
python3 tools/validate_product_state.py --root .
python3 tools/validate_rc5_coverage.py --root . --check-worktree
python3 tools/static_scan_rc4.py --root .
python3 skills/dev-flow/scripts/dev-flow.py validate-methods --root .
python3 skills/dev-flow/scripts/dev-flow.py validate-knowledge --root .
python3 skills/dev-flow/scripts/dev-flow.py check --plugin-root .
python3 skills/dev-flow-maintainer/scripts/validate-suite.py
python3 skills/company-data-security/scripts/doctor.py --plugin-root .
python3 -m compileall -q hooks skills evals tools
git diff --check
```

CI 不再在所有 OS/Python cell 中重复完整套件：一个 semantic job 执行完整语义/结构/产品状态/RC.5 静态追踪检查，机器可读 compatibility inventory 只在运行时、Hook、安装器、档案解析或平台敏感测试变化时启动 Ubuntu/macOS/Windows 与 Python 3.11/3.14 的 focused matrix；旧的 25 次诊断循环已移除。RC 修复期间只跑受影响检查，冻结候选只跑一次完整本地回归；模型指导变化另跑一次受影响案例 smoke。完整 live R4 和新的独立审查保留给稳定版或单独授权评估。模型结果不代表生产力、业务效果或总体质量分数。

发版按变更面分为 R1 standard、R2 runtime、R3 artifact/security、R4 model-semantic。`flow-metrics` 只验证分支激活与负向边界，不衡量生产力或效果。具体边界、命令和 `NOT RUN` 规则见 [docs/releasing.md](docs/releasing.md)。

## 版本和发布状态

- `2.0.0-rc.5` 是当前源码候选，聚焦个人辅助的界面收敛、可诊断性、隐私观测和信任边界；旧候选的 R4 失败已保留，当前修复尚未完成受影响语义 smoke、轻量方法静态审查、最终本地回归、push、tag、安装或发布。
- `v2.0.0-rc.4` 是最近已发布的 convergence-and-operations RC，也是 RC.5 的固定安装回滚标签；其发布包含明确记录的 R4 语义豁免。
- `v2.0.0-rc.2` 是上一 activation-hardening RC，也是 RC.3 的可固定安装回滚标签。
- `v2.0.0-rc.1` 是上一 RC，包含 Default-mode 需求确认、主动高级能力激活、Luna P0-P2、Codex 原生适配和 Flow Activation Coverage。
- `v1.1.2` 是最后一个 1.x 稳定标签；1.1.3 只存在于未发布源码历史，2.0 不提供 1.x 兼容或迁移保证。
- 源码、commit、push、tag、GitHub Release、Marketplace 安装和生产使用是不同状态；只有逐项执行和复核后才能声称完成。

RC.5 的需求、设计、实施拆解和当前证据边界位于 [docs/workstreams/dev-flow-2.0-rc.5](docs/workstreams/dev-flow-2.0-rc.5/)；RC.4 的发布审计保留在 [docs/workstreams/dev-flow-2.0-rc.4](docs/workstreams/dev-flow-2.0-rc.4/)。2.0 基础设计位于 [docs/workstreams/dev-flow-2.0](docs/workstreams/dev-flow-2.0/)，历史版本见 [CHANGELOG.md](CHANGELOG.md)。
