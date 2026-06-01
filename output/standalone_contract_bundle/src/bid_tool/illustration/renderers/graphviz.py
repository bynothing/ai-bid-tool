"""Graphviz renderer adapter.

The adapter always writes DOT source. If the local `dot` executable is
available it renders real Graphviz SVG/PNG. Otherwise it creates a lightweight
fallback SVG so the platform still returns a usable visual artifact.
"""
from __future__ import annotations

import math
import shutil
import subprocess
from pathlib import Path
from typing import Any

from ..core.job import IllustrationJob, IllustrationItem
from ..palettes import get_palette, relation_color, select_palette_for_item, style_from_item, triplet, use_palette
from .base import RenderContext, RenderResult
from .html import _safe_name


class GraphvizRenderer:
    """Render topology and dense relationship diagrams with DOT."""

    name = "graphviz"

    def render(self, job: IllustrationJob, items: list[IllustrationItem], context: RenderContext) -> list[RenderResult]:
        output_dir = context.output / "assets" / "graphviz"
        output_dir.mkdir(parents=True, exist_ok=True)
        results: list[RenderResult] = []
        dot_bin = shutil.which("dot")
        for item in items:
            palette_name = select_palette_for_item(job, item)
            with use_palette(palette_name):
                dot, graph = _to_dot(item)
            stem = _safe_name(item.id)
            dot_path = output_dir / f"{stem}.dot"
            svg_path = output_dir / f"{stem}.svg"
            dot_path.write_text(dot, encoding="utf-8")
            outputs = {"dot": dot_path.relative_to(context.output).as_posix()}
            warnings: list[str] = []
            if dot_bin and _run_dot(dot_bin, dot_path, svg_path, "svg"):
                outputs["svg"] = svg_path.relative_to(context.output).as_posix()
            else:
                with use_palette(palette_name):
                    svg_path.write_text(_fallback_svg(item, graph), encoding="utf-8")
                outputs["svg"] = svg_path.relative_to(context.output).as_posix()
                warnings.append("未检测到 Graphviz dot 或执行失败，已使用内置简易 SVG 布局作为降级输出")
            if context.png:
                png_path = output_dir / f"{stem}.png"
                if dot_bin and _run_dot(dot_bin, dot_path, png_path, "png"):
                    outputs["png"] = png_path.relative_to(context.output).as_posix()
                elif _svg_to_png(svg_path, png_path, context.png_scale):
                    outputs["png"] = png_path.relative_to(context.output).as_posix()
                else:
                    warnings.append("Graphviz PNG 导出失败；已保留 DOT 和 SVG")
            results.append(RenderResult(item.id, self.name, outputs, warnings))
        return results


def _to_dot(item: IllustrationItem) -> tuple[str, dict[str, Any]]:
    data = item.data or {}
    title = data.get("title") or item.insertion.get("caption") or item.id
    nodes, edges, clusters = _extract_graph(item)
    palette = get_palette()
    header = palette["header"]
    primary = palette["roles"]["primary"]
    lines = [
        "digraph G {",
        "  graph [rankdir=LR, bgcolor=\"white\", labelloc=t, labeljust=l,",
        f"         label=\"{_dot_escape(title)}\", fontsize=24, fontname=\"Microsoft YaHei\"];",
        f"  node [shape=box, style=\"rounded,filled\", fillcolor=\"{primary['light']}\",",
        f"        color=\"{primary['main']}\", fontcolor=\"{palette['text']}\", fontname=\"Microsoft YaHei\", fontsize=14, margin=\"0.12,0.08\"];",
        f"  edge [color=\"{header['alt']}\", fontname=\"Microsoft YaHei\", fontsize=12, arrowsize=0.8];",
    ]
    clustered_ids: set[str] = set()
    for idx, cluster in enumerate(clusters, start=1):
        cluster_nodes = cluster.get("nodes", [])
        if not cluster_nodes:
            continue
        lines.append(f"  subgraph cluster_{idx} {{")
        lines.append(f"    label=\"{_dot_escape(cluster.get('title', f'分组{idx}'))}\";")
        lines.append(f"    color=\"{palette['line']}\"; style=\"rounded\"; bgcolor=\"{palette['wash']}\";")
        for node in cluster_nodes:
            node_id = node["id"]
            clustered_ids.add(node_id)
            lines.append(_dot_node(node, indent="    "))
        lines.append("  }")
    for node in nodes:
        if node["id"] not in clustered_ids:
            lines.append(_dot_node(node))
    for edge in edges:
        source = _dot_id(edge.get("from", ""))
        target = _dot_id(edge.get("to", ""))
        if not source or not target:
            continue
        attrs = []
        if edge.get("label"):
            attrs.append(f'label="{_dot_escape(edge["label"])}"')
        relation = edge.get("relation")
        if relation:
            attrs.append(f'color="{relation_color(relation)}"')
        if relation == "data":
            attrs.append('style="dashed"')
        elif relation == "alert":
            attrs.append("penwidth=2")
        attr = f" [{', '.join(attrs)}]" if attrs else ""
        lines.append(f"  {_dot_id(source)} -> {_dot_id(target)}{attr};")
        if edge.get("bidirectional"):
            lines.append(f"  {_dot_id(target)} -> {_dot_id(source)} [style=\"dashed\", color=\"#b36b00\"];")
    lines.append("}")
    return "\n".join(lines), {"nodes": nodes, "edges": edges, "clusters": clusters}


def _extract_graph(item: IllustrationItem) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    data = item.data or {}
    nodes: list[dict[str, Any]] = []
    edges = list(data.get("edges", []))
    clusters: list[dict[str, Any]] = []
    if item.type == "network.topology":
        for zone_idx, zone in enumerate(data.get("zones", []), start=1):
            zone_nodes = []
            for node_idx, node in enumerate(zone.get("nodes", []), start=1):
                normalized = _normalize_node(node, f"z{zone_idx}_n{node_idx}", node_idx - 1)
                zone_nodes.append(normalized)
                nodes.append(normalized)
            clusters.append({"title": zone.get("title", f"区域{zone_idx}"), "nodes": zone_nodes})
        return nodes, edges, clusters
    if data.get("containers"):
        for c_idx, container in enumerate(data.get("containers", []), start=1):
            group_nodes = []
            for n_idx, node in enumerate(container.get("nodes", []), start=1):
                normalized = _normalize_node(node, f"c{c_idx}_n{n_idx}", n_idx - 1)
                group_nodes.append(normalized)
                nodes.append(normalized)
            clusters.append({"title": container.get("title", f"域{c_idx}"), "nodes": group_nodes})
        return nodes, edges, clusters
    raw_nodes = data.get("nodes") or data.get("items") or []
    for index, node in enumerate(raw_nodes, start=1):
        nodes.append(_normalize_node(node, f"n{index}", index - 1))
    if not edges and len(nodes) > 1:
        edges = [{"from": left["id"], "to": right["id"]} for left, right in zip(nodes, nodes[1:])]
    return nodes, edges, clusters


def _normalize_node(node: Any, fallback_id: str, index: int = 0) -> dict[str, Any]:
    if isinstance(node, dict):
        node_id = str(node.get("id") or fallback_id)
        title = str(node.get("title") or node.get("label") or node_id)
        desc = str(node.get("desc") or node.get("subtitle") or "")
        return {"id": node_id, "title": title, "desc": desc, "style": style_from_item(node, index)}
    return {"id": fallback_id, "title": str(node), "desc": "", "style": style_from_item(node, index)}


def _dot_node(node: dict[str, Any], indent: str = "  ") -> str:
    stroke, fill, _ = triplet(node.get("style"))
    label = node["title"] + (f"\\n{node['desc']}" if node.get("desc") else "")
    return f'{indent}{_dot_id(node["id"])} [label="{_dot_escape(label)}", fillcolor="{fill}", color="{stroke}"];'


def _run_dot(dot_bin: str, dot_path: Path, output_path: Path, fmt: str) -> bool:
    try:
        subprocess.run([dot_bin, f"-T{fmt}", str(dot_path), "-o", str(output_path)], check=True, timeout=60)
        return output_path.exists() and output_path.stat().st_size > 0
    except Exception:
        return False


def _svg_to_png(svg_path: Path, png_path: Path, scale: int) -> bool:
    try:
        import cairosvg  # type: ignore
        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), scale=scale)
        return True
    except Exception:
        pass
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1600, "height": 960}, device_scale_factor=scale)
            page.goto(svg_path.as_uri(), wait_until="load")
            page.locator("svg").screenshot(path=str(png_path), animations="disabled")
            browser.close()
        return True
    except Exception:
        return False


def _fallback_svg(item: IllustrationItem, graph: dict[str, Any]) -> str:
    nodes = graph.get("nodes", [])
    edges = graph.get("edges", [])
    palette = get_palette()
    header = palette["header"]
    width, height = 1600, 960
    cols = max(1, math.ceil(math.sqrt(max(1, len(nodes)))))
    rows = max(1, math.ceil(max(1, len(nodes)) / cols))
    cell_w = (width - 140) / cols
    cell_h = (height - 220) / rows
    positions: dict[str, tuple[float, float]] = {}
    node_parts = []
    for idx, node in enumerate(nodes):
        row, col = divmod(idx, cols)
        x = 70 + col * cell_w + cell_w / 2
        y = 170 + row * cell_h + cell_h / 2
        stroke, fill, _ = triplet(node.get("style"))
        positions[node["id"]] = (x, y)
        node_parts.append(
            f'<rect x="{x - 110:.1f}" y="{y - 42:.1f}" width="220" height="84" rx="10" fill="{fill}" stroke="{stroke}" stroke-width="2"/>'
            f'<text x="{x:.1f}" y="{y - 6:.1f}" text-anchor="middle" font-size="20" font-weight="700" fill="#062b52">{_xml(node["title"])}</text>'
            f'<text x="{x:.1f}" y="{y + 24:.1f}" text-anchor="middle" font-size="15" fill="#365b82">{_xml(node.get("desc", ""))}</text>'
        )
    edge_parts = []
    for edge in edges:
        source = positions.get(edge.get("from"))
        target = positions.get(edge.get("to"))
        if not source or not target:
            continue
        sx, sy = source
        tx, ty = target
        color = relation_color(edge.get("relation"))
        edge_parts.append(
            f'<line x1="{sx:.1f}" y1="{sy:.1f}" x2="{tx:.1f}" y2="{ty:.1f}" stroke="{color}" stroke-width="2.5" marker-end="url(#arrow)"/>'
        )
    title = item.data.get("title") or item.insertion.get("caption") or item.id
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">
<defs><marker id="arrow" viewBox="0 0 10 10" refX="9" refY="5" markerWidth="8" markerHeight="8" orient="auto"><path d="M0 0L10 5L0 10Z" fill="#1261a0"/></marker></defs>
<rect width="{width}" height="{height}" fill="#ffffff"/>
<rect width="{width}" height="118" fill="{header["main"]}"/>
<text x="52" y="72" font-size="42" font-weight="700" fill="#ffffff" font-family="Microsoft YaHei">{_xml(title)}</text>
{''.join(edge_parts)}
{''.join(node_parts)}
<text x="52" y="918" font-size="18" fill="#365b82" font-family="Microsoft YaHei">注：当前环境未安装 Graphviz dot，使用内置简易布局降级生成。</text>
</svg>'''


def _dot_id(value: str) -> str:
    cleaned = "".join(char if char.isalnum() or char == "_" else "_" for char in str(value))
    if not cleaned or cleaned[0].isdigit():
        cleaned = f"n_{cleaned}"
    return cleaned


def _dot_escape(value: Any) -> str:
    return str(value or "").replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _xml(value: Any) -> str:
    return str(value or "").replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
