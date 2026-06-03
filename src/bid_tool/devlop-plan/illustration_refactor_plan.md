# Illustration V2：面向智能体的图示生成执行环境总体设计文档

## 一、文档定位

本文档用于重新定义 `illustration_v2` 的整体设计思路、系统定位、架构边界与核心机制。

需要首先明确：`illustration_v2` 不是一个独立的软件产品，也不是一个面向普通用户直接操作的自动绘图系统。它的本质是一个 **Agent Execution Environment**，即面向智能体工作的图示生成执行环境。

它的目标不是让某个软件独立完成“理解内容、判断图型、自动画图、输出结果”的完整闭环，而是为智能体提供一套稳定、可调用、可校验、可反馈、可迭代修复的工程化绘图能力。

在这个体系中，智能体是主控方，`illustration_v2` 是执行环境。

智能体负责理解用户任务、分析业务材料、判断图示表达目标、选择图型与模板、组织结构化 Job，并根据执行环境反馈持续修正。`illustration_v2` 负责能力目录、模板契约、组件运行时、文本排版、几何控制、质量门禁、错误反馈和资产输出。

原始方案已经明确提出，`illustration_v2` 的目标不是让 LLM 直接生成 SVG，而是将绘图过程拆成结构化 Job、能力目录与模板决策、契约校验、稳定组件库组装 SVG、文本排版与几何稳定控制、SVG/PNG/manifest 输出等环节。这个方向是正确的，但需要进一步从 **智能体执行环境** 的角度重新组织。

---

# 二、核心定位

## 2.1 一句话定义

`illustration_v2` 是一个面向智能体的图示生成执行环境，用于将智能体生成的结构化图示任务，稳定转化为可校验、可导出、可交付的 SVG/PNG 图示资产。

---

## 2.2 扩展定义

`illustration_v2` 不直接面对最终用户，而是作为智能体的工具运行时存在。

用户面对的是智能体。
智能体面对的是 `illustration_v2`。
`illustration_v2` 面对的是结构化 Job、模板契约、组件渲染、文本排版、质量校验和资产输出。

因此，它的设计重点不是：

```text
如何做一个自动画图软件？
```

而是：

```text
如何让智能体稳定、可控、可验证地完成图示生成任务？
```

---

## 2.3 系统本质

`illustration_v2` 的本质是：

```text
Agent 的图示生成执行环境
```

它为智能体提供：

```text
能力发现
任务契约
模板约束
组件运行时
文本排版
几何控制
质量检查
错误反馈
修复建议
资产输出
执行记录
```

它不是为了绕开智能体，而是为了增强智能体。

它让智能体从“能理解、能写作”，进一步变成“能稳定调用工具、能校验结果、能持续修复、能交付图示资产”。

---

# 三、错误视角与正确视角

## 3.1 错误视角：独立软件产品

如果把 `illustration_v2` 当成独立软件，就容易形成这样的设计思路：

```text
用户输入内容
  -> 软件自动理解
  -> 软件自动判断图型
  -> 软件自动画图
  -> 软件自动输出结果
```

这个角度存在明显问题：

1. 它把业务理解能力错误地放到了脚本系统中。
2. 它模糊了智能体和执行环境的职责边界。
3. 它容易把系统设计成臃肿的软件产品。
4. 它会导致后续不断往“软件自己智能化”的方向堆功能。
5. 它忽略了智能体才是任务规划、语义判断、工具调用和结果修正的主控方。

---

## 3.2 正确视角：Agent Execution Environment

正确视角应该是：

```text
用户提出任务
  -> 智能体理解用户目标
  -> 智能体分析业务材料
  -> 智能体判断是否需要图示
  -> 智能体选择图示表达策略
  -> 智能体调用 illustration_v2 执行环境
  -> illustration_v2 校验、渲染、导出、反馈
  -> 智能体根据反馈修正
  -> 智能体完成最终交付
```

在这个视角中：

```text
智能体是主控方。
illustration_v2 是执行环境。
```

这也是后续所有设计判断的基础。

---

# 四、总体架构

## 4.1 总体链路

```text
User Task
  ↓
Agent Planning Layer
  ↓
Illustration Agent Execution Environment
  ↓
Agent Repair Loop
  ↓
Final Delivery
```

展开后：

```text
用户提出任务
  ↓
智能体理解任务目标
  ↓
智能体分析业务内容
  ↓
智能体判断是否需要图示
  ↓
智能体查询 illustration_v2 能力目录
  ↓
智能体选择图型与模板
  ↓
智能体生成结构化 Job
  ↓
illustration_v2 校验 Job 与模板契约
  ↓
illustration_v2 生成组件树
  ↓
illustration_v2 执行文本排版与几何控制
  ↓
illustration_v2 渲染 SVG / PNG
  ↓
illustration_v2 生成 manifest / QAReport
  ↓
智能体读取执行反馈
  ↓
智能体修正、降级、重试或请求人工复核
  ↓
智能体组织最终交付
```

---

## 4.2 架构分层

整体上可以分为四层：

```text
Agent Layer
  智能体任务理解、规划、选择、修正和交付

Execution Contract Layer
  能力目录、Job 契约、模板契约、组件契约

Rendering Runtime Layer
  组件运行时、文本排版、几何控制、SVG/PNG 渲染

Feedback & Delivery Layer
  QAReport、AgentFeedbackReport、manifest、资产输出
```

---

# 五、智能体与执行环境的职责边界

## 5.1 智能体负责什么

智能体负责上层智能和任务推进。

主要包括：

```text
理解用户意图
理解投标、方案、文档、材料内容
判断哪里需要图示
判断图示要表达什么
选择图示类型
选择合适模板
组织结构化 Job
压缩和改写图示文案
调用 illustration_v2
读取校验结果
读取 QAReport
读取 manifest
根据反馈修改 Job
必要时更换模板
必要时触发降级
必要时请求人工复核
生成最终交付说明
```

智能体在系统中扮演的是：

```text
任务规划者
业务理解者
语义判断者
工具调用者
反馈修正者
最终交付者
```

---

## 5.2 illustration_v2 负责什么

`illustration_v2` 负责确定性执行。

主要包括：

```text
暴露当前图示能力
维护能力目录
声明模板契约
校验 Job 合法性
校验模板容量
校验组件输入
执行固定几何布局
调用稳定组件库
处理文本换行
控制字号和槽位
生成 SVG
导出 PNG
生成 manifest
执行质量门禁
返回结构化错误
返回修复建议
标记是否需要人工复核
```

`illustration_v2` 在系统中扮演的是：

```text
能力环境
工具运行时
契约校验器
组件渲染器
文本排版器
几何控制器
质量门禁
反馈系统
资产输出器
```

---

# 六、核心设计原则

## 6.1 智能体可以决策，但不能绕过执行环境

智能体可以选择图型、模板和内容表达，但最终是否能执行、是否装得下、是否渲染成功、是否可交付，必须由执行环境校验。

```text
智能体可以选择模板。
但模板是否可用，由 illustration_v2 校验。

智能体可以组织内容。
但内容是否装得下，由 illustration_v2 判断。

智能体可以压缩文案。
但压缩后是否 fit，由 illustration_v2 检查。

智能体可以判断图示意图是否合理。
但图是否可交付，由 QAReport 判断。
```

---

## 6.2 智能体不直接手写 SVG

智能体不应该直接生成：

```text
SVG path
x / y / w / h
font-size
line-height
marker
rect
line
复杂坐标
自由 SVG 结构
```

原因是：

```text
直接生成 SVG 容易漂移
坐标一致性难以保证
文本排版容易溢出
视觉风格难以统一
后续维护成本高
无法形成稳定可复用能力
```

智能体应该生成结构化 Job，而不是底层 SVG。

---

## 6.3 脚本不承担深层业务理解

`illustration_v2` 不应该负责判断：

```text
这段材料的核心观点是什么
哪个章节最需要配图
图示应该服务什么叙事目的
不同图示之间如何形成整体表达
业务内容应该如何提炼
```

这些属于智能体的职责。

`illustration_v2` 只回答：

```text
这个 Job 是否合法
这个模板能否承载
这个组件能否渲染
这个文本是否溢出
这张图是否通过 QA
输出资产在哪里
```

---

## 6.4 质量不能由智能体主观宣布

智能体不能只凭主观判断说“图已经合格”。

最终质量必须由执行环境返回：

```text
QAReport
fit_score
warnings
errors
needs_human_review
manifest
```

也就是说：

```text
智能体负责解释结果。
illustration_v2 负责判定执行质量。
```

---

## 6.5 失败不是终点，而是反馈

`illustration_v2` 不能只返回异常堆栈，而要返回智能体可以理解、可以继续行动的结构化反馈。

错误反馈应该回答：

```text
哪里错了？
为什么错了？
能不能修？
应该怎么修？
是否建议降级？
是否需要人工复核？
```

这使得智能体可以形成修复闭环，而不是一次失败就中断任务。

---

# 七、核心概念模型

## 7.1 Capability Catalog：能力目录

能力目录是智能体发现绘图能力的入口。

它告诉智能体：

```text
当前能画什么类型的图
每种图适合表达什么内容
每种模板支持什么结构
每种模板容量是多少
哪些字段必须提供
哪些内容容易超限
什么情况下不适合使用该模板
失败后可以降级到什么模板
```

能力目录不是给普通用户看的配置，而是给智能体调用的能力索引。

---

## 7.2 Job Contract：任务输入契约

Job Contract 是智能体调用执行环境时必须遵守的数据协议。

它把智能体的自由语义表达，收束成执行环境可以处理的结构化输入。

典型结构包括：

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

其中：

```text
type 决定图型能力
renderer 表示渲染策略
intent 说明图示表达意图
data 承载模板所需结构化内容
```

---

## 7.3 Template Contract：模板契约

模板契约定义每个模板能承载什么内容、不能承载什么内容。

它至少应该包括：

```text
template_id
diagram_type
required_fields
optional_fields
capacity
text_limits
component_dependencies
fallback_options
qa_rules
example_jobs
```

模板契约的价值在于：

```text
让智能体知道如何组织输入
让 validator 有明确校验依据
让失败反馈可以指向具体字段
让后续降级策略有依据
```

---

## 7.4 Component Runtime：组件运行时

组件运行时是执行环境的核心。

它负责把模板编排结果渲染为稳定 SVG。

理想状态下，模板不应该直接拼 SVG，而是输出标准组件树：

```text
Agent 生成 Job
  -> 模板生成 ComponentSpec Tree
  -> Component Runtime 渲染 SVG
```

组件可以包括：

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
```

组件运行时解决的是图示稳定性问题。

---

## 7.5 Text Layout Engine：文本排版引擎

文本排版引擎负责判断智能体提供的文本能否安全进入固定槽位。

它需要支持：

```text
中文排版
英文排版
中英文混排
自动换行
字号降级
最大行数控制
slot fit 检查
data-fit 标记
排版反馈输出
```

它不只是“排版工具”，更是智能体文本表达的容量控制器。

它应该能告诉智能体：

```text
哪个文本槽位放不下
当前文本多长
目标长度是多少
必须保留哪些关键词
建议采取什么修复动作
```

---

## 7.6 Geometry Control：几何控制

几何控制必须由执行环境负责，不能交给智能体自由决定。

包括：

```text
画布尺寸
组件位置
组件大小
组件间距
连接线位置
箭头样式
边框圆角
标题区域
内容槽位
底部说明区域
```

智能体只决定语义结构，不决定几何细节。

---

## 7.7 QA Gate：质量门禁

每次渲染后，必须经过质量门禁。

检查项包括：

```text
text fit check
component bbox check
overlap check
connector crossing check
contrast check
png export check
manifest check
```

QA 结果建议分为：

```text
PASS：可直接交付
WARN：存在轻微问题，但可用
REVIEW：建议人工检查
FAIL：不可交付
```

质量门禁的意义是防止智能体把失败图、溢出图、错位图当成正式结果交付。

---

## 7.8 AgentFeedbackReport：智能体反馈报告

AgentFeedbackReport 是执行环境返回给智能体的结构化反馈。

它不是普通错误信息，而是智能体下一步行动的依据。

它应该包括：

```text
执行状态
是否可修复
需要智能体采取什么动作
错误列表
修复目标
降级选项
是否需要人工复核
```

示例结构：

```json
{
  "status": "validation_failed",
  "can_repair": true,
  "agent_action_required": "repair_job",
  "issues": [
    {
      "type": "text_overflow",
      "path": "illustrations[0].data.mechanisms[2].title",
      "current_text": "异常数据自动补传与一致性校验",
      "target_chars": 8,
      "must_keep": ["补传", "校验"],
      "suggested_action": "compress_text"
    }
  ],
  "fallback_options": [
    {
      "template_id": "generic.flow.v1",
      "reason": "当前内容超过 process.resilience.v2 容量"
    }
  ],
  "needs_human_review": false
}
```

---

## 7.9 Manifest：执行结果回执

manifest 是智能体判断本次执行结果的标准回执。

它应该回答：

```text
生成了哪些资产
使用了哪个模板
走了哪个 tier
是否发生降级
是否存在 warning
是否通过 QA
fit_score 是多少
是否需要人工复核
SVG 路径在哪里
PNG 路径在哪里
summary 路径在哪里
```

manifest 不只是文件清单，而是一次工具调用后的完整结果记录。

---

# 八、标准执行流程

## 8.1 成功执行流程

```text
1. 用户提出任务
2. 智能体理解任务和材料内容
3. 智能体判断需要生成图示
4. 智能体查询 illustration_v2 能力目录
5. 智能体选择合适图型和模板
6. 智能体生成结构化 Job
7. illustration_v2 校验 Job
8. illustration_v2 规划执行路径
9. illustration_v2 生成组件树
10. illustration_v2 渲染 SVG
11. illustration_v2 导出 PNG
12. illustration_v2 执行 QA
13. illustration_v2 输出 manifest
14. 智能体读取结果
15. 智能体交付图示资产
```

---

## 8.2 修复执行流程

```text
1. 智能体提交 Job
2. validator 返回 validation_failed
3. 智能体读取 AgentFeedbackReport
4. 智能体压缩文本、合并条目或调整结构
5. 智能体再次提交 Job
6. illustration_v2 重新校验
7. 校验通过后继续渲染
```

---

## 8.3 降级执行流程

```text
1. 智能体选择标准模板
2. 执行环境发现内容无法装入模板
3. 返回 capacity_exceeded 或 layout_failed
4. 智能体尝试压缩内容
5. 如果仍失败，智能体选择同图型简化模板
6. 如果仍失败，智能体选择通用结构化模板
7. 如果仍失败，输出人工复核占位图
```

---

# 九、Tier 执行策略

## 9.1 Tier 1：标准模板组件化渲染

适用条件：

```text
模板存在
契约通过
内容容量合规
QA PASS 或 WARN
```

输出：

```text
正式 SVG
正式 PNG
manifest
QAReport
needs_human_review = false
```

Tier 1 是最理想路径。

---

## 9.2 Tier 2：同图型简化模板

适用条件：

```text
原模板装不下
但图型仍然适合
内容可以压缩或合并
```

处理方式：

```text
减少卡片数量
合并同类项目
缩短标题描述
改用简单版布局
```

Tier 2 的目标是保留原图型表达，但降低内容密度。

---

## 9.3 Tier 3：通用结构化模板

适用条件：

```text
具体模板不适合
但内容仍可表达为通用流程、卡片、矩阵或架构
```

可提供：

```text
generic.flow.v1
generic.cards.v1
generic.matrix.v1
generic.architecture.v1
```

Tier 3 的目标是保留核心信息，而不强求使用原模板。

---

## 9.4 Tier 4：人工复核占位图

适用条件：

```text
语义复杂
契约失败
QA FAIL
智能体多次修复失败
无合适降级模板
```

输出：

```text
needs_human_review = true
结构化摘要
失败原因
建议人工处理方向
```

核心原则：

```text
不能把失败图伪装成成功图。
```

---

# 十、当前目录与模块定位

基于现有方案，当前目录大致包括：

```text
src/bid_tool/illustration_v2/
  api.py
  core/
    models.py
    catalog.py
    decision.py
    validator.py
    text_measure.py
    manifest.py
  renderers/
    components.py
    template_svg.py
  templates/
  examples/
  materials/
```

从 Agent Execution Environment 的视角看，各模块应重新理解为：

---

## 10.1 api.py

不是普通对外接口，而是智能体调用执行环境的入口。

它应承担：

```text
读取 Job
校验 Job
规划执行路径
触发渲染
触发 QA
输出 manifest
返回 Agent 可读结果
```

---

## 10.2 catalog.py

不是普通模板配置，而是智能体能力发现目录。

它应承担：

```text
声明可用图型
声明可用模板
声明模板适用场景
声明模板容量
声明文本限制
声明降级路径
声明示例 Job
```

---

## 10.3 validator.py

不是普通字段校验，而是智能体输入契约校验器。

它应承担：

```text
检查 Job 是否满足基础契约
检查模板必填字段
检查容量限制
检查文本限制
检查结构合法性
返回可修复反馈
```

---

## 10.4 decision.py

不是简单模板选择器，而是执行路径裁决器。

它应承担：

```text
判断是否能走 Tier 1
判断是否需要降级
判断是否需要人工复核
记录 degraded_from
记录 fallback_used
输出执行决策
```

---

## 10.5 components.py

不是普通 SVG 代码集合，而是稳定图形原语库。

它应承担：

```text
提供可复用图形组件
隔离底层 SVG 细节
统一视觉风格
输出组件 bbox
支持 QA 检查
```

---

## 10.6 text_measure.py

不是简单文本换行工具，而是文本容量控制器。

它应承担：

```text
判断文本能否放入槽位
处理中英文混排
输出 data-fit
生成文本溢出反馈
为智能体修复文案提供依据
```

---

## 10.7 manifest.py

不是普通输出清单，而是智能体执行结果回执。

它应承担：

```text
记录生成资产
记录模板和渲染器
记录 tier
记录 QA 结果
记录 warnings
记录是否降级
记录是否需要人工复核
```

---

# 十一、后续架构演进方向

## 11.1 从模板直出 SVG 演进为组件树渲染

当前部分模板仍然可能直接拼接 SVG。长期应演进为：

```text
Job
  -> Template Composer
  -> ComponentSpec Tree
  -> Component Runtime
  -> SVG / PNG
```

这样可以提升：

```text
稳定性
复用性
可测试性
可校验性
可扩展性
```

---

## 11.2 从字段校验演进为 Agent 可修复反馈

校验失败不能只是报错，而要变成智能体下一步行动的依据。

未来所有失败都应该尽量转化为：

```text
错误类型
错误路径
当前值
约束值
建议动作
是否可修复
是否建议降级
是否需要人工复核
```

---

## 11.3 从生成成功演进为质量可判定

生成出 SVG/PNG 不等于图示可交付。

后续要建立完整质量门禁：

```text
文本是否溢出
组件是否越界
组件是否重叠
连线是否异常
对比度是否足够
PNG 是否成功导出
manifest 是否完整
```

只有通过 QA 的结果，才能被智能体作为正式资产交付。

---

## 11.4 从单模板失败演进为降级执行链

标准模板失败后，系统不应该中断，而应该提供降级路径。

理想策略是：

```text
标准模板
  -> 同图型简化模板
  -> 通用结构化模板
  -> 人工复核占位图
```

这能保证智能体在复杂任务中具备持续推进能力。

---

## 11.5 从静态脚本演进为智能体工具运行时

最终，`illustration_v2` 不只是若干 Python 脚本，而应成为智能体可以稳定使用的工具运行时。

它应该具备：

```text
可发现
可调用
可校验
可反馈
可修复
可降级
可追踪
可交付
```

---

# 十二、建议的未来目录形态

后续可以逐步演进为：

```text
src/bid_tool/illustration_v2/
  api.py

  core/
    models.py
    catalog.py
    decision.py
    validator.py
    component_model.py
    agent_report.py
    manifest.py
    text_measure.py

  contracts/
    job_schema.py
    template_contracts.py
    component_contracts.py

  renderers/
    components.py
    component_svg.py
    template_svg.py

  qa/
    text_fit.py
    bbox.py
    overlap.py
    connector.py
    contrast.py
    raster.py
    report.py

  templates/
    arch_layered/
    platform_interface/
    process_resilience/
    inspection_cards/
    severity_closure/
    security_loop/
    generic_flow/
    generic_cards/
    generic_matrix/

  examples/
    valid_jobs/
    invalid_jobs/
    fallback_jobs/

  materials/
    references/
```

这个目录结构服务于一个目标：

```text
让智能体能清楚发现能力、提交任务、获得反馈、修正输入、完成交付。
```

---

# 十三、总体设计总结

`illustration_v2` 的核心价值，不在于它自己“变聪明”，而在于它让智能体拥有稳定的工程化绘图能力。

最终系统应该形成如下结构：

```text
Agent
  负责：
    理解任务
    判断图示需求
    选择图型模板
    组织结构化 Job
    调用执行环境
    读取反馈
    修复输入
    完成交付

illustration_v2
  负责：
    暴露能力目录
    定义输入契约
    校验 Job
    控制模板容量
    生成组件树
    稳定渲染 SVG
    导出 PNG
    执行 QA
    输出 manifest
    返回修复建议
```

最重要的边界是：

```text
智能体不直接手写 SVG。
智能体不直接控制几何。
智能体不绕过契约校验。
智能体不主观宣布质量合格。

illustration_v2 不负责深层业务理解。
illustration_v2 不替代智能体做任务规划。
illustration_v2 不自由改写业务内容。
illustration_v2 只负责确定性执行、校验、渲染、反馈和交付。
```

---

# 十四、最终定位表述

建议在正式方案开头使用下面这段作为核心定义：

> `illustration_v2` 的本质不是一个独立绘图软件，而是一个面向智能体的图示生成执行环境。
> 它不直接面对最终用户，而是作为 Agent 的工具运行时存在。
> 智能体负责理解用户任务、分析业务材料、判断图示表达目标、选择图型与模板、组织结构化 Job 并调用该环境；`illustration_v2` 负责提供能力目录、模板契约、组件运行时、文本排版、几何控制、质量门禁、错误反馈和资产输出。
> 因此，本系统的设计重点不是“让软件自动画图”，而是“让智能体能够稳定、可控、可验证地完成图示生成任务”。

一句话概括：

> **Illustration V2 是智能体的图示生成执行环境。
> 它让智能体从“能理解、能写作”，进一步具备“能稳定调用工具、能校验结果、能持续修复、能交付图示资产”的工程化执行能力。**
