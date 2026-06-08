# bid_tool Source Map

本目录是 `bid-tool` 的运行时代码。项目级计划、状态、架构讨论和质量目标不放在这里，统一放在 `docs/`。

## 目录

| 路径 | 职责 |
| --- | --- |
| `cli.py` | `bid-tool` 命令入口 |
| `pipeline/` | 9 阶段标书流水线 |
| `prompts/` | LLM Prompt 模板 |
| `schemas/` | JSON Schema 和 AI 接口协议 |
| `profiles/` | 项目类型配置 |
| `illustration_v2/` | 当前配图执行环境 |

## 开发规则

- 新运行时代码放在对应模块目录。
- 新 Schema 放 `schemas/`。
- 新 Prompt 放 `prompts/`。
- 新配图模板、契约和运行时素材放 `illustration_v2/`。
- 长期文档、计划、状态、交接不要放入 `src/`。

## 相关文档

- `docs/PROJECT_BUILD_OVERVIEW.md`
- `docs/PROJECT_STRUCTURE.md`
- `docs/FILE_GOVERNANCE.md`
- `docs/NAVIGATION.md`
