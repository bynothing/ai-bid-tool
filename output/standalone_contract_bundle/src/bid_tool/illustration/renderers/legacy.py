"""Internal adapter that reuses the existing SVG/ECharts toolkit helpers."""
from __future__ import annotations

from pathlib import Path

from ..core.job import IllustrationJob, IllustrationItem
from ..core.registry import get_diagram_type, normalize_type
from ..palettes import select_palette_for_item
from .base import RenderContext, RenderResult


class LegacyToolkitAdapter:
    """Render v2 items through the existing SVG/ECharts helper functions."""

    name = "legacy_toolkit"

    def render(self, job: IllustrationJob, items: list[IllustrationItem], context: RenderContext) -> list[RenderResult]:
        from .. import toolkit

        adapter_job = self._to_legacy_job(job, items)
        # Validation already done by platform v2; skip re-validation via legacy validate_job
        _, svg_package, chart_package = toolkit.validate_job(adapter_job)

        context.output.mkdir(parents=True, exist_ok=True)
        svg_file, _ = toolkit.write_input_packages(context.output, svg_package, chart_package)
        svg_results = toolkit.render_svg(svg_file, context.output, context.theme, context.png, context.png_scale)
        review_page = toolkit.create_echarts_review_page(chart_package, context.output)
        chart_exports: dict[str, dict[str, str]] = {}
        if review_page and context.export_echarts:
            chart_exports = toolkit.export_echarts_images(review_page, chart_package["charts"], context.output, context.png)

        records = toolkit.make_records(adapter_job, svg_results, chart_exports, review_page, context.output)
        return [
            RenderResult(
                item_id=record["id"],
                renderer=record["renderer"],
                outputs=record.get("outputs", {}),
            )
            for record in records
        ]

    def _to_legacy_job(self, job: IllustrationJob, items: list[IllustrationItem]) -> dict:
        legacy_items = []
        for item in items:
            spec = dict(item.data)
            spec.setdefault("id", item.id)
            spec.setdefault("palette", select_palette_for_item(job, item))
            diagram = get_diagram_type(item.type)
            if diagram and diagram.legacy_type:
                spec["type"] = diagram.legacy_type
            elif item.type.startswith("chart."):
                spec["type"] = item.type.removeprefix("chart.")
            else:
                spec["type"] = normalize_type(item.type)
            spec.setdefault("title", item.insertion.get("caption", item.id))

            renderer = "echarts_html" if normalize_type(item.type).startswith("chart.") else "svg"
            if item.renderer in {"echarts_html", "echarts"}:
                renderer = "echarts_html"
            elif item.renderer in {"svg", "svg_native"}:
                renderer = "svg"

            legacy_items.append({
                "id": item.id,
                "renderer": renderer,
                "insertion": item.insertion,
                "spec": spec,
            })
        return {
            "document": job.document,
            "style": {
                "theme": _theme_for_legacy(job.style.get("theme", "clarity_blue")),
                "preferredFormat": job.style.get("preferredFormat", "both"),
            },
            "illustrations": legacy_items,
        }


def _theme_for_legacy(theme: str) -> str:
    aliases = {
        "formal_blue": "clarity_blue",
        "formal_teal": "navy_teal",
        "formal_gold": "royal_gold",
    }
    return aliases.get(theme, theme)
