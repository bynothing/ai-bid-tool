# Navigation

最后更新：2026-06-07

本文档是 `bid-tool` 的人类与智能体导航页。它回答“我现在应该读哪个文件”。

## 我是第一次进入项目

按顺序读：

1. `README.md`：用户视角，知道工具如何运行。
2. `WORKSPACE.md`：持续开发入口。
3. `docs/PROJECT_BUILD_OVERVIEW.md`：工程建设总控。
4. `docs/PROJECT_FEATURES.md`：已经具备什么能力。
5. `docs/PROJECT_TODO.md`：接下来做什么。
6. `docs/PROJECT_STRUCTURE.md`：文件放哪里。

## 我是智能体，要继续开发

先读：

1. `AGENTS.md`
2. `docs/workspace/STATE.md`
3. `docs/PROJECT_TODO.md`
4. `docs/workspace/SESSION_HANDOFF.md`

然后根据任务类型进入专项文档。

## 我要做配图质量改造

读：

1. `docs/quality-targets/illustration/README.md`
2. `docs/quality-targets/illustration/REFERENCE_INVENTORY.md`
3. `docs/quality-targets/illustration/ACCEPTANCE_RUBRIC.md`
4. `docs/quality-targets/illustration/CONTINUOUS_IMPROVEMENT_LOOP.md`
5. `docs/quality-targets/illustration/ITERATION_001_PROCESS_INTERACTION.md`
6. `docs/quality-targets/illustration/TODO.md`

代码入口：

```text
src/bid_tool/illustration_v2/
```

## 我要改流水线

读：

1. `README.md` 中完整流程。
2. `docs/PROJECT_BUILD_OVERVIEW.md`
3. `src/bid_tool/pipeline/README.md`
4. `src/bid_tool/pipeline/engine.py`
5. 对应 `src/bid_tool/pipeline/stages/s*.py`
6. 对应 `src/bid_tool/schemas/*.schema.json`
7. 对应 `src/bid_tool/prompts/*.md`

## 我要改 Schema 或 Prompt

读：

1. `src/bid_tool/schemas/README.md`
2. 对应 schema 文件。
3. 对应 prompt 文件。
4. `tests/test_schemas.py`

注意：

- Schema 变更通常需要测试。
- 用户可见协议变更需要更新 `CHANGELOG.md`。

## 我要处理输出产物

读：

1. `docs/FILE_GOVERNANCE.md`
2. `docs/PROJECT_STRUCTURE.md`
3. `docs/workspace/STATE.md`

原则：

- 临时输出不入库。
- 质量基线可以保留说明文件，二进制大图默认本地存放。
- 可复现样本优先转入 `tests/fixtures/`。

## 我要提交代码

检查：

```powershell
git status --short --branch
python -m pytest
```

然后确认是否需要更新：

- `CHANGELOG.md`
- `docs/PROJECT_FEATURES.md`
- `docs/PROJECT_TODO.md`
- `docs/workspace/STATE.md`
- `docs/workspace/SESSION_HANDOFF.md`
- 专项 `RECORD.md`

## 常用地图

| 目标 | 文件 |
| --- | --- |
| 项目目标和现状 | `docs/PROJECT_BUILD_OVERVIEW.md` |
| 已完成功能 | `docs/PROJECT_FEATURES.md` |
| 待办任务 | `docs/PROJECT_TODO.md` |
| 文件治理 | `docs/FILE_GOVERNANCE.md` |
| 项目结构 | `docs/PROJECT_STRUCTURE.md` |
| 当前状态 | `docs/workspace/STATE.md` |
| 决策记录 | `docs/workspace/DECISION_LOG.md` |
| 配图质量 | `docs/quality-targets/illustration/README.md` |
| 方法论分享 | `docs/methodology/agent-complex-engineering-methodology.md` |
