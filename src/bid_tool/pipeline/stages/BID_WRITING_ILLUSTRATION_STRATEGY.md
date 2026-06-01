# 标书撰写过程中的配图策略与接口

> 本文规定在 S2/S3/S5/S6/S8 标书撰写过程中如何规划、生成、审查和装配配图。绘图平台统一使用 Illustration Job v2 作为对外接口。

## 1. 配图目标

标书配图不是装饰，而是服务评审理解和评分响应。每张图都必须回答一个明确问题：

- 技术方案是否清楚？
- 实施路径是否可信？
- 风险控制是否闭环？
- 评分点是否有证据支撑？
- 数据、接口、安全和运维是否可追溯？

不建议为了“看起来丰富”而无目的插图。每张图必须绑定章节、图题、表达意图和正文位置。

## 2. 阶段策略

### S2 大纲阶段：规划图位

S2 生成大纲时应同步规划图位，输出每章建议图件：

| 章节内容 | 推荐图 |
| --- | --- |
| 总体方案 | 总体架构图、方案总览图 |
| 数据/接口 | 数据流向图、接口关系图、交互规则适配图 |
| 实施计划 | 甘特图、里程碑图 |
| 质量/测试 | 流程图、闭环验证图 |
| 风险控制 | 风险矩阵、处置流程 |
| 评分响应 | 评分响应矩阵、需求覆盖矩阵 |
| 服务保障 | 服务流程图、组织保障图、巡检分类图、故障分级响应闭环图 |
| 安全保密 | 数据安全保密保障体系图、接口认证与审计闭环图 |

S2 只规划“需要什么图”，不生成详细图形数据。

### S3 正文阶段：写出图前后文

S3 正文中应为关键图留出自然上下文：

- 图前段落说明为什么需要这张图。
- 图后段落解释图中关键路径、关键节点和对标条款。
- 不在正文中直接写 SVG、ECharts option 或图片路径。

建议正文中可保留轻量插图意图：

```markdown
【建议配图：系统总体架构图；表达平台分层、核心能力和外部接口】
```

### S5 配图任务阶段：生成 Illustration Job v2

> **AI 生成数据前必须先阅读两份文档**：
> 1. [ILLUSTRATION_DATA_SPEC.md](../../illustration/ILLUSTRATION_DATA_SPEC.md) — 每种图型的完整 Schema、丰富示例、图标列表、颜色语义
> 2. [s5_illustration_prompt.md](../../prompts/s5_illustration_prompt.md) — S5 专用 prompt 模板（已内置上述规范）

S5 的目标是让 AI 输出一份统一配图任务：

```json
{
  "version": "2.0",
  "document": {},
  "style": {},
  "illustrations": []
}
```

要求：

- 每张图必须有 `id`、`type`、`renderer: "auto"`、`intent`、`insertion`、`data`、`visual`。
- **数据密度决定画质**：每个节点/卡片必须提供 `title` + `desc` + `icon` + `style` 四要素。
- 架构图必须包含 `actors`（用户入口）、`layers`（3-7层）、`integrations`（外部对接）、`requirements`（底部合规条）。
- 流程图节点必须包含 `desc`（描述），边必须包含 `relation`（颜色语义）。
- 当章节需要类似 example 图3-6 的正式标书 SVG 风格时，优先使用 `integration.interface_map`、`operation.inspection_taxonomy`、`operation.incident_response`、`architecture.security_ring`。
- AI 不需要选择底层绘图技术，平台会分析内容并自动决策。
- 数据图必须提供 `source`；模拟数据必须提供 `dataNotice` 和 `visual.watermark`。

### S6 图文合成阶段：按 manifest 装配

S6 不重新理解图形，只读取平台输出的：

```text
illustration-manifest.json
```

装配原则：

- 优先使用 `outputs.png`，适合 Word 稳定排版。
- 如目标支持 SVG，可使用 `outputs.svg`。
- `outputs.html` 用于人工审图和必要时重新导出。
- `section`、`caption`、`purpose` 用于定位和题注。
- `decision` 用于审计为什么选择某个渲染方式。

### S7/S8 校验与导出阶段

校验项：

- 每张图是否插入到对应章节。
- 图号是否连续。
- 图题是否与正文引用一致。
- 模拟数据是否标注。
- 数据来源是否存在。
- 图片是否清晰，文字是否可读。
- 决策记录是否合理，例如复杂关系图是否没有误用展示型模板。

## 3. 图型选择策略

AI 只选择语义图型，不选择绘图技术。

| 写作目的 | `type` | 说明 |
| --- | --- | --- |
| 展示系统分层 | `architecture.layered` | 总体架构、技术架构 |
| 展示部署和安全域 | `architecture.deployment` | 服务器、终端、安全域 |
| 展示网络链路 | `network.topology` | 网络拓扑、链路关系 |
| 展示接口关系 | `integration.interface_map` | 双平台、推送、反馈、ACK、安全要求 |
| 展示业务流程 | `process.flowchart` | 线性流程、分支流程 |
| 展示多角色协同 | `process.swimlane` | 部门、系统、角色职责 |
| 展示接口调用 | `interaction.sequence` | 时序、消息、回调 |
| 展示能力分组 | `capability.map` | 功能模块、响应能力 |
| 展示复杂关系 | `relationship.domain` | 模块、数据表、实体关系 |
| 展示实施周期 | `timeline.gantt` | 甘特图 |
| 展示关键节点 | `timeline.milestone` | 里程碑 |
| 展示风险等级 | `matrix.risk` | 概率 x 影响 |
| 展示评分覆盖 | `matrix.scoring_response` | 评分项 x 响应材料 |
| 展示方案对比 | `comparison.solution` | 我方方案 vs 常规方案 |
| 展示趋势/指标 | `chart.*` | ECharts 数据图 |

## 4. 自动渲染决策策略

AI 默认写：

```json
{
  "renderer": "auto"
}
```

平台会根据内容分析选择：

| 内容分析结果 | 渲染器 |
| --- | --- |
| 正式展示型框图、图3风格、接口关系、路线图、矩阵 | `html_css` |
| 数据图、趋势图、指标图、流向权重 | `echarts_html` |
| 复杂连线、密集关系、可编辑矢量、精确结构 | `svg_native` |
| 未来复杂拓扑自动布局 | `graphviz` |

AI 可通过 `visual` 表达约束：

```json
{
  "visual": {
    "editableVector": true,
    "preciseConnectors": true,
    "rendererPreference": "svg_native"
  }
}
```

## 5. 统一接口

### 5.1 JSON Job 接口

标准任务：

```json
{
  "version": "2.0",
  "document": {
    "title": "投标技术方案",
    "projectName": "项目名称",
    "bidSection": "技术方案"
  },
  "style": {
    "theme": "formal_blue",
    "tone": "formal_bid",
    "preferredFormat": "both"
  },
  "illustrations": [
    {
      "id": "overall_architecture",
      "type": "architecture.layered",
      "renderer": "auto",
      "intent": "展示系统分层架构、核心能力和外部接口关系",
      "insertion": {
        "section": "3.1 系统总体架构",
        "afterText": "本项目采用分层解耦架构。",
        "caption": "图 3-1 系统总体架构图",
        "purpose": "说明总体技术组成"
      },
      "data": {},
      "visual": {
        "density": "standard",
        "emphasis": "key_nodes",
        "legend": true
      }
    }
  ]
}
```

Schema：

[illustration_job_v2.schema.json](../src/bid_tool/schemas/illustration_job_v2.schema.json)

### 5.2 CLI 接口

```powershell
bid-tool illustrate --job examples/示例_配图平台v2任务.json --validate-only
bid-tool illustrate --job examples/示例_配图平台v2任务.json --png
bid-tool illustrate --job examples/示例_配图平台v2任务.json --no-echarts-export
```

### 5.3 Python API 接口

```python
from bid_tool.illustration import api

job = api.load("job.json")
errors, warnings = api.validate(job)
decisions = api.plan(job)
records = api.render(job, "output/illustrations", png=True)
types = api.list_diagram_types()
```

### 5.4 输出 Manifest 接口

平台输出：

```json
{
  "version": "2.0",
  "document": {},
  "sourceJob": "job.json",
  "illustrations": [
    {
      "id": "overall_architecture",
      "type": "architecture.layered",
      "renderer": "html_css",
      "section": "3.1 系统总体架构",
      "caption": "图 3-1 系统总体架构图",
      "purpose": "展示系统分层架构",
      "outputs": {
        "html": "assets/html/overall_architecture.html",
        "png": "assets/html/overall_architecture.png"
      },
      "warnings": [],
      "decision": [
        "内容分析: 展示型标书图...",
        "选择 HTML/CSS..."
      ]
    }
  ]
}
```

S6/S8 只依赖 manifest，不依赖内部 renderer。

## 6. AI 输出质量要求

每张图必须满足：

- `intent` 明确，不能空泛。
- `caption` 是正式图题。
- `section` 能定位到章节。
- `data` 足够完整，不能只写“画一个架构图”。
- 数据图必须有 `source`。
- 模拟数据必须有 `dataNotice`。
- 图中节点名称应短、准、专业。
- 不输出 SVG/HTML/JS 代码。

## 7. 人工审查清单

生成后检查：

- 图是否真的服务该章节。
- 图型选择是否合理。
- 自动决策是否合理。
- 图中文字是否清晰。
- 图例/注释/来源是否齐全。
- 是否有模拟数据水印。
- Word 中缩放后是否仍可读。
