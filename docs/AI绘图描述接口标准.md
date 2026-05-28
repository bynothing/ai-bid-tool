# AI SVG 框图绘图描述接口标准

## 1. 目的

本标准用于让大模型稳定生成“绘图描述”，由 SVG 渲染工具统一输出高质量框图。大模型不需要编写 SVG 坐标和样式，只需要描述图型、内容层次、节点关系、图标和插入位置。

本文件是 `svg` 单引擎的描述细则。面向完整招投标文档的自动插图，优先使用 [统一标书配图工具集调用说明](<统一标书配图工具集调用说明.md>) 和统一任务协议，将 SVG 框图与 ECharts 数据图共同编排到章节位置。

执行工具：[generate_architecture_diagram.py](<../src/generate_architecture_diagram.py>)

结构校验文件：[svg_diagram.schema.json](<../schema/svg_diagram.schema.json>)

数据型图件使用独立的本地页面与描述约定：

- 页面入口：[echarts-workbench/index.html](<../web/echarts-workbench/index.html>)
- 数据图 Schema：[echarts_diagram.schema.json](<../schema/echarts_diagram.schema.json>)

## 2. 调用约定

大模型输出 JSON 对象，根节点包含 `figures` 数组。描述可作为独立 `.json` 文件传入，也可以嵌入 Markdown 文档中的 `svg-diagrams` 代码块。

```powershell
python '.\src\generate_architecture_diagram.py' --spec '.\examples\example.json' --validate-only
python '.\src\generate_architecture_diagram.py' --spec '.\examples\example.json' --output '.\results\current\自定义输出' --theme clarity_blue --png
```

建议工作流：

```text
大模型阅读标书段落
  -> 输出符合 Schema 的 JSON 图示描述
  -> validate-only 校验
  -> 渲染 SVG/PNG
  -> 人工审图
  -> 修改 JSON 后重新渲染
```

## 3. 根对象

```json
{
  "documentTitle": "项目名称或文档名称",
  "figures": []
}
```

| 字段 | 必须 | 说明 |
| --- | --- | --- |
| `documentTitle` | 否 | 标书或解决方案名称 |
| `figures` | 是 | 需要生成的图数组，至少一张 |

## 4. 通用图字段

| 字段 | 必须 | 说明 |
| --- | --- | --- |
| `type` | 是 | 图型：`layered_architecture`、`flowchart`、`swimlane_flowchart`、`sequence_diagram`、`capability_map`、`relationship_map` |
| `title` | 是 | 图题，显示在图片标题栏 |
| `subtitle` | 否 | 图题下方的章节说明 |
| `placement` | 否 | 建议插入位置，如 `3.1 系统总体架构设计` |
| `note` | 否 | 底部注脚，用于说明边界、数据来源或待确认事项 |

## 5. 节点与图标

通用内容节点格式：

```json
{
  "title": "实时状态监控",
  "desc": "二维 / 三维 / 轨迹",
  "icon": "map",
  "style": "accent"
}
```

| 字段 | 必须 | 说明 |
| --- | --- | --- |
| `title` | 是 | 节点名称，应尽量控制在 4 至 12 个汉字 |
| `desc` | 否 | 补充描述，建议简短 |
| `icon` | 否 | 内置图标标识 |
| `style` | 否 | `default`、`accent`、`success`、`warning`、`danger` |

查询工具支持的图标：

```powershell
python '.\src\generate_architecture_diagram.py' --list-icons
```

当前图标目录：

| 图标 ID | 用途 |
| --- | --- |
| `government` | 监管机构、政府平台 |
| `organization` | 单位、企业、机构 |
| `user` / `admin` | 用户、管理员、审批人员 |
| `radiation` | 放射源或特殊设备 |
| `location` / `map` | 定位、轨迹、GIS 地图 |
| `workflow` / `form` | 审批流程、业务表单 |
| `dashboard` / `report` | 看板、统计、报表 |
| `database` / `server` | 数据资源、应用服务 |
| `shield` | 安全、权限、认证 |
| `api` | 接口、交换、对接 |
| `terminal` / `vehicle` | 终端、车辆 |
| `message` | 通知、消息渠道 |
| `settings` | 配置、运维 |
| `alert` / `check` | 异常、完成 |
| `sensor` / `network` / `cloud` | 采集、网络连接、云服务 |
| `lock` / `audit` | 访问安全、审计追溯 |
| `ai` | 智能分析、规则识别 |
| `browser` / `mobile` | Web 门户、移动应用 |
| `camera` / `gps` / `gateway` | 视频、卫星定位、接入网关 |
| `queue` / `file` / `search` / `chart` | 消息、资料、检索、图表 |
| `calendar` / `bell` / `email` | 计划、预警通知、邮件 |
| `key` / `firewall` / `backup` | 凭证、边界防护、备份恢复 |
| `cluster` / `monitor` | 集群、运维监控 |
| `upload` / `download` / `contract` | 上报、下载、合同规范 |

## 6. 分层架构图 `layered_architecture`

适用于总体架构、技术架构、数据架构、安全架构。

```json
{
  "type": "layered_architecture",
  "placement": "3.1 系统总体架构设计",
  "title": "平台系统总体架构图",
  "actors": [
    {"title": "监管部门", "desc": "分析研判", "icon": "government"}
  ],
  "layers": [
    {
      "label": "业务应用层",
      "en": "APPLICATIONS",
      "columns": 4,
      "items": [
        {"title": "实时监控", "icon": "map", "style": "accent"}
      ]
    }
  ],
  "integrations": [
    {"title": "国家平台", "icon": "api"}
  ]
}
```

约束：

- `layers` 至少一层。
- 每层建议 `3` 至 `8` 个节点，`columns` 建议 `3` 至 `5`。
- 最底层可使用 `"style": "dark"` 表现基础设施、安全或保障体系。

## 7. 流程图 `flowchart`

适用于业务闭环、审批流程、处置流程、实施路径。

```json
{
  "type": "flowchart",
  "title": "异常处置闭环流程图",
  "nodes": [
    {"id": "monitor", "title": "实时监测", "row": 0, "col": 0, "icon": "map"},
    {"id": "judge", "title": "存在异常?", "row": 0, "col": 1, "kind": "decision", "icon": "alert"},
    {"id": "done", "title": "闭环完成", "row": 1, "col": 2, "kind": "success", "icon": "check"}
  ],
  "edges": [
    {"from": "monitor", "to": "judge"},
    {"from": "judge", "to": "done", "label": "是"}
  ]
}
```

约束：

- `id` 必须唯一，且只使用字母、数字、下划线和横线。
- `row` 和 `col` 决定布局位置，大模型应避免多个节点占用同一坐标。
- 判断节点使用 `kind: "decision"`；结果节点可使用 `success` 或 `failure`。
- `edges.from` 和 `edges.to` 必须引用已存在节点。

## 8. 功能能力框图 `capability_map`

适用于功能响应、能力体系、建设内容总览。

```json
{
  "type": "capability_map",
  "title": "平台功能能力框图",
  "columns": 3,
  "groups": [
    {
      "label": "监测感知",
      "icon": "location",
      "items": [
        {"title": "实时状态", "icon": "dashboard"},
        {"title": "移动轨迹", "icon": "location"}
      ]
    }
  ]
}
```

约束：

- 每个能力分组建议 `2` 至 `6` 项。
- `columns` 推荐为 `2` 或 `3`，以确保标书页面可读性。

## 9. 泳道流程图 `swimlane_flowchart`

适用于跨角色办理、审批流转、事件处置与责任分工表达。

```json
{
  "type": "swimlane_flowchart",
  "title": "异常事件处置泳道图",
  "lanes": [
    {"id": "unit", "title": "涉源单位", "icon": "organization"},
    {"id": "platform", "title": "监管平台", "icon": "server"}
  ],
  "steps": [
    {"id": "submit", "lane": "unit", "order": 0, "title": "异常申报", "icon": "form"},
    {"id": "accept", "lane": "platform", "order": 1, "title": "事件受理", "icon": "workflow"}
  ],
  "edges": [
    {"from": "submit", "to": "accept", "label": "上报", "relation": "data"}
  ]
}
```

约束：

- `lanes[].id` 和 `steps[].id` 必须分别唯一；`steps[].lane` 必须引用现有泳道。
- `order` 表示从上到下的时序位置，跨泳道步骤应留出清楚的连线通道。

## 10. 时序图 `sequence_diagram`

适用于接口调用、数据上传、告警推送和系统间协同交互。

```json
{
  "type": "sequence_diagram",
  "title": "预警触发交互时序图",
  "participants": [
    {"id": "device", "title": "定位终端", "icon": "gps"},
    {"id": "service", "title": "预警服务", "icon": "ai"}
  ],
  "messages": [
    {"from": "device", "to": "service", "label": "上传位置", "relation": "data", "activate": true},
    {"from": "service", "to": "device", "label": "告警反馈", "relation": "alert"}
  ]
}
```

约束：

- `participants[].id` 必须唯一；消息的 `from` 和 `to` 必须引用现有参与方。
- `activate: true` 用于突出本次调用的处理方激活状态。
- 自调用可使用相同的 `from` 与 `to`，用于表达规则计算或内部校验。

## 11. 复杂关系架构图 `relationship_map`

适用于需要表达所属域、包含关系、跨模块交互及多类数据流向的系统框图。外层 `containers` 形成清晰边界，内部 `nodes` 通过 `id` 被连线引用。

```json
{
  "type": "relationship_map",
  "title": "监管数据联动关系图",
  "columns": 3,
  "containers": [
    {
      "id": "platform",
      "title": "平台核心域",
      "icon": "server",
      "style": "accent",
      "row": 0,
      "col": 0,
      "nodes": [
        {"id": "ingest", "title": "接入服务", "icon": "api", "style": "accent"},
        {"id": "warning", "title": "预警服务", "icon": "ai", "style": "danger"}
      ]
    }
  ],
  "edges": [
    {"from": "ingest", "to": "warning", "label": "状态识别", "relation": "flow"},
    {"from": "warning", "to": "ingest", "label": "告警回执", "relation": "alert", "bidirectional": true}
  ]
}
```

连线语义：

| `relation` | 表达含义 | 默认表现 |
| --- | --- | --- |
| `flow` | 业务处理流 | 蓝色实线 |
| `data` | 采集、存储、交换数据流 | 绿色虚线 |
| `control` | 指令、授权、调度 | 紫色长虚线 |
| `alert` | 告警、风险触发 | 红色加粗实线 |
| `sync` | 同步、反馈、回执 | 橙色点线 |

约束：

- 容器用于表示平台域、数据域、接入域或外部系统边界，不用于代替普通节点。
- `containers[].nodes[].id` 在整张图中必须唯一。
- 线条较多时优先分域，并将跨域主关系控制在可阅读范围内。
- 双向关系设置 `bidirectional: true`，避免用两条反向线重复表示。

## 12. 清晰展示约定

- 默认主题为 `clarity_blue`，使用纯白背景、纯白普通容器、高对比文字和清晰边框，适合 Word/PDF 标书插图。
- 节点颜色应表达含义：`accent` 强调核心模块，`success` 表示完成或安全，`warning` 表示待研判，`danger` 表示风险或告警。
- 对正式图件优先输出 SVG；需要评审浏览时同时输出 PNG。

## 13. 大模型生成规则

生成绘图描述时，大模型应遵循：

1. 仅使用文档中明确出现或可直接归纳的业务内容。
2. 对未确认的技术产品、接口范围、部署方式不作虚构，必要时写入 `note`。
3. 标题正式简洁，节点文字优先使用业务术语。
4. 同一文档内优先复用统一图标语义，例如数据均使用 `database`，流程均使用 `workflow`。
5. 总体架构图控制层次和节点数量，避免将详细功能清单全部堆入一张图。
6. 流程图必须保证所有分支都有明确去向。
7. 涉及多个责任主体的办理过程优先使用 `swimlane_flowchart`，涉及服务调用顺序的内容优先使用 `sequence_diagram`。

## 14. 验证与输出

```powershell
# 查询可用图标
python '.\src\generate_architecture_diagram.py' --list-icons
python '.\src\generate_architecture_diagram.py' --render-icon-catalog --output '.\results\current\图标目录' --png

# 只校验大模型生成的描述
python '.\src\generate_architecture_diagram.py' --spec '.\examples\示例_带图标绘图描述.json' --validate-only

# 输出 SVG 与 PNG
python '.\src\generate_architecture_diagram.py' --spec '.\examples\示例_带图标绘图描述.json' --output '.\results\current\图标应用示例' --png
python '.\src\generate_architecture_diagram.py' --spec '.\examples\示例_复杂关系架构描述.json' --output '.\results\current\复杂关系示例' --theme clarity_blue --png
python '.\src\generate_architecture_diagram.py' --spec '.\examples\示例_主流图型描述.json' --output '.\results\current\主流图型示例' --theme clarity_blue --png
```

## 15. 数据型图件 `ECharts HTML`

柱线趋势、雷达评价与 Sankey 数据流向不进入原生 SVG 框图描述，而由本地 ECharts 工作台渲染。AI 只输出符合 [echarts_diagram.schema.json](<../schema/echarts_diagram.schema.json>) 的数据语义描述，不输出 JavaScript 和任意 `option`。

当前支持类型：

| 类型 | 表达内容 | 必须提供的核心字段 |
| --- | --- | --- |
| `bar_line` | 数量与比例的并行趋势 | `categories`、`bar`、`line` |
| `radar` | 多维能力或指标对比 | `indicators`、`series` |
| `sankey` | 来源、汇聚、去向关系 | `nodes`、`links`、`unit` |

通用约束：

- 每张数据图应提供 `title`、`note`、`source`，推荐同时提供 `placement` 和 `dataNotice`。
- AI 不能伪造项目统计数据；模拟值必须在 `note` 或 `dataNotice` 中声明。
- 正式插图从页面导出 SVG；沟通预览可导出 PNG。

示例输入：[示例_ECharts数据图描述.json](<../examples/示例_ECharts数据图描述.json>)。
