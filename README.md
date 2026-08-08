# Dev Flow

[![CI](https://github.com/AldenClark/dev-flow/actions/workflows/ci.yml/badge.svg)](https://github.com/AldenClark/dev-flow/actions/workflows/ci.yml)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Dev Flow 是一套面向 Codex Multi-Agent V2 的轻量开发流程插件。它把“先理解现有代码、再确认需求和设计”落实为可追溯的工作包，并提供一套明确、可调整的 Rust 与前端工程偏好。

> English: a lightweight, repository-first and evidence-driven Codex workflow for high-quality software changes.

## 核心能力

- 在需求和方案前扫描真实代码、运行时事实与 Git 边界；
- 明确记录需求、验收标准、设计、改动范围、进度、决策、测试和审计；
- 按微小修改、日常需求、Bug 修复、大型功能、重构、迁移、安全与性能任务调整流程重量；
- 按 Rust 后端、Web、Apple/Android/Windows 客户端、FFI、CLI/TUI 等项目形态组织验证；
- 新依赖必须先比较候选方案、影响与维护成本，并取得明确批准；
- 只把边界清晰的独立工作交给子代理，由根代理负责综合、复核和最终验收；
- 管控浏览器、模拟器、设备、虚拟机、容器和服务等测试资源；
- 用蓝队审计、红队审计和新鲜验证证据阻止未经证实的完成声明。

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

仓库公开并创建 `v0.2.0` 标签后，可直接添加仓库内的 marketplace 并安装固定到该标签的插件：

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

在 Codex 中调用 `$dev-flow`，并描述目标、允许的交付范围以及兼容性要求。涉及技术选型时，流程会配合 `$engineering-preferences` 使用。

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

- `skills/dev-flow/`：生命周期、任务手册、工作包模板、测试和审计策略、CLI 与角色配置；
- `skills/engineering-preferences/`：工程宪章、依赖治理、机器可读偏好和选型目录；
- `hooks/`：仅对显式激活工作包生效的依赖、委派、进度与完成门禁；
- `evals/`：行为测试、结构契约和代表性项目案例；
- `governance/industry-practices.json`：外部实践到本地策略的采用记录。

## 验证

```bash
python3 -m unittest discover -s evals -v
python3 evals/run_contract_checks.py
python3 skills/dev-flow/scripts/dev-flow.py check --plugin-root "$PWD"
python3 -m compileall -q hooks skills evals
```

CI 在 Linux、macOS 和 Windows 上覆盖 Python 3.11 与当前 Python 3.14。实时模型行为评测与确定性仓库检查分离，避免把不可复现的模型结果伪装成静态门禁。

## 版本与兼容性

仓库使用 [Semantic Versioning](https://semver.org/)：

- `MAJOR`：工作包、CLI 或 hook 契约的不兼容变化；
- `MINOR`：向后兼容的新流程、命令、策略或能力；
- `PATCH`：兼容的修复、文档和规则校正。

源码与 Git tag 使用稳定版本（例如 `0.2.0`）；仅本地 Codex 开发重装时才临时追加 `+codex.<cachebuster>`，不把缓存破坏后缀发布为正式版本。变更记录见 [CHANGELOG.md](CHANGELOG.md)。

## 参与和安全

提交修改前请阅读 [CONTRIBUTING.md](CONTRIBUTING.md)。安全问题请遵循 [SECURITY.md](SECURITY.md)，不要在公开 Issue 中提交漏洞细节、凭据或敏感运行数据。

## License

MIT，详见 [LICENSE](LICENSE)。
