# 标书自动化生成管道 — 完整介绍

## 一、项目概述

本项目构建了一套 **9 阶段自动化标书生成管道**，用于将军事科研软件封装集成项目的招标文件自动转化为符合格式要求的投标技术方案（.docx）。

**核心能力：**
- 从招标文件自动提取 77 条技术要求，建立全文双向追溯矩阵
- 按评分标准自动设计 13 章大纲，100% 覆盖所有条款
- 生成去 AI 化的专业正文（约 3 万字），逐条对标响应
- 自动生成 41 张插图（架构图/流程图/界面原型/甘特图），按章插入
- 输出格式规范的 Word 文档（18MB，含 77 条需求对照表）
- 内建 14 项自动质量检查

**技术栈：** Python 3.10 + wxPython 4.2.1 + ctypes + Fortran DLL + SQLite + NumPy/SciPy + matplotlib

---

## 二、管道架构

```
s1 → s2 → s3 → [s4 人工冻结] → s5 → s6 → [s7 闭环校验] → s8 → s9
招标解析 → 大纲设计 → 正文撰写 → 内容冻结(人工) → 插图描述 → 图文合成 → 闭环校验 → 最终导出 → 偏离表填写
```

### S1 — 招标文件解析
- **输入：** 原始招标文件（.doc/.docx/.md）
- **输出：** 5 份 JSON（关键信息、一票否决项、评分标准、风险清单、技术需求）
- **产物：** `s1_key_info.json`、`s1_veto_items.json`、`s1_scoring.json`、`s1_risk.json`、`s1_tech_req.json`

### S2 — 大纲设计
- **输入：** S1 全部输出
- **输出：** 13 章大纲，每章标注对标的需求条款
- **产物：** `s2_outline.json`（含 coverage_map，100% 覆盖率）
- **门禁：** 覆盖率 100%，uncovered_reqs 为空

### S3 — 正文撰写
- **输入：** S1 + S2 全部输出
- **输出：** 13 章 Markdown 正文，逐节对标响应
- **产物：** `s3_body.json` + 13 个章节 `.md` 文件
- **门禁：** 文风得分 ≥ 80，禁用词 ≤ 5

### S4 — 内容冻结（人工）
- **流程：** 人工审核确认正文内容无误、文风达标
- **门禁：** 人工签字确认后可进入图示化阶段

### S5 — 插图描述
- **输入：** S3 正文 + illustration_manifest
- **输出：** 41 份结构化插图描述 JSON
- **产物流派：**
  - **SVG 插图（28 张）：** 架构图、流程图、能力图、关系图 → 由 LLM 根据 JSON 描述生成 SVG
  - **HTML 插图（13 张）：** 界面原型、甘特图、兼容性矩阵 → 由 `render_html_illustrations.py` 通过 Playwright 渲染为 PNG
- **产物：** `output/s5_illustrations/` 下 41 个 JSON 文件

### S6 — 图文合成
- **输入：** S4 冻结稿 + S5 插图
- **流程：**
  1. `s6_convert_to_job.py`：将 SVG 插图转为统一 Job 格式，生成 `illustration-manifest.json`
  2. `s6_synthesize.py`：将 41 张插图按章节插入正文 Markdown，生成 `s6_combined_bid_document.md`
- **产物：** 2152 行合并 Markdown，41 张图片全部嵌入

### S7 — 闭环校验
- **输入：** 全部前序产物
- **输出：** 评分标准-投标响应一一对应对照表
- **产物：** `s7_trace_matrix.json`、`verification_report.md`
- **门禁：** 覆盖率 ≥ 95%，★实质性条款 100% 响应

### S8 — 最终导出
- **输入：** S6 合成稿
- **流程：**
  1. `s8_export_docx.py`：Markdown → Word (.docx)，含正文排版、图片嵌入、表格转换、对照表生成
  2. `_verify_docx_full.py`：14 项自动质量检查
- **产物：** `投标文件_某软件封装集成项目_技术方案_[时间戳].docx`（约 18MB）

### S9 — 技术偏离表填写
- **输入：** S3 正文 + 报价文件模板 DOCX
- **输出：** 填写完成的技术偏离表（77 行 × 6 列），含 PAGEREF 交叉引用
- **流程：**
  1. 从 S3 章节 .md 文件中自动提取【对标条款】标记后的响应摘要（三级回退策略）
  2. 从报价文件 DOCX XML 中自动发现 `_Toc` 章节书签映射
  3. 通过 win32com（或 PDF 文本搜索）自动检测各章节起始页码
  4. 解析报价文件中的需求对照表（Table 11），获取 77 条技术要求数据
  5. 深克隆模板行 × 77，逐一填入 6 列（序号/技术要求/响应内容/偏离情况/页码/说明）
  6. 页码列插入 OOXML PAGEREF 字段，指向对应章节书签（Word 中 F9 更新后显示实际页码）
- **产物：** `s9_summaries.json`、`s9_bookmark_map.json`、`s9_page_numbers.json`、`s9_run_report.json`
- **门禁：** 77 行全部填写，响应摘要全员非空，PAGEREF 字段 77 个，偏离情况全部"无偏离"

---

## 三、关键技术决策

### 3.1 GUI 框架：wxPython（非 PyQt5）

**选择理由：**
- wxPython 4.2.1 是最后一个官方支持 Windows 7 SP1 64 位的 Python GUI 框架
- PyQt5 5.15.x 在 Win7 上存在依赖链问题（WebView2、Edge 运行库不可用）
- wxPython 基于原生 Windows 控件渲染，无需额外运行时
- 许可证为 wxWindows Library License，无 GPL 传染性风险

**统一范围：** CH-01 至 CH-05 共 14 处 PyQt5 引用，13 个 S5 插图 JSON，全部统一为 wxPython 技术栈。

### 3.2 Python 版本：3.10

Python 3.10 是最后一个官方支持 Windows 7 SP1 64 位的主版本（Python 3.11 起要求 Windows 10+），安全更新覆盖至 2026 年 10 月，覆盖本项目 18 个月周期。

### 3.3 离线部署

- 全程光盘单向导入开发资料
- USB 端口 BIOS 层面禁用（仅保留 RS485 适配器）
- 光驱只读（刻录功能物理断开）
- Inno Setup 构建离线安装包，所有依赖预打包

### 3.4 需求编号清洗

原始招标文件中不含 `RQ-TECH-XXX` 编号，这些是 AI 生成管道添加的注释。在 S8 导出阶段通过 `clean_body_text()` 函数（9 道正则清洗）去除正文中所有需求编号，仅保留于对照表中。

---

## 四、插图体系

### 4.1 插图分类

| 类型 | 数量 | 渲染方式 | 示例 |
|------|------|----------|------|
| 架构图 | 6 | SVG | 技术栈分层架构、五层系统架构 |
| 流程图 | 13 | SVG | 计算流程、部署流程、数据流 |
| 界面原型 | 11 | HTML→PNG | 主界面、数据导入、后处理工作台、MODBUS 监控 |
| 甘特图 | 1 | HTML→PNG | 项目实施里程碑排程 |
| 能力图 | 4 | SVG | 能力矩阵、功能映射 |
| 数据表 | 2 | SVG | 兼容性矩阵、权限矩阵 |
| 示意图 | 3 | SVG | 概念示意 |
| 关系图 | 1 | SVG | 需求-模块关联 |

### 4.2 HTML 插图设计系统

内建集中式 CSS 设计系统：

- **颜色令牌：** `--primary: #1a3a5c`、`--accent: #007bb5`、`--accent-warm: #e8833e`、语义色（success/warning/error）
- **5 级排版：** L0(42px)→L1(24px)→L2(18px)→L3(15px)→L4(13px)
- **30+ 组件类族：** `.panel`、`.data-table`、`.badge`、`.btn`、`.metric-card`、`.layout-quad`、`.app-titlebar` 等
- **参数化缩放：** `wrap_html(title, body_html, scale_factor=1.0)` — 甘特图 1.0x，界面原型 1.15x

### 4.3 插图分布

| 章节 | 插图数 | 章名 |
|------|--------|------|
| CH-01 | 2 | 项目理解与总体技术方案 |
| CH-02 | 2 | 资质、保密与合规保障 |
| CH-03 | 4 | 总体集成通用技术方案 |
| CH-04 | 4 | 人机交互界面设计 |
| CH-05 | 6 | 数据库模块技术方案 |
| CH-06 | 4 | 材料设计模块技术方案 |
| CH-07 | 4 | 热环境确定模块技术方案 |
| CH-08 | 3 | 热环境响应评估模块技术方案 |
| CH-09 | 3 | 运行环境兼容性与离线部署方案 |
| CH-10 | 2 | 集成对接与数据贯通方案 |
| CH-11 | 3 | 项目实施与交付方案 |
| CH-12 | 3 | 测试、验收与质量保障 |
| CH-13 | 1 | 售后服务与质保承诺 |

---

## 五、质量保障体系

### 5.1 门禁检查（每阶段自动执行）

| 阶段 | 门禁 |
|------|------|
| S1 | 5 份 JSON 通过 Schema 校验，必填字段非空 |
| S2 | 覆盖率 100%，uncovered_reqs 为空 |
| S3 | 文风得分 ≥ 80，禁用词 ≤ 5 |
| S4 | 人工签字确认 |
| S5 | illu_id 覆盖全部 manifest ID |
| S6 | 插图占位全部替换，图文编号一致 |
| S7 | 覆盖率 ≥ 95%，★条款 100% 响应 |
| S8 | 14 项自动检查 |
| S9 | 77 行全部填写；响应摘要全员非空；PAGEREF 字段 77 个；偏离情况全部无偏离 |

### 5.2 DOCX 验证项（`_verify_docx_full.py`）

1. 无 Markdown code fence 残留（```）
2. 无孤立的 `*` 模式（非图注/公式的星号）
3. 无原始表格 `|` 标记
4. 图片全部嵌入（41 张，17.8MB）
5. 图号按章连续、无缺号
6. 投标对照表存在
7. 无 `**` Markdown 残留
8. Word 表格数量正常（7 个）
9. 段落数合理
10. 无控制字符（乱码）
11. **正文中无 RQ-TECH 编号**（对照表中 92 条为合法）
12. **正文中无 `【对标条款】` 标记**

### 5.3 需求覆盖率

- 总需求：**77 条**
- ★实质性条款：**11 条**（100% 响应）
- 强制性条款：**63 条**
- 一般性条款：**3 条**
- 覆盖率：**100%**
- 遗漏：**0**

---

## 六、最终产出物

### 6.1 主文档

```
output/s8_final/投标文件_某软件封装集成项目_技术方案_[时间戳].docx
```

| 指标 | 值 |
|------|-----|
| 文件大小 | ~18 MB |
| 图片数量 | 41 张（28 SVG + 13 HTML） |
| 段落数 | 1,670（含表格单元格） |
| 章数 | 13 章 |
| 需求对照表 | 77 条 × 6 列 |
| 排版 | 仿宋 12pt，首行缩进 0.74cm，黑体标题 |

### 6.2 交付包

```
output/s8_final/deliverable_package/
├── 01_需求分析/      5 份 JSON（关键信息/技术要求/否决项/评分/风险）
├── 02_大纲设计/      s2_outline.json
├── 03_正文撰写/      s3_body.json + 3 章样本
├── 04_插图规划/      s6_unified_job.json
├── 05_插图生成/      48 个插图 JSON + 2 张样本 PNG
├── 06_文档合成/      illustration-manifest.json + 合成报告 + 合并 Markdown
├── 07_验证审查/      trace.json + trace_matrix + 验证报告
├── 08_最终输出/      2 个最终 DOCX
├── 完成报告.md
└── README.md
```

---

## 七、快速使用

### 完整跑管

```bash
cd "D:\AI_native_change\甘肃放射源项目\工程项目投标"

# 1. 渲染 HTML 插图（13 张）
python scripts/render_html_illustrations.py

# 2. 转换插图格式 + 生成清单
python scripts/s6_convert_to_job.py

# 3. 合并清单（HTML 条目 → 主清单）
python -c "
import json
with open('output/s6_synthesis/illustration-manifest.json') as f:
    m = json.load(f)
with open('output/s6_synthesis/html_manifest_entries.json') as f:
    h = json.load(f)
ids = {i['id'] for i in m['illustrations']}
for e in h['illustrations']:
    if e['id'] not in ids:
        m['illustrations'].append(e); ids.add(e['id'])
json.dump(m, open('output/s6_synthesis/illustration-manifest.json','w'), ensure_ascii=False, indent=2)
print(f'{len(m[\"illustrations\"])} illustrations')
"

# 4. 图文合成
python scripts/s6_synthesize.py

# 5. 导出 DOCX
python scripts/s8_export_docx.py

# 6. 验证
python scripts/_verify_docx_full.py
```

### 单图调试

```bash
# 渲染单张 HTML 插图（浏览器预览，不截图）
python scripts/render_html_illustrations.py --illu KU-016 --no-screenshot
```

---

## 八、关键文件索引

| 文件 | 用途 |
|------|------|
| `scripts/pipeline.py` | 8 阶段主控脚本（LLM 驱动模式） |
| `scripts/render_html_illustrations.py` | HTML 插图渲染器（~1100 行，含 CSS 设计系统） |
| `scripts/s6_convert_to_job.py` | S5→S6 插图格式转换 + 清单生成 |
| `scripts/s6_synthesize.py` | Markdown 图文合成 |
| `scripts/s8_export_docx.py` | Markdown→DOCX 导出（含 `clean_body_text()`） |
| `scripts/_verify_docx_full.py` | DOCX 14 项自动验证 |
| `scripts/s9_fill_deviation.py` | S9 偏离表填写主控脚本（~400 行，含摘要提取/书签发现/页码检测/PAGEREF 交叉引用） |
| `output/trace.json` | 77 条需求全生命周期追溯 |
| `output/s2_outline/s2_outline.json` | 13 章大纲 + 覆盖率映射 |
| `output/s5_illustrations/*.json` | 41 张插图结构化描述 |
| `output/s6_synthesis/s6_combined_bid_document.md` | 合并后完整标书 Markdown |
