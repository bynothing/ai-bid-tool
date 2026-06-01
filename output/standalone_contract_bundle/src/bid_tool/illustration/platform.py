"""Illustration platform v2 orchestration."""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .core.job import IllustrationJob, load_job
from .core.manifest import AssetRecord, write_platform_manifest
from .core.router import route_item
from .core.validator import quality_warnings, validate_platform_job
from .renderers.base import RenderContext, RenderResult
from .renderers.graphviz import GraphvizRenderer
from .renderers.html import HtmlCssRenderer
from .renderers.legacy import LegacyToolkitAdapter
from .renderers.mermaid import MermaidRenderer


SUPPORTED_RENDERERS = {"svg_native", "echarts_html", "html_css", "mermaid", "graphviz"}


def render_job_file(
    job_file: Path,
    output: Path,
    png: bool = False,
    png_scale: int = 2,
    export_echarts: bool = True,
) -> list[AssetRecord]:
    job = load_job(job_file.resolve())
    return render_job(job, output.resolve(), png=png, png_scale=png_scale, export_echarts=export_echarts)


def render_job(
    job: IllustrationJob,
    output: Path,
    png: bool = False,
    png_scale: int = 2,
    export_echarts: bool = True,
) -> list[AssetRecord]:
    """Validate, route, render, and write a v2 platform manifest."""

    errors = validate_platform_job(job)
    if errors:
        raise ValueError("配图平台任务校验失败:\n" + "\n".join(f"- {error}" for error in errors))

    routed = [(item, route_item(item)) for item in job.illustrations]
    unsupported = [route.renderer for _, route in routed if route.renderer not in SUPPORTED_RENDERERS]
    if unsupported:
        unique = ", ".join(sorted(set(unsupported)))
        raise NotImplementedError(
            f"以下渲染器已纳入平台规划但尚未实现: {unique}; "
            "请使用已实现的 renderer: auto/html_css/svg_native/echarts_html/mermaid/graphviz。"
        )

    groups = defaultdict(list)
    for item, route in routed:
        groups[route.renderer].append(item)

    theme = _adapter_theme(job.style.get("theme", "formal_blue"))
    context = RenderContext(output=output, theme=theme, png=png, png_scale=png_scale, export_echarts=export_echarts)
    results: dict[str, RenderResult] = {}
    for renderer, items in groups.items():
        adapter = _adapter_for(renderer)
        for result in adapter.render(job, items, context):
            result.renderer = renderer
            results[result.item_id] = result

    global_warnings = quality_warnings(job)
    records = []
    for item in job.illustrations:
        route = route_item(item)
        result = results.get(item.id, RenderResult(item.id, route.renderer))
        records.append(AssetRecord(
            id=item.id,
            type=route.type,
            renderer=route.renderer,
            section=item.insertion.get("section", ""),
            caption=item.insertion.get("caption", item.id),
            purpose=item.intent or item.insertion.get("purpose", ""),
            outputs=result.outputs,
            warnings=result.warnings,
            decision=list(route.reasons),
        ))
    if global_warnings and records:
        records[0].warnings.extend(global_warnings)
    write_platform_manifest(output, job.document, records, job.source)
    return records


def _adapter_theme(theme: str) -> str:
    aliases = {
        "formal_blue": "clarity_blue",
        "formal_teal": "navy_teal",
        "formal_gold": "royal_gold",
    }
    return aliases.get(theme, theme)


def _adapter_for(renderer: str):
    if renderer == "html_css":
        return HtmlCssRenderer()
    if renderer == "mermaid":
        return MermaidRenderer()
    if renderer == "graphviz":
        return GraphvizRenderer()
    return LegacyToolkitAdapter()
