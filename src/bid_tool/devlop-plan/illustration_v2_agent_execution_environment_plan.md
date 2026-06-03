# Illustration V2 Agent Execution Environment
# 系统工程实施计划框架

## 一、实施计划定位

`illustration_v2` 的建设不是一个普通功能开发任务，而是一个复杂系统工程。

它要解决的不是“生成一张图”，而是构建一个面向智能体的图示生成执行环境，使 Agent 能够稳定完成以下闭环：

```text
理解任务
  -> 判断图示需求
  -> 查询绘图能力
  -> 组织结构化 Job
  -> 调用执行环境
  -> 校验输入
  -> 组件化渲染
  -> 质量检查
  -> 读取反馈
  -> 修复或降级
  -> 输出可交付资产
```

因此，实施计划不能按“做几个模板、写几个脚本”的方式组织，而要按 **执行环境能力建设** 来拆解。

原始方案中已经明确提出，当前机制包括结构化 Job、能力目录、模板决策、契约校验、组件库 SVG 组装、文本排版、几何控制、SVG/PNG/manifest 输出等关键环节。后续实施计划应围绕这些环节形成系统化工程路径。

---

## 二、总体实施目标

整个实施计划的最终目标是：

> 构建一个 Agent 可发现、可调用、可校验、可反馈、可修复、可降级、可交付的图示生成执行环境。

具体可以拆成七个核心目标：

```text
1. 能力可发现
2. 输入有契约
3. 执行可控
4. 渲染稳定
5. 质量可判定
6. 失败可修复
7. 结果可交付
```

对应到系统能力，就是：

| 目标 | 系统能力 |
|---|---|
| 能力可发现 | Agent Capability Catalog |
| 输入有契约 | Job Contract / Template Contract / Component Contract |
| 执行可控 | Decision / Tier / Fallback |
| 渲染稳定 | Component Runtime / Text Layout / Geometry Control |
| 质量可判定 | QA Gate / fit_score / QAReport |
| 失败可修复 | AgentFeedbackReport / RepairInstruction |
| 结果可交付 | SVG / PNG / manifest / summary / AssetRecord |

---

## 三、总体实施框架

整个系统工程建议拆成 **八大实施域**：

```text
实施域 A：执行环境定位与接口边界
实施域 B：Agent 能力发现体系
实施域 C：结构化契约体系
实施域 D：组件化渲染运行时
实施域 E：文本排版与几何控制体系
实施域 F：质量门禁与反馈修复体系
实施域 G：降级执行与交付回执体系
实施域 H：样例、测试与持续回归体系
```

这八个实施域之间不是平行堆功能，而是有明确依赖关系：

```text
A 执行环境定位
  -> B 能力发现
  -> C 契约体系
  -> D 组件运行时
  -> E 排版与几何控制
  -> F 质量门禁与反馈修复
  -> G 降级与交付回执
  -> H 测试与持续回归
```

---

## 四、实施域 A：执行环境定位与接口边界

### 4.1 目标

先统一整个系统的根本定位：

```text
illustration_v2 不是独立绘图软件。
illustration_v2 是 Agent 的图示生成执行环境。
```

这一步是所有后续开发的基础。否则后续很容易继续按照“软件自动画图”的错误方向设计。

### 4.2 核心问题

本实施域要回答：

```text
Agent 负责什么？
illustration_v2 负责什么？
两者通过什么接口协作？
什么事情 Agent 不能直接做？
什么事情脚本不能越界做？
```

### 4.3 主要建设内容

```text
1. 统一项目文档表述
2. 统一 api.py 的调用入口说明
3. 明确 Agent 是主控方
4. 明确 illustration_v2 是执行环境
5. 明确 Agent 不直接手写 SVG
6. 明确脚本不承担深层业务理解
7. 明确质量必须由 QAReport / manifest 判定
```

### 4.4 关键交付物

```text
1. 系统总体设计文档
2. Agent Execution Environment 定位说明
3. Agent 与 illustration_v2 职责边界说明
4. API 入口说明
5. 模块职责说明
```

### 4.5 验收标准

```text
1. 所有核心文档都不再把 illustration_v2 描述为独立软件
2. 所有接口说明都面向 Agent 调用
3. 所有模块职责都能落到“执行环境”定位
4. Agent 与脚本的职责边界清晰
```

---

## 五、实施域 B：Agent 能力发现体系

### 5.1 目标

让 Agent 在生成图示前，能够明确知道当前执行环境具备哪些图示能力。

也就是说，Agent 不能靠猜，也不能靠读源码，而要通过标准能力目录发现：

```text
当前能画什么图？
每种图适合什么场景？
每个模板需要什么输入？
每个模板最多能装多少内容？
失败后能降级到哪里？
```

### 5.2 核心问题

本实施域要回答：

```text
Agent 如何知道当前支持哪些 diagram_type？
Agent 如何知道某个模板适合什么语义？
Agent 如何知道模板的容量边界？
Agent 如何知道输入字段要求？
Agent 如何知道 fallback 路径？
```

### 5.3 主要建设内容

```text
1. 增强 catalog.py
2. 建立 diagram_type 注册体系
3. 建立 template 注册体系
4. 为模板补充 best_for / not_for
5. 为模板补充 required_fields
6. 为模板补充 capacity
7. 为模板补充 text_limits
8. 为模板补充 fallback_options
9. 为模板补充 example_jobs
10. 提供 Agent 可调用的能力发现 API
```

### 5.4 核心接口形态

```python
def list_capabilities():
    pass


def describe_template(template_id):
    pass


def get_contract(template_id):
    pass


def get_examples(template_id):
    pass


def get_fallbacks(template_id):
    pass
```

### 5.5 关键交付物

```text
1. Agent Capability Catalog
2. 模板能力注册表
3. diagram_type 清单
4. template capability 描述
5. template contract 描述
6. fallback option 描述
7. example job 描述
```

### 5.6 验收标准

```text
1. Agent 可以通过 API 获得全部可用图型
2. Agent 可以知道每个模板适合和不适合的场景
3. Agent 可以知道每个模板的容量限制
4. Agent 可以知道每个模板的必填字段
5. Agent 可以知道模板失败后的降级路径
```

---

## 六、实施域 C：结构化契约体系

### 6.1 目标

建立 Agent 调用执行环境时必须遵守的结构化输入协议。

这一步的核心是把 Agent 的自由语义表达，收束成执行环境可以稳定处理的数据结构。

### 6.2 契约体系分层

结构化契约应至少分为三层：

```text
1. Job Contract
2. Template Contract
3. Component Contract
```

### 6.3 Job Contract

Job Contract 定义 Agent 提交给执行环境的总任务结构。

典型结构：

```json
{
  "version": "2.0",
  "document": {},
  "style": {},
  "illustrations": [
    {
      "id": "...",
      "type": "...",
      "renderer": "auto",
      "intent": "...",
      "insertion": {},
      "data": {}
    }
  ]
}
```

它解决的问题是：

```text
Agent 提交什么？
一次任务可以包含几张图？
每张图如何声明类型？
每张图如何表达意图？
模板数据放在哪里？
```

### 6.4 Template Contract

Template Contract 定义每个模板能接收什么结构的数据。

它解决的问题是：

```text
这个模板需要哪些字段？
每个字段是什么类型？
每类内容最多多少项？
每个文本槽位建议多少字？
哪些字段可选？
哪些字段必须存在？
```

### 6.5 Component Contract

Component Contract 定义组件运行时中每个组件需要什么输入。

它解决的问题是：

```text
组件需要哪些 props？
组件 layout 必须包含哪些字段？
组件是否允许 children？
组件输出哪些 bbox / qa metadata？
```

### 6.6 主要建设内容

```text
1. 建立 Job Schema
2. 建立 IllustrationSpec
3. 建立 Template Contract
4. 建立 Component Contract
5. 建立统一 ValidationResult
6. 建立 contract violation 错误类型
7. 将现有 examples 全部对齐新契约
```

### 6.7 关键交付物

```text
1. Job Contract 定义
2. Template Contract 定义
3. Component Contract 定义
4. 标准合法 Job 示例
5. 非法 Job 示例
6. 契约校验报告结构
```

### 6.8 验收标准

```text
1. Agent 可以根据 Job Contract 稳定构造输入
2. validator 可以判断 Job 是否符合契约
3. 模板可以根据 Template Contract 读取 data
4. 组件可以根据 Component Contract 渲染
5. 所有契约失败都能定位到具体字段路径
```

---

## 七、实施域 D：组件化渲染运行时

### 7.1 目标

将当前模板直接拼接 SVG 的方式，逐步升级为组件树渲染方式。

长期目标是：

```text
Job
  -> Template Composer
  -> ComponentSpec Tree
  -> Component Runtime
  -> SVG / PNG
```

### 7.2 核心思想

Agent 不直接生成 SVG。

模板也不应该长期散写 SVG。

模板应该负责把结构化数据编排成组件树。

组件运行时负责稳定渲染 SVG。

### 7.3 核心概念

#### ComponentSpec

```python
ComponentSpec(
    type="process_node",
    id="retry_node",
    layout={"x": 690, "y": 330, "w": 188, "h": 92},
    props={
        "title": "自动重试",
        "desc": "按策略重试上报"
    },
    children=[],
    meta={}
)
```

#### ComponentTree

```text
Canvas
  Header
  FlowStep
  FlowStep
  ExceptionCard
  ProcessNode
  InfoPanel
  Connector
  AssuranceStrip
```

### 7.4 主要建设内容

```text
1. 定义 ComponentSpec
2. 定义 ComponentTree
3. 建立 Component Registry
4. 建立 Component Renderer
5. 改造现有 components.py
6. 组件统一输出 SVG fragment
7. 组件统一输出 bbox
8. 组件统一输出 warning / qa meta
9. 模板逐步改为输出 ComponentTree
```

### 7.5 组件类型规划

基础组件：

```text
panel
tab_label
numbered_badge
flow_step
exception_card
process_node
info_panel
assurance_chip
bullet_list
connector
loop_connector
text_box
```

扩展组件：

```text
MatrixTable
PlatformStack
RadialControl
Timeline
Swimlane
MetricCard
Legend
Callout
EvidenceStrip
IconBadge
DataPipeline
CapabilityGrid
CompareBlock
RiskControlCard
```

### 7.6 模板迁移对象

现有模板包括：

```text
arch.layered.v2
platform.interface.v2
process.resilience.v2
inspection.cards.v2
severity.closure.v2
security.loop.v2
```

后续目标是全部迁移到组件树渲染模式。

### 7.7 关键交付物

```text
1. ComponentSpec 模型
2. ComponentTree 模型
3. Component Registry
4. Component Runtime Renderer
5. 组件 bbox 输出机制
6. 组件 QA metadata 输出机制
7. 组件化模板样例
```

### 7.8 验收标准

```text
1. 模板可以输出 ComponentTree
2. ComponentTree 可以被统一渲染为 SVG
3. 组件缺失时能返回结构化错误
4. 组件渲染失败时能返回 AgentFeedbackReport
5. 每个主要组件都有 bbox 信息
```

---

## 八、实施域 E：文本排版与几何控制体系

### 8.1 目标

建立稳定的文本排版和几何控制机制，避免智能体生成的内容在图示中出现溢出、重叠、错位和风格不一致。

### 8.2 文本排版目标

文本排版系统要解决：

```text
中文如何换行？
英文如何换行？
中英文混排如何处理？
标题太长怎么办？
描述太长怎么办？
列表项太多怎么办？
文本是否能放入固定槽位？
不能放下时如何反馈给 Agent？
```

### 8.3 几何控制目标

几何控制系统要解决：

```text
组件放在哪里？
组件多大？
组件之间间距多少？
连接线怎么走？
标题区域和正文区域如何分配？
底部说明区域如何固定？
画布尺寸如何统一？
```

### 8.4 核心原则

```text
Agent 不控制几何。
Agent 不决定字号。
Agent 不决定坐标。
Agent 只提供语义内容。
执行环境负责布局和排版。
```

### 8.5 主要建设内容

```text
1. 增强 TextSlot
2. 增强 fit_text()
3. 增强 emit_text()
4. 输出 data-fit
5. 输出 slot_id
6. 输出 target_chars
7. 输出 must_keep 建议
8. 统一画布尺寸
9. 统一组件布局规则
10. 统一连接线规则
```

### 8.6 关键交付物

```text
1. TextSlot 体系
2. TextFitResult
3. TextOverflowIssue
4. GeometryLayoutSpec
5. CanvasSpec
6. ConnectorLayoutRule
7. slot-level feedback
```

### 8.7 验收标准

```text
1. 中文文本可以稳定换行
2. 英文文本不破坏单词
3. 中英文混排基本稳定
4. 文本溢出能被标记
5. 文本溢出能反馈给 Agent
6. Agent 可以根据反馈压缩文本
7. 组件几何不由 Agent 直接控制
```

---

## 九、实施域 F：质量门禁与反馈修复体系

### 9.1 目标

建立完整的质量检查和反馈修复机制，使 Agent 能够判断生成结果是否可交付，并在失败时继续修复。

这一步是整个执行环境能否真正可靠的关键。

### 9.2 QA Gate

质量门禁至少包括：

```text
text fit check
component bbox check
overlap check
connector crossing check
contrast check
png export check
manifest check
```

### 9.3 QA 等级

建议分为四级：

```text
PASS：可直接交付
WARN：存在轻微问题，但可使用
REVIEW：建议人工检查
FAIL：不可交付
```

### 9.4 fit_score

fit_score 不应主观给出，而应由多项检查综合计算：

```text
文本适配
组件越界
组件重叠
连线质量
对比度
PNG 导出
manifest 完整性
```

### 9.5 AgentFeedbackReport

执行环境不能只返回错误堆栈，而要返回 Agent 可以行动的反馈。

反馈应包括：

```text
错误类型
错误位置
当前值
约束值
是否可修复
建议动作
是否建议降级
是否需要人工复核
```

### 9.6 RepairInstruction

典型修复动作包括：

```text
compress_text
merge_items
reduce_items
change_template
use_fallback
manual_review
```

### 9.7 关键交付物

```text
1. QAReport
2. QAIssue
3. fit_score 规则
4. AgentFeedbackReport
5. RepairInstruction
6. FallbackOption
7. HumanReviewAdvice
```

### 9.8 验收标准

```text
1. 生成成功不等于 QA 通过
2. QA FAIL 时 Agent 不应交付正式图
3. 文本溢出可以反馈到具体 slot
4. 组件越界可以反馈到具体 component
5. 所有可修复错误都有 suggested_action
6. 所有不可修复错误都能标记 needs_human_review
```

---

## 十、实施域 G：降级执行与交付回执体系

### 10.1 目标

标准模板失败时，系统不应直接中断，而应支持 Agent 按照明确策略继续推进任务。

同时，所有执行结果必须通过 manifest 形成标准回执。

### 10.2 降级执行策略

建议分为四级：

```text
Tier 1：标准模板组件化渲染
Tier 2：同图型简化模板
Tier 3：通用结构化模板
Tier 4：人工复核占位图
```

### 10.3 Tier 1：标准模板

适用条件：

```text
模板存在
契约通过
内容容量合规
QA PASS / WARN
```

### 10.4 Tier 2：同图型简化模板

适用条件：

```text
原模板装不下
但图型仍适合
内容可以压缩或合并
```

### 10.5 Tier 3：通用结构化模板

适用条件：

```text
具体模板不适合
但内容仍可表达为通用流程、卡片、矩阵、架构
```

典型模板：

```text
generic.flow.v1
generic.cards.v1
generic.matrix.v1
generic.architecture.v1
```

### 10.6 Tier 4：人工复核占位图

适用条件：

```text
语义复杂
契约失败
QA FAIL
多次修复失败
无合适降级模板
```

核心原则：

```text
不能把失败图伪装成成功图。
```

### 10.7 Manifest 回执体系

manifest 应该记录：

```text
asset_id
execution_status
template_id
renderer
tier
degraded_from
fallback_used
qa_level
fit_score
warnings
errors
needs_human_review
svg_path
png_path
summary_path
agent_action_required
```

### 10.8 关键交付物

```text
1. Tier 决策规则
2. fallback strategy
3. generic templates
4. manifest schema
5. AssetRecord
6. generation-summary
```

### 10.9 验收标准

```text
1. 模板失败时返回 fallback_options
2. Agent 可以选择降级路径继续执行
3. 降级信息写入 manifest
4. needs_human_review 标记准确
5. manifest 能作为 Agent 的执行结果回执
```

---

## 十一、实施域 H：样例、测试与持续回归体系

### 11.1 目标

构建系统级样例和测试体系，保证执行环境可以持续扩展，而不是靠单次运行判断是否成功。

### 11.2 样例体系

样例应分为：

```text
valid_jobs
invalid_jobs
overflow_jobs
fallback_jobs
reference_style_jobs
```

### 11.3 测试体系

测试应覆盖：

```text
catalog
contract
validator
component runtime
text layout
geometry
renderer
qa
fallback
manifest
api generate
```

### 11.4 回归目标

每次新增模板、组件、QA 规则或 fallback 策略后，都应保证：

```text
原有图型不被破坏
原有合法 Job 仍能成功
非法 Job 仍能返回预期错误
fallback 仍按预期触发
manifest 仍完整输出
```

### 11.5 关键交付物

```text
1. 示例 Job 集
2. 非法 Job 集
3. 溢出测试 Job
4. fallback 测试 Job
5. 单元测试
6. 集成测试
7. 快照测试
8. 回归测试命令
```

### 11.6 验收标准

```text
1. Agent 修改代码后可以自动运行测试
2. 合法样例必须成功
3. 非法样例必须返回结构化错误
4. fallback 样例必须进入预期降级路径
5. manifest 与 QAReport 必须完整
```

---

## 十二、系统工程依赖关系

整个系统不能随意并行堆功能，需要遵守依赖关系。

### 12.1 基础依赖链

```text
执行环境定位
  -> 能力目录
  -> 契约体系
  -> 校验反馈
  -> 组件运行时
  -> 模板组件化
  -> QA 门禁
  -> 降级策略
  -> manifest 回执
  -> 测试回归
```

### 12.2 关键依赖说明

```text
没有能力目录，Agent 不知道能调用什么。
没有契约体系，Agent 输入无法稳定执行。
没有校验反馈，Agent 无法修复错误。
没有组件运行时，模板无法稳定扩展。
没有 QA 门禁，生成成功不能代表可交付。
没有 fallback，复杂任务容易中断。
没有 manifest，Agent 无法判断执行结果。
没有测试体系，系统无法持续演进。
```

---

## 十三、完整框架总览

可以将整个实施框架概括为：

```text
Illustration V2 Agent Execution Environment

A. 执行环境定位与接口边界
   - 明确 Agent 是主控方
   - 明确 illustration_v2 是执行环境
   - 明确职责边界

B. Agent 能力发现体系
   - Capability Catalog
   - diagram_type
   - template capability
   - fallback options

C. 结构化契约体系
   - Job Contract
   - Template Contract
   - Component Contract
   - ValidationResult

D. 组件化渲染运行时
   - ComponentSpec
   - ComponentTree
   - Component Registry
   - Component Renderer

E. 文本排版与几何控制体系
   - TextSlot
   - TextFitResult
   - Geometry Control
   - Connector Layout

F. 质量门禁与反馈修复体系
   - QAReport
   - fit_score
   - AgentFeedbackReport
   - RepairInstruction

G. 降级执行与交付回执体系
   - Tier Strategy
   - Generic Fallback
   - Manifest
   - AssetRecord

H. 样例、测试与持续回归体系
   - valid jobs
   - invalid jobs
   - fallback jobs
   - regression tests
```

---

## 十四、最终实施原则

这个复杂系统工程后续拆解具体任务时，应遵守以下原则：

```text
1. 先搭执行环境边界，再做具体模板。
2. 先做能力目录，再做 Agent 调用。
3. 先做契约校验，再做渲染扩展。
4. 先做组件运行时，再迁移所有模板。
5. 先做 QA 门禁，再谈自动交付。
6. 先做反馈修复，再做复杂降级。
7. 先做样例测试，再持续扩展图型。
```

最重要的一条是：

```text
不要把它当成独立软件开发。
要把它当成 Agent 可持续使用和扩展的执行环境建设。
```

---

## 十五、下一步文档拆解建议

这份文档先完成了整个系统工程的完整框架。

后续可以继续拆成三份更具体的实施文档：

### 文档一：系统工程任务拆解文档

用于把八大实施域进一步拆成具体任务包：

```text
任务编号
任务目标
输入文件
修改位置
输出文件
验收标准
依赖关系
风险点
```

### 文档二：Agent 可执行开发任务清单

用于直接交给智能体执行：

```text
Step 1 修改哪些文件
Step 2 新增哪些模型
Step 3 写哪些测试
Step 4 运行哪些命令
Step 5 如何判断完成
```

### 文档三：模板组件化迁移专项计划

专门处理：

```text
process.resilience.v2
arch.layered.v2
platform.interface.v2
severity.closure.v2
security.loop.v2
inspection.cards.v2
generic fallback templates
```

这样可以避免一份文档过重，也能让后续任务拆解更准确。
