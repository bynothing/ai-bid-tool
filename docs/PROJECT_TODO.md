# Project Todo

最后更新：2026-06-08

本文档是 `bid-tool` 的工程项目级 TODO 队列。它覆盖整个标书自动化系统，不只覆盖配图专项。

状态说明：

| 状态 | 含义 |
| --- | --- |
| TODO | 未开始 |
| DOING | 正在做 |
| BLOCKED | 被阻塞 |
| DONE | 已完成 |
| WATCH | 暂不做但需要关注 |

优先级说明：

| 优先级 | 含义 |
| --- | --- |
| P0 | 当前最关键，直接影响主线成败 |
| P1 | 重要，完成 P0 后推进 |
| P2 | 中期建设项 |
| P3 | 长期优化 |

## P0：当前关键任务

| ID | 状态 | 任务 | 验收 | 关联 |
| --- | --- | --- | --- | --- |
| P0-001 | DONE | 配图质量第一轮：工艺流程 / 系统交互大图 | 完成基线、评分、契约草案和首个实现路径 | `IQ-008`、`ITERATION_001_PROCESS_INTERACTION.md` |
| P0-002 | TODO | 建立当前配图质量基线 | 至少 3 个当前输出按 Rubric 评分并记录缺陷 | `docs/quality-targets/illustration/generated-baselines/` |
| P0-003 | TODO | 决策层 tier/fallback 字段梳理 | `api.plan()` 和 manifest 显式包含 tier、renderer、template、reason、fallback | `src/bid_tool/illustration_v2/core/decision.py` |
| P0-004 | TODO | 建立第一批真实标书 fixture | 至少 5 个高频图型有可复现样本 | `tests/fixtures/illustration_cases/` |
| P0-005 | TODO | S5 prompt 与 v2 能力目录对齐 | AI 输出只依赖当前 `illustration_v2` 能力目录 | `src/bid_tool/prompts/`、`catalogs/` |

## P1：质量和稳定性建设

| ID | 状态 | 任务 | 验收 | 关联 |
| --- | --- | --- | --- | --- |
| P1-001 | TODO | 几何级 QA 最小实现 | 文本 fit、重叠、PNG 可读性可被测试或 manifest 捕获 | Phase 3 |
| P1-002 | TODO | 关系级 QA 最小实现 | 边数量、重复标签、主路径缺失、箭头穿越风险有 warning | 配图质量闭环 |
| P1-003 | TODO | Manifest 质量指标扩展 | 记录节点数、边数、标签数、tier、fallback、quality warnings | `core/manifest.py` |
| P1-004 | TODO | 配图 design tokens 初版 | 颜色、字体、边框、间距、标题区、图例区统一 | `docs/standards/illustration/` |
| P1-005 | TODO | Draw.io renderer 工程图策略化 | 主流程、辅助流程、图例、分区卡片可由结构化 Job 驱动 | `renderers/drawio.py` |

## P2：端到端交付能力

| ID | 状态 | 任务 | 验收 | 关联 |
| --- | --- | --- | --- | --- |
| P2-001 | TODO | DOCX 图文交付质量回归 | 至少 1 个端到端样本导出 DOCX，图、表、标题、目录可审阅 | S8 |
| P2-002 | TODO | 表格规划真实样本验证 | 至少 3 个真实章节表格规划合理，不与配图重复 | S5_tables |
| P2-003 | TODO | S1-S7 真实项目端到端回归 | 从输入材料到合成文档有完整样本和报告 | Pipeline |
| P2-004 | TODO | 偏离表流程验证 | S9 使用报价/偏离模板生成可审阅偏离表 | S9 |
| P2-005 | TODO | 人工确认 gate 体验整理 | S4 冻结、S5 图表确认、S7 校验确认有清晰操作指南 | README / docs |

## P3：效率和成本优化

| ID | 状态 | 任务 | 验收 | 关联 |
| --- | --- | --- | --- | --- |
| P3-001 | TODO | LLM 调用缓存策略 | 章节 hash、Job hash、模板版本 hash 可避免重复生成 | Pipeline / Illustration |
| P3-002 | TODO | 模型分层策略 | 便宜模型做扫描，强模型做复杂决策和修复 | Prompt / config |
| P3-003 | TODO | 配图模板扩类 | 高频图型优先命中 Tier 1，fallback 比例下降 | Phase 4 |
| P3-004 | TODO | 质量报告自动汇总 | 每次生成输出质量报告，汇总图、表、trace、风险 | S6/S7 |

## 已完成任务

| ID | 完成日期 | 任务 | 结果 |
| --- | --- | --- | --- |
| DONE-001 | 2026-06-07 | 建立项目记忆系统 | `WORKSPACE.md` + `docs/workspace/` |
| DONE-002 | 2026-06-07 | 整理项目文件结构 | `docs/PROJECT_STRUCTURE.md` |
| DONE-003 | 2026-06-07 | 建立项目级建设总控 | `docs/PROJECT_BUILD_OVERVIEW.md` |
| DONE-004 | 2026-06-07 | 建立配图质量目标区 | `docs/quality-targets/illustration/` |
| DONE-005 | 2026-06-07 | 盘点配图参考图 | 87 张参考图，4 类目标原型 |
| DONE-006 | 2026-06-07 | 制定配图质量第一轮计划 | `ITERATION_001_PROCESS_INTERACTION.md` |
| DONE-007 | 2026-06-07 | 当前测试基线验证 | `python -m pytest`，57 passed |
| DONE-008 | 2026-06-07 | 治理文件管理架构 | `AGENTS.md`、`NAVIGATION.md`、`FILE_GOVERNANCE.md`、源码模块地图 |
| DONE-009 | 2026-06-08 | 输出智能体复杂工程方法论 | `docs/methodology/agent-complex-engineering-methodology.md` |
| DONE-010 | 2026-06-08 | 配图质量第一轮：工艺流程 / 系统交互大图 | 新增 `process.interaction_map` Draw.io 路径、fixture、基线输出和评分记录 |

## 维护规则

每次开发结束：

1. 更新本文件中相关任务状态。
2. 如果任务完成，移动或复制到“已完成任务”。
3. 如果产生架构取舍，更新 `docs/workspace/DECISION_LOG.md`。
4. 如果产生质量样本，更新专项 `RECORD.md` 或 fixture。
5. 如果影响用户命令、Schema、流水线逻辑或输出正确性，更新 `CHANGELOG.md`。

## 下一步建议

当前优先执行：

```text
P0-001 / IQ-008
```

也就是：

```text
生成系统交互大图当前基线
  -> 保存 job/manifest/output
  -> 按 Rubric 打分
  -> 转成契约草案和开发任务
```
