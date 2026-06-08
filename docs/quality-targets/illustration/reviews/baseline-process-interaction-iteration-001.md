# Baseline Review: Process Interaction Map Iteration 001

## 基本信息

- 日期：2026-06-08
- 原型：A 工艺流程 / 系统交互大图
- 参考图：`docs/quality-targets/illustration/references/五菱总装A-H工艺段流程及系统交互点分析图 (1).png`
- 系统输出：`docs/quality-targets/illustration/generated-baselines/iteration-001-process-interaction/assets/drawio/assembly_process_interaction_map.png`
- 对应 job：`tests/fixtures/illustration_cases/process_interaction_map/job.json`
- 对应 renderer：`drawio`
- 决策层：`renderer: auto` 自动路由到 Tier 2 Draw.io，`needs_human_review=true`

## 当前输出评分

| 维度 | 分数 | 主要问题 |
| --- | ---: | --- |
| 信息清晰度 | 21 / 25 | 能看出 A-E 工艺主线、系统交互点和质量回流，图例从右侧长列改为底部说明后扫描路径更自然。 |
| 结构与布局 | 18 / 20 | 分区和步骤稳定，底部图例更紧凑，主体高度收敛；整体扫描路径更接近工程方案图。 |
| 箭头与关系表达 | 17 / 20 | 主流程粗实线，物料/异常走下方通道，返修/回流走外侧顶部绕行通道并使用语义色；回路线略长但避开了主流程交界。 |
| 文本与术语 | 12 / 15 | 节点标题短，术语区可读；部分边标签仍偏流程口径，后续需进一步压缩。 |
| 视觉专业度 | 13 / 15 | 工艺段采用语义配色，节点按 MES/WMS/QMS/设备类型区分，整体不再是单一浅蓝风格。 |
| 交付可用性 | 5 / 5 | 已导出 PNG/SVG/Draw.io，PNG 可审阅。 |
| 总分 | 86 / 100 | B，可作为阶段性可交付候选，但尚未达到目标级。 |

## 已完成工程动作

- 新增 `process.interaction_map` 自动决策路径，`renderer: auto` 可路由到 Draw.io。
- Draw.io renderer 新增工艺段分区布局，支持 `sections`、`primary_flow`、`support_flows`、`interaction_types`、`legend`、`glossary`。
- 主流程使用粗实线，辅助/回流关系使用虚线。
- 长图例自动切换为底部图例区，避免右侧长列拉高画布。
- 辅助/物料/返修关系增加独立走廊：物料/异常走下方通道，返修走上方通道。
- 辅助/物料/返修关系增加语义色：物料绿色、返修橙色、普通辅助灰色。
- 返修/回流线改为外侧绕行：从源工艺段外侧出线，沿顶部通道回到目标工艺段外侧，避开 C/D 主流程交界。
- 工艺段容器增加语义配色：上线准备、车身装配、电检标定、质量确认、下线入库分别使用克制的蓝、青绿、灰蓝、暖橙、靛蓝体系。
- 节点增加系统语义配色：MES、WMS、QMS、设备交互、VIN/扫码使用不同节点色，强化信息层级。
- 底部图例进一步压缩，从 170px 级高度降到约 140px。
- Manifest 记录 Tier 2、fallback、fit_score 和人工复核标记。
- 新增 fixture：`tests/fixtures/illustration_cases/process_interaction_map/job.json`。
- 新增测试覆盖自动路由、可编辑 `.drawio` 输出、分区、底部图例和主辅连线通道。

## 差距清单

| 优先级 | 差距 | 工程层级 | 建议任务 |
| --- | --- | --- | --- |
| P1 | 返修/回流线外侧绕行后路径偏长 | connector policy | 下一步压缩回流通道长度，并探索标签移入图例或说明区。 |
| P1 | 回流线外侧绕行后路径偏长 | connector policy | 探索回流关系的标签移位或图例化，降低顶部线段占用。 |
| P1 | 语义配色仍写在 renderer 内部 | design tokens | 将工艺段、系统节点、线型颜色抽成共享 design tokens。 |
| P1 | 当前仍是 Tier 2，不是冻结模板 | template contract | 将高频 A-H 工艺图沉淀为 Tier 1 模板候选。 |
| P2 | 自动 QA 只记录复杂度 warning，尚未检测箭头穿越文本 | QA | 增加连线穿越风险、节点重叠和边数量预算测试。 |

## 本轮结论

- 是否可交付：阶段性可交付候选，当前为 B 级。
- 是否进入 fixture：是。
- 是否更新 TODO：是，`IQ-008` 完成，`IQ-009` 进入持续完善。
- 下一步：继续推进 design tokens 抽象、回流线长度压缩和自动 QA，目标将评分提升到 90+。
