# Baseline Review: Layered Explainer Iteration 002

## 基本信息

- 日期：2026-06-08
- 原型：D 方法论 / 能力分层说明图
- 参考图：`C:/Users/杨辉/xwechat_files/bynothing_4346/temp/RWTemp/2026-06/6d6b01fa74e80f288cbbff6ee025c19a.jpg`
- 系统输出：`docs/quality-targets/illustration/generated-baselines/iteration-002-layered-explainer/assets/drawio/ai_seven_layer_explainer.png`
- 对应 job：`tests/fixtures/illustration_cases/layered_explainer/job.json`
- 对应 renderer：`drawio`
- 决策层：`renderer: auto` 自动路由到 Tier 2 Draw.io，`needs_human_review=true`

## 当前输出评分

| 维度 | 分数 | 主要问题 |
| --- | ---: | --- |
| 信息清晰度 | 23 / 25 | 七层结构、层名、说明和底部类比完整，参考图的核心信息组织方式已保留。 |
| 结构与布局 | 18 / 20 | 左编号、中卡片、圆形图标、右说明和底部类比结构稳定；细节层次仍可继续精修。 |
| 箭头与关系表达 | 18 / 20 | 使用虚线 callout 表示层级解释关系，克制清晰；后续可增加小圆点端点。 |
| 文本与术语 | 13 / 15 | 右侧说明完整，底部类比可读；部分长句仍需自动换行策略优化。 |
| 视觉专业度 | 13 / 15 | 红/橙/蓝分段和卡片层次接近参考图，但图标仍是文本缩写，不是图形 icon。 |
| 交付可用性 | 5 / 5 | 已导出 PNG/SVG/Draw.io，PNG 可审阅。 |
| 总分 | 90 / 100 | A-，可作为 layered explainer 图型的目标级基线候选。 |

## 已完成工程动作

- 新增 `architecture.layered_explainer` 图型。
- Draw.io renderer 支持左编号层级、中部层名/图标、右侧说明和底部类比区。
- 新增 fixture：`tests/fixtures/illustration_cases/layered_explainer/job.json`。
- 新增测试覆盖自动路由、层级结构、底部类比、语义色和 callout 边。
- 更新 `AI_ILLUSTRATION_API_V2.md`，让 AI 可生成该图型结构化 Job。

## 差距清单

| 优先级 | 差距 | 工程层级 | 建议任务 |
| --- | --- | --- | --- |
| P1 | 圆形图标仍是文本缩写 | visual system | 增加内置 icon token 或图标映射。 |
| P1 | 文本换行仍依赖 Draw.io | text QA | 为右侧说明增加容量检测和截断 warning。 |
| P2 | 仍是 Tier 2 Draw.io 实现 | template contract | 稳定后沉淀为 Tier 1 模板候选。 |

## 本轮结论

- 是否可交付：是，A- 目标级基线候选。
- 是否进入 fixture：是。
- 是否更新 TODO：是。
- 下一步：补 icon token、文本容量 QA，并将该图型纳入真实样本基线集。
