"""Mermaid renderer adapter.

This adapter emits Mermaid source plus a self-contained review HTML page. When
Playwright can load Mermaid from CDN, it also exports SVG/PNG previews.
"""
from __future__ import annotations

import html
from pathlib import Path
from typing import Any

from ..core.job import IllustrationJob, IllustrationItem
from ..palettes import get_palette, select_palette_for_item, style_from_item, use_palette
from .base import RenderContext, RenderResult
from .html import _safe_name


class MermaidRenderer:
    """Render flow/sequence/timeline diagrams through Mermaid syntax."""

    name = "mermaid"

    def render(self, job: IllustrationJob, items: list[IllustrationItem], context: RenderContext) -> list[RenderResult]:
        output_dir = context.output / "assets" / "mermaid"
        output_dir.mkdir(parents=True, exist_ok=True)
        results: list[RenderResult] = []
        for item in items:
            palette_name = select_palette_for_item(job, item)
            with use_palette(palette_name):
                source = _to_mermaid(item)
            stem = _safe_name(item.id)
            mmd_path = output_dir / f"{stem}.mmd"
            html_path = output_dir / f"{stem}.html"
            mmd_path.write_text(source + "\n", encoding="utf-8")
            with use_palette(palette_name):
                html_path.write_text(_page(item, source, job.document.get("title", "")), encoding="utf-8")
            outputs = {
                "mmd": mmd_path.relative_to(context.output).as_posix(),
                "html": html_path.relative_to(context.output).as_posix(),
            }
            warnings: list[str] = []
            svg_path = output_dir / f"{stem}.svg"
            if _export_mermaid_svg(html_path, svg_path):
                outputs["svg"] = svg_path.relative_to(context.output).as_posix()
            else:
                warnings.append("Mermaid SVG 自动导出失败；已保留 .mmd 源文件和 HTML 预览页")
            if context.png:
                png_path = output_dir / f"{stem}.png"
                if _screenshot_mermaid(html_path, png_path, context.png_scale):
                    outputs["png"] = png_path.relative_to(context.output).as_posix()
                else:
                    warnings.append("Mermaid PNG 导出失败；请确认 playwright 可用且可访问 Mermaid CDN")
            results.append(RenderResult(item.id, self.name, outputs, warnings))
        return results


def _to_mermaid(item: IllustrationItem) -> str:
    data = item.data or {}
    if item.type in {"interaction.sequence", "sequence_diagram"}:
        return _sequence(data)
    if item.type == "timeline.gantt":
        return _gantt(data)
    return _flowchart(data)


def _flowchart(data: dict[str, Any]) -> str:
    lines = [
        "---",
        f"title: {data.get('title', '流程图')}",
        "---",
        "flowchart LR",
    ]
    nodes = data.get("nodes") or _items_as_nodes(data.get("steps") or data.get("phases") or data.get("items") or [])
    seen: set[str] = set()
    classes: list[tuple[str, str]] = []
    for index, node in enumerate(nodes, start=1):
        node_id = _node_id(node, index)
        seen.add(node_id)
        classes.append((node_id, style_from_item(node, index - 1)))
        label = _label(node)
        kind = node.get("kind", "process") if isinstance(node, dict) else "process"
        if kind == "decision":
            lines.append(f'  {node_id}{{"{label}"}}')
        elif kind in {"success", "failure"}:
            lines.append(f'  {node_id}(("{label}"))')
        else:
            lines.append(f'  {node_id}["{label}"]')
    edges = data.get("edges") or []
    if edges:
        for edge in edges:
            source = _safe_mermaid_id(edge.get("from", ""))
            target = _safe_mermaid_id(edge.get("to", ""))
            if source not in seen or target not in seen:
                continue
            label = edge.get("label", "")
            arrow = f' -->|{_escape_mermaid(label)}| ' if label else " --> "
            lines.append(f"  {source}{arrow}{target}")
    else:
        ids = [_node_id(node, index) for index, node in enumerate(nodes, start=1)]
        for left, right in zip(ids, ids[1:]):
            lines.append(f"  {left} --> {right}")
    lines.extend(_class_defs())
    for node_id, style in classes:
        lines.append(f"  class {node_id} {style};")
    return "\n".join(lines)


def _class_defs() -> list[str]:
    roles = get_palette()["roles"]
    lines = []
    for name, colors in roles.items():
        lines.append(
            f"  classDef {name} fill:{colors['light']},stroke:{colors['main']},color:#062b52,stroke-width:1.6px;"
        )
    return lines


def _sequence(data: dict[str, Any]) -> str:
    lines = [
        "---",
        f"title: {data.get('title', '时序交互图')}",
        "---",
        "sequenceDiagram",
        "  autonumber",
    ]
    participants = data.get("participants", [])
    for index, participant in enumerate(participants, start=1):
        pid = _safe_mermaid_id(participant.get("id", f"P{index}"))
        label = _escape_mermaid(participant.get("title", participant.get("label", pid)))
        lines.append(f"  participant {pid} as {label}")
    for message in data.get("messages", []):
        source = _safe_mermaid_id(message.get("from", "A"))
        target = _safe_mermaid_id(message.get("to", "B"))
        arrow = "-->>" if message.get("relation") in {"sync", "data"} else "->>"
        if message.get("bidirectional"):
            arrow = "<<->>"
        label = _escape_mermaid(message.get("label", "调用"))
        lines.append(f"  {source}{arrow}{target}: {label}")
    return "\n".join(lines)


def _gantt(data: dict[str, Any]) -> str:
    lines = [
        "---",
        f"title: {data.get('title', '实施计划甘特图')}",
        "---",
        "gantt",
        "  dateFormat  YYYY-MM-DD",
        "  axisFormat  %m/%d",
        "  section 计划",
    ]
    cursor_day = 1
    for index, phase in enumerate(data.get("phases", []), start=1):
        start = int(float(phase.get("start", cursor_day - 1))) + 1
        end = int(float(phase.get("end", start)))
        duration = max(1, end - start + 1)
        task_id = f"t{index}"
        label = _escape_mermaid(phase.get("title", f"阶段{index}"))
        lines.append(f"  {label} :{task_id}, 2026-01-{start:02d}, {duration}d")
        cursor_day = end + 1
    return "\n".join(lines)


def _items_as_nodes(items: list[Any]) -> list[dict[str, Any]]:
    nodes = []
    for index, item in enumerate(items, start=1):
        if isinstance(item, dict):
            node = dict(item)
        else:
            node = {"title": str(item)}
        node.setdefault("id", f"N{index}")
        nodes.append(node)
    return nodes


def _node_id(node: Any, index: int) -> str:
    if isinstance(node, dict):
        return _safe_mermaid_id(node.get("id", f"N{index}"))
    return f"N{index}"


def _label(node: Any) -> str:
    if isinstance(node, dict):
        title = node.get("title", node.get("label", "节点"))
        desc = node.get("desc", "")
        return _escape_mermaid(f"{title}\\n{desc}" if desc else title)
    return _escape_mermaid(str(node))


def _safe_mermaid_id(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char == "_" else "_" for char in str(value))
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"N_{cleaned}"
    return cleaned


def _escape_mermaid(value: Any) -> str:
    return str(value or "").replace('"', "'").replace("\n", "<br/>")


def _page(item: IllustrationItem, source: str, doc_title: str) -> str:
    title = html.escape(str(item.data.get("title") or item.insertion.get("caption") or item.id), quote=True)
    source_html = html.escape(source)
    doc = html.escape(doc_title or "", quote=True)
    palette = get_palette()
    header = palette["header"]
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <title>{title}</title>
  <style>
    body {{ margin:0; background:#f4f8fc; font-family:"Microsoft YaHei",Arial,sans-serif; color:{palette["text"]}; }}
    .canvas {{ width:1600px; min-height:960px; padding:34px 42px; background:#fff; }}
    .header {{ margin:-34px -42px 28px; padding:28px 52px; color:#fff; background:linear-gradient(90deg,{header["main"]},{header["alt"]}); }}
    h1 {{ margin:0; font-size:38px; }}
    .doc {{ margin-top:8px; color:#d8ecfb; font-size:18px; }}
    .stage {{ padding:26px; border:1px solid #d3e3f2; border-radius:8px; background:#fff; }}
    .mermaid {{ display:flex; justify-content:center; }}
    details {{ margin-top:22px; }}
    pre {{ white-space:pre-wrap; background:#f5fbff; border:1px solid #d3e3f2; padding:16px; }}
  </style>
</head>
<body>
  <main class="canvas">
    <section class="header"><h1>{title}</h1><div class="doc">{doc}</div></section>
    <section class="stage"><pre class="mermaid">{source_html}</pre></section>
    <details><summary>Mermaid source</summary><pre>{source_html}</pre></details>
  </main>
  <script type="module">
    import mermaid from 'https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.esm.min.mjs';
    mermaid.initialize({{ startOnLoad: true, securityLevel: 'loose', theme: 'base' }});
  </script>
</body>
</html>
"""


def _export_mermaid_svg(html_path: Path, svg_path: Path) -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1600, "height": 960})
            page.goto(html_path.as_uri(), wait_until="networkidle", timeout=30000)
            page.wait_for_selector(".mermaid svg", timeout=30000)
            svg = page.locator(".mermaid svg").first.evaluate("node => node.outerHTML")
            svg_path.write_text(svg, encoding="utf-8")
            browser.close()
        return True
    except Exception:
        return False


def _screenshot_mermaid(html_path: Path, png_path: Path, scale: int) -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1600, "height": 960}, device_scale_factor=scale)
            page.goto(html_path.as_uri(), wait_until="networkidle", timeout=30000)
            page.wait_for_selector(".mermaid svg", timeout=30000)
            page.locator(".canvas").screenshot(path=str(png_path), animations="disabled")
            browser.close()
        return True
    except Exception:
        return False
