# 阶段 5：投标配图平台任务生成 Prompt

## 角色

你是一名投标文件信息图设计师，负责把标书正文中的关键技术方案、实施计划、评分响应、风险控制和数据统计转化为结构化配图任务。

你的输出不是图片，也不是 SVG、HTML 或 ECharts option。你的输出必须是可由独立绘图工具 `bid-illustrate` 调用的 **Illustration Job v2 JSON**。

## 输出要求

只输出 JSON 对象，不要使用 Markdown 代码块，不要输出任何解释文字。

顶层结构必须为：

```json
{
  "version": "2.0",
  "document": { "title": "投标技术方案", "projectName": "项目名称", "bidSection": "技术方案" },
  "style": { "theme": "formal_blue", "tone": "technical", "preferredFormat": "both", "palette": "engineering_blue" },
  "illustrations": []
}
```

每张图必须包含：`id` / `type` / `renderer: "auto"` / `intent` / `insertion{ section, caption }` / `data` / `visual`。

## 图型选择

| 章节目的 | type |
|---|---|
| 总体技术架构、平台组成、系统层级 | `architecture.layered` |
| 部署、安全域、服务器、终端 | `architecture.deployment` |
| 网络设备、链路、边界 | `network.topology` |
| 业务流程、服务流程、运维流程 | `process.flowchart` |
| 多部门/多角色协同 | `process.swimlane` |
| 接口调用、消息交互 | `interaction.sequence` |
| 功能模块、服务能力、响应能力 | `capability.map` |
| 系统、组件、数据库实体关系 | `relationship.domain` |
| 项目实施周期 | `timeline.gantt` |
| 关键节点和交付成果 | `timeline.milestone` |
| 风险概率和影响 | `matrix.risk` |
| 评分项与响应章节覆盖 | `matrix.scoring_response` |
| 双平台接口关系、数据推送反馈、接口安全要求 | `integration.interface_map` |
| 趋势、数量、比例、评价指标 | `chart.*`（如 `chart.bar_line`、`chart.pie_donut` 等）|

## 视觉规范

工程化正式风格：白底浅背景、深蓝灰主色、低饱和强调色、细边框圆角分区。不要为每张图切换大面积彩色主题。

框图采用"图3风格"：顶部深蓝标题栏 + 白底主体 + 底部说明/图例/结论。
renderer 默认 `auto`，不要手动指定。

## 五层信息结构（核心要求）

每张图的 `data` 必须同时包含以下五个层级：

| 层级 | 必须字段 |
|---|---|
| 顶层 | `title` + `subtitle`（可选 `summary`） |
| 中层 | `categories[]` / `platforms[]` / `levels[]` / `measures[]` / `layers[]` 之一 |
| 子层 | `content[]` + `checks[]` + `items[]`（可选 `flows[]`） |
| 辅助层 | `notes[]` + `requirements[]` + `safeguards[]`（至少含一种） |
| 结论层 | `note` / `conclusion` / `loop[]`（可选） |

### 字段规范

| 字段 | 说明 |
|---|---|
| `index` | 序号（整数），图中编号 |
| `icon` | 图标名：`server`/`shield`/`calendar`/`alert`/`check`/`bell`/`document`/`settings`/`monitor`/`user` 等 |
| `style` | 配色语义：`default` / `accent` / `success` / `warning` / `danger` / `purple` / `cyan` |
| `desc` | 单行描述 |
| `content[]` / `items[]` | 多行字符串数组 |
| `output` | 单行输出成果 |
| `checks[]` | 检查项数组 |
| `trigger` | 触发条件（单行） |
| `ackLabel` | 接口回执标签（flows 必须有） |

## type 与 data 字段对照

| type | 必须包含的 data 字段 |
|---|---|
| `architecture.layered` | `layers[]`（含 `index`/`label`/`items[]`） |
| `architecture.deployment` | `platforms[]`（含 `index`/`title`/`items[]`） |
| `process.flowchart` | `flows[]`（含 `index`/`title`/`icon`/`style`/`content[]`/`output`） |
| `integration.interface_map` | `leftPlatform` + `rightPlatform`（各含 `layers[]`）、`flows[]`（含 `ackLabel`）、`requirements[]`、`notes[]` |
| `operation.inspection_taxonomy` | `categories[]`（含 `index`/`icon`/`style`/`trigger`/`content[]`/`checks[]`/`output`） |
| `operation.incident_response` | `levels[]`（含 `definition`/`scenes[]`/`response`/`handling`/`service`/`upgrade`）、`steps[]`（含 `desc`/`output`）、`safeguards[]` |
| `architecture.security_ring` | `core`（含 `title`/`desc`/`icon`）、`measures[]`（含 `index`/`items[]`）、`loop[]`（含 `title`/`icon`） |
| `timeline.gantt` | `phases[]`（含 `start`/`end`/`desc`/`milestone`） |
| `matrix.risk` | `risks[]`（含 `probability`/`impact`/`level`/`mitigation`） |
| `chart.*` | 数据序列 + `source`（或 `dataNotice`） |

## 禁止事项

- 禁止旧版 `illu_id/type/text_content` 结构。
- 禁止 SVG / Mermaid / ECharts option。
- 禁止数据图缺少 `source`；模拟数据缺少 `dataNotice`。
- 禁止图题口语化；禁止节点名称空泛（如"平台能力""数据底座"）。
- **禁止 data 浅薄**：必须包含完整的五层结构（顶层/中层/子层/辅助层/结论层）。
- **禁止数组元素缺字段**：每个 `categories`/`steps`/`measures`/`flows`/`requirements`/`notes` 元素必须含 `index`、`icon`、`style`、`desc`/`items`/`content` 之一。
- **禁止 flows 缺 ackLabel**。

## 质量自检

- `id` 唯一，`intent` 明确，`type` 与章节目的匹配。
- `data` 含完整五层结构。
- 数组元素含 `index`/`icon`/`style`/`desc`。
- flows 含 `ackLabel`。
- 数据图含 `source` 或 `dataNotice`。
- 模拟数据含 `dataNotice` + `visual.watermark`。
- 输出完整 JSON，不要解释、不要 markdown 包裹。

## 禁止事项

- 禁止输出旧版 `illu_id/type/text_content` 结构。
- 禁止直接输出 SVG、Mermaid、ECharts option。
- 禁止数据图缺少 `source`。
- 禁止模拟数据不标注。
- 禁止图题口语化。
- 禁止节点名称空泛，如"平台能力""数据底座""智能赋能"。
- **禁止 data 字段浅薄单一**：每张图的 `data` 必须包含完整的五层信息结构（顶层/中层/子层/辅助层/结论层），不得只输出孤立的 `items[]` 数组。
- **禁止缺少 index/icon/style/desc**：categories、steps、measures、flows、requirements、notes 等数组中的每个元素必须包含 `index`（序号）、`icon`（图标）、`style`（配色风格）、`desc`/`description`/`items`（描述内容）。
- **禁止缺少辅助层信息**：notes（附注）、requirements（要求）、safeguards（保障措施）必须作为独立字段存在，不得省略。
- **禁止缺少 flows 的 ackLabel**：接口交互类图的每条 flow 必须有 `ackLabel`（回执标签）。

## 质量自检

输出前确认：

- 所有图件 `id` 唯一。
- 每张图有明确 `intent`。
- 每张图的 `type` 与章节目的匹配。
- 数据图包含 `source`。
- 模拟数据包含 `dataNotice` 和 `visual.watermark`。
- 图件数量不要过多，优先每章 1-3 张关键图。
- **data 包含完整的五层信息**：title/subtitle/summary（顶层）、categories/platforms/levels/measures（中层）、content/items/checks/flows（子层）、notes/requirements/safeguards（辅助层）、note/conclusion/loop（结论层）。
- **数组元素包含所有必要字段**：index、icon、style、desc/items 中至少一项。
- **flows 包含 ackLabel 字段**（接口类图）。


---

## 正文内容（插图占位检测）


## 表格化内容计划

### 已规划表格（请避免生成重复插图）
```json
{
  "version": "1.0",
  "document": {
    "title": "典型表格规划测试",
    "projectName": "中化施工总承包项目",
    "bidSection": "技术方案"
  },
  "strategy": {
    "summary": "将资源配置类内容优先表格化，避免与部署图重复。",
    "tableDensity": "medium",
    "avoidDuplicatingIllustrations": true
  },
  "tables": [
    {
      "id": "TB-001",
      "section": "CH-02",
      "title": "表2-1 施工现场临时设施配置表",
      "purpose": "结构化说明办公区、生活区、材料堆场和施工区的配置要求。",
      "reason": "配置清单类内容适合表格表达，不需要绘制成图。",
      "placement": "section_start",
      "columns": [
        "设施类别",
        "配置内容",
        "管理要求",
        "对应要求"
      ],
      "rows": [
        [
          "办公区",
          "项目经理部、会议室、资料室",
          "统一标识、专人管理",
          "现场管理要求"
        ],
        [
          "材料堆场",
          "钢筋、模板、周转材料分区堆放",
          "分类标识、防雨防潮",
          "文明施工要求"
        ]
      ],
      "sourceRefs": [
        "CH-02",
        "RQ-TECH-003"
      ],
      "notes": [
        "表格内容应与施工总平面图保持一致。"
      ]
    }
  ]
}
```

## 设计规范

{
  "font_family": "微软雅黑, Consolas",
  "font_size_range": "9pt-28pt",
  "icon_style": "线性图标, Material Design Icons 风格, 单色#1a3a5c",
  "connector_style": "实线箭头",
  "shadow_style": "box-shadow: 0 2px 8px rgba(0,0,0,0.08), 圆角矩形 border-radius: 6px",
  "border_style": "节点边框 1px solid #d0d5dd"
}

---

## 输出指令

请按以上 prompt 要求，输出一份完整 Illustration Job v2 JSON（60张图左右）。
将最终 JSON 保存为：
  output\s5_illustrations_prompt_smoke\s5_illustration_job.json

项目名称: 典型场景测试
