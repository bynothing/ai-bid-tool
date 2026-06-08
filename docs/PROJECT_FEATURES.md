# Project Features

最后更新：2026-06-08

本文档记录 `bid-tool` 已经完成或已经具备的工程能力。它用于帮助持续开发时快速判断：

- 哪些能力已经存在。
- 能力入口在哪里。
- 当前成熟度如何。
- 还存在什么限制。
- 验证方式是什么。

成熟度说明：

| 等级 | 含义 |
| --- | --- |
| M0 | 只有概念或文档，未形成可运行能力 |
| M1 | 有原型实现，可局部运行 |
| M2 | 有测试或 smoke，可重复验证 |
| M3 | 可进入主流程，具备基本交付稳定性 |
| M4 | 工程级稳定，有真实样本、质量门禁和回归 |

## 总体能力快照

| 能力域 | 当前等级 | 状态摘要 |
| --- | --- | --- |
| 项目记忆系统 | M3 | 已有状态、路线图、决策、知识地图、交接机制 |
| 文件管理治理 | M3 | 已有导航、智能体入口、文件治理和源码地图 |
| 9 阶段流水线 | M2 | 具备阶段结构、Schema、Prompt 和测试基础 |
| 表格规划 | M2 | 已有 S5_tables 阶段和 schema |
| 配图执行环境 v2 | M2 | 已有 API、CLI、能力目录、模板、Draw.io renderer |
| 工艺流程 / 系统交互大图 | M2 | `process.interaction_map` 可自动路由 Draw.io，有 fixture、基线和 86 分评分 |
| 配图质量目标体系 | M2 | 已有参考图、Rubric、Todo、第一轮迭代计划、A 类基线评分 |
| 图文合成 | M2 | S6 可消费配图 manifest 和表格计划 |
| 闭环校验 | M2 | 已有 trace/validator 测试基础 |
| DOCX 导出 | M1/M2 | README 中有导出路径，后续需强化交付回归 |
| 项目级总控 | M3 | 已有 `PROJECT_BUILD_OVERVIEW.md` |

## 已完成功能清单

### F-001：项目级记忆与交接系统

状态：完成

成熟度：M3

说明：

- 建立固定入口，避免依赖智能体长期记忆。
- 支持新会话快速恢复项目状态、路线、决策和上下文。

关键文件：

- `WORKSPACE.md`
- `docs/workspace/STATE.md`
- `docs/workspace/ROADMAP.md`
- `docs/workspace/DECISION_LOG.md`
- `docs/workspace/KNOWLEDGE_MAP.md`
- `docs/workspace/SESSION_HANDOFF.md`

验证：

- 新会话按入口读取即可恢复上下文。
- `python -m pytest` 当前 60 passed。

限制：

- 需要每次开发结束主动维护。

### F-002：项目级建设总控

状态：完成

成熟度：M3

说明：

- 汇总系统目标、现状、短板、主线、路线、质量门禁和下一步。

关键文件：

- `docs/PROJECT_BUILD_OVERVIEW.md`

验证：

- 已接入 `WORKSPACE.md`、`docs/README.md`、`entrypoint/ENTRYPOINT.md`。

限制：

- 需要随系统方向变化持续更新。

### F-003：项目文件结构治理

状态：完成

成熟度：M3

说明：

- 明确 `docs/`、`src/`、`tests/`、`output/` 的职责。
- 长期架构文档迁移到 `docs/architecture/`。
- 标准文档迁移到 `docs/standards/`。

关键文件：

- `docs/PROJECT_STRUCTURE.md`
- `docs/NAVIGATION.md`
- `docs/FILE_GOVERNANCE.md`
- `AGENTS.md`
- `src/bid_tool/README.md`
- `src/bid_tool/pipeline/README.md`
- `src/bid_tool/schemas/README.md`
- `src/bid_tool/illustration_v2/README.md`

验证：

- 新增文件有归位规则。
- 人和智能体有任务导航。
- 大型参考图和生成基线默认不入库。

限制：

- 旧产物目录仍需定期清理和归档。

### F-004：9 阶段标书流水线框架

状态：已具备

成熟度：M2

说明：

- 项目围绕 S1-S9 标书生成流程组织。
- 包含解析、大纲、正文、冻结、表格、配图、合成、校验、导出等阶段。

关键文件：

- `README.md`
- `src/bid_tool/pipeline/engine.py`
- `src/bid_tool/pipeline/stages/`
- `src/bid_tool/schemas/`
- `src/bid_tool/prompts/`

验证：

- `tests/test_validator.py`
- `tests/test_trace.py`
- `tests/test_schemas.py`

限制：

- 真实标书端到端回归样本仍不足。
- 各阶段 LLM 输出质量还需要真实项目校准。

### F-005：表格内容规划阶段

状态：已具备

成熟度：M2

说明：

- S5_tables 用于从冻结正文中识别适合表格化表达的内容。
- 配图阶段可避开已经表格化表达的内容。

关键文件：

- `src/bid_tool/pipeline/stages/s5_tables.py`
- `src/bid_tool/schemas/s5_table_plan.schema.json`
- `src/bid_tool/prompts/s5_table_prompt.md`

验证：

- `tests/test_schemas.py`
- README 流程说明。

限制：

- 需要更多真实正文样本验证表格规划质量。

### F-006：Illustration V2 配图执行环境

状态：已具备

成熟度：M2

说明：

- 当前配图主线已迁移到 `illustration_v2`。
- 提供 Job 加载、校验、规划、渲染和 manifest 输出。

关键文件：

- `src/bid_tool/illustration_v2/api.py`
- `src/bid_tool/illustration_v2/toolkit.py`
- `src/bid_tool/illustration_v2/core/`
- `src/bid_tool/illustration_v2/renderers/`
- `src/bid_tool/illustration_v2/templates/`

验证：

- `tests/test_illustration_v2.py`
- `python -m bid_tool.illustration_v2.toolkit --job examples/示例_配图平台v2任务.json --output output/workspace_smoke --png`

限制：

- 当前输出质量未达工程级。
- 决策层、QA 和模板覆盖率仍需加强。

### F-007：Draw.io 渲染与可编辑源文件方向

状态：已具备

成熟度：M1/M2

说明：

- 已有 Draw.io renderer 和本地工具脚本。
- 支持复杂工程图的可编辑 `.drawio` 源文件方向。

关键文件：

- `src/bid_tool/illustration_v2/renderers/drawio.py`
- `tools/DRAWIO.md`
- `tools/drawio.ps1`
- `tools/install-drawio.ps1`

验证：

- `output/drawio_complex_smoke/` 中有 smoke 产物。

限制：

- 需要纳入正式 fixture 和质量评分。
- 箭头治理、图例、复杂布局规则仍需工程化。

### F-008：配图质量目标体系

状态：已建立

成熟度：M2

说明：

- 已收集 87 张参考图。
- 已归纳 4 类目标原型。
- 已建立 Rubric、Todo、持续改进闭环和第一轮迭代计划。
- 已完成 A 类“工艺流程 / 系统交互大图”当前基线、评分和缺陷清单。

关键文件：

- `docs/quality-targets/illustration/README.md`
- `docs/quality-targets/illustration/REFERENCE_INVENTORY.md`
- `docs/quality-targets/illustration/ACCEPTANCE_RUBRIC.md`
- `docs/quality-targets/illustration/CONTINUOUS_IMPROVEMENT_LOOP.md`
- `docs/quality-targets/illustration/ITERATION_001_PROCESS_INTERACTION.md`
- `docs/quality-targets/illustration/TODO.md`

验证：

- 文档体系已接入项目入口。
- 当前测试基线仍为 57 passed。

限制：

- 当前只完成 1 个 A 类基线，距离至少 3 个系统输出基线仍有差距。

### F-009：工艺流程 / 系统交互大图初版

状态：已具备

成熟度：M2

说明：

- 新增 `process.interaction_map` 图型。
- `renderer: auto` 可自动路由到 Tier 2 Draw.io。
- 支持工艺段分区、段内步骤、主流程、辅助/回流关系、交互点、图例和术语区。
- 支持长图例底部布局、主辅流程分层通道和物料/返修/辅助语义线色。
- 支持返修/回流线外侧绕行，避免挤压主流程交界。
- 支持工艺段与系统节点语义配色，整体布局更紧凑。
- Manifest 标记 `needs_human_review=true`，说明当前仍是基线实现，不是最终工程级模板。

关键文件：

- `src/bid_tool/illustration_v2/core/decision.py`
- `src/bid_tool/illustration_v2/renderers/drawio.py`
- `tests/fixtures/illustration_cases/process_interaction_map/job.json`
- `docs/quality-targets/illustration/reviews/baseline-process-interaction-iteration-001.md`

验证：

- `tests/test_illustration.py`
- `python -m pytest` 当前 60 passed。

限制：

- 当前评分 86 / 100，是 B 级阶段性候选。
- design tokens、回流线长度压缩和几何 QA 仍需继续开发。

限制：

- 还未生成当前系统质量基线。
- 还未完成第一轮质量改造代码实现。

### F-009：配图 Manifest 装配契约

状态：已具备

成熟度：M2

说明：

- 配图输出通过 `illustration-manifest.json` 给 S6/S8 消费。
- 调用方不应依赖内部文件命名。

关键文件：

- `src/bid_tool/illustration_v2/core/manifest.py`
- `src/bid_tool/pipeline/stages/s6_synthesize.py`
- `src/bid_tool/pipeline/stages/BID_TOOL_ILLUSTRATION_ADAPTER.md`

验证：

- `tests/test_illustration.py`
- `tests/test_illustration_v2.py`

限制：

- manifest 需要进一步记录 tier、fallback、质量 warning、节点数、边数等指标。

### F-010：Schema 与基础测试体系

状态：已具备

成熟度：M2

说明：

- 多个阶段输出和配图 Job 有 schema 约束。
- 当前测试覆盖 schema、trace、validator、illustration。

关键文件：

- `src/bid_tool/schemas/`
- `tests/`

验证：

```text
python -m pytest
57 passed
```

限制：

- 真实样本 fixture 还不足。
- 缺少质量类自动 QA 测试。

## 当前功能缺口摘要

| 缺口 | 对应 TODO |
| --- | --- |
| 配图工程级质量不足 | `P0-001`、`IQ-*` |
| 当前系统输出基线缺失 | `P0-002` |
| 决策层 tier/fallback 记录不足 | `P0-003` |
| 真实标书 fixture 不足 | `P0-004` |
| 几何/关系 QA 不足 | `P1-001` |
| S5 prompt 与能力目录需要对齐 | `P1-002` |
| DOCX 交付质量回归不足 | `P2-001` |

项目级 Todo 见：

```text
docs/PROJECT_TODO.md
```
