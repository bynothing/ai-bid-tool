# Illustration V2 当前绘图机制架构说明

## 1. 当前目标

`illustration_v2` 的目标不是让 LLM 直接生成 SVG，而是把绘图过程拆成：

```text
外部内容/投标语义
  -> 结构化 Job
  -> 能力目录与模板决策
  -> 契约校验
  -> 稳定组件库组装 SVG
  -> 文本排版与几何稳定控制
  -> SVG/PNG/manifest 输出
```

核心原则：

- LLM 负责语义判断和结构化填充。
- 软件脚本负责确定性排版、组件渲染、校验和导出。
- SVG 内的可视元素尽量由稳定组件产生，而不是在模板中散写大量 `<rect>/<text>/<line>`。
- 运行时输入只影响组件内容和少量主题变量，不直接改动组件几何。

## 2. 当前目录分工

```text
src/bid_tool/illustration_v2/
  api.py                         对外调用入口
  core/
    models.py                    Job、Template、PlanDecision、AssetRecord 等数据模型
    catalog.py                   能力目录：模板、渲染器、契约、主题
    decision.py                  当前确定性决策层：选模板、选 tier、记录降级原因
    validator.py                 Job 与模板契约校验
    text_measure.py              中文/英文感知文本排版、测量、tspan 输出
    manifest.py                  输出 illustration-manifest.json 与 summary
  renderers/
    components.py                稳定 SVG 基础组件库
    template_svg.py              目前的模板渲染器与组件编排入口
  templates/
    ...                          模板说明、契约、快照位置
  examples/
    arch_layered_job.json        中文分层架构示例
    reference_style_job.json     中文参考风格五图示例
  materials/
    references/...               旧图示例素材，仅作视觉参考
```

## 3. 当前完整调用链

### 3.1 API 入口

调用方通过：

```python
from bid_tool.illustration_v2 import api

job = api.load_job(path)
errors, warnings = api.validate(job)
decisions = api.plan(job)
records = api.render(job, output, png=True)
```

当前 API 做四件事：

1. 读取 JSON Job。
2. 校验基础字段和模板契约。
3. 进行模板/渲染器决策。
4. 渲染 SVG/PNG，并写 manifest。

### 3.2 Job 输入

当前 Job 是结构化 JSON，核心字段是：

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

- `type` 决定候选图型能力，例如 `process.resilience_flow`。
- `renderer=auto` 表示由决策层选择渲染路径。
- `data` 是组件/模板的结构化内容来源。

## 4. 当前支持的 Tier 机制

当前决策层在 `core/decision.py` 中，是确定性逻辑：

### Tier 1：模板 SVG / 组件化 SVG

条件：

- 图型在能力目录中有注册模板。
- 输入内容通过模板契约校验。
- `fit_score >= 0.82`。

输出：

- `renderer = template_svg`
- `template = xxx.v2`
- `needs_human_review = false`

这是当前主路线。

### Tier 2：结构化 SVG 降级

条件：

- 图型有候选模板，但内容装不进模板契约。

输出：

- `renderer = structured_svg_fallback`
- manifest 中记录 `degraded_from` 和 `fallback`

### Tier 3：自由 SVG 兜底

条件：

- 没有注册模板。

输出：

- `renderer = free_svg_floor`
- `needs_human_review = true`

当前 Tier 2/3 仍比较简化，后续需要继续组件化。

## 5. 当前能力目录

`core/catalog.py` 注册了当前模板与契约：

| Template | Diagram Type | 来源 |
| --- | --- | --- |
| `arch.layered.v2` | `architecture.layered` | 分层架构试点 |
| `platform.interface.v2` | `relationship.platform_interface` | 参考图 3 |
| `process.resilience.v2` | `process.resilience_flow` | 参考图 4 |
| `inspection.cards.v2` | `taxonomy.inspection_cards` | 参考图 5 |
| `severity.closure.v2` | `process.severity_closure` | 参考图 6 |
| `security.loop.v2` | `security.closed_loop` | 参考图 7 |

能力目录当前包含：

- 模板 id。
- 图型 type。
- 渲染器。
- 模板摘要。
- 契约类型 `schema_kind`。
- 必填字段。
- 文本长度限制。
- 容量限制。
- 主题变量。

后续 LLM 选择图型和模板时，应该优先消费这份能力目录。

## 6. 当前组件库

`renderers/components.py` 是当前新增的基础组件库。

已有组件：

| 组件 | 作用 |
| --- | --- |
| `panel` | 稳定区域背景/边框 |
| `tab_label` | 固定标题胶囊 |
| `numbered_badge` | 序号圆标 |
| `flow_step` | 横向流程步骤节点 |
| `exception_card` | 异常/告警卡片 |
| `process_node` | 中间处理节点 |
| `info_panel` | 右侧说明面板 |
| `assurance_chip` | 底部保障点 |
| `bullet_list` | 稳定 bullet 列表 |
| `connector` | 折线/直线连接线 |
| `loop_connector` | 闭环/循环连接线 |
| `text_box` | 文本槽位排版组件 |

当前已经优先把 `process.resilience.v2` 的主要区域改为组件化渲染。

## 7. 文本排版机制

`core/text_measure.py` 控制所有动态文本的稳定排版。

当前能力：

- `TextSlot` 定义固定文本槽位。
- `fit_text()` 根据槽位宽高进行排版。
- `emit_text()` 输出 `<text><tspan>`，不再散写多行 `<text>`。
- `language = auto/cjk/latin`。
- 中文主导内容走 `cjk` 策略。
- 英文主导内容走 `latin` 策略。
- 混排时保留英文连续词，中文按 CJK 密集排版。
- 输出 SVG 中带 `data-fit="true|false"` 和 `data-strategy="cjk|latin"`，便于 QA。

当前测试已经验证：

- 中文内容会走 `cjk`。
- 英文内容会走 `latin`。
- 中文参考样例中没有 `data-fit="false"`。

## 8. LLM 当前控制什么

严格来说，`illustration_v2` 当前运行时本身还没有直接调用 LLM。

但在完整 bid-tool 流水线里，LLM 应该控制这些环节：

### 8.1 内容理解

LLM 读取投标章节、需求、技术方案，判断一张图要表达什么：

- 是流程？
- 是接口关系？
- 是分级响应？
- 是安全闭环？
- 是巡检分类？
- 是架构分层？

### 8.2 图型选择

LLM 基于能力目录选择：

```text
diagram_type
template_id
renderer preference
```

例如：

```json
{
  "type": "process.resilience_flow",
  "renderer": "auto"
}
```

### 8.3 结构化内容填充

LLM 不写 SVG，只填模板契约要求的数据：

```json
{
  "steps": [],
  "exceptions": [],
  "mechanisms": [],
  "sidePanels": [],
  "assurance": []
}
```

### 8.4 内容压缩/改写

当某个槽位装不下时，未来 LLM 可以根据软件反馈做“保意缩写”：

```json
{
  "slot_id": "mechanism.title",
  "original_text": "...",
  "target_chars": 8,
  "must_keep": ["补传", "重试"]
}
```

LLM 的职责是保留语义、压缩表达，不负责改坐标。

## 9. 软件脚本当前控制什么

软件脚本必须控制所有确定性部分：

### 9.1 能力目录

哪些模板可用、支持什么图型、容量是多少，由 `catalog.py` 控制。

### 9.2 契约校验

字段是否齐全、数量是否超限、文本是否过长，由 `validator.py` 控制。

### 9.3 决策与降级

当前 `decision.py` 控制：

- 选 Tier 1 / Tier 2 / Tier 3。
- 选 renderer。
- 记录 `fit_score`。
- 写入降级原因。

未来 LLM 可以参与推荐，但软件必须做最终复核。

### 9.4 组件几何

所有组件位置、尺寸、边框、箭头、字号范围，由组件库和模板编排控制。

LLM 不应该直接生成：

- `x/y/w/h`
- SVG path
- marker
- font-size
- line-height

### 9.5 文本排版

换行、缩字号、tspan 输出、中文/英文策略，由 `text_measure.py` 控制。

### 9.6 SVG/PNG 导出

`template_svg.py` 负责：

- 写 SVG。
- 通过 CairoSVG 或 Playwright 导出 PNG。
- 收集 warning。
- 返回 `AssetRecord`。

### 9.7 Manifest

`manifest.py` 负责统一输出：

- `illustration-manifest.json`
- `generation-summary.md`

调用方只应消费 manifest，不依赖内部文件名。

## 10. 当前机制的不足

### 10.1 组件库还不完整

目前只有 `process.resilience.v2` 开始组件化。

其他模板仍有部分散装 SVG：

- `platform.interface.v2`
- `inspection.cards.v2`
- `severity.closure.v2`
- `security.loop.v2`
- `arch.layered.v2`

后续应逐步迁移到组件库。

### 10.2 还没有统一 ComponentSpec 协议

当前组件调用仍是 Python 函数组装。

下一步应该引入：

```python
ComponentSpec:
  type
  id
  layout
  props
  children
```

这样 LLM 或规则层可以输出组件树，渲染器只负责执行。

### 10.3 几何校验还不完整

当前有 `data-fit` 检查，但还缺：

- bbox overflow 校验。
- 组件重叠校验。
- 连线穿框校验。
- 对比度校验。
- PNG 像素级 QA。

### 10.4 字体内嵌尚未完成

当前测量使用本地字体，SVG 使用字体栈。

后续应按稳定方案做：

- 字体子集化。
- woff2 base64 内嵌。
- 测量字体、渲染字体、导出字体同源。

## 11. 后续扩展路线

### Phase A：组件协议化

新增：

```text
core/component_model.py
renderers/component_svg.py
```

定义：

```python
ComponentSpec(
    type="process_node",
    id="retry",
    layout={"x": 690, "y": 330, "w": 188, "h": 92},
    props={"title": "自动重试", "desc": "按策略重试上报"},
    children=[]
)
```

收益：

- 模板不再直接拼 SVG。
- LLM 可以输出组件树草案。
- 软件可以校验组件树。
- 同一组件可复用于不同图型。

### Phase B：模板变成组件编排器

每个模板只负责：

- 选择组件。
- 计算固定槽位。
- 绑定数据到组件 props。
- 输出 ComponentSpec tree。

例如：

```text
process.resilience.v2
  -> Header
  -> FlowStep x 8
  -> ExceptionCard x 6
  -> ProcessNode x 4
  -> LoopConnector
  -> InfoPanel x 2
  -> AssuranceStrip
```

### Phase C：LLM 参与能力选择

给 LLM 的输入：

- 能力目录。
- 当前章节文本。
- 可用图型。
- 每个图型的契约。
- 当前内容约束。

LLM 输出：

```json
{
  "diagram_type": "process.resilience_flow",
  "template_id": "process.resilience.v2",
  "reason": "...",
  "data": {}
}
```

软件随后：

- 校验。
- 不通过则请求 LLM 改写。
- 再不通过则降级。

### Phase D：组件库扩展

后续新增更丰富表达效果时，应优先新增组件，而不是新增散装 SVG。

建议组件：

| 组件 | 用途 |
| --- | --- |
| `MatrixTable` | 分级响应、评分矩阵、风险矩阵 |
| `PlatformStack` | 双平台/多平台接口关系 |
| `RadialControl` | 安全体系、闭环治理、核心能力环 |
| `Timeline` | 实施计划、里程碑 |
| `Swimlane` | 多角色协作流程 |
| `MetricCard` | 指标展示、关键数值 |
| `Legend` | 图例 |
| `Callout` | 注释说明 |
| `EvidenceStrip` | 底部保障/依据/审计条 |
| `IconBadge` | 图标徽章 |

### Phase E：质量门禁

每次渲染后做：

```text
text fit check
component bbox check
overlap check
connector crossing check
contrast check
png export check
manifest check
```

任何失败都不能宣称 `fit_score=1.0`。

## 12. 推荐的最终形态

长期形态应该是：

```text
LLM:
  读内容
  选图型
  选模板
  填组件数据
  必要时做文本压缩

Software:
  维护能力目录
  校验契约
  生成组件树
  固定几何排版
  渲染 SVG
  导出 PNG
  做 QA
  写 manifest
```

最关键的边界：

```text
LLM 不画 SVG。
LLM 不写坐标。
LLM 不决定最终 fit 是否成功。

软件不理解业务深层语义。
软件不自由改写投标内容。
软件只做确定性选择、校验、排版和降级。
```

这样系统才能同时获得：

- LLM 的语义理解能力。
- 软件的稳定几何控制。
- 模板/组件的可复用能力。
- 后续图型扩展的可维护性。
