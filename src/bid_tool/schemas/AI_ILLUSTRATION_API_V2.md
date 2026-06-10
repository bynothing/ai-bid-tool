# AI 配图平台调用接口 v2

本文档面向 AI 调用方。AI 的任务是输出结构化 JSON，描述“标书中需要什么图、表达什么、放在哪里、有哪些数据”。AI 不需要写 SVG 坐标、ECharts option 或 HTML。

## 1. 输出原则

AI 必须遵守：

- 只输出 JSON 对象，不要包裹 Markdown 代码块。
- 每张图必须有 `id`、`type`、`intent`、`insertion.caption`。
- 优先使用 `renderer: "auto"`，除非用户明确指定底层引擎。
- 数据图必须提供 `source`；如果是模拟数据，必须提供 `dataNotice`。
- 图题要适合标书，避免口语化。
- 节点文字短而具体，不使用“赋能”“底座”等空泛词。
- 图形表达要服务章节内容，不为了好看而堆元素。

## 2. 顶层结构

```json
{
  "version": "2.0",
  "document": {
    "title": "技术投标方案",
    "projectName": "项目名称",
    "bidSection": "技术方案"
  },
  "style": {
    "theme": "formal_blue",
    "tone": "formal_bid",
    "preferredFormat": "both"
  },
  "illustrations": []
}
```

字段说明：

| 字段 | 必填 | 说明 |
| --- | --- | --- |
| `version` | 是 | 固定为 `2.0` |
| `document.title` | 是 | 标书或技术方案名称 |
| `document.projectName` | 否 | 项目名称 |
| `style.theme` | 否 | 默认 `formal_blue` |
| `style.tone` | 否 | 默认 `formal_bid` |
| `style.preferredFormat` | 否 | `svg`、`png`、`both` |
| `illustrations` | 是 | 图件数组 |

正式 JSON Schema：

[illustration_job_v2.schema.json](../src/bid_tool/schemas/illustration_job_v2.schema.json)

## 3. 单张图结构

```json
{
  "id": "overall_architecture",
  "type": "architecture.layered",
  "renderer": "auto",
  "intent": "展示系统总体架构、层级职责和外部接口关系",
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
    "legend": true,
    "numbering": false,
    "badges": true
  }
}
```

## 4. 图型选择

| 需求 | 推荐图型 | 说明 |
| --- | --- | --- |
| 展示系统分层与组件 | `architecture.layered` | 总体架构、技术架构 |
| 展示多层能力体系说明 | `architecture.layered_explainer` | 左编号层级 + 中部层名/图标 + 右侧说明 + 底部类比 |
| 展示服务器/网络区域 | `architecture.deployment` | 部署架构、安全域 |
| 展示网络设备和链路 | `network.topology` | 网络拓扑 |
| 展示业务办理步骤 | `process.flowchart` | 普通流程 |
| 展示多角色协同 | `process.swimlane` | 泳道流程 |
| 展示多工艺段流程与系统交互点 | `process.interaction_map` | 工艺段分区 + 主流程 + 辅助/回流关系 + 图例术语 |
| 展示接口调用先后 | `interaction.sequence` | 时序图 |
| 展示功能模块分类 | `capability.map` | 能力地图 |
| 展示系统/实体关系 | `relationship.domain` | 关系图 |
| 展示项目进度 | `timeline.gantt` | 甘特图 |
| 展示关键节点 | `timeline.milestone` | 里程碑 |
| 展示概率和影响 | `matrix.risk` | 风险矩阵 |
| 展示评分覆盖 | `matrix.scoring_response` | 评分响应矩阵 |
| 展示方案优劣 | `comparison.solution` | 对比卡片 |
| 展示双平台接口关系与数据交互 | `integration.interface_map` | 左右平台分层 + 中央交互链路 |
| 展示运维巡检分类 | `operation.inspection_taxonomy` | 三列分类卡片 + 总体输出 + 原则要求 |
| 展示故障分级响应与闭环 | `operation.incident_response` | 分级响应表 + 横向闭环流程 |
| 展示数据安全/保密保障体系 | `architecture.security_ring` | 中心核心体系 + 环形措施 + 管理闭环 |
| 展示数值趋势 | `chart.line_multi` / `chart.bar_line` | 趋势图 |
| 展示构成占比 | `chart.pie_donut` | 饼/环图 |
| 展示多指标评价 | `chart.radar` | 雷达图 |
| 展示流向权重 | `chart.sankey` | 桑基图 |
| 展示过程转化 | `chart.funnel` | 漏斗图 |
| 展示达成率 | `chart.gauge` | 仪表盘 |

## 5. 通用视觉字段

```json
{
  "density": "compact",
  "tone": "formal_bid",
  "emphasis": "critical_path",
  "legend": true,
  "numbering": true,
  "badges": true,
  "watermark": "模拟数据"
}
```

可选值：

| 字段 | 可选值 | 说明 |
| --- | --- | --- |
| `density` | `compact`、`standard`、`spacious` | 信息密度 |
| `tone` | `formal_bid`、`technical`、`executive` | 视觉语气 |
| `emphasis` | `none`、`key_nodes`、`critical_path`、`milestones`、`risk_levels` | 突出方式 |
| `legend` | 布尔 | 是否显示图例 |
| `numbering` | 布尔 | 是否显示编号 |
| `badges` | 布尔 | 是否显示状态/风险/阶段徽标 |
| `watermark` | 字符串 | 模拟数据或草案提示 |

## 5.1 默认框图风格

v2 平台中的框图默认采用类似“数据交互规则适配架构与接口关系图”的正式标书风格：

- 顶部深蓝标题栏，显示主标题、副标题和文档名称。
- 主体白底，使用细边框、浅色分区、圆角卡片。
- 架构/能力/关系图优先使用分层面板。
- 双系统/双平台关系优先使用左右平台 + 中央链路。
- 流程/时序图使用横向阶段卡片和箭头表达。
- 底部可配置通信与安全要求、说明、图例、结论条。
- 默认 `renderer` 使用 `auto`。展示型框图通常优先选择 `html_css`；如果需要可编辑矢量、精确连线或明确要求 SVG，平台会使用 `svg_native` 生成同一套正式标书风格。

如果需要 SVG 原生输出，可显式设置：

```json
{
  "renderer": "svg_native"
}
```

## 5.2 大模型式内容分析与自动渲染决策

`renderer: "auto"` 会进入内容分析决策层。平台不是固定使用某一种技术，而是先像设计助理一样理解图件内容，再选择更合适的表达方式。

分析过程会读取：

- `type`：图型语义。
- `intent`：图件想表达什么。
- `insertion.caption` / `purpose`：图题和用途。
- `data`：节点、层级、流程、连线、数据序列、风险项、交互链路。
- `visual`：是否要求可编辑矢量、精确连线、展示风格或渲染偏好。

平台会抽取这些信号：

| 信号 | 含义 |
| --- | --- |
| `数据图` | 存在数值序列、分类轴、指标值或 `chart.*` |
| `展示型标书图` | 总览、路线、矩阵、对比、接口关系、说明性架构 |
| `精确结构/复杂关系` | 节点多、连线多、分支多、需要严格连接关系 |
| `拓扑/网络语义` | 网络、链路、安全域、设备拓扑 |
| `接口/安全语义` | 接口、推送、反馈、ACK、HTTPS、MQTT、认证、签名、审计 |
| `矢量可编辑诉求` | `editableVector` 或文本中出现可编辑/SVG/矢量 |
| `精确连线诉求` | `preciseConnectors` 或复杂连线、回路、实体关系 |

默认规则：

| 内容特征 | 自动选择 | 原因 |
| --- | --- | --- |
| 展示型架构、能力、矩阵、对比、路线图 | `html_css` | 更接近图3风格，适合正式标书审阅 |
| 数据统计图 | `echarts_html` | 图例、坐标轴、标签和导出更成熟 |
| 节点很多、连线很多、关系复杂 | `svg_native` | 更适合精确矢量布局和连线表达 |
| 明确要求可编辑矢量或精确连线 | `svg_native` | 保留 SVG 的可编辑与精确控制优势 |
| 双平台接口关系、推送反馈、安全要求 | `html_css` / `svg_native` | 两者均支持图3风格；需要可编辑矢量时选 SVG |
| 巡检分类、故障闭环、安全环形保障 | `svg_native` | 原生支持图5、图6、图7一类正式标书结构 |
| 标准流程图、时序图、简单甘特图 | `mermaid` | 输出 `.mmd`、HTML、SVG/PNG，便于外部二次编辑 |
| 网络拓扑、复杂关系、部署关系 | `graphviz` | 输出 `.dot`、SVG/PNG；无 dot 环境时自动降级为简易 SVG |

AI 调用时推荐始终保留：

```json
{
  "renderer": "auto"
}
```

如确有特殊要求，可在 `visual` 中提供约束，平台仍会记录决策原因：

```json
{
  "visual": {
    "editableVector": true,
    "preciseConnectors": true,
    "rendererPreference": "svg_native"
  }
}
```

字段说明：

- `editableVector: true`：希望优先保留 SVG 矢量可编辑能力。
- `preciseConnectors: true`：存在复杂连接、回路、跨层连线，优先 SVG。
- `rendererPreference`：可选 `html_css`、`svg_native`、`echarts_html`；仅当该图型支持时生效。

生成后的 `illustration-manifest.json` 和 `生成清单.md` 会写入决策过程，例如：

```text
内容分析: 展示型标书图、接口/安全语义; 元素 22, 连线 0, 分支 0, 泳道 0
选择 HTML/CSS：内容偏正式标书展示，适合图3风格的标题栏、分区卡片、说明和结论条
```

## 6. 框图数据格式

### 6.1 分层架构 `architecture.layered`

```json
{
  "layers": [
    {
      "label": "应用服务层",
      "en": "APPLICATION",
      "items": [
        { "title": "实时监控", "desc": "状态、告警、轨迹", "icon": "monitor", "style": "accent" },
        { "title": "统计分析", "icon": "chart" }
      ]
    }
  ],
  "actors": [
    { "title": "监管部门", "icon": "government" }
  ],
  "integrations": [
    { "title": "上级平台", "icon": "cloud" }
  ],
  "note": "图中组件边界以最终接口清单为准。"
}
```

### 6.2 多层能力体系说明图 `architecture.layered_explainer`

适用于参考“AI 系统七层架构全景图”这类表达：一组从底层到高层的能力层级，每层包含编号、层名、短说明、右侧解释，并可在底部给出通俗类比。

当前自动决策会将该图型路由到 Draw.io renderer，输出可编辑 `.drawio`，并在可用时导出 SVG/PNG。该图型适合方法论、能力体系、平台分层、建设路径等标书说明图。

```json
{
  "title": "AI 系统七层架构全景图",
  "subtitle": "从 Token 到 Skills 的能力层级",
  "levels": [
    {
      "number": 7,
      "id": "skills",
      "title": "Skills",
      "subtitle": "技能 / 经验库",
      "icon": "SK",
      "description": "沉淀可复用的方法、经验与能力，持续积累，让 AI 越用越强。",
      "analogy": "经验手册",
      "color_role": "layer_red"
    }
  ],
  "analogyTitle": "通俗理解 · 一句话类比"
}
```

容量建议：

| 字段 | 建议上限 |
| --- | ---: |
| `levels` | 7 |
| `level.title` | 18 字 |
| `level.subtitle` | 18 字 |
| `level.description` | 46 字 |
| `level.analogy` | 16 字 |

### 6.3 流程图 `process.flowchart`

```json
{
  "nodes": [
    { "id": "start", "title": "接收需求", "row": 0, "col": 0, "kind": "process" },
    { "id": "review", "title": "技术评审", "row": 0, "col": 1, "kind": "decision" }
  ],
  "edges": [
    { "from": "start", "to": "review", "label": "提交材料", "relation": "flow" }
  ]
}
```

### 6.4 工艺流程与系统交互大图 `process.interaction_map`

适用于总装、生产、运维、审批等多业务段流程，需要同时表达：

- 工艺段或业务段分区。
- 段内关键步骤。
- 主流程段间关系。
- 辅助流程、物料关系、异常回流或复检关系。
- 系统交互点、线型图例和术语说明。

当前自动决策会将该图型路由到 Draw.io renderer，输出可编辑 `.drawio`，并在可用时导出 SVG/PNG。该图型仍属于 Tier 2 基线实现，`manifest` 会标记 `needs_human_review=true`，后续高频场景应沉淀为 Tier 1 模板。

```json
{
  "sections": [
    {
      "id": "A",
      "title": "A 上线准备",
      "subtitle": "计划下达",
      "steps": [
        {
          "id": "A1",
          "title": "订单排产",
          "description": "MES 下达工单",
          "interaction_type": "MES"
        }
      ]
    }
  ],
  "primary_flow": [
    { "from": "A", "to": "B", "label": "上线", "relation": "primary" }
  ],
  "support_flows": [
    { "from": "D2", "to": "C1", "label": "返修复检", "relation": "rework" }
  ],
  "interaction_types": [
    { "id": "MES", "title": "MES", "description": "工单、工艺参数、过程状态" }
  ],
  "legend": [
    { "title": "主流程", "description": "粗实线箭头表示工艺主路径" },
    { "title": "辅助/回流", "description": "细虚线箭头表示物料、异常和返修关系" }
  ],
  "glossary": [
    { "term": "VIN", "definition": "车辆唯一识别码" }
  ]
}
```

容量建议：

| 字段 | 建议上限 |
| --- | ---: |
| `sections` | 6 |
| 每个 `section.steps` | 4 |
| `primary_flow` | 8 |
| `support_flows` | 6 |
| `interaction_types + legend + glossary` | 8 |

### 6.5 甘特图 `timeline.gantt`

```json
{
  "unit": "月",
  "total": 12,
  "phases": [
    { "title": "项目启动", "start": 0, "end": 1, "desc": "启动会、计划确认", "milestone": true },
    { "title": "需求调研", "start": 1, "end": 3, "desc": "业务梳理、需求确认" }
  ],
  "milestones": [
    { "title": "需求评审", "time": "第3月" }
  ]
}
```

### 6.6 风险矩阵 `matrix.risk`

```json
{
  "risks": [
    {
      "title": "接口联调延期",
      "probability": 3,
      "impact": 4,
      "level": "high",
      "mitigation": "提前冻结接口清单并设置联调窗口"
    }
  ]
}
```

### 6.7 方案对比 `comparison.solution`

```json
{
  "columns": [
    {
      "title": "我方方案",
      "style": "success",
      "items": ["统一接入", "分层解耦", "全过程审计"]
    },
    {
      "title": "常规方案",
      "style": "default",
      "items": ["接口分散", "模块耦合", "审计粒度不足"]
    }
  ]
}
```

### 6.8 接口关系与数据交互图 `integration.interface_map`

适用于类似“省级平台与国家平台数据交互规则适配架构图”的正式标书大图。典型特点：

- 左右两侧是两个平台或系统，均按应用服务层、数据处理层、接口服务层、基础设施层分层。
- 中间是多条数据推送/反馈链路，支持不同颜色、方向、协议和 ACK 说明。
- 底部展示通信协议、认证鉴权、数据签名、传输安全、时间同步、接口规范。
- 最下方可展示说明、图例和“可追溯、可审计”等结论性表达。

```json
{
  "leftPlatform": {
    "title": "省级放射源在线监控平台",
    "layers": [
      {
        "title": "应用服务层",
        "items": ["放射源综合管理", "定位监控与轨迹", "预警管理与处置", "统计分析与报表"]
      }
    ]
  },
  "rightPlatform": {
    "title": "国家在线监控平台（生态环境部）",
    "layers": [
      {
        "title": "应用服务层",
        "items": ["放射源监管管理", "定位监控与展示", "预警接收与处置", "统计分析与评估"]
      }
    ]
  },
  "flows": [
    {
      "label": "① 放射源信息上报（推送）",
      "protocol": "HTTPS（JSON）",
      "direction": "right",
      "color": "#007bb5",
      "ack": "上报结果反馈（ACK）"
    }
  ],
  "requirements": [
    { "title": "通信协议", "desc": "HTTPS 1.2+ / MQTT TLS 1.2+" }
  ],
  "notes": ["① 放射源信息上报：省级平台按规则上报国家平台。"],
  "legend": [
    { "label": "实线箭头", "desc": "推送链路" },
    { "label": "虚线反馈", "desc": "ACK 确认" }
  ],
  "conclusion": "所有数据交互均需留痕、可追溯、可审计"
}
```

### 6.7 SVG 原生正式标书模板

以下图型在 `renderer: "svg_native"` 或 `visual.rendererPreference: "svg_native"` 时使用 SVG 原生模板：

| v2 图型 | SVG internal type | 结构特点 |
| --- | --- | --- |
| `integration.interface_map` | `interface_map` | 图3风格：左右平台分层，中间多条交互/回执链路，底部接口约束与说明 |
| `operation.inspection_taxonomy` | `inspection_taxonomy` | 图5风格：三列分类卡片，触发方式、巡检内容、核查要点、输出成果 |
| `operation.incident_response` | `incident_response` | 图6风格：上部分级响应表，下部七步闭环流程和保障措施 |
| `architecture.security_ring` | `security_ring` | 中心核心体系，外围 3-5 项环形保障措施，底部管理闭环 |

完整 SVG 示例见 `examples/示例_SVG支持图3-6风格.json`。

## 7. 数据图格式

### 7.1 多折线 `chart.line_multi`

```json
{
  "categories": ["一季度", "二季度", "三季度", "四季度"],
  "series": [
    { "name": "处理量", "unit": "件", "values": [120, 180, 230, 310] },
    { "name": "办结量", "unit": "件", "values": [110, 170, 220, 295] }
  ],
  "source": "项目统计口径",
  "dataNotice": "示例数据，正式投标前需替换为确认数据。"
}
```

### 7.2 饼/环图 `chart.pie_donut`

```json
{
  "unit": "%",
  "data": [
    { "name": "软件开发", "value": 45 },
    { "name": "系统集成", "value": 30 },
    { "name": "运维服务", "value": 25 }
  ],
  "source": "投标报价测算"
}
```

### 7.3 仪表盘 `chart.gauge`

```json
{
  "name": "需求覆盖率",
  "value": 96,
  "max": 100,
  "unit": "%",
  "source": "需求响应矩阵"
}
```

## 8. 常见错误

| 错误 | 修正 |
| --- | --- |
| 节点 title 太长 | 拆成 `title` + `desc` |
| 数据图没有 source | 补充数据来源 |
| 模拟数据未声明 | 增加 `dataNotice` |
| 所有图都用架构图 | 根据章节目的选择流程、矩阵、对比、数据图 |
| renderer 写死 SVG | 默认使用 `auto` |
| 连线太多 | 拆成总览图 + 子图 |

## 9. 最小完整示例

```json
{
  "version": "2.0",
  "document": {
    "title": "高风险放射源监管平台投标技术方案",
    "projectName": "高风险放射源监管平台"
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
      "intent": "展示平台总体分层架构与外部系统接入关系",
      "insertion": {
        "section": "3.1 系统总体架构",
        "caption": "图 3-1 系统总体架构图"
      },
      "data": {
        "actors": [
          { "title": "监管部门", "icon": "government" },
          { "title": "涉源单位", "icon": "organization" }
        ],
        "layers": [
          {
            "label": "业务应用层",
            "en": "APPLICATION",
            "items": [
              { "title": "实时监控", "icon": "monitor", "style": "accent" },
              { "title": "预警处置", "icon": "alert", "style": "danger" }
            ]
          },
          {
            "label": "数据与安全层",
            "en": "DATA & SECURITY",
            "items": [
              { "title": "监管数据库", "icon": "database" },
              { "title": "安全审计", "icon": "audit" }
            ]
          }
        ]
      },
      "visual": {
        "density": "standard",
        "emphasis": "key_nodes",
        "legend": true
      }
    }
  ]
}
```
## 默认配色策略补充

平台内置了参考 `src/bid_tool/illustration_v2/materials/references/legacy_illustration/example` 中图 3-6 的正式标书配色方案：深蓝标题栏、白底卡片、细边框、浅色分区，并在框图节点、阶段、流程线、要求项中默认使用多语义色轮换，避免生成结果只呈现单一蓝色。

当前支持多套主题，并会在渲染前根据内容自动选择：
- `example_formal`：通用正式标书蓝，适合一般架构、能力、关系、流程说明。
- `data_cyan`：数据接口青蓝，适合接口、API、同步、上报、统计、趋势类内容。
- `security_green`：安全合规绿蓝，适合安全、保密、合规、审计、权限、认证、加密类内容。
- `risk_orange`：风险故障橙红，适合风险、故障、异常、预警、应急、失败、超时类内容。
- `executive_gold`：汇报里程碑蓝金，适合里程碑、进度计划、成果汇报、方案对比类内容。
- `ops_indigo`：运维巡检靛蓝，适合巡检、监控、工单、运行维护、值守处置类内容。
- `process_violet`：流程治理紫，适合流程图、泳道图、审批流、闭环处理、跨角色协作。
- `infra_slate`：基础设施灰蓝，适合部署架构、网络拓扑、服务器、云资源、集群和机房。
- `service_emerald`：服务保障翠绿，适合服务体系、培训支持、售后保障、交付协同。
- `innovation_royal`：智能创新蓝紫，适合 AI、大模型、算法、自动化、数字化创新。
- `quality_mint`：质量核查薄荷绿，适合质量检测、验收、评审、校验、整改闭环。

自动匹配优先级为：显式指定 `palette` / `colorScheme` > 图型强语义 > 风险故障 > 安全合规 > 运维巡检 > 基础设施 > 服务保障 > 质量核查 > 智能创新 > 数据接口 > 里程碑/汇报 > 通用正式标书蓝。

如需人工锁定某张图的主题，可写：

```json
{
  "visual": {
    "palette": "security_green"
  }
}
```

默认语义色包括：
- `primary` / `default` / `blue`：正常流程、主链路、核心模块
- `success` / `green`：校验、入库、通过、保障类信息
- `warning` / `orange`：异常处理、预警、补传、提醒
- `danger` / `red`：高风险、失败、重大故障
- `purple`：核查、审计、补传队列、闭环复核
- `teal` / `cyan`：数据流、同步、接口联动
- `gold`：反馈、时间节点、重要提示

AI 调用时可以不写 `style`，渲染器会按元素顺序自动分配颜色。需要强调语义时，可在节点、阶段、`flows`、`requirements`、卡片分组中写入 `style`：

```json
{ "title": "异常捕获", "desc": "记录失败原因和来源", "style": "warning" }
```
