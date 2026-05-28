# 标书 AI 绘图服务深化规划

> 状态：规划稿  
> 日期：2026-05-27  
> 范围：在现有 SVG 框图验证成果上，建设面向大模型调用的标书图件生成服务。本文件不包含立即重构实施。

## 实施调整：数据图优先采用本地 HTML

依据当前使用诉求，数据型图件的第一阶段落地方式由“先建设 ECharts 服务端 SSR 引擎”调整为“先提供可离线打开的 ECharts HTML 工作台”。已实现入口为 [echarts-workbench/index.html](<../web/echarts-workbench/index.html>)，其优势是无需部署、可直接导入 AI JSON 审图并导出 SVG/PNG。

本调整不改变总体分工：专用 SVG 引擎仍负责架构图、流程图、时序图等框图；ECharts 负责趋势、雷达、Sankey 等数据型图件。后续在出现批量无人值守出图、文档自动组装或 API/MCP 调用需求时，再将相同 Schema 与渲染配置封装为服务。

## 1. 结论摘要

当前原型已经验证了正确方向：由 AI 输出结构化绘图描述，由程序稳定生成可插入标书的 SVG/PNG。但继续在单个 Python 文件中添加图型、主题、图标和导出逻辑，会很快失去可维护性。

建议建设一个独立的 **Proposal Diagram Service（标书图件服务）**，采用如下核心路线：

1. 对 AI 暴露统一的 `DiagramSpec v2` 协议，而不是让模型直接输出 SVG 坐标或任意 ECharts 配置。
2. 将“标书专用框图”与“数据可视化图表”交给不同渲染引擎，最终统一为 SVG/PNG 输出。
3. 专用 SVG 引擎负责高质量架构图、流程图、泳道图、时序图、关系图、部署图与安全体系图。
4. ECharts SVG SSR 引擎负责柱线图、雷达图、仪表盘、漏斗图、Sankey、关系网络、地图/热力和数据趋势图。
5. Mermaid 作为可选兼容引擎，用于快速导入已有文本图或技术附录草图，不作为正式标书美术质量的默认输出。
6. 新服务优先采用 TypeScript/Node.js 独立实现；当前 Python 原型冻结为基准样例和回归对照，不继续承担无限扩展职责。

## 2. 当前基础与痛点

### 2.1 已具备能力

当前验证目录已包含：

| 能力 | 当前状态 |
| --- | --- |
| AI JSON 描述接口 | 已有 JSON Schema 和提示词模板 |
| 输出格式 | SVG 与 PNG |
| 内置主题 | 默认净白高对比主题，另有多套主题 |
| 图标系统 | 47 个内置 SVG 语义图标 |
| 框图类型 | 分层架构、流程、泳道、时序、能力、复杂关系共 6 类 |
| 可审阅产物 | `results/current/` 已形成正式样例 |

### 2.2 维护问题

当前渲染脚本 [generate_architecture_diagram.py](<../src/generate_architecture_diagram.py>) 已达到 `1041` 行，主要职责集中在同一文件：

| 职责 | 当前位置 | 问题 |
| --- | --- | --- |
| 主题和颜色 Token | 文件头部 `THEMES` | 新风格会持续放大配置块 |
| 图标注册与 SVG path | 文件头部 `ICONS` | 图标扩容后不便检索、分类、测试 |
| SVG 基础组件 | `text` / `rect` / `item_card` 等 | 与图型布局相互依赖 |
| 6 类布局渲染器 | `render_*` | 新增图型会继续拉长主文件 |
| Schema 语义校验 | `validate_spec` | 每种图型的业务校验堆叠 |
| PNG 导出、清单、CLI | 文件末尾 | 与核心渲染职责混合 |

核心判断：当前文件适合作为效果验证原型，不适合作为长期服务内核。

## 3. 产品目标

### 3.1 核心用户场景

用户正在编写投标书、建设方案、汇报材料或技术响应文档，需要在指定章节生成美观且信息充分的图件：

| 场景 | 图件示例 |
| --- | --- |
| 总体方案 | 系统总体架构、技术架构、部署架构、数据架构、安全体系 |
| 业务响应 | 监管闭环、审批流程、应急处置、泳道责任图 |
| 技术说明 | 接口时序、系统集成、数据交换、网络拓扑 |
| 数据证明 | 建设规模统计、覆盖分析、趋势、指标雷达、风险分布 |
| 复杂表达 | 多系统协同、Sankey 数据流、地图态势、能力与指标复合图 |

### 3.2 必须达到的结果

- AI 能根据章节内容推荐图型并生成结构化描述。
- 输出图应适配 A4 文档阅读，文字清楚，信息完整，颜色具有语义。
- 输出为可编辑、可复用的 SVG，并可导出高清 PNG。
- 图中可附带插入位置、图题、来源说明与未确认信息提示。
- 同一标书的全部图件可共享主题、字体、图标与编号规则。
- 图件出错时能够反馈给 AI 修正描述，而不是依赖人工修改 SVG。

### 3.3 非目标

- 不以替代专业设计软件的自由手工排版为目标。
- 不让 AI 默认直接编写原始 SVG 或原始 ECharts `option`。
- 不在第一阶段建设复杂在线协同编辑器。

## 4. 图件能力规划

### 4.1 标书框图引擎负责的图型

这类图对内容布局、标题栏、图标、边框、正文可读性要求高，适合使用自有 SVG 组件和布局规则。

| 图型 ID | 图型 | 优先级 | 说明 |
| --- | --- | --- | --- |
| `architecture.layered` | 分层架构图 | P0 | 延续现有总体架构能力 |
| `process.flow` | 标准流程图 | P0 | 支持分支、回路、语义箭头 |
| `process.swimlane` | 泳道流程图 | P0 | 责任主体与审批流转 |
| `interaction.sequence` | 时序图 | P0 | 系统调用和事件交互 |
| `relationship.domain` | 领域关系图 | P0 | 容器、包含、跨域交换 |
| `capability.map` | 能力体系图 | P0 | 功能响应和能力分组 |
| `architecture.deployment` | 部署拓扑图 | P1 | 网络区域、服务器、终端、链路 |
| `architecture.security` | 安全防护体系图 | P1 | 边界、访问、审计、备份 |
| `data.pipeline` | 数据治理流程图 | P1 | 数据采集、治理、共享、应用 |
| `roadmap.timeline` | 建设路线图 | P2 | 阶段任务和交付物 |

### 4.2 ECharts 引擎负责的图型

ECharts 适合由 AI 提炼数据、维度、序列与标注，再由服务生成规范化 `option`。正式标书场景优先使用 ECharts 的 SVG 服务端输出。

| 图型 ID | 图型 | 标书使用场景 | 优先级 |
| --- | --- | --- | --- |
| `chart.bar` / `chart.line` | 柱状/折线图 | 投入、数量、趋势、覆盖率 | P1 |
| `chart.combo` | 柱线组合图 | 数量与百分比对照 | P1 |
| `chart.pie` / `chart.rose` | 饼图/玫瑰图 | 构成占比 | P1 |
| `chart.radar` | 雷达图 | 能力响应或评分维度 | P1 |
| `chart.gauge` | 仪表盘 | 达标率、完成率、风险等级 | P2 |
| `chart.funnel` | 漏斗图 | 受理、处置、闭环转化 | P2 |
| `flow.sankey` | 桑基图 | 数据来源至应用流向 | P1 |
| `network.graph` | 关系网络图 | 系统集成或关联主体 | P2 |
| `geo.map` / `geo.heatmap` | 区域图/热力图 | 区域分布、监测覆盖 | P2 |
| `tree.treemap` / `tree.sunburst` | 层次占比图 | 建设内容分解、资产分类 | P2 |

### 4.3 可选 Mermaid 适配

Mermaid 对 AI 生成文本图非常友好，覆盖流程、时序、类图、状态、甘特、ER、Sankey、架构等类型。建议定位为：

- 导入已有 Mermaid 描述，转换为预览或附录图。
- AI 快速草拟阶段用于确认逻辑关系。
- 不作为正式标书主图默认引擎，因为专用主题、复杂排版和品牌一致性受限。
- 外部输入必须沙箱化或禁用不安全内容后再渲染。

## 5. 总体服务架构

```text
章节文本 / 需求清单 / 已知数据 / 插图位置
                  |
                  v
         AI Diagram Planner
  识别应画什么图、抽取事实、选择图型
                  |
                  v
          DiagramSpec v2 JSON
    内容协议，不含底层 SVG 坐标和任意脚本
                  |
          +-------+-------+
          | 校验 / 补全 / 审核 |
          +-------+-------+
                  |
                  v
         Rendering Router
     按图型分发给对应渲染引擎
       /          |           \
      v           v            v
 Proposal SVG   ECharts SSR   Mermaid Adapter
 框图引擎       数据图引擎    可选兼容引擎
      \           |            /
       +----------+-----------+
                  |
                  v
       SVG Post Processor
  主题统一、字体、图题、编号、注脚、水印
                  |
                  v
        QA / Export / Manifest
  SVG、PNG、缩略图、清单、文档装配信息
```

### 5.1 关键原则

- **内容与渲染解耦**：AI 表达图中事实和关系，渲染器决定坐标、线条和排版。
- **多引擎统一外观**：无论使用原生 SVG 或 ECharts，均经过统一主题与文档包装层。
- **可验证优先**：每张图在渲染前进行 Schema 与语义校验，渲染后进行质量检查。
- **保留来源**：图件描述应记录来源段落、数据口径和推断信息，便于标书审校。

## 6. 推荐技术架构

### 6.1 技术选型结论

| 项目 | 推荐选择 | 理由 |
| --- | --- | --- |
| 新服务语言 | TypeScript / Node.js | 与 ECharts、Mermaid、前端预览生态直接兼容；类型可映射 AI 协议 |
| API 形式 | HTTP JSON API + MCP tools | HTTP 方便文档系统集成，MCP 方便大模型直接调用 |
| Schema | JSON Schema + TypeScript 类型生成 | 同时支持 AI 约束、运行期校验和开发期类型 |
| 标书框图引擎 | 自研 SVG component/layout 模块 | 保持当前已验证的正式视觉质量 |
| 数据图引擎 | Apache ECharts SVG SSR | 服务端生成矢量图，适合 Markdown/PDF/Word 插图 |
| 可选文本图引擎 | Mermaid adapter | 快速覆盖补充图型与外部文本导入 |
| PNG/PDF 导出 | SVG 后处理 + Playwright/Sharp 类导出层 | 统一图件输出，不让每个引擎单独处理 |

### 6.2 关于现有前端依赖

当前 `digital-frontend/yudao-ui-admin-v2/package.json` 中同时存在 `echarts: 4.9.0` 与 `echarts5: npm:echarts@^5.4.0`。绘图服务不应直接复用业务前端依赖树：

- 服务需要独立锁定并测试 ECharts 版本，避免业务页面升级影响标书出图。
- Apache ECharts 官方说明基于 `5.3.0+` 可使用无额外依赖的字符串型 SVG SSR。
- 实施 PoC 时应独立验证最新可用主版本的 SVG 输出、中文字体和所需图型后再固定版本。

## 7. AI 绘图协议设计

### 7.1 不直接向 AI 暴露的内容

- SVG 坐标、path、CSS。
- 任意 JavaScript 表达式。
- 未约束的 ECharts `option`。
- 未审核的外部图片 URL 或脚本片段。

原因：这些内容让输出不可控、难验证、难复用，且引入渲染与安全风险。

### 7.2 `DiagramSpec v2` 分层结构

建议协议从“单个图型字段集合”提升为四层：

```json
{
  "version": "2.0",
  "document": {
    "projectName": "甘肃省高风险放射源监管平台",
    "section": "3.2 数据联动与业务协同设计",
    "figureNo": "图 3-4",
    "title": "监管数据联动关系图"
  },
  "presentation": {
    "type": "relationship.domain",
    "theme": "proposal.clean-blue",
    "density": "detailed",
    "format": ["svg", "png"],
    "pageFit": "a4-landscape"
  },
  "content": {
    "nodes": [],
    "groups": [],
    "relations": [],
    "series": []
  },
  "evidence": {
    "sourceParagraphs": [],
    "assumptions": [],
    "unconfirmed": []
  }
}
```

### 7.3 协议中的公共语义

| 语义对象 | 用途 |
| --- | --- |
| `document` | 标书章节、图号、图题、插入位置 |
| `presentation` | 图型、主题、信息密度、纸张适配、输出格式 |
| `content.entities` | 系统、角色、设备、数据集、能力、步骤 |
| `content.relations` | 流转、包含、调用、同步、告警、控制 |
| `content.metrics` | 图表数据、单位、维度、来源、统计口径 |
| `evidence` | 来源依据、AI 推断、待确认事项 |
| `annotations` | 注脚、重点提示、结论标签 |

### 7.4 引擎专有 payload

公共协议之下，按图型提供受控 payload：

| 引擎 | Payload 示例 |
| --- | --- |
| Proposal SVG | `layers`、`lanes`、`participants`、`containers`、`edges` |
| ECharts | `dataset`、`dimensions`、`seriesIntent`、`highlightRules`、`axisUnit` |
| Mermaid | `source` 仅作为导入/兼容字段，默认不允许由外部未信任内容直接渲染 |

## 8. 服务模块拆分

建议新建独立服务目录，不继续扩大 `src/generate_architecture_diagram.py`：

```text
proposal-diagram-service/
|-- apps/
|   |-- api/                         # HTTP API 与任务管理
|   `-- preview/                     # 可选预览审核界面
|-- packages/
|   |-- spec/                        # DiagramSpec v2、Schema、迁移器
|   |-- ai-planner/                  # 提示词、图型选择、内容抽取
|   |-- theme/                       # 标书主题、字体、色彩语义
|   |-- icon-catalog/                # 图标元数据与 SVG 资产
|   |-- layout-core/                 # 对齐、连线、避障、文本测量
|   |-- renderer-proposal-svg/       # 专用框图渲染器
|   |-- renderer-echarts/            # 图表/Sankey/地图 SVG SSR
|   |-- renderer-mermaid/            # 可选文本图适配器
|   |-- export/                      # SVG、PNG、文档引用、缩略图
|   `-- quality/                     # 溢出、遮挡、对比度、快照检测
|-- fixtures/                        # 标书真实场景测试输入
|-- baselines/                       # 视觉回归基线图
`-- docs/
```

### 8.1 当前 Python 原型的归宿

| 处理方式 | 内容 |
| --- | --- |
| 冻结 | 当前 Python 脚本作为 `prototype-v1` 视觉基准，不再新增图型 |
| 迁移 | 将现有 6 类图型样例变成 v2 fixtures 与视觉回归用例 |
| 重建 | 在 `renderer-proposal-svg` 中逐图型重建，并与现有 PNG 比较 |
| 淘汰条件 | 新服务输出满足质量门槛且覆盖已有样例后，再停止旧脚本入口 |

## 9. 渲染引擎分工

### 9.1 Proposal SVG 引擎

专用框图引擎需要重点建设：

- Token 化主题系统：背景、正文、边界、语义色、字体、间距、页面尺寸。
- SVG 组件库：标题区、容器、卡片、徽标、图例、注脚、强调标签。
- 图标资产库：按业务、技术、安全、终端、数据、统计分类，而不是直接堆常量。
- 布局模块：层级布局、泳道布局、时序布局、容器关系布局。
- 连线路由：正交走线、端点避让、标签避让、跨容器通道和线路优先级。
- 文本排版：中文测宽、自动换行、最大文字密度、溢出告警。

### 9.2 ECharts SSR 引擎

ECharts 不接收 AI 生成的原始 `option`；服务提供模板构建器：

```text
AI 输出 chart.radar + 指标/数值/口径/强调项
  -> Spec Validator
  -> RadarOptionBuilder
  -> 标书主题映射
  -> ECharts SVG SSR
  -> 通用标题/图号/注脚包装
```

实施规则：

- 默认 `renderer: "svg"`、`ssr: true`、固定宽高并关闭不适合静态文档的动画。
- 数据图的颜色需使用标书主题 Token，避免与框图视觉脱节。
- 任何指标图必须具备 `unit`、`source`、`period` 或 `assumption` 字段。
- 地图图件必须明确地图数据来源与授权条件。
- 图表输出应被统一包装为含图题、结论短句和数据口径注脚的完整插图。

### 9.3 Mermaid 适配引擎

可用能力：

- 输入已有 Mermaid 代码并生成 SVG。
- 快速验证流程、时序、甘特、ER 等技术关系。

限制策略：

- 正式标书默认不从 Mermaid 图直接交付，除非通过视觉审核。
- 服务端限制配置项与安全级别，禁止外部脚本和危险链接。
- 如果 AI 已能输出 `DiagramSpec v2`，应优先走专用 SVG 引擎而非生成 Mermaid 文本。

## 10. AI 调用服务设计

### 10.1 AI 的两阶段职责

建议不要让 AI 一次完成“判断画什么 + 填满内容 + 出图”。

| 阶段 | AI 输入 | AI 输出 | 人工可审核点 |
| --- | --- | --- | --- |
| 图示策划 | 章节文本、图件目标 | 图件清单、图型建议、插入位置、缺失数据 | 是否值得画、内容是否真实 |
| 绘图描述 | 已确认图件任务、内容事实 | `DiagramSpec v2` | 节点、数据、关系、口径是否正确 |

### 10.2 MCP/服务工具建议

| 工具名 | 作用 |
| --- | --- |
| `diagram.list_types` | 返回可用图型及适用场景 |
| `diagram.list_icons` | 返回图标分类和语义 |
| `diagram.list_themes` | 返回标书主题及视觉用途 |
| `diagram.plan_for_section` | 根据章节提议应生成的插图列表 |
| `diagram.validate_spec` | 校验 AI 输出并返回可修复错误 |
| `diagram.render` | 输出单张 SVG/PNG 和清单信息 |
| `diagram.render_document_set` | 按文档章节批量生成成套图件 |
| `diagram.review` | 返回文字溢出、遮挡、密度或数据口径问题 |
| `diagram.export_package` | 输出用于 Word/PPT/Markdown 的图件包 |

### 10.3 API 返回内容

每次生成不应只返回图片文件：

```json
{
  "jobId": "diagram-job-001",
  "specVersion": "2.0",
  "artifacts": {
    "svg": "...",
    "png": "...",
    "thumbnail": "..."
  },
  "documentUse": {
    "placement": "3.2 数据联动设计",
    "caption": "图 3-4 监管数据联动关系图",
    "altText": "..."
  },
  "quality": {
    "status": "passed",
    "warnings": []
  },
  "evidence": {
    "unconfirmed": []
  }
}
```

## 11. 美观与内容质量标准

### 11.1 标书视觉准则

| 维度 | 要求 |
| --- | --- |
| 背景 | 正式主图默认纯白，不使用大面积灰色底 |
| 文字 | 标题、模块、说明三级层次清晰；缩放到 Word 页面宽度仍可读 |
| 颜色 | 色彩用于语义，不用于无意义装饰；告警、数据、控制、成功等固定语义 |
| 线条 | 箭头端点可见，连线不覆盖文字，关系复杂时具备图例 |
| 内容 | 图中要有足够业务细节，但每个图只表达一个主题 |
| 文档化 | 图题、图号、插入章节、来源/假设/注脚完整 |

### 11.2 自动质量检查

| 检查项 | 实现思路 | 优先级 |
| --- | --- | --- |
| Schema 合法性 | JSON Schema + 语义引用校验 | P0 |
| 文本溢出 | 文本测宽与组件边界检测 | P0 |
| 节点重叠 | 组件 bounds 碰撞检测 | P0 |
| 箭头遮挡 | 路由与端点碰撞检测 | P0 |
| 信息密度 | 节点/边/文本数量阈值警告 | P1 |
| 对比度 | 主题 token 可读性检查 | P1 |
| 视觉回归 | 固定 fixtures 的 PNG 快照比较 | P1 |
| 数据口径完整性 | 图表必须包含单位与来源 | P1 |

## 12. 分阶段建设路线

### 阶段 0：冻结基线与协议升级准备

目标：让现有成果成为可靠参考，而不是继续演进的单文件主干。

交付：

- 冻结当前 Python 原型、Schema v1、现有正式输出作为 `prototype-v1` 基线。
- 固定现有 6 类图与 47 个图标的测试输入、PNG 参考图。
- 编写 `DiagramSpec v2` 草案与 v1 到 v2 转换规则。

验收：

- 所有现有样例可重复生成。
- 能明确区分“现有效果基线”与“新服务实现”。

### 阶段 1：服务骨架与专用 SVG 引擎 MVP

目标：建立可维护的新工程结构，并重建最核心图件。

交付：

- TypeScript 服务骨架、Schema 校验、主题包、图标包、SVG 导出层。
- 首批图型：`architecture.layered`、`process.flow`、`relationship.domain`。
- `diagram.validate_spec`、`diagram.render` API/MCP 能力。
- 标书净白主题与视觉回归测试。

验收：

- 三类核心图输出质量不低于 Python 基线。
- 任一新图型不需要修改服务入口或其他渲染器文件。

### 阶段 2：流程交互图与 ECharts 数据图

目标：覆盖标书中高频流程、接口和统计图。

交付：

- `process.swimlane`、`interaction.sequence`。
- ECharts SVG SSR 引擎与图表模板：柱、线、组合、饼、雷达、Sankey。
- 图表数据来源、单位和周期字段校验。
- 统一标题栏、注脚和 PNG 导出。

验收：

- AI 可以从一段章节和一组统计数据生成成套框图 + 数据图。
- SVG 插入 Word/PDF 后文字和矢量线条保持清晰。

### 阶段 3：AI 编排与批量文档产物

目标：从“生成一张图”升级为“为一份标书规划并生成图件集”。

交付：

- `diagram.plan_for_section` 与 `diagram.render_document_set`。
- 图件清单、编号、章节插入位置、alt text、注脚自动输出。
- AI 校验修正循环：内容不足或关系错误时返回结构化反馈。

验收：

- 对典型方案章节自动建议并生成一组风格一致的图件。
- 人工主要审核业务真实性和表达重点，而不是手调布局。

### 阶段 4：高级图型和文档装配

目标：覆盖更复杂项目和交付流程。

候选交付：

- 地图/热力图、部署拓扑、安全体系、建设路线/Gantt。
- Word/PPT/Markdown 插入辅助能力。
- 可视化预览审核页和局部编辑能力。

## 13. 首轮开发工作包

建议按以下顺序开始实施：

| 顺序 | 工作包 | 产物 |
| --- | --- | --- |
| 1 | 定义 `DiagramSpec v2` | Schema、类型定义、AI 示例 |
| 2 | 创建 TypeScript 服务工程 | API、MCP 接口骨架、测试框架 |
| 3 | 提取主题和图标资产 | 主题 token、分类图标目录、预览页 |
| 4 | 重建分层架构与关系图 | 核心 SVG renderer、视觉基线 |
| 5 | 接入 ECharts SVG SSR | 柱线/雷达/Sankey 样例 |
| 6 | 增加 AI 策划与校验工具 | 章节到图件计划、Spec 修复反馈 |

## 14. 风险与控制

| 风险 | 表现 | 控制方式 |
| --- | --- | --- |
| AI 编造内容 | 图中出现文档未确认能力或数据 | `evidence` 字段、待确认标记、人工审核门 |
| 图型过多导致维护困难 | 每张图单独堆布局代码 | renderer 插件机制、共享布局和组件包 |
| ECharts 输出风格不一致 | 统计图像网页仪表盘而非标书图 | 统一主题包装层和静态图表模板 |
| 文本过长或交叉线过多 | 图件虽完整但不可读 | 密度阈值、自动拆图建议、质量审查 |
| Mermaid 外部内容风险 | 文本渲染引入不安全配置 | 仅可选引擎、沙箱渲染、禁止直接发布 |
| 前端依赖冲突 | 页面 ECharts 与服务端版本互相影响 | 服务单独锁定依赖和发布 |

## 15. 决策点

开始实施前，需要确认以下产品决策：

| 决策 | 推荐默认值 |
| --- | --- |
| 是否新建独立 TypeScript 服务，而不是持续扩展 Python | 是 |
| 首批服务化图型 | 分层架构、普通流程、复杂关系 |
| ECharts 首批图型 | 柱线组合、雷达、Sankey |
| 是否支持 Mermaid | 作为可选导入/草稿适配，不作为正式图默认引擎 |
| 首期交付方式 | MCP tools + 本地 CLI，HTTP API 同步预留 |
| 正式输出主题 | 净白高对比商务主题作为默认 |

## 16. 参考依据

- Apache ECharts 官方 SSR 说明：支持服务端直接输出 SVG 字符串，并建议在可使用 SVG 的静态文档场景优先使用 SVG 渲染。  
  <https://echarts.apache.org/handbook/en/how-to/cross-platform/server/>
- Apache ECharts 官方功能说明：提供柱、线、关系图、地图、热力、Treemap、Sunburst、漏斗、仪表等丰富图型，并支持自定义 series。  
  <https://echarts.apache.org/en/feature.html>
- Mermaid 官方说明：使用文本定义生成 SVG，覆盖流程、时序、状态、ER、甘特、Sankey、Architecture 等多种图型，并提示外部内容安全边界。  
  <https://mermaid.js.org/intro/>
