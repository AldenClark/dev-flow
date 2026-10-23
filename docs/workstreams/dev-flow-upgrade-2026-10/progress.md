<!-- dev-flow-workstream-contract: v1 -->
# Dev Flow 整体升级：当前事实与进展

- State: implementation-complete
- Current slice: S4
- Terminal condition: 整体接受后的实现覆盖四方向及精简目标，实际diff与必要证据收口；没有安装/发布或模型收益推断。
- Updated: 2026-10-23 Asia/Shanghai

## Current truth

- Source candidate: `2.1.0`
- Source phase: `source-candidate`; workspace: `development` from `v2.0.3`.
- Published stable/default installation: `v2.0.3`; candidate rollback target: `v2.0.3`. Historical 2.0.3 rollback remains `v2.0.2`.
- Local commit authorized on 2026-10-23; implementation-complete remains distinct from release-qualified.

Delivery state: commit=passed; hosted_ci=not-run; cross_platform=not-run; independent_review=not-run; tag=not-run; artifact=not-run; publication=not-run; isolated_install=not-run.

The commit status records only the authorized local Git action; Git owns its exact identity. Existing scoped reviews and native/behavior evidence remain below, with original failures, skips, rechecks and limits. Final-version hosted CI, cross-platform qualification, cumulative independent release review, tag, artifact, publication and isolated installation are not run for 2.1.0; older release passes and waivers do not transfer.

## 当前本地基线

2026-10-23核查：源码 `/Users/ethan/Repo/dev-flow`，`main`，HEAD `a970b80f3f48f75dad069deeba181faf04d688d8`，开始时工作区干净。`product-state.json`记录源码/稳定2.0.3、工作副本development、公开回退v2.0.2；这是既有交付事实，不是本次候选资格。

桌面应用 `/Applications/ChatGPT.app` 为26.1016.61520/build21421；运行中的内置CLI路径与 `codex --version` 对应0.163.0-alpha.11.1。CLI features输出：code_mode_interrupt/hooks/multi_agent/multi_agent_v2=true，executor_capability_discovery_v2=false；wake_on_agent_messages未列出。CLI配置/默认值不能替代本会话实际能力：本会话已实际使用Code Mode、工具调用、store和子代理，未主动中断或验证晚到自动唤醒。

`codex plugin list --marketplace dev-flow --json`报告2.0.3 installed/enabled；缓存 `/Users/ethan/.codex/plugins/cache/dev-flow/dev-flow/2.0.3`。开始时源码与缓存的156个tracked skills/hooks/plugin manifest文件字节相同、零缺失；下述DLP源码修复后不再声称一致，缓存未修改。当前技能目录和实际读取指向该缓存；每个Hook的批准、实际执行与运行中字节指纹仍不能由此推断。配置中的root模型为gpt-6-astra/ultra，不能当成本turn服务端实际模型证明；已观察派发工具支持策略中的Luna/Sol/Astra ID，P4独立调查按gpt-6.1-sol/medium派发。

## 历史材料恢复与修正

已读交接四入口，并按room_history/saved_conversations原话追溯。关键来源：`room_history.md:768-780`整体升级、`:818-830`撤回仓促候选、`:894-904`已有方法未串好、`:1153-1180`技术思路是探索输入、`:1280-1284`复杂度收益目标。早期用户持续知识/消融诉求见 `saved_conversations.md:3293-3297,3929-3933,5240-5244`；助手随后建议不等于用户全盘接受。

`/Users/ethan/Documents/Codex/2026-10-09/task/phase2-study/whole-version-revision-v2/` 实际存在，含baseline/candidate与25文件candidate.patch。补丁SHA256为 `e68057f95d2190d5d29b8fbc3dfcf81be778ef172aead8f3c208494924964305`，匹配历史末次报告。两个目录的rev-parse均返回a970b80；目录diff读取超时且另一stat读取无结果后停止，故未证明当前目录完整差异等于patch。没有应用或运行旧候选。

在研究根和候选根未恢复原始测试执行日志及独立第16轮记录。`room_history.md:1068-1078`曾汇报复核完成，状态为reported，非本次raw verified。143+39、190+39、83项分属不同修订，不能拼成当前通过。旧v2未明确覆盖随后自主探索与10/13精简目标。

保留撤回：Windows两次清单检查中第一次失败，第二次必要；RC.8总方案并非未交付；S6的较好表现来自2.0.3；自动归档清理与知识演练是构造例，不是完整真实收益证据。

## 最新官方宿主事实

GitHub官方核查到2026-10-22 16:03 UTC：Latest仍是[稳定0.163.0](https://github.com/openai/codex/releases/tag/rust-v0.163.0)，最新预发布为[0.164.0-alpha.12](https://github.com/openai/codex/releases/tag/rust-v0.164.0-alpha.12)。没有由这些上游事实推断桌面已采用。

- [#51835](https://github.com/openai/codex/pull/51835)已稳定；中断结束cell/嵌套调用，store保留。取消不回滚外部副作用。
- [#54619](https://github.com/openai/codex/pull/54619)在alpha.12、不在stable；内容指纹参与Hook授权，脚本/升级/回滚需重新确认。排除__pycache__/.venv/*.pyc/*.egg-info，不是所有cache均排除。
- [#54961](https://github.com/openai/codex/pull/54961)在alpha.12，UnderDevelopment/default=false；晚到root消息只处理一次，用户中断/Plan/child不自动唤醒。
- [#55144](https://github.com/openai/codex/pull/55144)在alpha.12、不在stable；Pre/PostModelRequest每attempt观测，不能veto或改写上下文，同步post可延迟工具派发。未计划新增这些Hook。
- [#52241](https://github.com/openai/codex/pull/52241)已稳定，fresh/fork children的能力来源/禁用插件继承与历史复制不同；[#52659](https://github.com/openai/codex/pull/52659)虽已合入stable，对应context默认值flag仍默认false。
- 权限恢复[#53150](https://github.com/openai/codex/pull/53150)/[#53419](https://github.com/openai/codex/pull/53419)已稳定，当前策略/显式覆盖优先，不能从旧授权提升权限。
- partial-write #54505、thread/sample #55339、V2来源与发现 #55330/#55957/#55968、cleanup #56044在alpha.12；thread/sample未运行。network review domains [#56154](https://github.com/openai/codex/pull/56154)仅主线合并，与alpha.12仍diverged（ahead1/behind3）。

以上是上游源码/发布证据；本机真正中断、内容重新授权、晚到wake、模型Hook时序、resume沙箱恢复均NOT RUN。不用host fixture宣称验证上游本体。

## 本地执行证据

- 首次 `python3 skills/dev-flow/scripts/dev-flow.py route-agent --help` 在导入阶段失败：`ModuleNotFoundError: tomllib`。默认/usr/bin/python3不适用；已存在python3.13可运行，未安装依赖或改环境。不是产品测试断言失败。
- `python3.13 tools/validate_product_state.py --root .`：valid；仅结构一致性，无新发布/安装证明。
- 实施前基线源码运行 `route-task --intent design --requirement-class semantic-change --compact`：`publish-understanding-and-continue`，确认现版策略可达。
- `python3.13 -m unittest -v` 的6个已有定向测试通过：`evals.test_dev_flow_v2.RoutingTests` 下 semantic_change_stops_only_for_a_surviving_user_choice、established_defect_and_mechanical_work_skip_confirmation、read_only_intents_do_not_acquire_a_requirements_confirmation、settled_u1_method_baseline_tracks_design_permission；`RuntimeGuidanceContractTests` 下 evidence_freshness_distinguishes_affected_and_unrelated_edits、continuation_contract_has_semantic_checkpoint_and_negative_trigger（名称均带test_前缀）。这些证明实施前基线契约及邻接负例，不证明升级收益，也不消除与新需求的冲突。
- 当前本轮读取资料时出现secret_assignment脱敏/输出大小限制提示；逐事件分类与修复见下，不按类别摘要直接判误报。没有关闭安全Hook或重取原始敏感内容绕过限制。

## 近期会话调查

用户追加后默认窗口2026-10-09至10-23，先读会话metadata和有相关目标的root。该日期创建目录内，Aegir/PushGo/dev-flow共7个root（含本次）和546个子会话；未全读子会话。工具最近50条列表补充发现；这不是全量近期活跃会话覆盖，旧创建而近期更新的会话可能遗漏。

调查分DLP因果与流程正反例两条，保留用户授权/后续修正、实际加载、首工具结果；不凭助手总结归因，不按命中次数算失败率。4个有判别力的root已读，重点结果如下（时间UTC）：

| 观察 | 原始来源与证据 | 对升级的意义 |
|---|---|---|
| 达到主要收益后继续精细清理 | [审查全项目过度设计](codex://threads/01a132e9-5c88-7412-96c8-e7899e529acf)，10/21 13:17–13:45，turn `01a15e9b-d141-71e0-bdcd-3bf65b54dd22`；加载2.0.3命令 `exec-36720186-b0c7-4f01-b2eb-46bf832da94c` exit0；首批25项后又删除695个xcresult原件、17个clone和18个日志压缩；用户明确“做得有些过了”“控制一下收敛范围” | 初始请求包括过期数据/测试记录，不能诬称全部越权；缺的是足够收益与剩余工作的停止判断 |
| 纠正传播有效 | 同轮第二次收口消息之后无新工具动作，只有最终回复 | 保留现有纠正传播；不能把前期过深写成从不遵从用户纠正 |
| 保留失败和环境差别 | 同线程10/19 04:26–05:10，turn `01a15269-811a-7493-bbb6-96933e86727a`；实际加载dev-flow/debugging/test-system；原设备15PASS/1FAIL/19NOT RUN没有被API37单方法成功覆盖，最后仍BLOCKED | 现版验证规则有有效执行正例；用户给了详细prompt，不能证明普通短需求下自然触发 |
| 观察内容优先于exit和文件存在 | 同轮 `exec-585174ce-bb67-497b-b0d9-40018f968123` 发现导出json/xml仅41字节，实际是run-as unknown-package错误 | 应保留敏感oracle；多一个hash/收据不能修复错误观察对象 |
| 有界清理也能完成目标 | [清理 PushGo 缓存与历史日志](codex://threads/01a15704-c92d-74e1-9993-e1206f6a44db)，10/20 01:55–01:57，关闭句柄后仅清6.07GiB再生产物、保留证据 | 无本轮DevFlow读取证据，作为对照，不归功插件 |
| 准确限制交付声明 | [在 Parallels Windows 11 安装应用](codex://threads/01a15484-0db6-7b10-8fc8-acf47fc4832f)，10/19 14:15–14:38：UI运行、service失败并清理失败注册；最终明确Debug界面不等于隧道/MSI/签名 | 无本轮DevFlow加载证据，属于有效结果表达对照 |

[收敛 Aegir 磁盘占用](codex://threads/01a151be-6070-7201-9428-c6bb037c09d3)的最新10/22轮明确新增清理过期证据授权，不能用更早保护要求认定该轮越权。Aegir近期协议验收又有用户明确要求多平台完整链条与资源/并发验证，不能仅凭范围大、耗时长归入过度验证。没有取得新的干净上下文知识续接实效证据，保留not_observed。

## DLP因果与实际修复

近期102个会话文件含DLP提示，包含fork继承/重复，不是102次独立事件或误报率。只归类有上下文的事件：

- **确证误报**：本线程2026-10-22 15:59:46 UTC，原生回执JSONL行55，对应工具文本行56（子输出第169行）已有固定脱敏标记 `[REDACTED_SECRET]`。本地等值核验和合成API均确认它被 `C4-SENSITIVE-ASSIGNMENT` 命中；不是恢复秘密值。缓存2.0.3来源和当前相关三文件字节一致在修前已核对。
- **不确定**：本线程16:04:08 UTC行191，历史patch输出已截断，只能看到secret_assignment+limit摘要，不能倒推为误报。
- **保守策略摩擦**：PushGo子会话 `01a13d66-cb7c-7770-a1bb-ab5b985a070d`，10/15 02:41:07 UTC行383，测试字面量命中。测试用途不自动豁免，不认定为缺陷。
- **大小边界**：read_thread大结果超过inspection limit，与assignment matcher分开；不调整上限来隐藏原因。

根因：`_PLACEHOLDER_RE`未识别已有固定方括号标记；高置信赋值规则命中后，Hook的4000字符可见上下文上限放大了影响。修复仅加完整标记分支，继续fullmatch，不豁免任意方括号内容/含redacted的字符串；基线仅更新engine哈希。没有改Hook、安装或权限。Markdown反引号包裹引用是另一个合成候选，未作无证据泛化修复。

先加2个测试，修前4个引擎输入与短/长Hook报告共6个子例FAIL；一行规则修复后2测试PASS。测试同时覆盖marker拼接token、相近非marker值、同报告嵌套token，真实秘密形态继续拦截。随后 `python3.13 -m unittest evals.test_dlp_engine_audit evals.test_dlp_hook_audit evals.test_data_security`：93 tests，OK。数据安全doctor：required_failures=0，live/account项仍not_observed。独立P4安全复核无实质发现，未重复测试。

S3结束时文档与局部源码检查（不覆盖后续S2改动）：`check-workstream --check-worktree --strict`、`validate-knowledge`、`validate-suite.py`、plugin `check`、3个变化Python文件的compileall和 `git diff --check`均通过。product-state结构检查复用上文未失效结果。未运行完整发行回归、hosted/platform矩阵、真实模型对照、日常安装或现场Hook重载；本次不作release-readiness声明。

调查代理两次直接包装Hook合成探针被外层PreToolUse阻止、未执行，已停止该辅助方式。后来通过现有unittest harness执行的上述本地Hook子进程测试有实际结果；它不等于日常宿主安装执行。首失败保留，未用修后结果覆盖。

## 初批整体候选实际落点与比较边界

用户于2026-10-23通过异步问题 call_d45a8dbdc2814317bac7148a4a99327a 明确回复“接受 B，按整体方案分批实施”。四方向与精简目标已在同一工作副本串联，未应用旧候选。下面是基于既有真实输入的源码契约对照，不是新增模型重放或效果评测：

| 已有输入/失败机制 | 2.0.3强基线与断点 | 本次实际落点和可声明边界 |
|---|---|---|
| 目标/想法需要自主技术探索；重要首次功能需整体确认 | 已有需求与架构owner，但清楚的U1直接放行，工具不可用时禁止文字选项 | requirements/kernel/architecture/交互契约串联；CLI分别报告业务范围和实施待确认；前后确定性分支与邻接小修负例已检查 |
| 保存状态的展示精简与恢复入口含义不同 | 已有知识owner，但current truth容易混合要求和实现 | knowledge-topology区分原话、接受子集、当前要求、差额、局部替代与回滚；methodology日常入口给出贯穿示例，明确它是构造说明，非真实续接效果 |
| 验证减负与错误观察对象 | 现版真实案例能保留首失败；超量验证不是一概规则缺失 | verification/quality要求追加检查的风险、改变的决定及停止条件；复用有效证据，exit0/文件存在不能替代正确观察 |
| 精简任务中辅助工作继续扩大 | 近期已加载2.0.3案例达到主收益后继续清理，用户要求收敛 | architecture/change-review及蓝红brief保留机制净收益评价；必要不变量与额外保证分开，旁支缺陷先证明是否阻断目标 |
| 方法名被提到但下游不消费 | 方法池和风险选择已存在 | kernel、orchestration、worker/test/reviewer提示交接实际洞见和被改变的假设/断言；不增加默认代理、方法台账或强制消融 |
| 固定脱敏标记被再当秘密 | 真实本会话回执与合成反例已确认 | 一行fullmatch分支、对应基线及2项回归；真实秘密形态/相近值负对照保留，其他DLP摩擦不宣称修复 |

初批无新增依赖、Hook、审批存储或CLI flag；后续最小续修增加的一个诊断flag及v3语义见末节。保留现有公开命令、参数和别名；初批路由语义从rc8.v1改为v2，compact保留实施停顿和非授权声明，旧route不能直接复用。`product-state.json`只更新development工作区的workstream指向；2.0.3发布、稳定、回退及交付记录未改，新发行版本未指定。普通静态入口总量13456字节，低于既有13500上限（基线13469），未提高预算；这仅是上下文成本指标，不是效果指标。

## 初批S2/S4验证与首失败

- 新增CLI边界测试在修前出现1失败及3个compact缺字段错误；修后通过。重要首次功能待确认时设计可继续、实施不可放行；confirmed/waived仍明确未经CLI验证，user-choice-open不能与其组合。旧compact语义不复用、方法前提不依赖首次实施确认、小修/只读负例均有覆盖。
- 独立P4清洁上下文审查发现managed路由仍写“确认后才能design.md”，与新边界冲突。新增现有用例内的断言先失败，再改成settled-business-scope；定向测试通过，独立复核关闭唯一实质发现。审查只证明源码/契约一致性，不是模型行为收益。
- 首次分组回归暴露系统Python3.9的`tomllib`缺失：即便主命令为3.13，部分既有测试仍用`python3`启动子进程。之后仅在测试进程PATH前置已有3.13目录，不改全局配置、不安装依赖。另有2处旧措辞断言和上下文预算超限，已通过语义对齐及删减重复指导修复；32项受影响检查通过。子代理的同类3.9首次失败也保留，分别使用现有3.13/3.14验证。
- 一次整体原生回归：`PATH=<已有Python3.13 bin>:$PATH python3 -W error::ResourceWarning -m unittest discover -s evals -v`，813项、67.200秒；首次805通过、1项native-Windows-only跳过、7项失败。首次原生日志：[native-regression-first.log](/tmp/dev-flow-upgrade-20261023/native-regression-first.log)。7项均定位为文案契约/入口引用的兼容问题，包括遗漏main skill的Default/user-interaction引用；未用重试掩盖失败或放宽原本应保护的语义；首次确认语义的既有断言按已接受的新需求明确更新。
- 修复后只运行这7项及2项context-budget检查：9项通过，日志[affected-recheck.log](/tmp/dev-flow-upgrade-20261023/affected-recheck.log)。其余805项未受这些语义等价文案修正影响，复用原结果，不重复整套。DLP93项定向证据保留，且被整套覆盖；不把次数相加当独立样本。
- product-state、knowledge、suite、plugin、methods、39项结构contracts、data-security doctor通过；doctor仍保留manual/live未观察门。Python编译及diff空白检查通过。最终文档结构检查见下方HC2；之后没有修改功能代码。

可声明的是本地源码契约、确定性路由/响应校验、合成与原生单元回归，以及下文记录的3案例/8次启动限定真实任务行为观察。该观察不覆盖真实用户多轮澄清、重要新功能首次实施前确认、长期收益、host中断/唤醒/Hook授权实际运行、hosted跨平台或候选安装资格；这些仍NOT RUN或not_observed。原有发布事实不覆盖本候选。

## 初批采用与回退

初批本地实施收口时尚未提交；其后已按用户授权形成下文记录的2.1.0本地提交，未推送、发布、日常插件安装或改变账户/安全配置。迁移及宿主限制见[design.md](design.md#迁移与回退)。限定行为观察仅支持其报告范围，不提供发布或安装资格；未来这些动作仍需按所需声明补足相应证据并单独取得授权，不是本次候选实现验收的前置条件。后续新增模型比较先明确预算与目的。回退只选择性撤销本次diff并恢复匹配的路由代码/语义，不reset工作区、不覆盖后来用户改动；保留已接受决定和原始研究证据。回滚安装遇内容指纹变化仍按实际宿主重新授权。

| ID | Condition | Gate | Status | Closure/decision |
|---|---|---|---|---|
| HC1 | 整体方向与首次重要功能理解已明确接受 | implementation | passed | 2026-10-23用户明确接受B；仅本地候选，不含发布/安装/新增模型评测 |
| HC2 | 四方向及精简目标的实际diff、必要正负例和交接一致 | implementation | passed | 本地回归及受影响复验、独立审查修复复核、validators和工作流结构收口；不推断模型收益 |
| HC3 | 已证实固定脱敏标记误报修复及秘密检测负例保留 | implementation | passed | 首失败保留；2个新回归、93项定向检查、doctor、独立复核；未修所有未分类摩擦 |
| HC4 | 未覆盖的用户确认、宿主和平台资格按实际采用声明具备 | qualification | not-run | 3案例8次限定行为观察已完成，完整首次确认、宿主及平台资格未覆盖；不作为本次实现验收前置条件，implementation-complete不是release-qualified |

Active convergence checkpoint: 未出现同一辅助机制两次无进展修理。历史目录diff不继续追绿；首次失败保留，语义等价文案修正只重验受影响项；不新增证明包或持续扩展检查。

## 2026-10-23 最小范围续修与真实案例复核

用户明确要求先修上一轮评估第1、3、4项，再用已有真实案例复核第2、5、6项，控制收敛范围，暂不提交、发布或安装。本轮沿用本工作流；不扩展平台、评测预算或日常宿主。

### 第1、3、4项实际修复

- CLI：风险仍可作为能力选择信号，但只有调用者提供的有效 `--repo-fact` 才推导 `repository-facts` 前提。U1只表达语义深度；单个诊断标志 `--first-important-implementation` 表达重要新功能首次实施，兼容旧 `large-feature` 输入。普通U1和单纯design不自动要求整体确认；未决业务选择仍阻止依赖它的工作，已接受同范围内容仍通过既有确认输入复用。flag不证明同意或授予权限。compact、输入纠错/别名、路由basis同步，语义升v3拒绝复用v2；README和设计投影同步。
- 知识：本地相对Markdown交接结果附带本机可读性、Git跟踪范围、实际核对的HEAD SHA及当前正文在该版本的可取得性。只有正文与该SHA的blob一致才报告available；未跟踪且HEAD不存在为not-available，正文已变、符号链接或取证不足为unknown。结果为信息，不把未跟踪文档升级成错误或要求提交。缓存每个目标的检查，沿用2MiB读取边界；Skill只补一句交付范围解释，没有新命令、文件或台账。
- DLP：完整简单的未加引号相对文档链接 `[configuration](docs/configuration.md)` 不再作为秘密字面赋值；仅覆盖小写简单label和docs下的Markdown路径。任意括号、外部/畸形链接、引号及结构化秘密字面量继续检测，高置信秘密在label、路径或相邻位置继续扫描。长安全报告可见；保持Hook上限及已有完整脱敏标记修复。未据此泛化到所有Markdown格式。

首失败与受影响检查：CLI三个新增/改写行为用例修前出现5个失败子例（包含新flag尚未支持）；日志 `/tmp/dev-flow-upgrade-20261023/followup/cli-first.log`。修后这3项通过。CLI/公开入口/增量路由三个受影响模块运行125项，首次122通过、3失败；失败为compact字段集合、design旧停顿预期及全参数纠错输入遗漏新flag。按本次明确语义更新后只重验这3项，均通过；日志 `cli-affected.log`、`cli-recheck.log`。没有重跑125项。

DLP修前合成输入确实命中C4-SENSITIVE-ASSIGNMENT；修后engine/hook两模块51项通过，保留秘密负例。知识原15项通过；最后SHA绑定、缓存及链接祖先修正后仅重验3项相关知识用例，并补跑受引擎影响的44项data-security用例，合计47项通过。先前整套813项的无关结果复用，不把重叠次数当独立样本。

### 第2、5、6项已有真实案例的定向结论

| 项目与实际来源 | 因果核对及本次处置 | 证据边界/停止条件 |
|---|---|---|
| 第2项：Aegir真实协议验收，turn `01a161d1-5ffa-7ae1-8795-9ce0f70e1a26` | 原始JSONL行159579明确六平台三协议授权，159586读缓存2.0.3；不能按规模判过测。行173227设备status已passed，173260的success_contract却无条件要求timeout_producer_fence_observed；173291纠正这个正常/超时分支错位，173591/173739复用8路结果并补16/32。当前候选的新增检查价值/停止和额外保证原则已有对应落点，本轮不加同义规则、不改Aegir工程。 | 是旧版实际执行负例及纠正正例，不能认领为候选收益；保持超时终止保护与未闭环缺陷，不因正常路径通过覆盖旧失败。因果边界已清楚，停止扩样本。 |
| 第5项：本次升级的真实多目标请求与接受B | 对照原请求消息01a16456-31da-7c60-8762-d5f52ad46d1f、明确接受B和本工作流design/implementation：四方向及贯穿精简目标先共同定案，内部S1–S4只划分执行，未用单点试用代替整体版本。现有lifecycle的完整目标复核和dependency-aware outcomes已覆盖；未找到需再改开头的具体遗漏。 | 是本次实际计划/确认链的范围证据；不是独立新任务长期接手效果。不为一个未发生的缩范围假设继续改规则。 |
| 第6项：S4/S5/S6历史复盘、近期交付/诊断正例和本轮首失败 | 历史S4确有局部5文件扩成累计234文件验收，但保留真实链路发现；S5体现精简目标滑向正确性，S6现版2.0.3已有改进，不能给候选计收益。近期上传会话01a15d87中push报错后核对远端ref；耗电01a16167中Batt/AC条件不同，未把循环次数变化当耗电改善。静态文案断言只承担导航/必要概念缺失检查；本轮新增CLI、知识、DLP断言检验可观察输出和邻接负例，不再追加同义措辞断言。 | 采用已有证据区分错误条件、有效执行、宿主限制和收益未知。不重开构造任务/付费比较，不删现有必要静态检查；真实候选全链效果仍not_observed。 |

Aegir原始记录仅窄读 `/Users/ethan/.codex/sessions/2026/10/12/rollout-2026-10-12T19-39-29-01a12fe9-2121-7741-a337-87f83e278844.jsonl` 已确定行；其他近期证据沿用上一轮已核验的原始root。本次未新扫全量历史。无新依赖、默认代理、审批存储、Hook或持续观测层。

续修独立审查发现一个相邻DLP边界：assignment捕获在空格前截断多词label，短label测试又因低于置信长度阈值碰巧通过。补入 `configuration reference` 和长Hook报告后2项均先失败；改为在原文匹配完整链接、校验结束边界，任意追加值仍检测。只重验这2项，均通过，独立复核关闭该发现；未重跑51项。日志 `dlp-multiword-first.log`、`dlp-multiword-recheck.log`。引擎基线SHA已同步并校验与当前字节相符。

39项contracts、知识及suite validators通过；data-security doctor在末次仅相邻链接解析修正之前required_failures=0、manual/live门仍未观察，随后仅重验引擎SHA绑定和相关2项行为，不冒充实际宿主Hook执行。变化Python文件编译及git diff --check通过。product-state、methods及plugin结构未再变化，复用初批未失效检查；未重跑完整原生/发布套件。最终strict工作流结构回执保存在 `/tmp/dev-flow-upgrade-20261023/followup/workstream.json`。

本轮第1、3、4项本地修复和第2、5、6项已有案例复核完成。实施边界保持不变，未修改其他项目、提交、发布、安装或新增模型评测；部署、宿主加载、真实模型收益与长期接手效果仍NOT RUN/not_observed。已关闭独立审查发现并停止追加辅助修理。

## 2026-10-23 已授权的限定真实任务行为观察

用户确认3个现有案例、最多8次启动、24分钟子任务预算，要求不重试、不追加、完成后报告差异/用量/局限。实际串行8次全部完成，观察用时722.4秒（12分02.4秒），每项未达3分钟，无中断、重试、后代或额外裁判模型。实际模型/effort均GPT-6.1 Sol medium，67次底层响应；8不表示底层调用次数或金额硬上限。此前确定性测试未重跑，源码/指导未修改。

S2两版均查到既有IPC/命令、区分新旧选择路径与发布/热应用/重启；候选更显式区分目标和候选机制。S1两版均仅改既有requirements.md，新上下文不读前任回复/原始输入也能恢复意图、实现证据边界及未决选择。S5两版均保留总复杂度目标、比较替代职责、未将旁支bug自动前置；但都倾向局部等价首批，候选P1局部/P2机制级排序未证明更优。基线S1/S5各出现一次缺失的交互引用路径，随后自行纠正，候选未出现同类误读。整体未观察到实质回退，也没有足够证据证明整体收益或用量优势。

8个子任务合计输入3,336,845 tokens（缓存输入3,096,320）、输出23,700，总3,360,545；按原生response_id去重并与thread总计核对。协调/报告另有时间戳快照，不包含最终回复后的用量，金额未观察。原始用量、冻结身份、工具轨迹与最终对照见[本轮研究报告](/Users/ethan/Documents/Codex/2026-10-23/dev-flow-behavior-0751/SUMMARY.md)。两个政策及只读输入副本和正式源字节核对无变化；只在两个研究副本编辑需求文档。此后本工作流仅追加这段执行事实。

限制：每臂每案例一次、已知案例/共同边界提示、观察者非盲；S2部分历史源码，S1仅文档和本地接手，S5无历史完整源码。没有真实用户多轮澄清/重要首次编码确认、应用实现、运行/性能、宿主Hook或跨环境长期知识证据。冻结候选未包含后续协调指导措辞修订（当前文件与冻结副本SHA-256不同）；该修订不属于本次观察。旧qualification门仍not-run；限定行为观察完成不等于发布资格。达到预定准入上限后已停止，不扩展规则/实验，也未暂存、提交、推送、发布或安装。

## 2026-10-23 协调开销的最小指导修订

用户明确接受仅调整现有协调指导，要求替换/合并原文、保留预算/授权/证据检查，不加脚本、台账或管理层，不追加评测或重跑已有测试。已在multi-agent-v2-orchestration.md合并未变路由复用与逐次派发核对、精简活跃上下文、按通知/实际截止点等待、完成时必要边界核对及结束时一次完整汇总；用量报告明确父/子、缓存/未缓存输入、输出和采集截止。没有新增运行机制或效果声明。本轮仅做改动文档的diff/空白/既有链接与strict工作流结构检查，未重跑测试、启动模型任务、暂存、提交、推送、发布或安装。

## 2026-10-23 版本与本地提交收口

用户在整体候选收口后明确指定版本2.1.0，授权将本次候选整理为本地提交，排除无关改动；禁止追加评测、重跑测试、推送、发布和安装。已同步插件manifest、canonical product-state、README、changelog、发行说明/构建示例及workflow默认版本。保留原工作流路径和实施目标；源码phase为source-candidate，workspace仍development，published stable仍2.0.3，默认安装仍固定v2.0.3。本段是此前“不提交/版本待定”阶段的后续授权与当前状态，不改写历史观察。

本地提交仅纳入本次候选源码、契约、既有测试用例、文档与版本投影；原始会话、外部研究副本、临时日志和个人配置不纳入。此前已有的确定性/原生验证、受影响复查、有限独立审查及3案例8任务观察继续按其实际字节和范围复用；未重跑完整套件，不把版本更新视作新验证。协调指导的节省效果、实际宿主/Hook加载、完整用户旅程、跨环境长期交接、托管平台、制品、发布与安装仍NOT RUN/not_observed。仅核对版本/文档结构与Git暂存范围；这不是release-readiness或模型收益声明。

版本投影/文档结构首次检查保留在 `/tmp/dev-flow-2.1.0-product-state.json` 与 `/tmp/dev-flow-2.1.0-workstream.json`：README历史版本表述被识别成第二个当前发布投影，S4尚未列入新授权的manifest/workflow版本路径。已只调整该表述及精确写入范围；随后只复核这两项结构检查与diff空白，不运行测试或评测。

## 2026-10-23 独立审查后的候选实现收尾

起点核对：HEAD为审查基线 `5d559b0f5f87b09e7ca6d87a952ded8f6b3ab941`，工作树干净，无后续修复可复用。本轮只修改协调reference、4个既有测试文件与本工作流design/progress，未改CLI实现、版本/交付状态、用户明确waiver设计或宿主集成边界；本轮修复按后续用户明确授权整理为单一本地提交，版本保持2.1.0；此提交步骤不追加评测或重跑测试，不推送、发布或安装。不要求发布或安装作为实现验收前提。

协调约束现在明确：某次派发必须成功返回有效、非空child identity，取得前不得等待该子任务或轮询其状态；创建失败、缺少身份或结果不确定时先按既有失败/恢复规则核对实际dispatch/host状态，保留首失败，不假装已启动、不直接盲重试。空接收者/agent state不能算委派，不把本机执行冒称child结果；根代理在集成或下游使用前核对实际写入、当前Git/diff和受影响证据，child报告不能证明集成通过。route-agent的model/effort/fork仍按返回值使用，route-task维持无状态诊断定位，不增加门禁或状态机。

首失败：审查点对应的rc3、quality-practices、scripts三个既有用例均复现旧精确文案失败；直接消费者test_agent_dispatch还复现第四个旧措辞失败。新增identity契约用例在文档修前4个子例失败，暴露有效身份、前置等待限制及不确定派发恢复缺失。分别保留 `first-contract-failures.log`、`dispatch-contract-first.log` 与 `identity-before-fix.log`，路径均在 `/tmp/dev-flow-2.1.0-review-closeout/`。未删除必要语义断言；改为关键主语/否定/时序条款匹配，负对照确认去掉有效身份、禁止等待、失败不算启动、先恢复再重试、路由model/effort/fork或报告不能证明集成时会被识别。这只证明书面契约的敏感性，不是宿主执行或真实模型行为证明。

定向验证：`python3.13 -m unittest -v`显式运行4个原失败用例、新identity用例、host-inventory/dispatch-readiness CLI用例、routine direct/packet-free CLI用例和correction/late-child恢复用例，共8项通过（0.142秒）；完整名称与结果见 `/tmp/dev-flow-2.1.0-review-closeout/targeted-final.log`。未重跑全套、未追加模型对照；此前未受影响的源码/原生证据复用。

已先读原始SUMMARY并核对冻结协调副本：3案例/8次启动完成、两版主要判据均达到、候选优势有限；每臂每案例一次、观察者知晓版本。重要首次功能的真实用户确认未覆盖，冻结副本没有后续compact-context等协调措辞，本次补回的identity约束亦未经过该行为对照。design与前文概括性NOT RUN已同步为这个限定结论；不把已完成观察抹成未执行，也不推断整体收益。宿主实际执行、完整用户旅程、长期/跨环境效果和发布/安装资格仍未验证；用户waiver及Codex #56234的宿主遥测顺序不在本次修复范围，未作为候选安全缺陷修补。

## 2026-10-23 2.1.0 发布准备与本次明确豁免

在本地收尾提交 `7315ddb1cff4a58651f804969271a996e626cdec` 后，用户要求完成2.1.0发布，随后明确选择“允许原生／CI，明确豁免本次未覆盖的模型旅程”。这仅解除本次最终原生与托管验证限制，授权必要的提交、推送、制品、标签及公开发布；未覆盖的稳定功能旅程按本次明确决定记WAIVED，不继承旧版豁免、不计PASS、不启动新付费模型对照或裁判。日常插件不安装或切换；实际宿主、完整真实确认、长期收益仍未观察。

对v2.0.3（b5951234）至7315ddb的累计静态独立审查完成：traceability、影响图、示例契约、功能交互、黑白盒oracle及假设/premortem六种视角各有源码检查结论，未发现已证实的实质缺陷。检查为静态/有界，不代替原生、托管、制品或安装证据。

最终本地原生全套只运行一次：822项，69.428秒；首次820通过、1项native-Windows-only跳过、1项失败，原始日志保留。失败来自FLOW-AMBIGUOUS-DEFECT-UPGRADES-TO-U1的旧expect仍把普通U1歧义当成首次重要功能确认。按已接受契约仅改该fixture，新增confirmation_required/first_important_implementation为false及implementation_allowed仍false的断言；路由实现未改，未决业务选择继续阻止依赖设计和实施。目录匹配、故意错误预期负对照及相关既有路由用例3项复查通过（1.349秒）；未重跑本地全套。有效的820项及既有控制证据复用，最终精确SHA的托管全套另行观察。初始测试准备曾遗漏uv解释器prefix/bin，尚未启动测试；核对空回执目录后改用本机已有3.13目录，只设置该子进程PATH，未安装依赖或改全局配置。

product-state、39项contracts、methods、knowledge、plugin、suite、data-security doctor、RC5 coverage与RC4静态扫描均通过；doctor人工/live门保持未观察。发布材料、原始native-first.log、activation-recheck.log、原生调用身份及独立审查范围保存在 `/Users/ethan/Documents/Codex/2026-10-23/dev-flow-2.1.0-release-iijj7rx5/`。先前7315ddb本地源码制品保留为已失效候选证据，不用于最终发布；新的精确SHA、托管平台、制品/证明及公开结果只按后续实际回执更新。

首轮精确SHA托管CI（259d55a，[39887910894](https://github.com/AldenClark/dev-flow/actions/runs/39887910894)）保留失败：Ubuntu语义全套、macOS 3.11/3.14及Ubuntu 3.11兼容通过；Windows 3.11/3.14均在同一知识交接测试失败，各361项、1失败/4跳过。原测试用write_text在Windows产生CRLF，Git归一化的HEAD是LF；严格逐字节契约下unknown正确，原测试却无条件期待available，属于夹具/oracle假设。临时仓库core.autocrlf=true已复现这个字节差异和相同unknown结果，未改真实仓库或全局Git配置。只改该用例：正例显式写LF并先核对HEAD blob与工作字节相同，再加纯CRLF差异必须unknown的负例，原本正文编辑unknown和未跟踪not-available负例保留。默认及autocrlf=true两个定向运行各1项通过（0.211/0.200秒）；生产实现不改，本地全套不重跑。原始托管失败、字节复现及定向结果保存在同一发布证据目录；后续新SHA托管结果单独记录，不重命名旧失败。
