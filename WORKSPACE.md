# bid-tool 工作空间

本文档是本项目后续持续开发的工作入口。项目真实代码位于：

```text
D:\AI_native_change\bid-tool
```

本轮同时创建了 VS Code / Codex 工作空间文件：

```text
C:\Users\杨辉\Documents\自动标书项目\bid-tool.code-workspace
```

## 项目记忆系统

本项目不依赖智能体长期记忆。每次开发进入时，先读取下面的固定文件恢复上下文：

1. `WORKSPACE.md`：项目根入口。
2. `docs/workspace/STATE.md`：当前状态、测试基线、风险和下一步。
3. `docs/PROJECT_BUILD_OVERVIEW.md`：工程项目级建设总控。
4. `docs/PROJECT_FEATURES.md`：已完成功能和能力成熟度。
5. `docs/PROJECT_TODO.md`：全工程 TODO 队列。
6. `docs/NAVIGATION.md`：按任务类型导航。
7. `docs/FILE_GOVERNANCE.md`：文件管理和 Git 跟踪规则。
8. `docs/workspace/ROADMAP.md`：阶段计划、任务板和验收标准。
9. `docs/PROJECT_STRUCTURE.md`：项目文件结构和新增文件归位规则。
10. `docs/quality-targets/illustration/README.md`：配图质量目标、人工参考入口和持续 Todo。
11. `docs/workspace/KNOWLEDGE_MAP.md`：背景知识、模块地图和查找命令。
12. `docs/workspace/DECISION_LOG.md`：关键架构决策。

维护规则见：

```text
docs/workspace/MAINTENANCE_PROTOCOL.md
```

每次开发结束，至少更新 `STATE.md`、`ROADMAP.md` 或 `SESSION_HANDOFF.md` 中的一个，确保下一次能继续。

## 当前定位

`bid-tool` 是一个面向标书自动生成的 9 阶段流水线项目，核心链路是：

```text
招标材料
  -> S1 解析
  -> S2 大纲
  -> S3 正文
  -> S4 冻结
  -> S5 表格与配图任务
  -> S6 图文合成
  -> S7 闭环校验
  -> S8/S9 导出与偏离表
```

当前最重要的工程问题是：如何在标书正文基础上，构建高质量、稳定、快速、高性价比的自动配图能力。

## 工作区状态提醒

当前 Git 工作区已有大量未提交改动，主要集中在：

- `src/bid_tool/illustration_v2/`
- `src/bid_tool/pipeline/stages/`
- `src/bid_tool/schemas/`
- `tests/`
- 旧版 `src/bid_tool/illustration/` 删除迁移

后续开发必须先看 `git status --short --branch`，不要回滚既有改动。新增功能应尽量小步提交，并把“已有改动”和“新开发改动”在提交说明里分清楚。

## 快速进入

```powershell
cd D:\AI_native_change\bid-tool
pip install -e .
pip install -e ".[full]"
bid-tool --help
bid-illustrate --help
pytest
```

如果只验证配图工具：

```powershell
bid-illustrate --job examples/示例_配图平台v2任务.json --output output/workspace_smoke --png
```

如果需要 Draw.io 能力：

```powershell
tools\drawio.ps1 --help
```

## 核心开发文档

| 文档 | 用途 |
| --- | --- |
| `README.md` | 项目总入口与命令 |
| `AGENTS.md` | 智能体启动协议 |
| `docs/NAVIGATION.md` | 人和智能体导航 |
| `docs/FILE_GOVERNANCE.md` | 文件治理和 Git 跟踪规则 |
| `docs/PROJECT_BUILD_OVERVIEW.md` | 工程项目级建设总控 |
| `docs/PROJECT_FEATURES.md` | 已完成功能和能力成熟度 |
| `docs/PROJECT_TODO.md` | 全工程 TODO 队列 |
| `docs/PROJECT_STRUCTURE.md` | 项目文件结构与放置规则 |
| `src/bid_tool/schemas/AI_ILLUSTRATION_API_V2.md` | AI 配图 Job v2 调用协议 |
| `src/bid_tool/schemas/illustration_job_v2.schema.json` | Job v2 JSON Schema |
| `docs/architecture/illustration-v2/current-architecture.md` | 当前配图 v2 架构 |
| `docs/architecture/illustration-v2/stable-svg-rendering.md` | 稳定 SVG 渲染方案 |
| `docs/standards/illustration/drawing-content-standard.md` | 绘图内容标准 |
| `docs/standards/illustration/drawio-integration.md` | Draw.io 集成说明 |
| `docs/quality-targets/illustration/README.md` | 配图质量目标入口 |
| `docs/quality-targets/illustration/TODO.md` | 配图工程级质量持续任务 |
| `src/bid_tool/pipeline/stages/BID_WRITING_ILLUSTRATION_STRATEGY.md` | 标书流水线中的配图策略 |
| `src/bid_tool/pipeline/stages/BID_TOOL_ILLUSTRATION_ADAPTER.md` | 流水线调用配图工具的适配说明 |

## 自动配图的北极星

自动配图不应该让大模型直接画 SVG 坐标。稳定路线应当是：

```text
LLM 理解正文与评分点
  -> 选择图型 / 模板 / 表达意图
  -> 生成结构化 Illustration Job
  -> 软件执行契约校验、排版、路由和渲染
  -> 输出 SVG/PNG/manifest
  -> S6/S8 装配进标书
```

一句话：LLM 做语义和决策，软件做确定性绘制和质量门禁。

## 配图能力分层

### Tier 1：模板 + 契约生成

这是主路线，目标是高质量、高稳定。

- 适合：总体架构、接口关系、故障闭环、安全保障、巡检分类、评分响应矩阵等高频标书图。
- 方法：冻结几何模板，运行时只填槽位内容、主题变量和少量状态。
- 质量保证：Schema、容量限制、文本槽位、几何 QA、manifest 留痕。
- 成本优势：LLM 只生成结构化 JSON，不生成大段 SVG，速度快且 token 成本低。

### Tier 2：柔性渲染器

这是通用降级路线，目标是不因模板不足而卡住流水线。

- 数据图：ECharts。
- 复杂关系、拓扑、部署：Draw.io / Graphviz。
- 标准流程、时序、甘特：Mermaid 或 Draw.io。
- 标书展示型页面：HTML/CSS 或组件化 SVG。

### Tier 3：自由矢量兜底

这是最后兜底，目标是不开天窗。

- 允许质量低于 Tier 1。
- 必须在 manifest 中标记 `needs_human_review=true`。
- 后续应通过样本沉淀，把常见 Tier 3 场景升级为 Tier 1 模板。

## 当前优先级

### P0：把决策层做成一等核心

目标：让 `renderer: "auto"` 不只是选渲染器，而是选择完整产出路径。

应输出：

- 能力目录：模板能力 + 柔性渲染器能力 + 各自不适用条件。
- 决策记录：选择原因、降级原因、是否需要人工复核。
- Manifest 字段：`tier`、`template`、`renderer`、`fit_score`、`degraded_from`、`warnings`。

### P1：建立真实样本基准集

目标：不用示例自嗨，直接用真实标书内容评估。

建议建立：

```text
tests/fixtures/illustration_cases/
  architecture_layered/
  interface_map/
  incident_response/
  inspection_taxonomy/
  security_loop/
  dense_topology/
  scoring_matrix/
```

每个 case 至少包含：

- 输入章节片段。
- 期望图型。
- 期望 Job。
- 输出 SVG/PNG。
- manifest。
- 人工质量备注。

### P2：几何级 QA

目标：让“成功”以渲染结果为准，而不是以 JSON 字段合法为准。

最低门禁：

- 无 `data-fit="false"`。
- 文本不爆框。
- 元素不重叠。
- 连线不穿越关键文本。
- PNG 导出清晰可读。
- 图题、章节、图号和正文引用一致。

### P3：低成本 LLM 策略

目标：让大模型只花在高价值决策上。

推荐拆分：

```text
便宜模型：章节扫描、候选图位、普通 Job 草稿
强模型：复杂图型选择、契约修复、保意压缩
确定性代码：Schema 校验、容量判断、渲染、QA、manifest
```

缓存策略：

- 按章节 hash 缓存候选图位。
- 按 Job hash 缓存渲染结果。
- 按模板契约版本缓存修复提示。
- 只有正文或模板契约变化时才重跑相关图。

## 下一阶段建议任务板

当前任务板以 `docs/workspace/ROADMAP.md` 为准。配图质量专项任务以 `docs/quality-targets/illustration/TODO.md` 为准。

最近建议优先级：

1. 人工在 `docs/quality-targets/illustration/references/` 提供 5-10 张目标参考图，并填写参考说明。
2. 建立当前系统输出基线和评分记录，明确“不清楚、不美观、箭头乱”的具体样本。
3. 梳理架构图、流程图、接口图的表达模型和箭头治理策略。
4. 梳理 `illustration_v2/core/decision.py`，确认 Tier 字段、降级链和 manifest 是否完整。
5. 给模板 SVG / Draw.io 输出增加几何 QA 和关系 QA 的最小自动检查。

## 开发纪律

- 每次重大修改同步更新 `CHANGELOG.md`。
- Schema、CLI、流水线行为变更必须配测试。
- 旧版 `illustration` 到 `illustration_v2` 的迁移不要混入无关重构。
- 配图质量问题优先沉淀为 fixture，而不是只修某一张图。
- 任何自动降级都必须写入 manifest，不能静默发生。
