"""SVG renderer adapter for the v2 illustration platform.

Imports the mature SVG rendering functions from svg_renderer.py and wraps them
as a standard RendererAdapter. Data is normalised through the shared normalizer
before rendering, so callers never need to know about v1 field names.
"""
from __future__ import annotations

from pathlib import Path

from ..core.job import IllustrationJob, IllustrationItem
from ..palettes import select_palette_for_item, use_palette
from ..svg_renderer import RENDERERS as SVG_RENDERERS, WIDTH as SVG_WIDTH
from ..svg_renderer import _theme_with_palette, slug
from ..themes import THEMES
from .base import RenderContext, RenderResult
from .normalize import normalize


# -- Map v2 diagram types to SVG renderer function names -----------------------
_TYPE_TO_SVG = {
    "architecture.layered":      "layered_architecture",
    "layered_architecture":      "layered_architecture",
    "process.flowchart":         "flowchart",
    "flowchart":                 "flowchart",
    "interaction.sequence":      "sequence_diagram",
    "sequence_diagram":          "sequence_diagram",
    "process.swimlane":          "swimlane_flowchart",
    "swimlane_flowchart":        "swimlane_flowchart",
    "capability.map":            "capability_map",
    "capability_map":            "capability_map",
    "relationship.domain":       "relationship_map",
    "relationship_map":          "relationship_map",
    "integration.interface_map": "interface_map",
    "interface_map":             "interface_map",
    "operation.inspection_taxonomy": "inspection_taxonomy",
    "inspection_taxonomy":       "inspection_taxonomy",
    "operation.incident_response": "incident_response",
    "incident_response":         "incident_response",
    "architecture.security_ring": "security_ring",
    "security_ring":             "security_ring",
}


class SvgRenderer:
    """Render structured diagrams as production-quality SVG."""

    name = "svg_native"

    def render(
        self,
        job: IllustrationJob,
        items: list[IllustrationItem],
        context: RenderContext,
    ) -> list[RenderResult]:
        output_dir = context.output / "assets" / "svg"
        output_dir.mkdir(parents=True, exist_ok=True)
        results: list[RenderResult] = []

        for item in items:
            data = normalize(item.type, dict(item.data))
            data.setdefault("title", item.insertion.get("caption", item.id))
            data.setdefault("subtitle", item.intent or "")

            svg_func_name = _TYPE_TO_SVG.get(item.type)
            if svg_func_name is None or svg_func_name not in SVG_RENDERERS:
                results.append(RenderResult(
                    item.id, self.name, {},
                    [f"SVG 渲染器不支持图型 {item.type}，请使用 html_css 或其它渲染器"],
                ))
                continue

            theme_key = context.theme if context.theme in THEMES else "clarity_blue"
            try:
                palette_name = select_palette_for_item(job, item)
                with use_palette(palette_name):
                    svg = SVG_RENDERERS[svg_func_name](data, _theme_with_palette(THEMES[theme_key]))
            except Exception as exc:
                results.append(RenderResult(
                    item.id, self.name, {},
                    [f"SVG 渲染失败: {exc}"],
                ))
                continue

            filename = f"{slug(data['title'])}.svg"
            svg_path = output_dir / filename
            svg_path.write_text(svg, encoding="utf-8")
            outputs = {"svg": svg_path.relative_to(context.output).as_posix()}
            warnings: list[str] = []

            if context.png:
                png_dir = output_dir / "png"
                png_dir.mkdir(parents=True, exist_ok=True)
                png_path = png_dir / f"{slug(data['title'])}.png"
                if _svg_to_png(svg, png_path, SVG_WIDTH, context.png_scale):
                    outputs["png"] = png_path.relative_to(context.output).as_posix()
                else:
                    warnings.append("SVG PNG 导出失败，请安装 playwright 或 cairosvg")

            results.append(RenderResult(item.id, self.name, outputs, warnings))

        return results


def _svg_to_png(svg: str, png_path: Path, width: int, scale: int) -> bool:
    """Render SVG string to PNG via cairosvg or playwright."""
    try:
        import cairosvg  # type: ignore
        cairosvg.svg2png(
            bytestring=svg.encode("utf-8"), write_to=str(png_path),
            output_width=width * scale, output_height=0,
        )
        return True
    except (ImportError, OSError):
        pass
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": width, "height": 1000}, device_scale_factor=scale)
            page.set_content(f'<html><body style="margin:0">{svg}</body></html>')
            page.locator("svg").screenshot(path=str(png_path), timeout=60000)
            browser.close()
        return True
    except Exception:
        return False
