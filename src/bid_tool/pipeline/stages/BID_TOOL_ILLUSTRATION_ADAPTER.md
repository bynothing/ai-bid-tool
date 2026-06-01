# bid-tool 调用独立绘图工具的适配边界

本文只描述 bid-tool 作为调用方时如何接入独立绘图工具。绘图工具自身接口见：

```text
src/bid_tool/illustration/ILLUSTRATION_EXTERNAL_INTERFACE.md
```

## 1. 推荐链路

```text
S2/S3 章节与插图占位
  -> S5 生成 Illustration Job v2
  -> illustration.api.validate(job)
  -> illustration.api.plan(job)
  -> illustration.api.render(job, output/s5_illustrations/images, png=True)
  -> 读取 illustration-manifest.json
  -> S6/S8 按 manifest.outputs 插入文档
```

bid-tool 不应该关心渲染器内部生成了 `assets/svg`、`assets/html` 还是 `review/echarts`。后续阶段只读取 manifest。

## 2. S5 职责

S5 只生成独立绘图工具输入：

```text
output/s5_illustrations/s5_illustration_job.json
```

该文件必须是 Illustration Job v2：

```json
{
  "version": "2.0",
  "document": {},
  "style": {
    "theme": "formal_blue",
    "tone": "technical",
    "preferredFormat": "both",
    "palette": "engineering_blue"
  },
  "illustrations": []
}
```

S5 不生成：

- SVG 坐标。
- ECharts option。
- Mermaid 源码。
- `inputs/svg-diagrams.json`。
- renderer 私有 spec。

## 3. 绘图调用职责

调用方式二选一。

Python API：

```python
from bid_tool.illustration import api

job = api.load("output/s5_illustrations/s5_illustration_job.json")
errors, warnings = api.validate(job)
if errors:
    raise ValueError(errors)
records = api.render(job, "output/s5_illustrations/images", png=True)
```

CLI：

```powershell
bid-illustrate --job output/s5_illustrations/s5_illustration_job.json --output output/s5_illustrations/images --png
```

`bid-tool illustrate` 只是兼容包装，不是绘图工具的主接口。

## 4. S6/S8 职责

S6/S8 只读取：

```text
output/s5_illustrations/images/illustration-manifest.json
```

插图路径选择顺序：

1. 优先 `outputs.png`，用于 DOCX/PDF。
2. 没有 PNG 时使用 `outputs.svg`，用于可编辑矢量归档。
3. `outputs.html`、`outputs.reviewHtml` 只作为审图辅助。

禁止在 S6/S8 中拼接内部路径，例如：

```text
assets/svg/01_xxx.svg
assets/svg/png/01_xxx.png
```

## 5. 当前代码中的历史兼容点

`s6_synthesize.py` 仍保留旧版 Phase A：

```text
S5 单图旧结构 -> s6_unified_job.json(version=1.0) -> legacy toolkit
```

这条路径只应用于历史旧项目迁移。新链路不应再依赖它。

建议后续处理：

- 将 `convert_s5_to_job()` 标记为 legacy。
- 新增 `render_v2_job()` 或在 pipeline engine 中直接调用 `illustration.api.render()`。
- S6 的 synthesize 阶段只接收 manifest，不再负责转换绘图任务。
- 将旧版 `TYPE_MAP` / `CONVERTERS` 移到 `legacy` 命名空间，避免误用。

## 6. 质量门禁

bid-tool 调用前应做两级检查：

1. `api.validate()`：检查 v2 协议、图型、必填字段。
2. `api.plan()`：生成渲染规划，人工可审阅 renderer 分配是否合理。

正式渲染失败时，不应在 S6 中修补内部 renderer 输入，而应回到 S5 job 修复 `type`、`data` 或 `visual`。
