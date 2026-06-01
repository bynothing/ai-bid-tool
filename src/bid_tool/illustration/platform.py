"""Illustration platform v2 orchestration.

Receives a job, normalises data, routes to the best renderer per item, and
writes a unified manifest.  Callers never need to know which renderer was used.
"""
from __future__ import annotations

from collections import defaultdict
from pathlib import Path

from .core.job import IllustrationItem, IllustrationJob, load_job
from .core.manifest import AssetRecord, write_platform_manifest
from .core.router import route_item
from .core.validator import quality_warnings, validate_platform_job
from .renderers.base import RenderContext, RenderResult
from .renderers.echarts_v2 import EChartsRenderer
from .renderers.graphviz import GraphvizRenderer
from .renderers.html import HtmlCssRenderer
from .renderers.mermaid import MermaidRenderer
from .renderers.svg_v2 import SvgRenderer


# -- Renderer registry ---------------------------------------------------------
# Each value is a callable that returns a RendererAdapter-like object.
_RENDERER_REGISTRY: dict[str, object] = {
    "html_css":     HtmlCssRenderer,
    "svg_native":   SvgRenderer,
    "echarts_html": EChartsRenderer,
    "mermaid":      MermaidRenderer,
    "graphviz":     GraphvizRenderer,
}

SUPPORTED_RENDERERS = set(_RENDERER_REGISTRY.keys())


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
        raise ValueError("配图平台任务校验失败:\n" + "\n".join(f"- {e}" for e in errors))

    # -- Route every item to a concrete renderer --
    routed = [(item, route_item(item)) for item in job.illustrations]
    unsupported = [r.renderer for _, r in routed if r.renderer not in SUPPORTED_RENDERERS]
    if unsupported:
        unique = ", ".join(sorted(set(unsupported)))
        raise NotImplementedError(f"未实现的渲染器: {unique}")

    # -- Group items by renderer --
    groups: dict[str, list[IllustrationItem]] = defaultdict(list)
    for item, route in routed:
        groups[route.renderer].append(item)

    theme = _adapter_theme(job.style.get("theme", "formal_blue"))
    context = RenderContext(
        output=output, theme=theme, png=png,
        png_scale=png_scale, export_echarts=export_echarts,
    )

    # -- Dispatch to each renderer --
    results: dict[str, RenderResult] = {}
    for renderer_name, items in groups.items():
        adapter_cls = _RENDERER_REGISTRY[renderer_name]
        adapter = adapter_cls()
        for result in adapter.render(job, items, context):
            result.renderer = renderer_name
            results[result.item_id] = result

    # -- Build manifest records --
    global_warnings = quality_warnings(job)
    records: list[AssetRecord] = []
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
