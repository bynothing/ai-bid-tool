# bid-tool — 标书自动生成工具

9 阶段标书流水线 + 表格规划 + 配图工具集，将招标文件转化为可提交的 Word 投标文件。

> **文档更新约定**：每次重大修改必须同步更新 `CHANGELOG.md`（格式见该文件）。判断标准：是否影响标书输出正确性、是否新增/修改用户可见命令、是否修改 Schema 或流水线逻辑。

---

## 核心文档索引

| 文档 | 定位 |
|------|------|
| [src/bid_tool/illustration_v2/toolkit.py](src/bid_tool/illustration_v2/toolkit.py) | **配图工具入口** — 当前 `bid-illustrate` 命令入口与参数契约 |
| [src/bid_tool/schemas/AI_ILLUSTRATION_API_V2.md](src/bid_tool/schemas/AI_ILLUSTRATION_API_V2.md) | **AI 配图接口** — AI 输出结构化 JSON 配图任务的协议规范 |
| [WORKSPACE.md](WORKSPACE.md) | **持续开发入口** — 项目记忆系统、当前主线、工作区纪律 |
| [docs/PROJECT_STRUCTURE.md](docs/PROJECT_STRUCTURE.md) | **文件结构说明** — 顶层目录、文档归位、源码归位规则 |
| [docs/architecture/illustration-v2/current-architecture.md](docs/architecture/illustration-v2/current-architecture.md) | **平台设计方案** — v2 架构、渲染器选型逻辑、配色体系 |
| [docs/standards/illustration/drawing-content-standard.md](docs/standards/illustration/drawing-content-standard.md) | **绘图内容规范** — 节点文字、箭头标签、复杂度、配色和布局约束 |
| [docs/standards/illustration/drawio-integration.md](docs/standards/illustration/drawio-integration.md) | **Draw.io 集成** — 可编辑 `.drawio` 源文件、CLI 导出与 lint 规则 |
| [src/bid_tool/pipeline/stages/BID_WRITING_ILLUSTRATION_STRATEGY.md](src/bid_tool/pipeline/stages/BID_WRITING_ILLUSTRATION_STRATEGY.md) | **配图策略** — S2/S3/S5/S6/S8 中的配图规划与审查流程 |
| [src/bid_tool/pipeline/stages/BID_TOOL_ILLUSTRATION_ADAPTER.md](src/bid_tool/pipeline/stages/BID_TOOL_ILLUSTRATION_ADAPTER.md) | **调用方适配** — bid-tool 如何调用独立绘图工具 |
| [CHANGELOG.md](./CHANGELOG.md) | 修改历史 |

---

## 安装

```bash
cd D:\AI_native_change\bid-tool
pip install -e .

# 可选：PNG 导出（playwright 截图）
pip install playwright && playwright install chromium

# 全部可选依赖
pip install -e ".[full]"
```

验证安装：

```bash
bid-tool --help
```

---

## 完整标书生成流程（分步说明）

以下是生成一份完整投标文件的标准操作流程，每个需要用户确认的环节都会明确标注。

### 第一步：初始化项目

```bash
# 创建项目目录（建议一个投标项目一个独立目录）
mkdir "D:\投标项目\某施工总承包项目-投标"
cd "D:\投标项目\某施工总承包项目-投标"

# 在项目目录下初始化（project name 不要带"-投标"后缀）
bid-tool init --project "某施工总承包项目" --type construction
```

**产物**：`pipeline_state.json`、`trace.json`

### 第二步：准备招标文件

将原始材料放入 `inputs/` 目录：

```
inputs/
├── 招标文件.md                    ← 必填，招标文件全文（支持 .md/.txt）
├── 技术要求附件.md                ← 推荐，如有独立技术规格书
├── 评分标准说明.md                ← 推荐，如有评分办法文件
└── 报价文件模板.docx              ← S9 偏离表必须，可从招标代理处获取
```

### 第三步：运行 S1 — 招标文件解析

```bash
bid-tool run --from s1 --to s1
```

LLM 会分析招标文件，提取：
- 项目关键信息（工期、质保，质量标准等）
- 一票否决项清单
- 评分标准拆解
- 风险分析
- 技术需求逐条（每条带 RQ-TECH-XXX 编号）

**产物**：`s1_analysis/s1_key_info.json`、`s1_veto_items.json`、`s1_scoring.json`、`s1_risk.json`、`s1_tech_req.json`

**用户确认**：检查 `s1_analysis/` 下各 JSON 文件内容是否正确。如有问题，直接编辑 JSON 文件修正，然后继续。

### 第四步：运行 S2 — 大纲设计

```bash
bid-tool run --from s2 --to s2
```

LLM 根据 S1 输出设计章节大纲，每条技术需求映射到对应章节。

**产物**：`s2_outline/s2_outline.json`

**用户确认**：打开 `s2_outline.json`，核对：
- 章节划分是否符合招标要求
- 各章节覆盖的技术需求是否完整
- 是否有遗漏或多余的章节

### 第五步：运行 S3 — 正文撰写

```bash
bid-tool run --from s3 --to s3
```

LLM 根据 S1+S2 输出撰写 12 章正文，每段正文绑定对应技术需求（RQ-TECH-XXX）。

**产物**：`s3_body/ch_01.md` ~ `ch_12.md`（每章一个 Markdown 文件）

**用户确认（关键）**：逐一审阅每章内容：
- 技术方案是否完整响应了招标文件要求
- 文字表达是否符合企业风格
- 数据和承诺是否合理
- 如有修改建议，直接编辑对应的 `ch_xx.md` 文件

### 第六步：运行 S4 — 内容冻结

> **⏸ 人工确认环节** — 流水线在此暂停，必须用户确认后才能继续

```bash
# 审阅完 S3正文后，执行内容冻结
bid-tool gate s4 --confirm
```

**此环节做什么**：人工确认 S3正文内容无误后，生成 `frozen_approval.json`，将正文内容冻结，后续 S5_tables/S5/S6/S7/S8 不得再修改正文。

**如果不冻结直接继续会怎样**：S5_tables 会基于 S3 正文规划表格，S5 会继续生成插图描述。如果后续发现正文有问题再回头改，表格规划、插图描述和配图都要重新做，代价很大。

**如果发现正文有问题**：回到第五步，直接修改 `s3_body/ch_xx.md`，修改后再执行 S4 冻结。

### 第七步：运行 S5_tables — 表格内容规划

```bash
bid-tool run --from s5_tables --to s5_tables
```

LLM 会基于冻结正文判断哪些内容更适合用表格表达，例如资源配置、职责分工、风险措施、验收项、评分响应对照等。

**产物**：`s5_tables/table_insertion_plan.json`

**用户确认**：检查表格是否真的提升可读性，是否与正文和评分点一致，是否与后续配图重复。

### 第八步：运行 S5 — 插图描述生成

```bash
bid-tool run --from s5 --to s5
```

LLM 分析正文中的插图占位符（`![图 TU-XXX ...]`）和 `s5_tables/table_insertion_plan.json`，为每张插图生成 JSON 描述文件，并避开已经表格化表达的内容。

**产物**：`s5_illustrations/s5_illustration_job.json`（v2 配图任务）+ `s5_illustrations/images/`（配图输出）

**用户确认**：检查配图任务 JSON 中每张插图的描述是否合理，特别是：
- 标题和层级是否正确
- 节点文字是否与正文内容一致
- 图型类型是否适合表现该内容

### 第九步：运行 S6 — 表格 + 图文合成 + 配图生成

```bash
# 生成所有插图（SVG + PNG + 审图页）
bid-tool illustrate --job "output/s5_illustrations/s5_illustration_job.json" --output "output/s5_illustrations/images" --png
```

**产物**：
- `output/s5_illustrations/images/assets/svg/*.svg` — 矢量图
- `output/s5_illustrations/images/assets/svg/png/*.png` — PNG 图（用于嵌入 DOCX）
- `output/s5_illustrations/images/assets/html/*.html` — 审图 HTML
- `output/s5_tables/table_insertion_plan.json` — 表格插入计划
- `s6_synthesis/s6_combined_bid_document.md` — 图文合并后的完整标书

**用户确认**：打开合并后的 `s6_combined_bid_document.md`，检查：
- 每张插图是否插入了正确位置
- 插图标题是否正确（TU-XXX 与正文引用是否对应）
- 是否有错位或重复的插图

### 第九步：运行 S7 — 闭环校验

```bash
bid-tool run --from s7 --to s7
```

自动校验：每条 RQ-TECH 需求是否在正文中得到响应，覆盖率是否达标。

**产物**：`s7_verification/s7_trace_matrix.json`（评分-响应对照表）、`verification_report.md`

**用户确认**：审阅 `verification_report.md`：
- 所有 ★实质性条款是否无偏离
- 覆盖率是否 100%
- 如有警告项，评估是否需要回头修改正文

### 第十步：运行 S8 — 最终导出

```bash
# 生成技术方案 DOCX（含插图和完整对照表）
python -c "
from bid_tool.pipeline.stages.s8_export import export_to_docx
chapter_map = {
    'CH-01': '第一章 总体概述',
    'CH-02': '第二章 施工现场平面布置和临时设施',
    'CH-03': '第三章 施工方案与技术措施',
    'CH-04': '第四章 质量管理体系与措施',
    'CH-05': '第五章 安全管理体系与措施',
    'CH-06': '第六章 环境保护管理体系与措施',
    'CH-07': '第七章 工程进度计划与措施',
    'CH-08': '第八章 资源配备计划',
    'CH-09': '第九章 施工主要机械设备配备',
    'CH-10': '第十章 项目管理机构配备',
    'CH-11': '第十一章 成品保护及后期服务措施',
    'CH-12': '第十二章 应急管理预案',
}
export_to_docx(
    combined_md='output/s6_synthesis/s6_combined_bid_document.md',
    s6_dir='output/s6_synthesis',
    s8_dir='output/s8_final',
    trace_path='output/trace.json',
    chapter_name_map=chapter_map,
    project_name='某施工总承包项目'
)
"
```

**产物**：`output/s8_final/投标文件_某施工总承包项目_技术方案_YYYYMMDD_HHMMSS.docx`

包含内容：
- 完整 12 章正文（带格式和图片）
- 25 张插图
- 附录：技术响应与投标要求对照表（78 条，来源 trace.json）

### 第十一步：运行 S9 — 技术偏离表

```bash
python -m bid_tool.pipeline.stages.s9_deviation run \
    --template "inputs/报价文件模板.docx" \
    --body "output/s3_body" \
    --output "output/s9_deviation"
```

**产物**：`output/s9_deviation/投标文件_某施工总承包项目_偏离表_YYYYMMDD_HHMMSS.docx`

---

## 一键运行（跳过人工确认）

如果对 S1/S2/S3/S5 的 LLM 输出有把握，可以一次性运行多个阶段：

```bash
# S1+S2+S3 连续运行（跳过 S4 人工冻结，直接到 S5）
bid-tool run --from s1 --to s3

# 一次性全部完成（不推荐，跳过了所有人工确认环节）
bid-tool run
```

**警告**：一次性运行到 S8 会跳过 S4 冻结，意味着 S5 插图基于未经确认的正文生成，后续修改正文代价很大。建议至少在 S3 和 S4 之间停下来审阅正文。

---

## 流水线阶段一览

| 阶段 | 名称 | 触发方式 | 人工确认 | 说明 |
|------|------|----------|----------|------|
| S1 | 招标文件解析 | LLM | 建议确认 | 提取关键信息、否决项、评分标准、风险、技术需求 |
| S2 | 大纲设计 | LLM | 建议确认 | 生成章节大纲，映射技术需求到章节 |
| S3 | 正文撰写 | LLM | **必须确认** | 撰写 12 章正文，每段绑定技术需求 |
| S4 | 内容冻结 | 人工 | **必须确认** | 冻结 S3 正文，后续不得修改，否则插图需重做 |
| S5_tables | 表格内容规划 | LLM | 建议确认 | 基于正文识别适合表格化表达的内容 |
| S5 | 插图描述生成 | LLM | 建议确认 | 为每张插图生成 v2 JSON 描述 |
| S6 | 表格图文合成 | 自动 | 可选确认 | 插入表格，生成并合成配图 |
| S7 | 闭环校验 | LLM | 建议确认 | 校验覆盖率，输出校验报告 |
| S8 | 最终导出 | 自动 | 可选确认 | DOCX 含图 + 对照表 |
| S9 | 技术偏离表 | 自动 | 必须确认 | 填写偏离表，输出 DOCX |

---

## 配图工具独立使用

不需要运行流水线时，也可以单独使用配图工具生成 SVG/PNG 图。当前有三种用法：

```bash
# 方式 1：仍在 bid-tool 环境中调用
bid-tool illustrate --job examples/示例_配图平台v2任务.json --output output/my_illustrations --png

# 方式 2：安装后直接调用独立命令
bid-illustrate --job examples/示例_配图平台v2任务.json --output output/my_illustrations --png

# 方式 3：生成可解压运行的独立绘图工具包
bid-tool illustration-bundle --output dist/bid-illustration-standalone --zip
cd dist/bid-illustration-standalone
python run_illustration.py --job examples/示例_配图平台v2任务.json --output output/my_illustrations --png
```

常用校验和参数：

```bash
bid-tool illustrate --job examples/示例_配图平台v2任务.json --validate-only
bid-tool illustrate --job examples/示例_配图平台v2任务.json --output output/my_illustrations --png --png-scale 3
```

独立工具包只包含绘图运行时、V2 schema、示例、ECharts 工作台和使用文档，不包含 S1-S9 标书流水线。

---

## 项目类型配置

`src/bid_tool/profiles/` 下的 YAML 文件定义项目类型：

- `software.yaml` — 软件封装集成项目（13 章模板）
- `construction.yaml` — 施工总承包项目（12 章模板）

如需新建项目类型，参考现有 YAML 文件格式创建新文件。

---

## 目录结构

```
bid-tool/
├── README.md                       # 本文件
├── CHANGELOG.md                    # 修改历史
├── pyproject.toml                  # 包配置
├── src/bid_tool/
│   ├── cli.py                      # 统一 CLI 入口 (bid-tool init/run/status/gate/illustrate/export)
│   ├── __init__.py                 # 版本号导出
│   ├── pipeline/                   # 流水线子系统
│   │   ├── engine.py              # 状态机 + 阶段调度
│   │   ├── validator.py            # Schema 门禁校验
│   │   ├── trace.py                # 需求追溯矩阵
│   │   └── stages/                 # S1~S9 阶段脚本
│   │       ├── s1_parse.py         # S1 招标文件解析
│   │       ├── s2_outline.py       # S2 大纲设计
│   │       ├── s3_body.py          # S3 正文撰写
│   │       ├── s5_illustrate.py    # S5 插图描述生成
│   │       ├── s6_synthesize.py    # S6 图文合成
│   │       ├── s7_verify.py        # S7 闭环校验
│   │       ├── s8_export.py        # S8 DOCX 导出
│   │       └── s9_deviation.py     # S9 偏离表填写
│   ├── illustration/               # 配图子系统
│   │   ├── toolkit.py              # 配图工具统一入口（bid-tool illustrate）
│   │   ├── platform.py             # v2 配图平台编排
│   │   ├── svg_renderer.py         # SVG 图型渲染
│   │   ├── palettes.py             # 配色方案（11 套）
│   │   ├── icons.py                # 47 个内置 SVG 图标
│   │   └── echarts_workbench/      # 离线 ECharts 工作台
│   ├── schemas/                   # JSON Schema（12 个）
│   ├── prompts/                    # LLM 提示词模板（5 个）
│   └── profiles/                   # 项目类型配置 YAML
├── examples/                       # 正式 v2 配图任务示例
└── tests/                          # pytest 测试
```

---

## 常见问题

**Q: 流水线在 LLM 阶段暂停后如何继续？**

A: 将 `output/sX_analysis/*_rendered_prompt.md` 复制到 LLM（Claude/GPT），将输出的 JSON 保存到对应目录，然后运行 `bid-tool run --from sX+1`。

**Q: S3 正文写完后发现内容有问题，能修改吗？**

A: 能，但必须**先改正文再执行 S4 冻结**。S4 冻结后如需修改正文，需先删除 `output/s4_frozen/frozen_approval.json`，重新执行 S4。修改正文后 S5/S6/S7/S8 都需要重新运行。

**Q: 生成的 DOCX 中插图是旧图怎么办？**

A: 删除 `output/s5_illustrations/images/assets/` 下所有旧文件，重新运行 S6 配图生成。

**Q: 对照表显示"trace.json 不可用"怎么处理？**

A: 检查 `output/trace.json` 是否存在。S1 完成时会自动生成 trace.json。

**Q: 如何跳过某个阶段？**

A: 使用 `bid-tool run --from sX`，已完成的阶段会自动跳过。

---

## 运行测试

```bash
cd D:\AI_native_change\bid-tool
python -m pytest tests/ -v
```
