# bid-tool 修改历史

本文档记录 bid-tool 的所有重大修改。凡涉及以下情况之一者，必须更新本文件：
- 新增阶段或删除阶段
- 修改流水线状态机逻辑
- 修改 Schema（字段名、字段类型、新增/删除字段）
- 修改配图工具的图型渲染逻辑（LAYOUT、渲染器函数）
- 修改用户可见的 CLI 命令参数
- 修改提示词模板的结构
- 新增或删除项目类型配置（profiles/*.yaml）
- 修复了影响标书输出正确性的 bug（如图片嵌入错误、章节内容错位）

## 格式

每个条目包含：
- **日期**（YYYY-MM-DD）
- **版本号**（如 v1.1.0，每次重大修改递增）
- **修改类型**：功能新增 / 功能修改 / Bug修复 / 文档更新 / 重大重构
- **修改内容**：具体说明
- **影响范围**：哪些文件或模块受到影响

---

## 2026-05-30 — v1.2.0

**类型**：功能新增 + 流水线调整 + Schema 更新

### 修改内容

**1. 新增表格内容规划阶段**

- 新增 `s5_tables` 阶段，位于 S4 内容冻结之后、S5 配图描述之前。
- 新增 `s5_table_prompt.md`，用于基于冻结正文识别适合表格化表达的内容。
- 新增 `s5_table_plan.schema.json`，约束 `table_insertion_plan.json` 的表格位置、列、行、用途和来源。

**2. 图文合成支持先插表格再插图**

- S6 合成阶段读取 `output/s5_tables/table_insertion_plan.json`。
- S6 会把表格插入章节 Markdown，并继续插入最新绘图 manifest 中的图片/HTML 资产。
- S6 报告新增表格数量和表格插入日志。

**3. 配图阶段避开表格化内容**

- S5 配图 prompt 会读取表格计划，提示 LLM 不要把清单、对照、资源配置类内容重复生成插图。

### 影响范围

- `src/bid_tool/pipeline/engine.py`
- `src/bid_tool/pipeline/validator.py`
- `src/bid_tool/pipeline/stages/s5_tables.py`
- `src/bid_tool/pipeline/stages/s5_illustrate.py`
- `src/bid_tool/pipeline/stages/s6_synthesize.py`
- `src/bid_tool/prompts/s5_table_prompt.md`
- `src/bid_tool/schemas/s5_table_plan.schema.json`
- `pyproject.toml`
- `README.md`

---

## 2026-05-29 — v1.1.0

**类型**：功能新增 + 功能修改 + 文档更新

### 修改内容

**1. 绘图平台独立化**

- 新增 `bid_tool.illustration.standalone`，可生成只包含绘图运行时、V2 schema、示例和文档的独立工具包。
- 新增 `bid-tool illustration-bundle` 命令，支持输出目录和 zip 压缩包。
- 独立包内提供 `run_illustration.py`，解压后可直接运行绘图任务。

**2. 独立 CLI**

- 新增安装后可直接调用的 `bid-illustrate` 命令。
- 新增 `bid-illustration-bundle` 命令。
- `bid-tool illustrate` 补齐 `--png-scale` 参数转发。

**3. 打包资源声明**

- `pyproject.toml` 增加 schema、Markdown 文档和 ECharts 工作台资源的 package-data 配置。

### 影响范围

- `src/bid_tool/illustration/standalone.py`
- `src/bid_tool/cli.py`
- `pyproject.toml`
- `README.md`
- `src/bid_tool/illustration/ILLUSTRATION_CLI_USAGE.md`

---

## 2026-05-28 — v1.0.0

**类型**：功能新增 + Bug修复

### 修改内容

**1. LAYOUT 参数字典化**（`svg_renderer.py`）

将所有渲染函数中的硬编码数值提取到 `LAYOUT` 字典，共 ~100 个参数，包括：
- 字体大小（title、section、node、desc 等 10 种）
- 卡片尺寸（card_h、flow_box_w、layer_dark_card_h 等）
- 间距和边距（header_h、note_bar_h、layer_per_row 等）

所有渲染函数（`defs`、`page_start`、`note_bar`、`item_card`、`render_layered_architecture`、`render_flowchart`、`render_sequence_diagram`、`render_swimlane_flowchart`、`render_relationship_map`、`render_capability_map`）全部改为引用 `LAYOUT` 字典，不再硬编码数值。

**2. `--font-scale` CLI 参数**（`svg_renderer.py`）

新增命令行参数 `--font-scale`，可将全部 LAYOUT 值整体缩放，默认 1.0。
用法示例：`--font-scale 0.85`（缩小 15%）、`--font-scale 1.1`（放大 10%）
新增 `apply_font_scale()` 函数支持代码内调用。

**3. PNG 输出到 `png/` 子目录**（`svg_renderer.py`）

修复 PNG 混在 SVG 目录的问题，PNG 现自动输出到 `output/png/` 子目录。

**4. trace.json 对照表兼容性修复**（`s8_export.py`）

修复 trace.json 字段名不匹配导致的"对照表数据来源 trace.json 不可用"问题：
- `text` → `req_text`
- `outline_id` → `covered_by[0]`
- `body_ids` → `covered_by[1:]`
- 新增 `chapter_name_map` 参数支持 CH-01~CH-12 映射为中文章节名

**5. 中化项目 ch_02.md 图片引用修正**

- 移除错误的 TU-021（保修服务流程图）引用（出现在第 2.2 节）
- 插入正确的 TU-021b（临时水电系统示意图）
- 删除重复的"本章插图"附录段落

### 影响范围

- `src/bid_tool/illustration/svg_renderer.py` — 完全重构 LAYOUT 引用
- `src/bid_tool/pipeline/stages/s8_export.py` — trace.json 字段兼容 + 对照表修复
- `D:\AI_native_change\中化项目\output\s6_synthesis\s6_combined_bid_document.md` — 图片引用修正

### 注意事项

- 之前生成的 PNG 可能混在 SVG 目录中，重新生成时需先清空旧文件
- 调整字体大小时优先使用 `--font-scale`，如需永久调整再修改 LAYOUT 默认值

---

## 2026-05-27 — v0.9.0

**类型**：功能新增

### 修改内容

**1. 首次将两套系统整合为 bid-tool 工具包**

- 工程项目投标流水线（9 阶段 S1~S9）
- 标书框图生成工具集（SVG 渲染 + ECharts）
- 统一入口：`bid-tool init/run/status/gate/illustrate/export`

**2. 新增 svg_renderer.py 配图工具**

支持 6 种 SVG 图型：layered_architecture、flowchart、sequence_diagram、swimlane_flowchart、capability_map、relationship_map

### 影响范围

- 新建 `src/bid_tool/illustration/` 子系统
- 新建 `src/bid_tool/pipeline/stages/s1_parse.py` ~ `s9_deviation.py`
