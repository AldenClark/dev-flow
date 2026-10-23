<!-- dev-flow-workstream-contract: v1 -->
# Dev Flow 整体升级：实施边界

> Status: implemented in the source-candidate worktree for `2.1.0`; local commit only, not release-qualified.

## 目标与来源

本次是同一整体版本目标下的研究、设计竞争、验证和分批实施：需求澄清与业务/技术双层回述、风险相称的验证、意图与决定传承、已有方法的实际使用。贯穿评价标准是实际收益和复杂度成本；精简任务不得自动变成可靠性补齐任务。

最高来源是[本次用户请求及后续修正](codex://threads/01a16456-214a-7e82-8075-763c5eb5bb10)。原始请求消息 `01a16456-31da-7c60-8762-d5f52ad46d1f`；追加近期本地会话与 DLP 调查消息 `01a1645d-64b9-77f2-bdbc-7d302b795408`。历史交接包位于 `/Users/ethan/Downloads/DevFlow_Upgrade_Handoff`，仅作可追溯证据，不授予今天的动作权限。

## 范围与保护

- 已授权：当前工作副本内研究、编辑、必要本地测试；只读调查相关近期本地会话与历史研究材料。
- 重要新功能首次实施前，展示整体理解与关键技术影响，取得明确确认；只重开实质变化的决定。局部回答、沉默、诊断字段不代替整体接受。
- 不覆盖用户改动，不应用旧候选补丁，不编辑其他项目，不修改日常插件安装、账户、授权或安全设置。2026-10-23追加授权仅将本次候选更新为2.1.0并整理为本地提交；不推送、打标签、发布、部署或安装，不追加评测或重跑测试。
- 旧模型实验额度不继承。额外批量模型评测或裁判调用须先给有界目的与预算并单独确认；当前会话研究、正常独立审查和静态测试继续。
- 保留现有 GPT 模型路由、原生验证能力与必要安全保护。整体候选收口后，用户明确指定源码版本为2.1.0；版本号不代表发布资格。

## 分批顺序

| Slice | Outcome | Write prefixes | Protected paths | Evidence | Status | Decision |
|---|---|---|---|---|---|---|
| S1 | 事实、历史原话、近期会话、竞争方案与代表输入对齐 | `docs/workstreams/dev-flow-upgrade-2026-10/`, `docs/index.md` | `governance/product-state.json`, `hooks/`, `skills/` | 当前源码/宿主观察、首失败、来源与差距图 | complete | 事实与方案已具体化，用户2026-10-23明确接受B |
| S2 | 在接受方向下串联四方向、目标保持和诊断语义 | `skills/`, `governance/`, `evals/`, `README.md`, `CHANGELOG.md`, `docs/` | `hooks/` | 直接触发、邻接负例、CLI兼容、方法与知识交接 | complete | B已接受；只对新的重大业务或权限变化重新确认 |
| S3 | 修复已证实的DLP误报并保留秘密检测负对照 | `skills/company-data-security/`, `hooks/`, `evals/`, `docs/workstreams/dev-flow-upgrade-2026-10/` | `.codex-plugin/` | 真实事件的最小合成复现、首失败与受影响回归 | complete | 完整脱敏标记误报已窄修并经独立复核，不宣称全部DLP摩擦修复 |
| S4 | 整体diff、必要回归、宿主限制、迁移回退与授权版本/提交收口 | `docs/`, `governance/`, `README.md`, `CHANGELOG.md`, `.codex-plugin/plugin.json`, `.github/workflows/release-candidate.yml` | - | 原始目标对照、仍有效原生证据、必要validators与明确NOT RUN | complete | 不把内部拆批当作独立产品交付 |

S2 依赖整体方向接受。S3 的确定性缺陷复现和窄修可独立推进，不能借此引入新安全政策。S4 在实际变更稳定后运行受影响检查；只有提出 release-readiness 声明时才要求仓库规定的完整资格检查，缺失证据不得由历史文字补齐。

方案与待定技术在 [design.md](design.md)，变化中的事实、结果和未决项在 [progress.md](progress.md)。保持本实施边界稳定；只有真实范围或决定变化才修改。
