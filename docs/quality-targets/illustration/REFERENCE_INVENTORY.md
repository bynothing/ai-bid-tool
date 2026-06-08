# Reference Inventory

最后更新：2026-06-07

当前 `references/` 中已有人工参考素材：

```text
total = 87
png   = 54
jpeg  = 31
jpg   = 2
```

这些参考图不应直接被当成“照抄样式”，而应先抽象成可实现的图型原型、布局规则、连线规则和质量标准。

## 已观察到的目标原型

### A. 工艺流程 / 系统交互大图

代表素材：

```text
五菱总装A-H工艺段流程及系统交互点分析图 (1).png
```

目标特征：

- 多个业务段/工艺段用彩色分区卡片表达。
- 主流程用粗箭头贯穿，辅助流程用虚线或细线表达。
- 每个分区内有局部步骤序列，不把所有步骤拉成一条长链。
- 右侧或底部有图例、类型说明、术语说明。
- 颜色承担语义：不同流程段、交互点类型、异常/同步/交通管制等。

需要学习：

- 分区卡片结构。
- 主次箭头层级。
- 图例和术语说明区。
- 复杂信息的分层压缩。

不直接学习：

- 过重的金属边框和装饰背景。
- 过多小字密集堆叠。

适用图型：

- `process.flowchart`
- `process.swimlane`
- `integration.interface_map`
- `relationship.platform_interface`
- `architecture.deployment`

### B. 分层协作架构图

代表素材：

```text
Gemini_Generated_Image_8rdx4o8rdx4o8rdx.png
```

目标特征：

- 左侧用层级标签建立阅读骨架。
- 中央是核心业务/执行链路。
- 上方是入口、决策、状态视图。
- 右侧是保障层或风险控制层。
- 红色异常路径只用于强语义的中断、暂停、风险。

需要学习：

- 层级标签 + 主体区域组合。
- 角色视图、状态视图、保障视图的结构化放置。
- 异常路径强约束。

不直接学习：

- AI 生成图中过多拟物图标。
- 不可控的纹理背景和复杂阴影。

适用图型：

- `architecture.layered`
- `architecture.security_ring`
- `security.closed_loop`
- `capability.map`

### C. 改造前后对比架构图

代表素材：

```text
77b64863d7dd30936cfd7baf836bff87.jpg
```

目标特征：

- 左右对比清楚：原有方式 vs 改造后方式。
- 中央有升级箭头和关键变化说明。
- 下方展开核心机制工作流。
- 图例明确区分数据流、控制流、轮询/异步等线型。
- 编号标注把图中关键点和说明区关联起来。

需要学习：

- before/after 对比结构。
- 中央转化箭头。
- 底部机制拆解。
- 编号标注和图例。

适用图型：

- `comparison.solution`
- `architecture.layered`
- `integration.interface_map`
- `matrix.scoring_response`

### D. 方法论 / 对比卡片

代表素材：

```text
mmexport1780845797403.png
```

目标特征：

- 两栏或多栏对比。
- 少连线，靠标题、图标、条目和结论条表达。
- 每栏内部有短句、示例和底部本质总结。
- 适合表达原则、方法、能力差异，不适合强行画复杂箭头。

需要学习：

- 卡片化对比。
- 条目式信息结构。
- 底部结论条。
- 用“少线”提高表达清晰度。

适用图型：

- `comparison.solution`
- `capability.map`
- `matrix.scoring_response`
- `taxonomy.inspection_cards`

## 第一轮目标抽象

第一轮不要试图覆盖 87 张参考图。先选择 4 个原型各 1 张作为 A 级目标：

| 原型 | 目标 | 后续产物 |
| --- | --- | --- |
| A | 工艺流程 / 系统交互大图 | `target-process-interaction.md` |
| B | 分层协作架构图 | `target-layered-collaboration.md` |
| C | 改造前后对比架构图 | `target-before-after.md` |
| D | 方法论 / 对比卡片 | `target-comparison-card.md` |

每个目标产物必须包含：

- 目标图引用。
- 可学习特征。
- 不学习特征。
- 对应图型。
- 当前系统差距。
- 可开发任务。
- 可测试验收。

## 下一步

1. 为 4 个目标原型补充 `reviews/target-*.md`。
2. 用当前系统生成同类图，放入 `generated-baselines/`。
3. 按 `ACCEPTANCE_RUBRIC.md` 对目标图和系统输出分别打分。
4. 把差距转成 `TODO.md` 中的具体任务。
