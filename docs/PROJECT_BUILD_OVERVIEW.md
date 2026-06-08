# Project Build Overview

最后更新：2026-06-07

本文档是 `bid-tool` 的工程项目级建设总控文档。它回答：

- 这个系统要建成什么。
- 当前已经具备什么能力。
- 当前核心短板是什么。
- 后续按什么阶段持续建设。
- 每次开发如何验证、记录和反馈。

## 一句话目标

构建一个面向标书自动化的工程系统，将招标材料稳定转化为可审阅、可校验、可配图、可导出的投标技术文件，并逐步形成可持续迭代的知识、质量和交付闭环。

## 北极星

```text
招标材料
  -> 结构化解析
  -> 需求/评分/风险抽取
  -> 大纲与章节生成
  -> 人工确认与冻结
  -> 表格规划
  -> 工程级自动配图
  -> 图文合成
  -> 响应闭环校验
  -> Word/偏离表导出
```

最终系统不只是“生成一份文字”，而是要做到：

- 响应完整：招标要求、评分点、实质性条款可追踪。
- 内容可控：关键阶段可人工确认和冻结。
- 表达专业：表格和配图能提升评审理解。
- 输出稳定：Markdown、图片、manifest、DOCX 导出可复现。
- 过程可审计：每一步有状态、输入、输出、验证和修改记录。

## 当前系统定位

`bid-tool` 当前是一个 9 阶段标书自动生成流水线 + 配图执行环境。

核心模块：

| 模块 | 当前职责 | 关键路径 |
| --- | --- | --- |
| CLI | 用户命令入口 | `src/bid_tool/cli.py` |
| Pipeline | S1-S9 阶段编排 | `src/bid_tool/pipeline/README.md` |
| Schemas | 阶段输出和配图 Job 约束 | `src/bid_tool/schemas/README.md` |
| Prompts | LLM 阶段提示词 | `src/bid_tool/prompts/` |
| Illustration V2 | 配图执行环境 | `src/bid_tool/illustration_v2/README.md` |
| Docs Memory | 项目记忆和路线 | `docs/workspace/` |
| Quality Targets | 配图质量目标闭环 | `docs/quality-targets/illustration/` |

## 当前建设现状

### 已具备

已完成功能清单以 `docs/PROJECT_FEATURES.md` 为准。摘要：

- 项目记忆系统。
- 项目级建设总控。
- 项目文件结构治理。
- 9 阶段标书流水线框架。
- 表格内容规划阶段。
- `illustration_v2` 配图执行环境。
- Draw.io 渲染与可编辑源文件方向。
- 配图质量目标体系。
- 配图 manifest 装配契约。
- Schema 与基础测试体系。
- 当前测试基线：`python -m pytest`，57 passed。

### 当前核心短板

| 短板 | 影响 | 当前处理方向 |
| --- | --- | --- |
| 配图效果不达工程级 | 图不清楚、箭头乱、评审理解困难 | 建立质量目标区和第一轮系统交互图攻坚 |
| 真实样本不足 | 示例不能暴露真实标书复杂度 | 建立 `tests/fixtures/illustration_cases/` |
| 决策层仍需加强 | `renderer:auto` 需要更清楚的 tier/fallback 记录 | Phase 1 决策层升级 |
| 几何/关系 QA 不足 | 能生成不代表可交付 | Phase 3 QA 门禁 |
| S5 prompt 与能力目录可能漂移 | AI 输出可能与当前 v2 能力不匹配 | S5 prompt 与 v2 catalog 对齐 |
| 输出质量记录还不够系统化 | 改进难以复盘 | `RECORD.md`、review、fixture 闭环 |

## 当前最重要主线

### 主线 A：配图质量工程化

目标：

把配图从“能生成”提升到“工程级可交付”。

当前状态：

- 已收集 87 张参考图。
- 已归纳 4 类目标原型。
- 已建立 `ACCEPTANCE_RUBRIC.md`。
- 第一轮攻坚对象：工艺流程 / 系统交互大图。

下一步：

1. 生成当前系统同类基线图。
2. 按 Rubric 打分。
3. 将目标转成 Job 契约草案。
4. 选择 Draw.io 或模板 SVG 实现第一版。
5. 沉淀 fixture 和 QA warning。

入口：

```text
docs/quality-targets/illustration/ITERATION_001_PROCESS_INTERACTION.md
```

### 主线 B：决策层与降级链

目标：

让 `renderer: "auto"` 成为可审计的产出路径决策，而不是简单渲染器选择。

下一步：

- `api.plan()` 显式输出 tier、renderer、template、reason、fallback。
- manifest 记录降级原因和人工复核标记。
- 高频 fallback 场景转成模板建设需求。

入口：

```text
docs/architecture/illustration-v2/decision-analysis.md
src/bid_tool/illustration_v2/core/decision.py
```

### 主线 C：真实样本与回归

目标：

用真实标书片段驱动质量提升，而不是只用示例 Job。

建议目录：

```text
tests/fixtures/illustration_cases/
```

每个 case：

```text
input.md
job.json
expected.md
quality.md
```

## 阶段路线

| 阶段 | 状态 | 目标 | 关键验收 |
| --- | --- | --- | --- |
| Phase 0 | 完成 | 项目记忆系统和基础结构 | 新会话可通过固定入口恢复上下文 |
| Phase Q | 进行中 | 目标驱动的配图质量改造 | 参考目标、基线评分、第一轮质量迭代 |
| Phase 1 | 待启动 | 决策层升级 | plan/manifest 有 tier/fallback/reason |
| Phase 2 | 待启动 | 真实样本和质量评测 | 至少 5 个高频图型 fixture |
| Phase 3 | 待启动 | 几何级和关系级 QA | fit、重叠、箭头、标签能被检测 |
| Phase 4 | 待启动 | 模板扩类和成本优化 | 高频图型优先命中 Tier 1 |
| Phase 5 | 待规划 | DOCX 交付质量闭环 | 图文、表格、样式、偏离表稳定导出 |

## 项目级 TODO

完整任务队列见：

```text
docs/PROJECT_TODO.md
```

当前 P0：

1. 配图质量第一轮：工艺流程 / 系统交互大图。
2. 建立当前配图质量基线。
3. 决策层 tier/fallback 字段梳理。
4. 建立第一批真实标书 fixture。
5. S5 prompt 与 v2 能力目录对齐。

## 质量门禁

任何涉及生成结果的开发，至少验证：

```powershell
python -m pytest
```

配图相关开发还要验证：

```powershell
python -m bid_tool.illustration_v2.toolkit --job <job.json> --output <output-dir> --png
```

配图质量专项还要补充：

- Rubric 评分。
- review 记录。
- manifest 检查。
- 如可复现，沉淀 fixture。

## 记录体系

| 信息 | 记录位置 |
| --- | --- |
| 人/智能体导航 | `docs/NAVIGATION.md` |
| 文件治理 | `docs/FILE_GOVERNANCE.md` |
| 已完成功能 | `docs/PROJECT_FEATURES.md` |
| 项目级 TODO | `docs/PROJECT_TODO.md` |
| 当前状态 | `docs/workspace/STATE.md` |
| 总体路线 | `docs/workspace/ROADMAP.md` |
| 项目结构 | `docs/PROJECT_STRUCTURE.md` |
| 架构决策 | `docs/workspace/DECISION_LOG.md` |
| 项目知识地图 | `docs/workspace/KNOWLEDGE_MAP.md` |
| 会话交接 | `docs/workspace/SESSION_HANDOFF.md` |
| 配图质量目标 | `docs/quality-targets/illustration/` |
| 修改历史 | `CHANGELOG.md` |

## 每次开发闭环

```text
读取状态
  -> 确认任务
  -> 小步实现
  -> 自动测试
  -> 生成/评审样本
  -> 更新状态与 Todo
  -> 必要时更新决策日志和 CHANGELOG
```

每次开发结束至少更新：

- `STATE.md` 或 `SESSION_HANDOFF.md`
- 对应专项 Todo / RECORD
- 涉及重大变更时更新 `CHANGELOG.md`

## 当前下一步

最高优先级：

1. 将 `process.interaction_map` 当前工艺段配色、系统节点配色、线型语义抽成 design tokens。
2. 压缩返修/回流线长度，并评估是否将回流标签移入图例或说明区。
3. 补充 `process.interaction_map` 的自动 QA：主流程缺失、图例缺失、边数量预算、线型语义。
4. 执行 `P0-002`：再建立至少 2 个当前系统输出基线，完成 3 个基线评分。
4. 执行 `P0-002`：再建立至少 2 个当前系统输出基线，完成 3 个基线评分。

并行可推进：

- S5 prompt 与 `illustration_v2` 能力目录对齐。
- 建立第一批真实标书 fixture。
