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
| 展示服务器/网络区域 | `architecture.deployment` | 部署架构、安全域 |
| 展示网络设备和链路 | `network.topology` | 网络拓扑 |
| 展示业务办理步骤 | `process.flowchart` | 普通流程 |
| 展示多角色协同 | `process.swimlane` | 泳道流程 |
| 展示接口调用先后 | `interaction.sequence` | 时序图 |
| 展示功能模块分类 | `capability.map` | 能力地图 |
| 展示系统/实体关系 | `relationship.domain` | 关系图 |
| 展示项目进度 | `timeline.gantt` | 甘特图 |
| 展示关键节点 | `timeline.milestone` | 里程碑 |
| 展示概率和影响 | `matrix.risk` | 风险矩阵 |
| 展示评分覆盖 | `matrix.scoring_response` | 评分响应矩阵 |
| 展示方案优劣 | `comparison.solution` | 对比卡片 |
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

### 6.2 流程图 `process.flowchart`

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

### 6.3 甘特图 `timeline.gantt`

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

### 6.4 风险矩阵 `matrix.risk`

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

### 6.5 方案对比 `comparison.solution`

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

