# 配图工具 CLI 外部使用说明

本文面向外部调用方，说明如何单独使用配图工具生成工程化图件，包括 SVG、PNG、HTML 预览、ECharts 审图页和生成清单。外部系统只需要准备一份 Illustration Job v2 JSON，然后调用独立 CLI。

稳定接口边界见 [ILLUSTRATION_EXTERNAL_INTERFACE.md](ILLUSTRATION_EXTERNAL_INTERFACE.md)。完整 bid-tool 流水线只是调用方，不是绘图工具的前置条件。

## 1. 适用场景

配图工具适合生成投标文件中的：

- 架构图、流程图、泳道图、时序图、能力地图、关系图
- 接口关系与数据交互图
- 运维巡检分类图
- 故障分级响应与问题闭环流程图
- 数据安全保密保障体系图
- 风险矩阵、甘特图、方案对比图
- 柱线图、雷达图、桑基图等数据图

外部调用方必须使用 V2 协议：`version: "2.0"`，并让 AI 输出 `renderer: "auto"`。平台会根据图型和内容自动选择 `html_css`、`svg_native`、`echarts_html`、`mermaid` 或 `graphviz`。

## 2. 安装准备

在 bid-tool 项目目录中安装：

```powershell
cd D:\AI_native_change\bid-tool
pip install -e .
```

验证命令是否可用：

```powershell
bid-tool --help
```

如果需要生成 PNG，建议安装完整依赖：

```powershell
pip install -e ".[full]"
playwright install chromium
```

说明：

- 只生成 SVG 时，不一定需要 Playwright。
- 生成 PNG、导出 ECharts 图片时，建议安装 `full` 依赖。
- 如果外部系统不安装命令行脚本，也可以使用 `python -m bid_tool.illustration.toolkit` 调用。

## 3. 最小调用

校验任务文件，不生成图片：

```powershell
bid-tool illustrate --job examples\示例_AI接口调用_SVG图3-6风格_v2.json --validate-only
```

生成 SVG 和 PNG：

```powershell
bid-tool illustrate ^
  --job examples\示例_AI接口调用_SVG图3-6风格_v2.json ^
  --output output\illustration_cli_demo ^
  --png
```

生成完成后，图片在：

```text
output\illustration_cli_demo\assets\svg\*.svg
output\illustration_cli_demo\assets\svg\png\*.png
```

清单文件在：

```text
output\illustration_cli_demo\生成清单.md
output\illustration_cli_demo\illustration-manifest.json
```

## 4. 推荐 CLI

### 4.1 推荐入口：bid-illustrate

```powershell
bid-illustrate --job <任务JSON> [--output <输出目录>] [--png] [--validate-only] [--no-echarts-export]
```

### 4.2 bid-tool 兼容入口

```powershell
bid-tool illustrate --job <任务JSON> [--output <输出目录>] [--png] [--validate-only] [--no-echarts-export]
```

参数说明：

| 参数 | 是否必填 | 说明 |
| --- | --- | --- |
| `--job` | 是 | 配图任务 JSON 文件路径 |
| `--output` | 否 | 输出目录；不传时默认为当前目录下 `output/illustrations` |
| `--png` | 否 | 同步生成 PNG 预览图 |
| `--validate-only` | 否 | 只校验任务 JSON，不生成图片 |
| `--no-echarts-export` | 否 | ECharts 数据图只生成本地审图页，不自动导出 SVG/PNG |

常用示例：

```powershell
# 1. 只校验
bid-tool illustrate --job examples\示例_配图平台v2任务.json --validate-only

# 2. 生成图片
bid-tool illustrate --job examples\示例_配图平台v2任务.json --output output\v2_demo --png

# 3. 生成 SVG 图3-6 风格模板
bid-tool illustrate --job examples\示例_AI接口调用_SVG图3-6风格_v2.json --output output\svg_style_demo --png

# 4. 数据图只生成审图页面，不自动导出图片
bid-tool illustrate --job examples\示例_绘图平台功能测试.json --output output\review_only --png --no-echarts-export
```

### 4.3 高级入口：python -m bid_tool.illustration.toolkit

底层工具支持更多参数，例如 `--png-scale`：

```powershell
python -m bid_tool.illustration.toolkit ^
  --job examples\示例_AI接口调用_SVG图3-6风格_v2.json ^
  --output output\svg_style_demo ^
  --png ^
  --png-scale 2
```

高级参数：

| 参数 | 说明 |
| --- | --- |
| `--png-scale 1|2|3` | PNG 导出倍数，正式文档推荐 2 或 3 |
| `--open-preview` | 生成完成后打开 ECharts 本地审图页 |

## 4.4 Mermaid 和 Graphviz 调用

平台已支持 `mermaid` 和 `graphviz` 渲染器。外部调用时仍然使用同一个入口：

```powershell
bid-tool illustrate --job examples\示例_Mermaid_Graphviz渲染器_v2.json --output output\mermaid_graphviz_demo --png
```

Mermaid 适合：

- 流程图：`process.flowchart`
- 时序图：`interaction.sequence`
- 简单甘特图：`timeline.gantt`

Graphviz 适合：

- 网络拓扑：`network.topology`
- 复杂关系：`relationship.domain`
- 部署关系：`architecture.deployment`

如果本机安装了 Graphviz 的 `dot` 命令，Graphviz 会输出真正的 Graphviz 布局 SVG/PNG；如果没有安装，也会输出 `.dot` 源文件，并使用内置简易 SVG 布局降级生成可预览图片。

Mermaid 输出依赖浏览器加载 Mermaid 脚本。若网络或浏览器环境不可用，工具仍会保留 `.mmd` 源文件和 HTML 预览页。

## 5. 输入 JSON 格式

外部调用建议使用 v2 格式：

```json
{
  "version": "2.0",
  "document": {
    "title": "某项目投标技术方案",
    "projectName": "某项目",
    "bidSection": "技术方案"
  },
  "style": {
    "theme": "formal_blue",
    "tone": "formal_bid",
    "preferredFormat": "both"
  },
  "illustrations": [
    {
      "id": "interface_rules_map",
      "type": "integration.interface_map",
      "renderer": "auto",
      "intent": "说明双平台之间的数据推送、回执、安全校验和异常补传机制",
      "insertion": {
        "section": "3.2 数据接口与交互规则",
        "caption": "图 3-2 数据交互规则适配架构与接口关系图",
        "purpose": "说明接口关系和数据交互规则"
      },
      "visual": {
        "tone": "formal_bid",
        "rendererPreference": "svg_native",
        "editableVector": true
      },
      "data": {
        "title": "2025数据交互规则适配架构与接口关系",
        "subtitle": "业务系统、监管平台与数据链路的接口关系",
        "leftPlatform": {
          "title": "承建单位业务平台",
          "subtitle": "采集、治理、推送",
          "icon": "server",
          "layers": [
            { "title": "业务应用层", "items": ["项目管理", "巡检填报", "问题闭环"] },
            { "title": "数据服务层", "items": ["数据清洗", "规则校验", "接口封装"] }
          ]
        },
        "rightPlatform": {
          "title": "监管/业主集成平台",
          "subtitle": "接收、核验、反馈",
          "icon": "government",
          "layers": [
            { "title": "接口接入区", "items": ["HTTPS API", "消息回执"] },
            { "title": "数据核验区", "items": ["字段完整性", "重复校验"] }
          ]
        },
        "flows": [
          { "title": "基础数据同步", "protocol": "HTTPS + JSON", "style": "default" },
          { "title": "巡检结果上报", "protocol": "API实时推送", "style": "accent" }
        ],
        "requirements": [
          { "title": "统一身份认证", "style": "default" },
          { "title": "字段规则校验", "style": "accent" }
        ],
        "note": "接口关系图需要同时体现方向、协议、回执、安全约束与异常补传机制。"
      }
    }
  ]
}
```

字段说明：

| 字段 | 说明 |
| --- | --- |
| `version` | 固定写 `"2.0"` |
| `document` | 当前标书/项目基本信息 |
| `style.theme` | 主题色，常用 `formal_blue` |
| `style.preferredFormat` | 推荐写 `both`，表示同时保留 SVG/PNG |
| `illustrations` | 图件数组，一次可生成多张图 |
| `id` | 图件唯一 ID，只能使用字母、数字、下划线、短横线 |
| `type` | 图型语义，例如 `integration.interface_map` |
| `renderer` | 推荐写 `auto` |
| `intent` | 说明这张图要表达什么 |
| `insertion` | 标书中的章节、图题和用途 |
| `visual` | 视觉偏好、是否需要 SVG、是否可编辑 |
| `data` | 图的结构化内容 |

## 6. 图型与 renderer 选择

推荐外部调用方优先写 `renderer: "auto"`，由工具自动选择。

常用图型：

| 场景 | type | 推荐 renderer |
| --- | --- | --- |
| 双平台接口关系、数据交互规则 | `integration.interface_map` | `auto` 或 `svg_native` |
| 巡检分类、服务保障分类 | `operation.inspection_taxonomy` | `auto` 或 `svg_native` |
| 故障分级响应、问题闭环流程 | `operation.incident_response` | `auto` 或 `svg_native` |
| 数据安全保密保障体系 | `architecture.security_ring` | `auto` 或 `svg_native` |
| 总体分层架构 | `architecture.layered` | `auto` |
| 流程图 | `process.flowchart` | `auto` / `mermaid` |
| 泳道流程 | `process.swimlane` | `auto` |
| 时序交互 | `interaction.sequence` | `auto` / `mermaid` |
| 网络拓扑 | `network.topology` | `auto` / `graphviz` |
| 复杂关系图 | `relationship.domain` | `auto` / `graphviz` |
| 风险矩阵 | `matrix.risk` | `auto` |
| 甘特计划 | `timeline.gantt` | `auto` |
| 柱线组合、雷达、桑基 | `chart.bar_line` / `chart.radar` / `chart.sankey` | `auto` |

当外部明确需要 SVG 可编辑矢量图时，增加：

```json
"visual": {
  "rendererPreference": "svg_native",
  "editableVector": true
}
```

## 7. 输出目录结构

执行：

```powershell
bid-tool illustrate --job examples\示例_AI接口调用_SVG图3-6风格_v2.json --output output\demo --png
```

典型输出：

```text
output/demo/
├── illustration-manifest.json       # 机器可读清单，供外部系统集成
├── 生成清单.md                       # 人工审查清单
├── inputs/
│   ├── svg-diagrams.json             # 路由后传给 SVG 渲染器的输入
│   └── echarts-diagrams.json          # 路由后传给 ECharts 的输入
└── assets/
    └── svg/
        ├── *.svg                     # SVG 矢量图
        ├── result.json               # SVG 渲染器结果
        ├── 生成清单.md
        └── png/
            └── *.png                 # PNG 预览图
```

如果任务中包含 ECharts 数据图，还可能输出：

```text
output/demo/review/echarts/index.html # 本地审图页面
output/demo/assets/echarts/*.svg
output/demo/assets/echarts/*.png
```

如果任务中包含 Mermaid 图，还可能输出：

```text
output/demo/assets/mermaid/*.mmd     # Mermaid 源码
output/demo/assets/mermaid/*.html    # Mermaid 预览页
output/demo/assets/mermaid/*.svg
output/demo/assets/mermaid/*.png
```

如果任务中包含 Graphviz 图，还可能输出：

```text
output/demo/assets/graphviz/*.dot    # DOT 源码
output/demo/assets/graphviz/*.svg
output/demo/assets/graphviz/*.png
```

外部系统建议读取 `illustration-manifest.json`，不要自己猜文件名。该文件会记录每张图的：

- `id`
- `type`
- `renderer`
- `section`
- `caption`
- `outputs.svg`
- `outputs.png`
- `decision`
- `warnings`

## 8. 外部系统集成建议

推荐流程：

1. 外部系统或 AI 生成一份 v2 JSON。
2. 先执行 `--validate-only`。
3. 校验通过后执行正式生成。
4. 读取 `illustration-manifest.json` 获取图片路径。
5. 将 PNG 插入 Word/PDF，将 SVG 作为可编辑矢量源文件归档。

示例：

```powershell
$job = "D:\work\illustration_job.json"
$out = "D:\work\illustration_output"

bid-tool illustrate --job $job --validate-only
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

bid-tool illustrate --job $job --output $out --png
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Get-Content "$out\illustration-manifest.json"
```

## 9. 独立工具包

如果只交付绘图能力，不交付完整 `bid-tool` 标书流水线，可以生成独立工具包：

```powershell
bid-tool illustration-bundle --output dist\bid-illustration-standalone --zip
```

交付后，使用方解压目录，直接运行：

```powershell
cd dist\bid-illustration-standalone
python run_illustration.py --job examples\示例_统一文档配图任务.json --validate-only
python run_illustration.py --job examples\示例_统一文档配图任务.json --output output\demo --png
```

独立包内包含：

- `src/bid_tool/illustration/`：绘图平台运行时。
- `src/bid_tool/schemas/`：V2 绘图 schema 和 SVG/ECharts 子 schema。
- `examples/`：V2 示例任务。
- `docs/`：CLI、API、架构说明。
- `run_illustration.py`：免安装启动脚本。

独立包不包含 S1-S9 标书流水线；如果需要在完整标书流程里使用，仍然调用：

```powershell
bid-tool illustrate --job output\s5_illustrations\s5_illustration_job.json --output output\s5_illustrations\images --png
```

## 10. 常见问题

### 10.1 图片生成在哪里？

看 `--output` 参数指定的目录。SVG 通常在：

```text
<output>\assets\svg\*.svg
```

PNG 通常在：

```text
<output>\assets\svg\png\*.png
```

最稳妥的方式是读取：

```text
<output>\illustration-manifest.json
```

### 10.2 只生成了 SVG，没有 PNG？

确认命令里加了 `--png`：

```powershell
bid-tool illustrate --job xxx.json --output output\demo --png
```

如果仍失败，安装 PNG 依赖：

```powershell
pip install -e ".[full]"
playwright install chromium
```

### 10.3 ECharts 数据图没有导出图片？

不要加 `--no-echarts-export`。如果环境没有 Playwright，可以先用本地审图页：

```powershell
bid-tool illustrate --job xxx.json --output output\demo --png --no-echarts-export
```

然后打开：

```text
output\demo\review\echarts\index.html
```

### 10.4 想强制生成 SVG 风格的图3-6模板？

在图件中设置：

```json
"renderer": "auto",
"visual": {
  "rendererPreference": "svg_native",
  "editableVector": true
}
```

并选择对应图型：

- `integration.interface_map`
- `operation.inspection_taxonomy`
- `operation.incident_response`
- `architecture.security_ring`

### 10.5 校验失败怎么办？

先运行：

```powershell
bid-tool illustrate --job xxx.json --validate-only
```

常见原因：

- `id` 含中文或空格
- 漏写 `version: "2.0"`
- 漏写 `document.title`
- 漏写 `insertion.caption`
- `rendererPreference` 写了该图型不支持的 renderer
- 数据图缺少 `source` 或模拟数据说明

## 11. 推荐示例文件

| 示例 | 用途 |
| --- | --- |
| `examples/示例_AI接口调用_SVG图3-6风格_v2.json` | 外部 AI 调用 SVG 图3-6 风格模板 |
| `examples/示例_Mermaid_Graphviz渲染器_v2.json` | Mermaid 与 Graphviz 渲染器示例 |
| `examples/示例_配图平台v2任务.json` | v2 综合示例 |
| `examples/示例_绘图平台功能测试.json` | 多图型功能测试 |
| `examples/示例_接口关系与数据交互图.json` | 接口关系图专项示例 |

## 12. 相关文档

- AI 协议细节：`docs/AI_ILLUSTRATION_API_V2.md`
- 标书配图策略：`docs/BID_WRITING_ILLUSTRATION_STRATEGY.md`
- 平台架构说明：`docs/ILLUSTRATION_SOFTWARE_ARCHITECTURE.md`
- v2 JSON Schema：`src/bid_tool/schemas/illustration_job_v2.schema.json`
## 默认配色

CLI 不需要额外参数即可启用默认工程化配色。`html_css`、`svg_native`、`mermaid`、`graphviz` 渲染器默认使用 `engineering_blue`：深蓝灰标题栏、白底浅蓝灰分区、细边框、低饱和强调色。

工具不会再按图型自动切换整套主题，避免一份文档中出现过多彩色风格。绿色、琥珀、红色主要用于通过、风险、异常等状态语义。

外部系统只需要在 JSON 中保留 `renderer: "auto"`。如果希望某张图固定特殊主题，可写：

```json
{
  "visual": {
    "palette": "risk_orange"
  }
}
```

如果希望某个节点或流程固定语义颜色，可在对应对象上增加 `style`：

```json
{ "title": "去重校验", "style": "success" }
{ "title": "异常补传", "style": "warning" }
{ "title": "闭环核查", "style": "purple" }
```

不写 `style` 时，工具会在同一套工程蓝灰体系内做低饱和轮换，保持层级区分但不破坏整体一致性。
