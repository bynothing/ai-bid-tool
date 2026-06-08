# 智能体开发复杂工程应用的方法论

副标题：以 `bid-tool` 自动标书系统为例

最后更新：2026-06-08

## 1. 为什么需要一套方法论

复杂工程应用不是一次性功能开发。它通常具备这些特征：

- 目标长期演化，不可能一次设计完。
- 涉及多个模块、阶段、数据契约、质量标准和交付形式。
- 人和智能体会在不同会话中持续接力。
- 很多问题一开始是模糊的，比如“配图不好看”“标书不够专业”“输出不稳定”。
- 如果只依赖智能体长期记忆，项目上下文会漂移，任务会重复分析，开发方向会失焦。

因此，复杂工程应用首先要建设的不是某个功能，而是一套可持续工程化协作系统。

在 `bid-tool` 中，我们面对的是一个自动标书系统：

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

这类系统的核心不是“让智能体多写代码”，而是让智能体和人都能持续理解、计划、执行、验证、记录和改进。

## 2. 总原则：先治理工程上下文，再治理功能

复杂系统开发最容易失败的地方，不是代码写不出来，而是上下文失控：

- 文件放置混乱。
- 目标和现状混在一起。
- TODO 分散在聊天记录里。
- 已完成功能没人维护。
- 输出质量靠主观感觉。
- 每次新会话都重新摸索。

因此，第一原则是：

```text
复杂工程先建立外置记忆系统，再进入功能迭代。
```

`bid-tool` 的做法是建立三类入口：

| 层级 | 文件 | 作用 |
| --- | --- | --- |
| 总入口 | `WORKSPACE.md` | 项目持续开发入口 |
| 智能体入口 | `AGENTS.md` | 新会话启动协议 |
| 导航入口 | `docs/NAVIGATION.md` | 按任务类型找文件 |

智能体进入项目，不靠回忆，而是执行固定读取顺序：

```powershell
git status --short --branch
Get-Content WORKSPACE.md -TotalCount 220
Get-Content docs\workspace\STATE.md -TotalCount 220
Get-Content docs\PROJECT_BUILD_OVERVIEW.md -TotalCount 260
Get-Content docs\PROJECT_FEATURES.md -TotalCount 260
Get-Content docs\PROJECT_TODO.md -TotalCount 260
Get-Content docs\NAVIGATION.md -TotalCount 260
Get-Content docs\FILE_GOVERNANCE.md -TotalCount 260
```

这一步的目标，是让每次开发都有同一个起点。

## 3. 方法框架：五层项目记忆

复杂工程应用建议建立五层项目记忆。

### 3.1 项目总控层

回答：

- 我们在建什么。
- 当前做到哪。
- 当前主线是什么。
- 最大短板是什么。
- 下一步优先级是什么。

`bid-tool` 对应文件：

```text
docs/PROJECT_BUILD_OVERVIEW.md
```

它不是详细计划，而是工程项目级总控。

### 3.2 已完成功能层

回答：

- 已经具备哪些能力。
- 成熟度如何。
- 入口在哪里。
- 有什么限制。
- 怎么验证。

`bid-tool` 对应文件：

```text
docs/PROJECT_FEATURES.md
```

成熟度可以用 M0-M4：

| 等级 | 含义 |
| --- | --- |
| M0 | 只有概念或文档 |
| M1 | 有原型实现 |
| M2 | 有测试或 smoke |
| M3 | 可进入主流程 |
| M4 | 工程级稳定，有真实样本和质量门禁 |

这能避免两个问题：

- 已有能力被重复实现。
- 原型能力被误认为可交付能力。

### 3.3 TODO 任务层

回答：

- 接下来做什么。
- 优先级是什么。
- 当前状态是什么。
- 完成标准是什么。

`bid-tool` 对应文件：

```text
docs/PROJECT_TODO.md
```

任务必须包含：

```text
ID / 状态 / 任务 / 验收 / 关联文档
```

坏任务：

```text
优化配图。
```

好任务：

```text
P0-001：配图质量第一轮：工艺流程 / 系统交互大图
验收：完成基线、评分、契约草案和首个实现路径
```

### 3.4 状态和交接层

回答：

- 当前工作区状态是什么。
- 最近跑过什么验证。
- 哪些风险要注意。
- 下一次从哪里继续。

`bid-tool` 对应文件：

```text
docs/workspace/STATE.md
docs/workspace/SESSION_HANDOFF.md
```

这层文件应该写事实，不写愿望。

### 3.5 决策记录层

回答：

- 为什么选择这个架构。
- 为什么不选择另一条路线。
- 这个决策影响哪些模块。

`bid-tool` 对应文件：

```text
docs/workspace/DECISION_LOG.md
```

复杂工程最怕反复推翻。决策日志不是形式主义，它是给未来的人和智能体看的“为什么”。

## 4. 文件治理：让目录结构成为工程协议

复杂项目不能让文件自然生长。文件结构本身必须被治理。

`bid-tool` 建立了：

```text
docs/PROJECT_STRUCTURE.md
docs/FILE_GOVERNANCE.md
```

核心规则：

- 运行时代码放 `src/bid_tool/`。
- 项目级计划、状态、架构和标准放 `docs/`。
- 测试样本放 `tests/fixtures/`。
- 用户示例放 `examples/`。
- 临时输出放 `output/`。
- 大型参考图片默认不入 Git，只保留说明和索引。

对于智能体来说，文件治理有两个价值：

1. 减少查找成本。
2. 降低误改、误提交、误删的风险。

例如 `bid-tool` 中的配图参考图达到 151MB 左右，如果不治理，仓库很快会变重。正确做法是：

```text
参考图本地存放
  -> README / inventory / review 入库
  -> 关键样本转 fixture
  -> 大图默认 .gitignore
```

## 5. 把模糊目标转成质量闭环

复杂工程中很多重要问题最初都很模糊。

例如 `bid-tool` 的核心问题之一：

```text
配图能生成，但不好看、不清楚、箭头混乱，没有工程级效果。
```

这种问题不能直接进入代码实现。必须先转成闭环：

```text
人工参考目标
  -> 质量评分标准
  -> 当前系统基线
  -> 差距分析
  -> 任务拆解
  -> 开发实现
  -> 自动验证
  -> 人工复评
  -> 回归沉淀
```

`bid-tool` 对应目录：

```text
docs/quality-targets/illustration/
```

其中：

| 文件 | 作用 |
| --- | --- |
| `REFERENCE_INVENTORY.md` | 盘点参考图，归纳目标原型 |
| `ACCEPTANCE_RUBRIC.md` | 将“好看/清楚”转成评分 |
| `TODO.md` | 配图质量专项任务 |
| `CONTINUOUS_IMPROVEMENT_LOOP.md` | 持续改进流程 |
| `ITERATION_001_PROCESS_INTERACTION.md` | 第一轮具体攻坚计划 |
| `RECORD.md` | 每轮记录 |

这背后的通用方法是：

```text
不要直接优化主观感受。
先定义目标，再建立评分，再生成基线，再做开发。
```

## 6. 复杂功能要分成“主线 + 专项”

在 `bid-tool` 中，项目总目标是自动标书生成，但当前最重要专项是配图质量。

项目级主线：

```text
标书自动化：解析 -> 写作 -> 表格 -> 配图 -> 校验 -> 导出
```

专项主线：

```text
配图质量：参考图 -> 评分 -> 基线 -> 契约 -> 渲染 -> QA -> 回归
```

两者不能混在一个 TODO 里，也不能互相割裂。

推荐结构：

```text
docs/PROJECT_TODO.md                     全工程任务
docs/quality-targets/<domain>/TODO.md    专项任务
```

项目级 TODO 只记录关键任务入口，专项 TODO 负责细节拆解。

## 7. 代码实现前先定义契约

智能体开发复杂工程时，很容易直接修改代码。但复杂系统真正稳定的是契约。

在 `bid-tool` 中，契约包括：

- Pipeline 阶段输出 Schema。
- Illustration Job v2 Schema。
- Manifest 输出契约。
- 模板 contract。
- Prompt 输入输出格式。

配图质量问题也要先转成契约，例如：

```text
sections[]          业务段/工艺段
steps[]             段内步骤
primary_flow[]      主流程
support_flows[]     辅助流程
interaction_types[] 交互点类型
legend              图例
glossary            术语说明
```

只有契约清楚，渲染器才有稳定输入，测试才有明确对象。

方法原则：

```text
先约束输入，再实现输出。
先定义失败，再追求成功。
```

## 8. 每次开发都要闭环

复杂工程开发不能以“我改完了”结束，而要以“状态被更新，下一次能继续”结束。

推荐闭环：

```text
读取状态
  -> 选择 TODO
  -> 小步实现
  -> 自动测试
  -> 生成样本
  -> 人工/规则评审
  -> 更新 TODO
  -> 更新状态
  -> 必要时更新决策和 changelog
```

`bid-tool` 的最小验证：

```powershell
python -m pytest
```

配图相关还要有 smoke：

```powershell
python -m bid_tool.illustration_v2.toolkit --job <job.json> --output <output-dir> --png
```

如果涉及质量专项，还要有：

- Rubric 评分。
- Review 记录。
- Manifest 检查。
- Fixture 或 baseline。

## 9. 智能体协作的关键纪律

### 9.1 不依赖长期记忆

所有重要状态都必须落文件：

- 当前状态。
- 下一步。
- 决策理由。
- 质量目标。
- 任务完成情况。

### 9.2 不把聊天记录当项目管理

聊天可以启发，不能作为唯一记录。结论要落到：

- `PROJECT_TODO.md`
- `PROJECT_FEATURES.md`
- `STATE.md`
- `DECISION_LOG.md`
- 专项 `RECORD.md`

### 9.3 不让输出目录变成知识源

`output/` 是生成产物，不是事实来源。重要输出必须转成：

- fixture
- manifest
- review
- record
- 文档说明

### 9.4 不把原型当成熟能力

必须记录成熟度。M1 原型和 M4 工程级能力完全不同。

### 9.5 不让“优化”没有验收

每个 TODO 都要有验收。尤其是质量类任务。

## 10. 可复用模板

任何复杂工程应用都可以采用以下文件结构：

```text
PROJECT/
  README.md
  WORKSPACE.md
  AGENTS.md
  CHANGELOG.md
  docs/
    NAVIGATION.md
    FILE_GOVERNANCE.md
    PROJECT_BUILD_OVERVIEW.md
    PROJECT_FEATURES.md
    PROJECT_TODO.md
    PROJECT_STRUCTURE.md
    workspace/
      STATE.md
      ROADMAP.md
      DECISION_LOG.md
      KNOWLEDGE_MAP.md
      MAINTENANCE_PROTOCOL.md
      SESSION_HANDOFF.md
    architecture/
    standards/
    quality-targets/
  src/
  tests/
  examples/
  tools/
  output/
```

最小版本可以只保留：

```text
WORKSPACE.md
AGENTS.md
docs/PROJECT_BUILD_OVERVIEW.md
docs/PROJECT_FEATURES.md
docs/PROJECT_TODO.md
docs/workspace/STATE.md
docs/workspace/DECISION_LOG.md
```

## 11. bid-tool 当前实践总结

`bid-tool` 目前已经完成了工程上下文治理的地基：

- 建立项目级总控。
- 建立已完成功能清单。
- 建立全工程 TODO。
- 建立智能体启动协议。
- 建立文件治理规则。
- 建立源码地图。
- 建立配图质量目标体系。
- 将“配图不好”转化为第一轮可执行质量攻坚。

当前下一步不是继续写更多文档，而是执行第一个闭环任务：

```text
P0-001 / IQ-008
生成系统交互大图当前基线
  -> 保存 job/manifest/output
  -> 按 Rubric 打分
  -> 转成契约草案和开发任务
```

这就是复杂工程智能体开发的核心节奏：

```text
先让项目能被理解，
再让任务能被执行，
再让结果能被验证，
最后让经验能被沉淀。
```
