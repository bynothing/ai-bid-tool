# 绘图平台软件实现架构

> 本文面向工程实现和后续扩展，说明 bid-tool 绘图平台如何分层、解耦、扩展以及对外统一调用。

## 1. 架构目标

绘图平台的核心目标是把 AI 生成的语义化绘图任务转化为可进入投标文件的高质量图件。平台不绑定某一种绘图技术，而是根据内容自动选择 HTML/CSS、SVG、ECharts 等最优表达方式。

工程目标：

- 对外只有统一接口，不暴露内部 renderer 细节。
- 图型语义、渲染决策、具体渲染器、产物清单彼此解耦。
- 新增图型时尽量只改注册表、schema/文档和对应 renderer。
- 新增渲染器时只实现 adapter，不影响 AI 任务协议。
- V2 平台协议作为正式对外接口，旧版 V1 任务不再公开支持。

## 2. 分层架构

```text
┌────────────────────────────────────────────┐
│ 对外入口层                                  │
│ CLI / Python API / Pipeline / Future HTTP   │
└─────────────────┬──────────────────────────┘
                  │
┌─────────────────▼──────────────────────────┐
│ 应用编排层                                  │
│ platform.py：校验 -> 决策 -> 分组 -> 渲染 -> manifest │
└─────────────────┬──────────────────────────┘
                  │
┌─────────────────▼──────────────────────────┐
│ 领域核心层                                  │
│ job / registry / decision / router / validator / manifest │
└─────────────────┬──────────────────────────┘
                  │
┌─────────────────▼──────────────────────────┐
│ 渲染适配层                                  │
│ RendererAdapter：html_css / svg_native / echarts_html / mermaid / graphviz │
└─────────────────┬──────────────────────────┘
                  │
┌─────────────────▼──────────────────────────┐
│ 基础设施层                                  │
│ svg_renderer.py / echarts_workbench / Playwright / file system │
└────────────────────────────────────────────┘
```

## 3. 模块职责

### 3.1 对外入口层

| 模块 | 职责 |
| --- | --- |
| `bid_tool.cli` | 命令行入口，解析参数后调用 toolkit/platform |
| `illustration.toolkit` | 正式 V2 CLI 工具入口，读取任务后委派给 platform |
| `illustration.api` | 新增稳定 Python API 门面，供流水线、HTTP/MCP 服务、测试调用 |
| `illustration.standalone` | 生成独立绘图工具包，供解压后直接运行 |

推荐外部调用 `illustration.api`：

```python
from bid_tool.illustration import api

errors, warnings = api.validate("examples/示例_配图平台v2任务.json")
plan = api.plan("examples/示例_配图平台v2任务.json")
records = api.render(
    "examples/示例_配图平台v2任务.json",
    "output/illustrations",
    png=True,
    export_echarts=False,
)
```

### 3.2 应用编排层

文件：[platform.py](../src/bid_tool/illustration/platform.py)

职责：

1. 接收 `IllustrationJob`。
2. 调用 `validate_platform_job` 做语义校验。
3. 调用 `route_item` 获取每张图的最终渲染器。
4. 按渲染器分组。
5. 调用对应 `RendererAdapter`。
6. 汇总输出记录。
7. 写入 `illustration-manifest.json` 和 `生成清单.md`。

这一层不应该包含具体画图逻辑，也不应该直接解析 HTML/SVG/ECharts 细节。

### 3.3 领域核心层

| 文件 | 职责 |
| --- | --- |
| `core/job.py` | V2 job 规范化，形成 `IllustrationJob` 和 `IllustrationItem` |
| `core/registry.py` | 图型注册表，声明图型 ID、默认渲染器、支持渲染器、SVG 内部映射 |
| `core/decision.py` | 内容分析决策层，基于 intent/data/visual 选择最佳渲染器 |
| `core/router.py` | 将图型和决策结果转成最终 `Route` |
| `core/validator.py` | 平台语义校验和质量 warning |
| `core/manifest.py` | 输出 manifest 和 Markdown 清单 |

领域核心层不依赖具体 renderer。

### 3.4 渲染适配层

| 文件 | 职责 |
| --- | --- |
| `renderers/base.py` | 定义 `RenderContext`、`RenderResult`、`RendererAdapter` 协议 |
| `renderers/html.py` | HTML/CSS 标书大图渲染器，负责图3风格、甘特、风险、对比等 |
| `renderers/legacy.py` | 复用现有 SVG/ECharts toolkit helper 的内部适配器 |

新增渲染器时，应遵守 `RendererAdapter` 协议：

```python
class NewRenderer:
    name = "new_renderer"

    def render(self, job, items, context):
        return [RenderResult(...)]
```

### 3.5 基础设施层

| 模块 | 说明 |
| --- | --- |
| `svg_renderer.py` | SVG 框图渲染能力 |
| `echarts_workbench/` | 离线 ECharts 审图和导出工作台 |
| `themes.py` / `icons.py` | SVG 主题和图标资源 |
| Playwright | HTML/ECharts 导出 PNG |
| 文件系统 | 生成 assets、review、manifest |

基础设施层可以被 adapter 使用，但不应反向依赖平台核心。

## 4. 数据流

### 4.1 v2 标准流程

```text
Illustration Job v2
  -> api/toolkit
  -> IllustrationJob.from_raw
  -> validate_platform_job
  -> route_item
       -> decision.analyze_content
       -> decision.decide_renderer
  -> group by renderer
  -> RendererAdapter.render
  -> AssetRecord
  -> write_platform_manifest
```

### 4.2 SVG/ECharts 内部适配流程

```text
Illustration Job v2
  -> route_item selects svg_native / echarts_html
  -> internal adapter package
  -> split_specs
  -> svg_renderer / echarts_workbench
  -> platform manifest
```

V2 中如果自动选择 `svg_native` 或 `echarts_html`，会通过内部适配器复用 SVG/ECharts helper。这个转换是实现细节，不是外部 V1 协议。

## 5. 统一对外接口

### 5.1 CLI

```powershell
bid-tool illustrate --job examples/示例_配图平台v2任务.json --png
bid-tool illustrate --job examples/示例_配图平台v2任务.json --validate-only
bid-tool illustrate --job examples/示例_配图平台v2任务.json --no-echarts-export
bid-illustrate --job examples/示例_配图平台v2任务.json --png
bid-tool illustration-bundle --output dist/bid-illustration-standalone --zip
```

### 5.2 Python API

```python
from bid_tool.illustration import api

job = api.load("job.json")
errors, warnings = api.validate(job)
decisions = api.plan(job)
records = api.render(job, "output/illustrations", png=True)
types = api.list_diagram_types()
```

### 5.3 未来 HTTP/MCP API

未来服务层应只包装 `illustration.api`：

| API | 内部调用 |
| --- | --- |
| `POST /illustrations/validate` | `api.validate` |
| `POST /illustrations/plan` | `api.plan` |
| `POST /illustrations/render` | `api.render` |
| `GET /illustrations/types` | `api.list_diagram_types` |

## 6. 自动决策层

`decision.py` 将绘图选择拆成两步：

1. `analyze_content(item)`：分析图件语义和结构。
2. `decide_renderer(item)`：给候选渲染器打分并选择最高分。

分析信号：

- 图型语义：`type`
- 表达目标：`intent`
- 图题/用途：`caption`、`purpose`
- 结构复杂度：节点、连线、分支、泳道
- 数据属性：series、categories、chart 类型
- 视觉约束：`editableVector`、`preciseConnectors`
- 关键词：接口、安全、拓扑、ACK、HTTPS、MQTT、审计等

决策原则：

| 内容特征 | 选择 |
| --- | --- |
| 数据统计、趋势、指标 | `echarts_html` |
| 正式标书展示、图3风格、矩阵、路线、对比 | `html_css` |
| 密集结构、复杂关系、精确连线、可编辑矢量 | `svg_native` |
| 拓扑/复杂关系自动布局 | 未来 `graphviz`，当前回退 `svg_native` |

决策原因会进入 manifest，便于审计和调参。

## 7. 扩展方式

### 7.1 新增图型

1. 在 `core/registry.py` 注册图型。
2. 在 `docs/AI_ILLUSTRATION_API_V2.md` 添加字段说明和示例。
3. 如需要新数据约束，补充 schema 或 validator。
4. 在已有 renderer 中实现模板，或新增 renderer adapter。
5. 添加示例 JSON。
6. 添加测试和烟测。

### 7.2 新增渲染器

1. 在 `renderers/` 下实现 adapter。
2. 在 `platform.py` 的 renderer 工厂中注册。
3. 在 `registry.py` 中将相关图型加入支持渲染器。
4. 如适合自动选择，在 `decision.py` 中增加评分规则。
5. 更新文档和示例。

### 7.3 新增主题/视觉规范

建议后续新增 `design/` 层：

```text
design/
  tokens.py       # 字号、间距、圆角、阴影
  themes.py       # formal_blue / formal_green / formal_gold
  components.py   # 标题栏、卡片、图例、注释等组件配置
```

当前 HTML/CSS renderer 内部已有样式，但长期应迁移到 design 层，减少模板和视觉规范耦合。

## 8. 当前技术债与建议

| 问题 | 建议 |
| --- | --- |
| `toolkit.py` 仍保留部分 SVG/ECharts helper | 对外只走 V2 CLI/API，helper 后续逐步下沉到 adapter/infrastructure |
| `html.py` 包含较多 CSS 和模板字符串 | 后续拆成 `design/components` 和模板文件 |
| `legacy.py` 复用既有 SVG/ECharts helper，仍有耦合 | 等原生 V2 SVG/ECharts adapter 成熟后逐步替换 |
| 旧 V1 schema 已移出公开接口 | 外部统一使用 `illustration_job_v2.schema.json` |
| `_fix_fonts.py` 存在既有语法错误 | 与平台无关，但建议清理或移出包编译路径 |

## 9. 推荐边界

平台核心层应该保持纯逻辑：

- 不读写具体图片文件。
- 不调用 Playwright。
- 不拼 HTML/SVG 字符串。
- 不依赖 ECharts。

渲染器适配层可以依赖外部工具：

- HTML/CSS renderer 可使用 Playwright。
- ECharts renderer 可使用离线 workbench。
- SVG renderer 可使用现有 `svg_renderer.py`。
- Graphviz/Mermaid adapter 可调用外部 CLI 或库。

这个边界能保证：**图型语义、内容分析、渲染技术和文件产物各自演进，不互相绑死。**
