"""ECharts renderer adapter for the v2 illustration platform.

Creates a self-contained HTML review page with embedded ECharts for data-driven
charts (bar/line, radar, pie, etc.).  SVG/PNG export is attempted via Playwright
when available but is never required — the HTML page alone is a valid deliverable.
"""
from __future__ import annotations

import html
import json
import shutil
from pathlib import Path

from ..core.job import IllustrationJob, IllustrationItem
from ..palettes import get_palette, select_palette_for_item, use_palette
from .base import RenderContext, RenderResult
from .normalize import normalize

# -- Path to the ECharts web runtime (shipped with the package) ----------------
_WEB_RUNTIME = Path(__file__).resolve().parent.parent / "echarts_workbench"


class EChartsRenderer:
    """Render data charts as interactive ECharts review pages."""

    name = "echarts_html"

    def render(
        self,
        job: IllustrationJob,
        items: list[IllustrationItem],
        context: RenderContext,
    ) -> list[RenderResult]:
        output_dir = context.output / "assets" / "echarts"
        output_dir.mkdir(parents=True, exist_ok=True)

        charts: list[dict] = []
        for item in items:
            data = normalize(item.type, dict(item.data))
            data.setdefault("title", item.insertion.get("caption", item.id))
            charts.append(data)

        # Write the review page
        review_dir = context.output / "review" / "echarts"
        if review_dir.exists():
            shutil.rmtree(review_dir)
        shutil.copytree(_WEB_RUNTIME, review_dir, dirs_exist_ok=True)
        for cruft in ("README.md",):
            p = review_dir / cruft
            if p.exists():
                p.unlink()

        payload = "window.DEMO_CHART_PACKAGE = " + json.dumps(
            {"documentTitle": job.document.get("title", ""), "charts": charts},
            ensure_ascii=False, indent=2,
        ) + ";\n"
        (review_dir / "demo-specs.js").write_text(payload, encoding="utf-8")
        review_page = review_dir / "index.html"

        # Attempt SVG/PNG export via Playwright (best-effort)
        exported: dict[str, dict[str, str]] = {}
        if context.export_echarts:
            exported = _export_charts(review_page, charts, output_dir, context.png)

        results: list[RenderResult] = []
        for item, chart in zip(items, charts):
            cid = chart.get("id", item.id)
            outputs: dict[str, str] = {
                "reviewHtml": review_page.relative_to(context.output).as_posix(),
            }
            outputs.update(exported.get(cid, {}))
            results.append(RenderResult(item.id, self.name, outputs))

        return results


def _export_charts(
    review_page: Path, charts: list[dict], output_dir: Path, png: bool
) -> dict[str, dict[str, str]]:
    """Try to export SVG/PNG from the ECharts review page."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return {}

    exported: dict[str, dict[str, str]] = {}
    try:
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1600, "height": 1040})
            page.on("pageerror", lambda err: None)  # swallow JS errors
            page.goto(review_page.as_uri(), wait_until="load", timeout=30000)
            try:
                page.wait_for_selector("#chart-stage svg", timeout=10000)
            except Exception:
                browser.close()
                return {}
            for idx, chart in enumerate(charts):
                cid = chart.get("id", f"chart{idx}")
                try:
                    page.locator(".chart-tab").nth(idx).click()
                    page.wait_for_timeout(200)
                    with page.expect_download(timeout=10000) as dl:
                        page.locator("#download-svg").click()
                    svg_path = output_dir / f"{cid}.svg"
                    dl.value.save_as(svg_path)
                    exported.setdefault(cid, {})["svg"] = svg_path.relative_to(output_dir.parent).as_posix()
                    if png:
                        with page.expect_download(timeout=10000) as dl:
                            page.locator("#download-png").click()
                        png_path = output_dir / f"{cid}.png"
                        dl.value.save_as(png_path)
                        exported.setdefault(cid, {})["png"] = png_path.relative_to(output_dir.parent).as_posix()
                except Exception:
                    continue
            browser.close()
    except Exception:
        pass
    return exported
