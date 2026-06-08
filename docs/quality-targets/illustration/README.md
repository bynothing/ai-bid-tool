# Illustration Quality Target

本目录用于沉淀“自动配图要达到什么效果”。它是人工参考目标区，也是后续配图质量开发的长期任务入口。

当前核心问题：

- 配图能生成，但不够美观。
- 信息表达不清楚，评审看图后不能快速理解方案。
- 箭头、连线、层级关系混乱。
- 输出效果没有达到工程级、标书级、可交付级。

本目录的作用不是存放一次性审美意见，而是建立一个可持续迭代的质量目标体系：

```text
人工参考目标
  -> 质量评分标准
  -> 真实缺陷记录
  -> 开发 Todo
  -> 阶段计划
  -> 每轮产出复盘
```

## 目录结构

```text
docs/quality-targets/illustration/
  README.md
  TARGET_BRIEF.md              人工填写的目标说明
  REFERENCE_INVENTORY.md       参考图清单、目标原型和第一轮抽象
  REFERENCE_INTAKE_TEMPLATE.md 人工提交参考图时的说明模板
  ACCEPTANCE_RUBRIC.md         工程级配图评分标准
  CONTINUOUS_IMPROVEMENT_LOOP.md 持续开发、测试、反馈、改进闭环
  ITERATION_001_PROCESS_INTERACTION.md 第一轮工艺流程/系统交互图攻坚计划
  DEVELOPMENT_PLAN.md          基于目标的开发计划
  TODO.md                      持续任务板
  RECORD.md                    迭代记录、样本记录、结论记录
  references/                  人工提供的参考图、截图、PPT、PDF、链接说明
  generated-baselines/         当前系统生成结果的基线快照
  reviews/                     人工评审记录与对比分析
```

## 使用流程

1. 人工把参考图、截图、PPT 页、PDF 页或链接说明放入 `references/`。
2. 人工按 `REFERENCE_INTAKE_TEMPLATE.md` 说明每个参考图为什么好、哪些特征必须学习。
3. 用 `REFERENCE_INVENTORY.md` 把参考图归类成目标原型。
4. 将总体目标写入 `TARGET_BRIEF.md`。
5. 开发前读取 `CONTINUOUS_IMPROVEMENT_LOOP.md`、`ACCEPTANCE_RUBRIC.md` 和 `TODO.md`。
6. 每次优化后，把系统输出放入 `generated-baselines/` 或测试 fixture，并在 `RECORD.md` 记录对比结果。
7. 通过 `TODO.md` 持续拆解任务，不把质量提升停留在一句“优化美观”上。

## 质量方向

优先解决的不是装饰，而是表达质量：

- 一眼能看出主题、边界、层级、主路径。
- 箭头少而准，方向清楚，语义明确。
- 节点文字短、具体、可读。
- 版式稳定，元素有对齐、间距和视觉层级。
- 输出嵌入 Word 后仍清晰。
- 图形风格正式，适合投标文件，不像临时草图。

## 与代码的关系

本目录是目标和任务来源。具体实现仍在：

```text
src/bid_tool/illustration_v2/
```

真实回归样本建议沉淀到：

```text
tests/fixtures/illustration_cases/
```

每当一个质量问题可以复现，应优先转成 fixture 或 Todo，而不是只调某一张图。

## 当前参考图状态

`references/` 中已有 87 张参考图，已初步归纳为 4 类目标原型：

1. 工艺流程 / 系统交互大图。
2. 分层协作架构图。
3. 改造前后对比架构图。
4. 方法论 / 对比卡片。

第一轮建议从“工艺流程 / 系统交互大图”开始，因为它最集中地暴露信息组织、箭头治理和图例说明能力。

第一轮入口：

```text
ITERATION_001_PROCESS_INTERACTION.md
reviews/target-process-interaction.md
```
