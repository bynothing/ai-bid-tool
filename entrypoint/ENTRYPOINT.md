# bid-tool Workspace Entrypoint

> 工作区记录入口。用于快速恢复当前项目状态、定位重点目录，并承接本次 illustration 工具分析结论。

## 当前工作区

- 项目根目录：`D:\AI_native_change\bid-tool`
- 重点分析目录：`src/bid_tool/illustration`
- 关联流水线目录：`src/bid_tool/pipeline/stages`
- 关联 schema 目录：`src/bid_tool/schemas`
- 关联示例目录：`examples`
- 当前关注主题：投标配图工具 `illustration` 的 v2 平台化能力与流水线接入状态

## 分析目录

### 配图工具核心

- `src/bid_tool/illustration/api.py`：对外 Python API 门面，提供 `load`、`validate`、`plan`、`render`、`list_diagram_types`。
- `src/bid_tool/illustration/toolkit.py`：独立 CLI 入口，支撑 `bid-illustrate` 与 `bid-tool illustrate`。
- `src/bid_tool/illustration/platform.py`：v2 平台编排层，负责校验、路由、渲染分组和 manifest 输出。
- `src/bid_tool/illustration/standalone.py`：独立绘图工具包构建入口。

### 配图核心模型与路由

- `src/bid_tool/illustration/core/job.py`：Illustration Job v2 数据模型。
- `src/bid_tool/illustration/core/registry.py`：语义图型注册表，目前可列出 28 类图型。
- `src/bid_tool/illustration/core/decision.py`：`renderer=auto` 的内容分析与渲染器决策。
- `src/bid_tool/illustration/core/router.py`：将图型和渲染策略解析为最终渲染器。
- `src/bid_tool/illustration/core/validator.py`：schema 与语义校验。
- `src/bid_tool/illustration/core/manifest.py`：统一生成 `illustration-manifest.json` 和人工审查清单。

### 渲染器目录

- `src/bid_tool/illustration/renderers/html.py`：HTML/CSS 标书大图渲染器。
- `src/bid_tool/illustration/renderers/svg_v2.py`：SVG native 适配器，复用 `svg_renderer` 能力。
- `src/bid_tool/illustration/renderers/echarts_v2.py`：ECharts 数据图与审图页面渲染器。
- `src/bid_tool/illustration/renderers/mermaid.py`：Mermaid `.mmd`、HTML、SVG/PNG 预览适配器。
- `src/bid_tool/illustration/renderers/graphviz.py`：Graphviz/DOT 拓扑与复杂关系图适配器。
- `src/bid_tool/illustration/renderers/normalize.py`：v2 数据到各渲染器输入的规范化。

### 流水线接入点

- `src/bid_tool/pipeline/stages/s5_illustrate.py`：生成 `s5_illustration_job.json` 的 prompt 与校验入口。
- `src/bid_tool/pipeline/stages/s6_synthesize.py`：调用 illustration API 渲染，并读取 manifest 插入章节 Markdown。
- `src/bid_tool/pipeline/stages/s7_verify.py`：需求覆盖与闭环校验，主要消费 trace，不负责绘图。
- `src/bid_tool/pipeline/engine.py`：阶段顺序包含 `s5_tables -> s5 -> s6 -> s7`。
- `src/bid_tool/pipeline/validator.py`：S5 使用 `illustration_job_v2.schema.json` 做门禁校验。

### 公开协议与文档

- `src/bid_tool/schemas/illustration_job_v2.schema.json`：当前正式公开输入协议。
- `src/bid_tool/schemas/AI_ILLUSTRATION_API_V2.md`：AI 生成配图任务的协议说明。
- `src/bid_tool/illustration/ILLUSTRATION_EXTERNAL_INTERFACE.md`：独立绘图工具外部接口。
- `src/bid_tool/illustration/ILLUSTRATION_CLI_USAGE.md`：CLI 使用说明。
- `src/bid_tool/illustration/ILLUSTRATION_PLATFORM_DESIGN.md`：平台设计方案。
- `src/bid_tool/illustration/ILLUSTRATION_SOFTWARE_ARCHITECTURE.md`：软件架构说明。
- `src/bid_tool/pipeline/stages/BID_TOOL_ILLUSTRATION_ADAPTER.md`：bid-tool 调用 illustration 平台的适配边界。

## 当前功能现状

- illustration 已经是 v2 平台化结构，不再只是单一 SVG 工具。
- 对外入口包括：
  - `bid-tool illustrate --job ...`
  - `bid-illustrate --job ...`
  - `bid-illustration-bundle --output ...`
- 支持渲染器：
  - `html_css`
  - `svg_native`
  - `echarts_html`
  - `mermaid`
  - `graphviz`
- `renderer: "auto"` 会基于图型、意图、数据复杂度、连线数量、是否数据图、是否拓扑图等信号自动决策。
- 输出统一以 `illustration-manifest.json` 为后续 S6/S8 装配契约，调用方不应依赖内部文件命名。
- 示例 v2 JSON 可通过 `--validate-only` 校验。

## 已发现断点

1. `api.plan()` 当前返回 `{id, type, decision}`，没有返回 `renderer` 字段；但 S6 和测试期望 `decision["renderer"]` 存在。
2. `s6_synthesize.render_v2_job()` 调用 `api.render(..., export_echarts=...)`，但 `api.render()` 当前签名没有 `export_echarts` 参数。
3. `src/bid_tool/illustration/_fix_fonts.py` 存在语法错误；主链路编译在排除该文件后通过。
4. 当前工作区已有大量未提交改动，后续实现前需要区分已有改动与新改动。

## 快速验证命令

```powershell
cd D:\AI_native_change\bid-tool

python -m bid_tool.cli illustrate --job examples\示例_独立绘图工具最小闭环.json --validate-only
python -m bid_tool.illustration.toolkit --job examples\示例_配图平台v2任务.json --validate-only
python -c "from bid_tool.illustration import api; print(len(api.list_diagram_types()))"
python -m compileall -q -x "_fix_fonts\.py" src\bid_tool\illustration
```

## 建议下一步

- 修复 `api.plan()`，让返回项包含最终 `renderer`。
- 修复 `api.render()` 签名，透传 `export_echarts` 到 `platform.render_job/render_job_file`。
- 再运行 illustration 相关测试；当前环境缺少 `pytest`，需要安装或切换到已有测试环境。
- 单独评估 `_fix_fonts.py` 是否仍需保留；如果不在主链路中，建议迁移或修复语法后再纳入编译门禁。
