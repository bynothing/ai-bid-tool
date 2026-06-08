# Iteration 001: Process Interaction Map

最后更新：2026-06-08

## 本轮目标

将“工艺流程 / 系统交互大图”作为第一轮质量攻坚对象，解决当前配图中最核心的问题：

- 信息组织不清楚。
- 主路径和辅助关系混在一起。
- 箭头混乱。
- 图例和术语说明缺失。
- 复杂内容被硬塞进一张图但缺少层级。

## 目标参考

```text
docs/quality-targets/illustration/references/五菱总装A-H工艺段流程及系统交互点分析图 (1).png
```

## 目标原型

```text
Process Interaction Map
```

它不是普通流程图，而是：

```text
业务段/工艺段分区
  + 每段内部步骤
  + 主流程方向
  + 系统交互点
  + 辅助/物料/回流关系
  + 图例和术语说明
```

## 本轮开发原则

- 先表达清楚，再追求精美。
- 主流程必须一眼能看懂。
- 辅助关系不能抢主流程。
- 图例必须解释颜色、线型和交互点。
- 超容量必须拆图或摘要，不硬塞。

## 任务分解

### 1. 当前系统基线

任务：

- 准备一个同类 Job，表达多工艺段/多系统交互点。
- 用当前 `illustration_v2` 生成输出。
- 保存到 `generated-baselines/iteration-001-process-interaction/`。
- 用 `ACCEPTANCE_RUBRIC.md` 打分。

验收：

- 有 job、manifest、png/svg 或 drawio 输出。
- 有 review 记录。
- 明确当前系统主要差距。

### 2. Job 契约草案

任务：

设计一个能表达此类图的结构化数据草案：

```text
sections[]              工艺段/业务段
  id
  title
  subtitle
  color_role
  steps[]
    id
    title
    description
    interaction_type
    upstream
    output
primary_flow[]          主流程段间关系
support_flows[]         辅助流程/物料/回流
interaction_types[]     交互点类型和颜色
legend                  图例
glossary                术语说明
```

验收：

- 草案能覆盖参考图的主要信息结构。
- 可以映射到 Draw.io 或模板 SVG。
- 明确容量限制。

### 3. 布局策略

任务：

- 定义多分区卡片布局。
- 主流程采用横向或分层横向路径。
- 图例/术语说明固定放右侧或底部。
- 卡片内部步骤采用短标题 + 2 行说明。

验收：

- 布局不依赖自由坐标生成。
- 主路径有固定通道。
- 辅助关系有独立线型或说明区。

### 4. 箭头策略

任务：

- 主流程：粗实线箭头。
- 辅助流程：细虚线箭头。
- 双向/循环：双向或回环线。
- 汇入/合流：单独符号或图例。
- 标签去重：消除低价值“请求/调用/反馈”。

验收：

- 箭头数量有预算。
- 箭头不穿越关键文本。
- 图例解释所有线型。

### 5. 渲染落点

候选路径：

1. 先用 Draw.io renderer 做工程图表达。
2. 稳定后沉淀为 Tier 1 模板或 template_svg 组件。

原因：

- Draw.io 更适合复杂分区、可编辑源文件和连接线调试。
- 模板化适合后续高频场景稳定复制。

验收：

- renderer 决策能解释为什么选 Draw.io 或模板。
- 输出 `.drawio`、`.svg/.png` 和 manifest。

### 6. QA 与回归

任务：

- manifest 记录节点数、边数、标签数、图例数。
- 对边数量超过阈值给 warning。
- 对缺失图例、重复标签、主流程缺失给 warning。
- 将样本加入 `tests/fixtures/illustration_cases/`。

验收：

- `python -m pytest` 通过。
- fixture 可复现。
- review 总分提升。

## 本轮完成标准

本轮达到以下标准即可关闭：

- 当前系统基线已记录。
- 目标图评审已记录。
- Job 契约草案完成。
- 至少实现一个可运行输出。
- Rubric 总分达到 70+。
- 箭头与关系表达不低于 14 分。
- 至少一个质量问题转为自动 warning 或测试。

## 2026-06-08 进展

已完成：

- 新增 `process.interaction_map` 初版实现路径。
- `renderer: auto` 可自动路由到 Tier 2 Draw.io。
- Draw.io renderer 支持 `sections`、`primary_flow`、`support_flows`、`interaction_types`、`legend`、`glossary`。
- 生成当前系统 A 类基线：`docs/quality-targets/illustration/generated-baselines/iteration-001-process-interaction/`。
- 评审记录：`docs/quality-targets/illustration/reviews/baseline-process-interaction-iteration-001.md`。
- 回归样本：`tests/fixtures/illustration_cases/process_interaction_map/job.json`。
- 当前评分：83 / 100。

下一步重点：

- 将辅助/回流关系放入更稳定的专用连线通道。
- 动态调整图例区位置和尺寸，减少主体下方留白。
- 将主辅线型策略沉淀为 design tokens 和自动 QA。

## 2026-06-08 第二步优化

已完成：

- 长图例自动切换为底部图例区。
- 物料/异常辅助线走下方通道。
- 返修/回流线走上方通道。
- 物料、返修、普通辅助关系使用不同语义色。
- 新增底部图例和辅助通道回归测试。

当前评分提升到：

```text
84 / 100
```

剩余问题：

- 返修线已改为外侧绕行，不再压迫 C/D 顶部标题区，但路径偏长。
- 底部图例区仍可压缩。
- 线型语义尚未抽成共享 design tokens。

## 2026-06-08 第三步优化

已完成：

- 返修/回流线从“C/D 交界通道”改为“外侧顶部绕行通道”。
- 回流线从源工艺段外侧出线，从目标工艺段外侧入线，减少与主流程箭头挤压。
- 回归测试更新为验证外侧绕行锚点和顶部通道。

当前评分：

```text
86 / 100
```

新的权衡：

- 绕行后关系更清楚，但路径更长。
- 下一步应考虑将回流线标签移入图例或说明区，减少顶部线段标签占用。

## 2026-06-08 第四步优化

已完成：

- 工艺段容器从单一浅蓝改为语义配色：
  - 上线准备：工程蓝。
  - 车身装配：青绿。
  - 电检标定：灰蓝。
  - 质量确认：暖橙。
  - 下线入库：靛蓝。
- 节点按系统交互类型配色：
  - MES：蓝。
  - WMS：绿。
  - QMS：橙。
  - 设备交互：靛蓝。
  - VIN / 扫码：中性灰。
- 底部图例进一步压缩，整体画布高度降低。
- 回归测试新增语义色和紧凑图例断言。

当前评分：

```text
86 / 100
```

剩余问题：

- 颜色与线型策略仍散落在 Draw.io renderer 中，下一步应抽成 design tokens。
- 回流线外侧绕行清楚，但路径偏长。
- 尚未建立自动视觉 QA，只能通过 fixture 和人工复查判断。

## 不在本轮范围

- 不追求完全复刻参考图。
- 不做金属边框、复杂纹理、拟物装饰。
- 不一次性覆盖所有 87 张参考图。
- 不把所有图型都迁移到同一模板。
