# Bid Illustration Platform 设计方案

> 状态：v2 落地方案
> 范围：将现有配图工具升级为面向投标文件的 AI 图形编排与多渲染绘图平台。

## 1. 目标

平台的目标不是简单把 JSON 画成 SVG，而是把投标文件中的技术方案、实施计划、评分响应、风险控制和数据统计转化为可直接进入 Word 标书的高质量图件。

必须同时满足：

- AI 可稳定调用：输入协议明确，错误可反馈，示例可复制。
- 表达清晰：每张图有明确 intent，图型选择服务于章节含义。
- 视觉美观：默认正式、清爽、专业，适合政企/工程/软件类投标。
- 多引擎渲染：不绑定 SVG，可按图型选择 SVG、ECharts、HTML/CSS、Mermaid、Graphviz。
- 文档可装配：输出 SVG/PNG/HTML 和 `illustration-manifest.json`，供 S6/S8 自动插入。

## 2. 总体架构

```text
S3/S5 章节内容或人工任务
        |
        v
AI 生成 Illustration Job v2
        |
        v
core.validator        结构校验、语义校验、可读性预警
        |
        v
core.registry         图型注册表：图型、默认渲染器、能力说明
        |
        v
core.router           renderer=auto 时选择最合适渲染器
        |
        +-------------------+-------------------+----------------+
        |                   |                   |                |
        v                   v                   v                v
  svg_native           echarts_html          html_css        mermaid/graphviz
        |                   |                   |                |
        +-------------------+-------------------+----------------+
                            |
                            v
core.quality           输出存在性、文字长度、模拟数据、水印、来源检查
                            |
                            v
core.manifest          统一生成 manifest、Markdown 清单和装配元数据
```

## 3. 目录规划

```text
src/bid_tool/illustration/
  toolkit.py                    # 兼容旧 CLI，逐步转为平台入口
  core/
    job.py                      # v2 数据结构与 v1/v2 识别
    registry.py                 # 图型注册表
    router.py                   # 渲染器选择
    validator.py                # 统一语义校验
    quality.py                  # 美观与可读性检查
    manifest.py                 # 输出清单模型
  renderers/
    base.py                     # RendererAdapter 协议
    legacy.py                   # 复用现有 svg_renderer/toolkit 能力
    html_renderer.py            # 后续 HTML/CSS 高质量卡片、矩阵、路线图
    mermaid_renderer.py         # 后续 Mermaid
    graphviz_renderer.py        # 后续 Graphviz
  design/
    tokens.py                   # 字号、间距、圆角、阴影
    themes.py                   # 平台主题，映射现有 themes.py
```

第一阶段不强行搬空现有 `svg_renderer.py` 和 ECharts 工作台，先用 adapter 包装，保证旧任务稳定。

## 4. Illustration Job v2

v2 任务面向语义图型，而不是底层引擎：

```json
{
  "version": "2.0",
  "document": {
    "title": "项目投标技术方案",
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
      "id": "implementation_plan",
      "type": "timeline.gantt",
      "renderer": "auto",
      "intent": "展示项目实施阶段、关键里程碑与交付成果",
      "insertion": {
        "section": "5.1 项目实施计划",
        "caption": "图 5-1 项目实施计划甘特图"
      },
      "data": {},
      "visual": {
        "density": "standard",
        "emphasis": "milestones",
        "legend": true,
        "numbering": true
      }
    }
  ]
}
```

兼容策略：

- `version=1.0`：走现有 `proposal_illustration_job.schema.json`，保留 `renderer/spec`。
- `version=2.0`：走平台协议，`type/data/visual` 为主。
- v2 中允许显式传 `legacySpec`，用于暂时复用现有 SVG/ECharts 图型。

## 5. 图型注册表

图型注册表负责告诉平台：

- 图型 ID。
- 适用场景。
- 默认渲染器。
- 可选渲染器。
- 必备数据字段。
- 视觉建议。
- 是否适合正式标书主图。

第一批注册图型：

| 图型 ID | 名称 | 默认渲染器 | 说明 |
| --- | --- | --- | --- |
| `architecture.layered` | 分层架构图 | `svg_native` | 系统总体架构、技术架构 |
| `architecture.deployment` | 部署架构图 | `svg_native` | 服务器、网络域、终端 |
| `architecture.security` | 安全体系图 | `svg_native` | 安全边界、防护措施 |
| `network.topology` | 网络拓扑图 | `graphviz` | 复杂链路可自动布局 |
| `process.flowchart` | 标准流程图 | `svg_native` | 业务、运维、服务流程 |
| `process.swimlane` | 泳道流程图 | `svg_native` | 多角色协同流程 |
| `interaction.sequence` | 时序图 | `svg_native` | 接口调用、事件交互 |
| `capability.map` | 能力地图 | `svg_native` | 功能模块、服务能力 |
| `relationship.domain` | 关系图 | `svg_native` | 组件、实体、系统关系 |
| `timeline.gantt` | 甘特图 | `html_css` | 实施计划、进度安排 |
| `timeline.milestone` | 里程碑图 | `html_css` | 阶段成果与关键节点 |
| `matrix.risk` | 风险矩阵 | `html_css` | 概率 x 影响 |
| `matrix.scoring_response` | 评分响应矩阵 | `html_css` | 评分点与响应章节 |
| `comparison.solution` | 方案对比图 | `html_css` | 我方方案与常规方案 |
| `overview.one_page` | 一页式总览图 | `html_css` | 高级综合表达 |
| `chart.*` | 数据图 | `echarts_html` | 柱、线、饼、雷达、桑基等 |

## 6. 渲染器策略

### svg_native

继续承担高可控框图：架构、流程、泳道、时序、能力、关系。输出 SVG/PNG。

### echarts_html

承担数据图：柱线、雷达、桑基、饼/环、堆叠柱、折线、漏斗、仪表盘、热力图。输出离线审图页、SVG/PNG。

### html_css

承担美观优先的投标表达图：路线图、甘特图、风险矩阵、评分矩阵、对比卡片、一页式总览。用 HTML/CSS 做排版，用 Playwright 截图导出 PNG，必要时保留 HTML 作为审图资产。

### mermaid

作为快速结构图和技术附录图的可选引擎，不作为正式主图默认输出。适合流程、时序、甘特草稿。

### graphviz

作为复杂拓扑和关系自动布局引擎。适合网络拓扑、系统依赖、组织关系。

## 7. 视觉设计规范

默认风格为 `formal_bid`：

- 白底或极浅背景。
- 深蓝作为主标题和关键结构色。
- 青绿/金色作为强调色。
- 圆角 8px 左右，阴影轻微。
- 标题区、主体区、注释区稳定。
- 数据图必须有单位、来源、模拟数据说明。
- 图例使用小面积，不压迫主体。
- 卡片和分区有足够留白，节点文字不拥挤。

统一视觉参数：

```json
{
  "density": "compact | standard | spacious",
  "tone": "formal_bid | executive | technical",
  "emphasis": "none | key_nodes | critical_path | milestones | risk_levels",
  "legend": true,
  "numbering": true,
  "badges": true,
  "watermark": "模拟数据"
}
```

## 8. 质量门禁

生成前：

- JSON Schema 校验。
- 图型是否已注册。
- 渲染器是否可用。
- v2 数据是否可转换为目标渲染器输入。

生成后：

- 输出文件存在。
- 每张图至少有 SVG、PNG 或 HTML 中的一种资产。
- 数据图有 `source` 和单位。
- `dataNotice` 存在时自动进入注释或水印。
- 节点数量、连线数量过多时给 warning。
- 标题、节点、图例文字过长时给 warning。

## 9. 实施阶段

### 阶段 1：平台协议与骨架

- 新增 v2 设计文档和 AI 调用说明。
- 新增 `core/` 与 `renderers/` 基础模块。
- 注册现有 v1 图型到 registry。
- `toolkit.py` 保持旧入口，增加 v2 识别和路由。

### 阶段 2：兼容现有能力

- v1 任务完全兼容。
- v2 的 `architecture.layered`、`process.flowchart`、`process.swimlane`、`interaction.sequence`、`capability.map`、`relationship.domain` 可转为现有 SVG spec。
- v2 的 `chart.*` 可转为现有 ECharts package。

### 阶段 3：美观型 HTML/CSS 渲染器

- 支持 `timeline.gantt`、`timeline.milestone`、`matrix.risk`、`comparison.solution`。
- 输出 HTML 审图页和 PNG。

### 阶段 4：扩展引擎

- Mermaid adapter。
- Graphviz adapter。
- PlantUML 可选 adapter。

### 阶段 5：流水线集成

- S5 prompt 改为输出 v2 job。
- S6 读取平台 manifest。
- README 增加 v2 工作流。

