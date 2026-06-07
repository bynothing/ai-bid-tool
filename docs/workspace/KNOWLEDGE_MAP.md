# Knowledge Map

本文件记录项目背景知识和快速查找路径。它不是完整文档的替代品，而是告诉新会话先理解什么、去哪里找。

## 项目背景

`bid-tool` 面向自动撰写标书，目标是把招标材料转化为可审阅、可导出的投标技术文件。

核心流水线：

```text
S1 招标解析
S2 大纲设计
S3 正文撰写
S4 内容冻结
S5 表格与配图任务
S6 图文合成
S7 闭环校验
S8 导出
S9 偏离表
```

快速入口：

- `README.md`
- `WORKSPACE.md`
- `docs/PROJECT_STRUCTURE.md`
- `src/bid_tool/pipeline/engine.py`
- `src/bid_tool/pipeline/stages/`
- `src/bid_tool/schemas/`
- `src/bid_tool/prompts/`

## 配图能力背景

标书配图的目标不是装饰，而是帮助评审快速理解：

- 技术架构是否清楚。
- 实施路径是否可信。
- 风险控制是否闭环。
- 安全、接口、数据、运维是否可追溯。
- 评分点是否有明确响应证据。

当前主入口：

- `src/bid_tool/illustration_v2/api.py`
- `src/bid_tool/illustration_v2/toolkit.py`
- `src/bid_tool/illustration_v2/core/`
- `src/bid_tool/illustration_v2/renderers/`
- `src/bid_tool/illustration_v2/templates/`
- `src/bid_tool/illustration_v2/catalogs/capability_catalog.json`

公开协议：

- `src/bid_tool/schemas/AI_ILLUSTRATION_API_V2.md`
- `src/bid_tool/schemas/illustration_job_v2.schema.json`

配图内容规范：

- `docs/standards/illustration/drawing-content-standard.md`
- `docs/standards/illustration/drawio-integration.md`
- `src/bid_tool/pipeline/stages/BID_WRITING_ILLUSTRATION_STRATEGY.md`
- `src/bid_tool/pipeline/stages/BID_TOOL_ILLUSTRATION_ADAPTER.md`

架构和方案：

- `docs/architecture/illustration-v2/current-architecture.md`
- `docs/architecture/illustration-v2/stable-svg-rendering.md`
- `docs/architecture/illustration-v2/refactor-goal.md`
- `docs/architecture/illustration-v2/decision-analysis.md`
- `docs/architecture/illustration-v2/agent-execution-environment-design.md`
- `docs/architecture/illustration-v2/agent-execution-environment-plan.md`

## 当前配图调用链

```text
S5 / 外部调用方
  -> Illustration Job v2 JSON
  -> api.load_job()
  -> validate_job()
  -> plan_job()
  -> render_decision()
  -> write_manifest()
  -> S6/S8 根据 manifest 装配
```

关键代码：

- Job 模型：`src/bid_tool/illustration_v2/core/models.py`
- 能力目录：`src/bid_tool/illustration_v2/core/catalog.py`
- 决策层：`src/bid_tool/illustration_v2/core/decision.py`
- 校验：`src/bid_tool/illustration_v2/core/validator.py`
- 文本排版：`src/bid_tool/illustration_v2/core/text_measure.py`
- Manifest：`src/bid_tool/illustration_v2/core/manifest.py`
- 模板 SVG：`src/bid_tool/illustration_v2/renderers/template_svg.py`
- Draw.io：`src/bid_tool/illustration_v2/renderers/drawio.py`

## 高频图型

优先理解这些类型：

| 用途 | 当前/目标图型 |
| --- | --- |
| 总体架构 | `architecture.layered` |
| 接口关系 | `relationship.platform_interface` / `integration.interface_map` |
| 故障闭环 | `process.severity_closure` / `operation.incident_response` |
| 运维巡检 | `taxonomy.inspection_cards` / `operation.inspection_taxonomy` |
| 安全保障 | `security.closed_loop` / `architecture.security_ring` |
| 评分响应 | `matrix.scoring_response` |
| 数据趋势 | `chart.*` |
| 复杂拓扑 | `architecture.deployment` / `network.topology` |

## 常用查找命令

查图型和模板：

```powershell
rg "architecture.layered|security.closed_loop|process.severity" src\bid_tool\illustration_v2
```

查 manifest 字段：

```powershell
rg "manifest|needs_human_review|fit_score|degraded" src\bid_tool\illustration_v2 tests
```

查 S5/S6 接入：

```powershell
rg "illustration|s5_illustration|manifest" src\bid_tool\pipeline src\bid_tool\prompts tests
```

查旧版引用：

```powershell
rg "src/bid_tool/illustration|ILLUSTRATION_DATA_SPEC|bid_tool\.illustration" README.md src tests entrypoint docs
```

## 质量语言

后续描述配图问题时，尽量使用可复现术语：

- 图型选择错误。
- 模板容量不足。
- 文本槽位溢出。
- 元素重叠。
- 连线穿越正文。
- 图题与正文引用不一致。
- manifest 未记录降级。
- fallback 比例过高。
- PNG 嵌入 Word 后不可读。

## 不要混淆

- `illustration_v2` 是当前新开发主路线。
- 旧版 `illustration` 在当前工作区中正在迁移删除，不应作为新能力入口。
- `output/` 下多数内容是生成产物或历史验证，不应直接当作源代码事实。
- 示例 Job 可用于 smoke，但不能替代真实样本评估。
