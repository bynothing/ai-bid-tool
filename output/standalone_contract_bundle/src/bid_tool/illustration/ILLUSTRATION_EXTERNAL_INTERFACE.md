# 独立绘图渲染工具外部接口

本文定义独立绘图工具的稳定边界。外部系统只需要按 Illustration Job v2 生成 JSON，调用 CLI 或 Python API，读取 manifest；不需要了解 bid-tool 的 S1-S9 标书流水线。

## 1. 边界

独立工具负责：

- 校验 Illustration Job v2。
- 根据 `type`、`renderer`、`intent`、`data` 和 `visual` 规划渲染器。
- 生成 SVG、PNG、HTML 预览、ECharts/Mermaid/Graphviz 相关产物。
- 输出机器可读 `illustration-manifest.json`。

独立工具不负责：

- 解析招标文件。
- 生成标书正文。
- 决定图片插入 Word 的具体段落。
- 处理 bid-tool 的 S1-S9 阶段目录。

bid-tool 作为调用方时，只应把标书阶段输出转换为 Illustration Job v2，再调用本工具。

## 2. 推荐调用

安装后优先使用独立命令：

```powershell
bid-illustrate --job job.json --validate-only
bid-illustrate --job job.json --output output/illustrations --png --png-scale 2
```

在完整 bid-tool 中也保留兼容入口：

```powershell
bid-tool illustrate --job job.json --output output/illustrations --png
```

交付给外部系统时，可构建独立包：

```powershell
bid-illustration-bundle --output dist/bid-illustration-standalone --zip
```

独立包解压后调用：

```powershell
python run_illustration.py --job job.json --output output/illustrations --png
```

## 3. Python API

```python
from bid_tool.illustration import api

job = api.load("job.json")
errors, warnings = api.validate(job)
plan = api.plan(job)
records = api.render(job, "output/illustrations", png=True, png_scale=2)
types = api.list_diagram_types()
```

API 语义：

| 函数 | 说明 |
| --- | --- |
| `load(path)` | 读取并规范化 v2 任务 |
| `validate(path_or_job)` | 返回 `(errors, warnings)`，不生成文件 |
| `plan(path_or_job)` | 返回每张图的最终渲染器和决策原因 |
| `render(path_or_job, output, png=False, png_scale=2, export_echarts=True)` | 执行渲染并写 manifest |
| `list_diagram_types()` | 返回工具支持的图型注册表 |

## 4. 输入协议

输入文件必须是 JSON 对象，版本固定为：

```json
{
  "version": "2.0",
  "document": { "title": "技术方案" },
  "style": {
    "theme": "formal_blue",
    "tone": "technical",
    "preferredFormat": "both",
    "palette": "engineering_blue"
  },
  "illustrations": []
}
```

单张图：

```json
{
  "id": "overall_architecture",
  "type": "architecture.layered",
  "renderer": "auto",
  "intent": "展示系统分层、关键组件与支撑关系",
  "insertion": {
    "section": "3.1",
    "caption": "图 3-1 系统总体架构图",
    "purpose": "说明总体技术组成"
  },
  "visual": {
    "density": "standard",
    "tone": "technical"
  },
  "data": {
    "title": "系统总体架构",
    "layers": []
  }
}
```

正式约束见：

```text
src/bid_tool/schemas/illustration_job_v2.schema.json
```

## 5. 默认工程化风格

默认 `palette` 为 `engineering_blue`：

- 主色：工程蓝灰。
- 底色：白底、浅蓝灰分区、细边框。
- 强调色：低饱和蓝、青、灰紫。
- 状态色：绿色、琥珀、红色只用于通过、风险、异常等语义。
- 不按图型自动切换整套主题，避免同一份文档显得混乱。

如果外部确实需要单图主题，可显式传入：

```json
{
  "visual": {
    "palette": "risk_orange"
  }
}
```

推荐只在风险、故障、告警类单图中显式使用特殊主题。

## 6. 输出协议

渲染完成后，外部系统只应读取：

```text
<output>/illustration-manifest.json
```

manifest 结构：

```json
{
  "version": "2.0",
  "document": {},
  "sourceJob": "job.json",
  "illustrations": [
    {
      "id": "overall_architecture",
      "type": "architecture.layered",
      "renderer": "html_css",
      "section": "3.1",
      "caption": "图 3-1 系统总体架构图",
      "purpose": "说明总体技术组成",
      "outputs": {
        "html": "assets/html/overall_architecture.html",
        "png": "assets/html/overall_architecture.png"
      },
      "warnings": [],
      "decision": []
    }
  ]
}
```

外部系统不要推断文件名；以 `outputs` 为准。

## 7. 返回码

CLI 约定：

| 返回码 | 含义 |
| --- | --- |
| `0` | 成功 |
| `2` | 输入任务校验失败 |
| 其他非零 | 运行环境或渲染失败 |

推荐外部系统先运行 `--validate-only`，再正式渲染。

## 8. bid-tool 调用方边界

bid-tool 的 S5/S6 只做适配：

1. 从章节、正文、插图占位和项目上下文生成 Illustration Job v2。
2. 调用 `bid_tool.illustration.api.validate/plan/render`。
3. 读取 `illustration-manifest.json`。
4. 将 manifest 中的 `outputs.png` 或 `outputs.svg` 交给后续 DOCX/PDF 装配。

bid-tool 不应该：

- 直接调用 `svg_renderer.py`。
- 直接写 `inputs/svg-diagrams.json`。
- 依赖 `assets/svg/01_xxx.svg` 这类内部文件名。
- 在 S5/S6 中拼接 renderer 私有字段。

这个边界保证绘图工具可以独立演进，也方便后续替换为 HTTP/MCP 服务。
