# Illustration Quality Record

本文件记录配图质量目标区的迭代过程。

## 2026-06-07：建立质量目标区

背景：

当前系统已有配图能力，但产出效果不足：不够美观、信息表达不清楚、箭头混乱，没有达到工程级标书图的交付标准。

本次建立：

- `TARGET_BRIEF.md`：人工目标说明。
- `REFERENCE_INTAKE_TEMPLATE.md`：参考图提交模板。
- `ACCEPTANCE_RUBRIC.md`：100 分评分标准。
- `DEVELOPMENT_PLAN.md`：质量提升阶段计划。
- `TODO.md`：持续任务板。
- `references/`：人工参考素材目录。
- `generated-baselines/`：当前系统输出基线目录。
- `reviews/`：人工评审和对比记录目录。

当前结论：

- 后续配图优化必须先对齐人工参考目标。
- 质量问题要转化为 Todo、评分、fixture，而不是停留在口头反馈。
- 优先解决信息表达和箭头关系，再做视觉美化。

验证：

```text
python -m pytest
57 passed
```

## 2026-06-07：参考图盘点与闭环计划

新增参考素材状态：

```text
total = 87
png   = 54
jpeg  = 31
jpg   = 2
```

抽样观察了 4 类目标：

- 工艺流程 / 系统交互大图。
- 分层协作架构图。
- 改造前后对比架构图。
- 方法论 / 对比卡片。

新增文件：

- `REFERENCE_INVENTORY.md`
- `CONTINUOUS_IMPROVEMENT_LOOP.md`
- `ITERATION_001_PROCESS_INTERACTION.md`
- `reviews/REVIEW_TEMPLATE.md`
- `reviews/target-process-interaction.md`
- `generated-baselines/README.md`
- `references/README.md`

当前结论：

- 第一轮质量改造建议从“工艺流程 / 系统交互大图”开始。
- 优先解决信息组织、主辅流程分层、图例说明和箭头治理。
- 暂不追求装饰性边框、拟物图标和所有图型同时美化。

第一轮下一步：

1. 生成当前系统同类基线图。
2. 按 Rubric 对基线打分。
3. 将 `ITERATION_001_PROCESS_INTERACTION.md` 中的 Job 契约草案转为示例 Job 或 schema 草案。
4. 选择 Draw.io renderer 或 template_svg 作为第一轮实现路径。

验证：

```text
python -m pytest
57 passed
```

## 2026-06-08：A 类基线与首个实现路径

本次围绕“工艺流程 / 系统交互大图”完成第一轮工程闭环。

新增能力：

- `process.interaction_map` 图型初版。
- 决策层支持 `renderer: auto` 自动路由到 Draw.io。
- Draw.io renderer 支持工艺段分区、段内步骤、主流程、辅助/回流关系、图例和术语说明。
- Manifest 记录 Tier 2、fallback、fit_score 和 `needs_human_review=true`。

新增样本与基线：

- fixture：`tests/fixtures/illustration_cases/process_interaction_map/job.json`
- 本地基线：`docs/quality-targets/illustration/generated-baselines/iteration-001-process-interaction/`
- 评审：`docs/quality-targets/illustration/reviews/baseline-process-interaction-iteration-001.md`

当前评分：

```text
86 / 100
```

结论：

- 当前输出已从 C 级基线提升为 B 级阶段性可交付候选，但还不是目标级模板。
- 已完成长图例底部布局、主辅流程通道和语义线色初版。
- 已完成回流线外侧绕行，避开 C/D 主流程交界。
- 已完成语义配色和紧凑图例优化，整体视觉专业度提升。
- 下一步应集中处理 design tokens、回流线长度压缩和自动 QA。

## 2026-06-08：D 类多层能力说明图基线

本次根据用户提供的“AI 系统七层架构全景图”参考图，新增一个更适合方法论、能力体系和层级说明的图型。

新增能力：

- `architecture.layered_explainer` 图型。
- `renderer: auto` 自动路由到 Draw.io。
- 支持左侧编号层级、中部层名/图标、右侧说明、底部通俗类比区。

新增样本与基线：

- fixture：`tests/fixtures/illustration_cases/layered_explainer/job.json`
- 本地基线：`docs/quality-targets/illustration/generated-baselines/iteration-002-layered-explainer/`
- 评审：`docs/quality-targets/illustration/reviews/baseline-layered-explainer-iteration-002.md`

当前评分：

```text
90 / 100
```

结论：

- 该图型已达到 A- 目标级基线候选。
- 后续重点是 icon token、文本容量 QA 和 Tier 1 模板化。
