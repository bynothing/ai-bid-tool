# Bid Illustration Standalone

This directory is a standalone runtime for the bid illustration platform V2.
It does not include the full bid-tool pipeline.

## Quick Start

```powershell
python run_illustration.py --job examples\示例_统一文档配图任务.json --validate-only
python run_illustration.py --job examples\示例_统一文档配图任务.json --output output\illustrations --png
```

## Dependencies

Minimum:

```powershell
pip install jsonschema pyyaml
```

Optional PNG and ECharts export:

```powershell
pip install cairosvg playwright
playwright install chromium
```

## Public Contract

External jobs must use `version: "2.0"` and the schema:

`src/bid_tool/schemas/illustration_job_v2.schema.json`

Use `renderer: "auto"` unless a specific renderer is required. The platform
will choose from `html_css`, `svg_native`, `echarts_html`, `mermaid`, and
`graphviz`.
