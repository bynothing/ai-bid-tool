"""Draw.io renderer adapter.

The renderer borrows the practical rules from the public drawio-skill project:
use real Draw.io containers/swimlanes, keep children relative to containers,
pin orthogonal connectors, leave routing corridors, and lint the XML before
export. It writes editable `.drawio` files first; SVG/PNG export is optional.
"""
from __future__ import annotations

import math
import os
import re
import subprocess
import xml.etree.ElementTree as ET
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from ..core.models import AssetRecord, IllustrationItem, IllustrationJob, PlanDecision


GENERIC_EDGE_LABELS = {
    "请求",
    "调用",
    "流转",
    "传递",
    "读取",
    "写入",
    "同步",
    "通知",
    "反馈",
    "处理",
    "联动",
    "业务请求",
}


@dataclass(slots=True)
class RenderContext:
    output: Path
    theme: str
    png: bool = False
    png_scale: int = 2


@dataclass(slots=True)
class RenderResult:
    item_id: str
    renderer: str
    outputs: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def render_decision(
    job: IllustrationJob,
    decision: PlanDecision,
    output: Path,
    *,
    theme: str,
    png: bool = False,
    png_scale: int = 2,
) -> AssetRecord:
    """Render one v2 decision through Draw.io and return a manifest record."""

    context = RenderContext(output=output, theme=theme, png=png, png_scale=png_scale)
    result = DrawioRenderer().render(job, [decision.item], context)[0]
    return AssetRecord(
        id=decision.item.id,
        type=decision.item.type,
        renderer=decision.renderer,
        section=str(decision.item.insertion.get("section", "")),
        caption=str(decision.item.insertion.get("caption", decision.item.id)),
        outputs=result.outputs,
        template=decision.template_id,
        theme=theme,
        fit_score=decision.fit_score,
        tier=decision.tier,
        degraded_from=decision.degraded_from,
        needs_human_review=decision.needs_human_review,
        warnings=result.warnings,
        decision=decision.to_dict()["decision"],
    )


@dataclass(slots=True)
class DrawNode:
    id: str
    title: str
    subtitle: str = ""
    kind: str = "service"
    group: str = ""
    x: int = 0
    y: int = 0
    width: int = 190
    height: int = 76
    parent: str = "1"


@dataclass(slots=True)
class DrawContainer:
    id: str
    title: str
    x: int
    y: int
    width: int
    height: int
    color_index: int
    kind: str = "swimlane"


@dataclass(slots=True)
class DrawEdge:
    id: str
    source: str
    target: str
    label: str = ""
    relation: str = ""


@dataclass(slots=True)
class DrawPlan:
    title: str
    subtitle: str
    width: int
    height: int
    nodes: list[DrawNode] = field(default_factory=list)
    edges: list[DrawEdge] = field(default_factory=list)
    containers: list[DrawContainer] = field(default_factory=list)

    def container_by_id(self, container_id: str) -> DrawContainer | None:
        return next((container for container in self.containers if container.id == container_id), None)


class DrawioRenderer:
    """Render editable engineering diagrams through Draw.io files."""

    name = "drawio"

    def render(self, job: IllustrationJob, items: list[IllustrationItem], context: RenderContext) -> list[RenderResult]:
        output_dir = context.output / "assets" / "drawio"
        output_dir.mkdir(parents=True, exist_ok=True)
        results: list[RenderResult] = []
        drawio_cmd = _find_drawio_command()

        for item in items:
            stem = _safe_name(item.id)
            drawio_path = output_dir / f"{stem}.drawio"
            xml = _drawio_xml(job, item)
            drawio_path.write_text(xml, encoding="utf-8")

            outputs = {"drawio": drawio_path.relative_to(context.output).as_posix()}
            warnings = _validate_drawio_xml(xml)

            if drawio_cmd:
                svg_path = output_dir / f"{stem}.svg"
                if _export(drawio_cmd, drawio_path, svg_path, "svg"):
                    outputs["svg"] = svg_path.relative_to(context.output).as_posix()
                else:
                    warnings.append("Draw.io SVG 导出失败；已保留可编辑 .drawio 源文件")

                if context.png:
                    png_path = output_dir / f"{stem}.png"
                    if _export(drawio_cmd, drawio_path, png_path, "png"):
                        outputs["png"] = png_path.relative_to(context.output).as_posix()
                    else:
                        warnings.append("Draw.io PNG 导出失败；已保留可编辑 .drawio 源文件")
            else:
                warnings.append("未检测到 Draw.io CLI；已生成可编辑 .drawio 源文件，跳过 SVG/PNG 导出")

            results.append(RenderResult(item.id, self.name, outputs, warnings))
        return results


def _drawio_xml(job: IllustrationJob, item: IllustrationItem) -> str:
    raw = item.data.get("drawioXml") or item.data.get("drawio_xml") or item.data.get("mxfile")
    if isinstance(raw, str) and raw.strip():
        return raw.strip() + "\n"

    plan = _normalize_plan(_plan_diagram(job, item))
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    mxfile = ET.Element("mxfile", {
        "host": "bid-tool",
        "modified": now,
        "agent": "bid-tool drawio renderer",
        "version": "30.0.4",
    })
    diagram = ET.SubElement(mxfile, "diagram", {"id": _xml_id(item.id), "name": _safe_name(plan.title)[:60] or "Page-1"})
    model = ET.SubElement(diagram, "mxGraphModel", {
        "dx": str(plan.width),
        "dy": str(plan.height),
        "grid": "1",
        "gridSize": "10",
        "guides": "1",
        "tooltips": "1",
        "connect": "1",
        "arrows": "1",
        "fold": "1",
        "page": "1",
        "pageScale": "1",
        "pageWidth": str(plan.width),
        "pageHeight": str(plan.height),
        "background": "#f7fafc",
        "math": "0",
        "shadow": "0",
    })
    root = ET.SubElement(model, "root")
    ET.SubElement(root, "mxCell", {"id": "0"})
    ET.SubElement(root, "mxCell", {"id": "1", "parent": "0"})

    _add_header(root, plan)
    for container in plan.containers:
        ET.SubElement(root, "mxCell", {
            "id": container.id,
            "value": container.title,
            "style": _container_style(container),
            "vertex": "1",
            "parent": "1",
        }).append(_geometry(container.x, container.y, container.width, container.height))

    for index, node in enumerate(plan.nodes, start=1):
        ET.SubElement(root, "mxCell", {
            "id": node.id,
            "value": _cell_text(node.title, node.subtitle),
            "style": _node_style(node, index),
            "vertex": "1",
            "parent": node.parent,
        }).append(_geometry(node.x, node.y, node.width, node.height))

    incoming, outgoing = _edge_counts(plan.edges)
    label_counts = _label_counts(plan.edges)
    for index, edge in enumerate(plan.edges, start=1):
        source = _node_by_id(plan, edge.source)
        target = _node_by_id(plan, edge.target)
        if not source or not target:
            continue
        label = _edge_label(edge, label_counts, index, len(plan.edges))
        edge_cell = ET.SubElement(root, "mxCell", {
            "id": edge.id or f"E{index}",
            "value": label,
            "style": _edge_style(plan, edge, source, target, outgoing.get(source.id, 1), incoming.get(target.id, 1), index, bool(label)),
            "edge": "1",
            "parent": "1",
            "source": source.id,
            "target": target.id,
        })
        geometry = ET.SubElement(edge_cell, "mxGeometry", {"relative": "1", "as": "geometry"})
        points = _edge_waypoints(plan, source, target)
        if points:
            array = ET.SubElement(geometry, "Array", {"as": "points"})
            for x, y in points:
                ET.SubElement(array, "mxPoint", {"x": str(x), "y": str(y)})

    ET.indent(mxfile, space="  ")
    return ET.tostring(mxfile, encoding="unicode", xml_declaration=True) + "\n"


def _plan_diagram(job: IllustrationJob, item: IllustrationItem) -> DrawPlan:
    title = item.data.get("title") or item.insertion.get("caption") or item.id
    subtitle = job.document.get("title", "")
    if item.type in {"architecture.layered", "layered_architecture"} and item.data.get("layers"):
        return _plan_layers(title, subtitle, item)
    if item.type in {"architecture.deployment", "network.topology"} and item.data.get("zones"):
        return _plan_zones(title, subtitle, item)
    if item.type == "integration.interface_map":
        return _plan_interface(title, subtitle, item)
    if item.type in {"process.flowchart", "flowchart"}:
        return _plan_flowchart(title, subtitle, item)
    return _plan_general(title, subtitle, item)


def _plan_layers(title: str, subtitle: str, item: IllustrationItem) -> DrawPlan:
    nodes: list[DrawNode] = []
    containers: list[DrawContainer] = []
    margin_x, top_y = 60, 130
    row_h, gap_y = 136, 28
    width = 1180
    for layer_idx, layer in enumerate(item.data.get("layers", []), start=1):
        cid = f"C_layer_{layer_idx}"
        y = top_y + (layer_idx - 1) * (row_h + gap_y)
        containers.append(DrawContainer(cid, str(layer.get("title") or layer.get("label") or f"Layer {layer_idx}"), margin_x, y, width - 120, row_h, layer_idx - 1))
        entries = layer.get("items", [])
        count = max(len(entries), 1)
        card_w = min(210, max(170, (width - 220 - (count - 1) * 28) // count))
        for item_idx, entry in enumerate(entries, start=1):
            node = _node(entry, len(nodes) + 1)
            node.parent = cid
            node.group = cid
            node.x = 36 + (item_idx - 1) * (card_w + 28)
            node.y = 46
            node.width = card_w
            node.height = 68
            node.subtitle = node.subtitle or str(layer.get("title") or "")
            nodes.append(node)
    height = top_y + len(containers) * (row_h + gap_y) + 50
    return DrawPlan(title, subtitle, width, max(520, height), nodes, _edges(item), containers)


def _plan_zones(title: str, subtitle: str, item: IllustrationItem) -> DrawPlan:
    zones = item.data.get("zones", [])
    width = max(1180, 280 * max(len(zones), 4))
    top_y, gap_x = 130, 26
    container_w = max(240, (width - 120 - (len(zones) - 1) * gap_x) // max(len(zones), 1))
    max_items = max([len(zone.get("nodes", []) or zone.get("devices", [])) for zone in zones] or [1])
    container_h = max(300, 84 + max_items * 94)
    containers: list[DrawContainer] = []
    nodes: list[DrawNode] = []
    for zone_idx, zone in enumerate(zones, start=1):
        cid = f"C_zone_{zone_idx}"
        x = 60 + (zone_idx - 1) * (container_w + gap_x)
        containers.append(DrawContainer(cid, str(zone.get("title") or zone.get("label") or f"Zone {zone_idx}"), x, top_y, container_w, container_h, zone_idx - 1))
        entries = zone.get("nodes", []) or zone.get("devices", [])
        for item_idx, entry in enumerate(entries, start=1):
            node = _node(entry, len(nodes) + 1)
            node.parent = cid
            node.group = cid
            node.x = 28
            node.y = 48 + (item_idx - 1) * 88
            node.width = container_w - 56
            node.height = 64
            node.subtitle = node.subtitle or str(zone.get("title") or "")
            nodes.append(node)
    return DrawPlan(title, subtitle, width, top_y + container_h + 70, nodes, _edges(item), containers)


def _plan_interface(title: str, subtitle: str, item: IllustrationItem) -> DrawPlan:
    raw_nodes, edges = _extract_graph(item)
    preferred = ["business", "gateway", "adapter", "target", "audit", "retry"]
    nodes = _ordered_nodes(raw_nodes, preferred)
    width = 1180
    positions = [
        (80, 250), (300, 160), (520, 250), (740, 160), (960, 90), (960, 330)
    ]
    for index, node in enumerate(nodes):
        x, y = positions[index] if index < len(positions) else (80 + (index % 5) * 220, 450 + (index // 5) * 120)
        node.x, node.y = x, y
        node.width, node.height = 176, 76
    containers = [
        DrawContainer("C_interface_left", "调用方与网关", 54, 126, 430, 338, 0, "box"),
        DrawContainer("C_interface_right", "目标平台与审计闭环", 708, 70, 442, 430, 2, "box"),
    ]
    for node in nodes:
        node.parent = "1"
    return DrawPlan(title, subtitle, width, 560, nodes, edges, containers)


def _plan_flowchart(title: str, subtitle: str, item: IllustrationItem) -> DrawPlan:
    raw_nodes, edges = _extract_graph(item)
    nodes = raw_nodes or [_node(step, index) for index, step in enumerate(item.data.get("steps", []), start=1)]
    width = 980
    top_y = 126
    for index, node in enumerate(nodes):
        node.x = 390
        node.y = top_y + index * 106
        node.width = 200
        node.height = 70
        if index == 0 or "开始" in node.title or "发现" in node.title:
            node.kind = "start"
        elif index == len(nodes) - 1 or "归档" in node.title or "结束" in node.title:
            node.kind = "end"
        elif "分级" in node.title or "判断" in node.title or "审核" in node.title:
            node.kind = "decision"
            node.width = 180
            node.height = 86
    if not edges and len(nodes) > 1:
        edges = [DrawEdge(f"E{idx}", nodes[idx].id, nodes[idx + 1].id) for idx in range(len(nodes) - 1)]
    return DrawPlan(title, subtitle, width, top_y + len(nodes) * 106 + 120, nodes, edges, [])


def _plan_general(title: str, subtitle: str, item: IllustrationItem) -> DrawPlan:
    nodes, edges = _extract_graph(item)
    if not nodes:
        nodes = [_node({"title": title, "description": item.intent}, 1)]
    columns = 4 if len(nodes) > 9 else 3 if len(nodes) > 4 else max(1, len(nodes))
    for index, node in enumerate(nodes):
        node.x = 70 + (index % columns) * 240
        node.y = 140 + (index // columns) * 124
        node.width = 190
        node.height = 76
    width = max(900, 120 + columns * 240)
    height = 260 + math.ceil(len(nodes) / columns) * 124
    return DrawPlan(title, subtitle, width, height, nodes, edges, [])


def _normalize_plan(plan: DrawPlan) -> DrawPlan:
    container_titles = {container.id: container.title for container in plan.containers}
    for node in plan.nodes:
        parent_title = container_titles.get(node.parent, "")
        node.title = _compact_text(node.title, 14)
        node.subtitle = _normalize_subtitle(node.subtitle, parent_title)
    for edge in plan.edges:
        edge.label = _compact_text(edge.label, 10)
    return plan


def _normalize_subtitle(value: str, parent_title: str) -> str:
    subtitle = _compact_text(value, 16)
    if not subtitle:
        return ""
    if parent_title and _similar_text(subtitle, parent_title):
        return ""
    return subtitle


def _similar_text(left: str, right: str) -> bool:
    left_clean = re.sub(r"[\s与和及层区域专区]+", "", left)
    right_clean = re.sub(r"[\s与和及层区域专区]+", "", right)
    if not left_clean or not right_clean:
        return False
    return left_clean in right_clean or right_clean in left_clean


def _compact_text(value: Any, max_chars: int) -> str:
    text = re.sub(r"\s+", " ", str(value or "").strip())
    if len(text) <= max_chars:
        return text
    for sep in ("；", ";", "，", ",", "、", "/", " "):
        pos = text.rfind(sep, 0, max_chars)
        if pos >= max_chars // 2:
            return text[:pos].strip()
    return text[: max_chars - 1].rstrip() + "…"


def _extract_graph(item: IllustrationItem) -> tuple[list[DrawNode], list[DrawEdge]]:
    data = item.data or {}
    nodes: list[DrawNode] = []

    for key in ("nodes", "steps", "phases", "items"):
        if data.get(key):
            nodes.extend(_node(value, idx) for idx, value in enumerate(data[key], start=1))
            break

    if data.get("actors") or data.get("integrations"):
        for entry in [*data.get("actors", []), *data.get("integrations", [])]:
            nodes.append(_node(entry, len(nodes) + 1))

    if data.get("layers"):
        for layer_idx, layer in enumerate(data["layers"], start=1):
            for item_idx, entry in enumerate(layer.get("items", []), start=1):
                node = _node(entry, len(nodes) + 1)
                node.subtitle = node.subtitle or str(layer.get("title") or layer.get("label") or "")
                node.id = node.id or _xml_id(f"L{layer_idx}_{item_idx}")
                nodes.append(node)

    if data.get("zones"):
        for zone in data["zones"]:
            for entry in zone.get("nodes", []) or zone.get("devices", []):
                node = _node(entry, len(nodes) + 1)
                node.subtitle = node.subtitle or str(zone.get("title") or zone.get("label") or "")
                nodes.append(node)

    edges = _edges(item)
    if not edges and len(nodes) > 1:
        edges = [DrawEdge(f"E{index + 1}", nodes[index].id, nodes[index + 1].id) for index in range(len(nodes) - 1)]
    return nodes, edges


def _edges(item: IllustrationItem) -> list[DrawEdge]:
    raw_edges = item.data.get("edges") or item.data.get("flows") or []
    edges: list[DrawEdge] = []
    for index, edge in enumerate(raw_edges, start=1):
        source = str(edge.get("from") or edge.get("source") or "")
        target = str(edge.get("to") or edge.get("target") or "")
        if source and target:
            edges.append(DrawEdge(
                id=f"E{index}",
                source=_xml_id(source),
                target=_xml_id(target),
                label=str(edge.get("label") or edge.get("title") or ""),
                relation=str(edge.get("relation") or ""),
            ))
    return edges


def _node(value: Any, index: int) -> DrawNode:
    if isinstance(value, dict):
        raw = dict(value)
    else:
        raw = {"title": str(value)}
    title = str(raw.get("title") or raw.get("label") or raw.get("name") or f"节点{index}")
    subtitle = str(raw.get("subtitle") or raw.get("description") or raw.get("desc") or "")
    node_id = _xml_id(str(raw.get("id") or f"N{index}"))
    return DrawNode(node_id, title, subtitle, _infer_kind(title, subtitle, raw))


def _ordered_nodes(nodes: list[DrawNode], preferred: list[str]) -> list[DrawNode]:
    by_id = {node.id: node for node in nodes}
    ordered = [by_id[item] for item in preferred if item in by_id]
    ordered.extend(node for node in nodes if node not in ordered)
    return ordered


def _infer_kind(title: str, subtitle: str, raw: dict[str, Any]) -> str:
    text = f"{title} {subtitle} {raw.get('kind', '')} {raw.get('type', '')}".lower()
    if _has_any(text, ["数据库", "db", "data", "仓库", "缓存", "redis", "mysql", "存储"]):
        return "database"
    if _has_any(text, ["mq", "queue", "队列", "消息", "bus"]):
        return "queue"
    if _has_any(text, ["gateway", "网关", "waf", "lb", "负载"]):
        return "gateway"
    if _has_any(text, ["外部", "third", "目标平台", "第三方"]):
        return "external"
    if _has_any(text, ["判断", "分级", "审核", "decision"]):
        return "decision"
    return "service"


def _add_header(root: ET.Element, plan: DrawPlan) -> None:
    ET.SubElement(root, "mxCell", {
        "id": "header_bg",
        "value": "",
        "style": "rounded=1;whiteSpace=wrap;html=1;arcSize=6;fillColor=#0f2f57;strokeColor=#0f2f57;shadow=0;",
        "vertex": "1",
        "parent": "1",
    }).append(_geometry(36, 26, plan.width - 72, 76))
    ET.SubElement(root, "mxCell", {
        "id": "title",
        "value": _cell_text(plan.title, plan.subtitle),
        "style": "text;html=1;strokeColor=none;fillColor=none;fontSize=24;fontStyle=1;fontColor=#ffffff;align=left;verticalAlign=middle;spacingLeft=16;",
        "vertex": "1",
        "parent": "1",
    }).append(_geometry(48, 34, plan.width - 120, 60))


def _container_style(container: DrawContainer) -> str:
    palette = _palette(container.color_index)
    if container.kind == "box":
        return (
            "rounded=1;whiteSpace=wrap;html=1;container=1;pointerEvents=0;arcSize=4;"
            f"fillColor={palette['container_fill']};strokeColor={palette['stroke']};"
            "fontStyle=1;fontSize=14;fontColor=#1e3a5f;align=left;verticalAlign=top;spacingLeft=12;spacingTop=8;dashed=1;"
        )
    return (
        "swimlane;whiteSpace=wrap;html=1;startSize=34;container=1;recursiveResize=0;collapsible=0;"
        f"fillColor={palette['container_fill']};strokeColor={palette['stroke']};"
        f"swimlaneFillColor={palette['header_fill']};fontColor=#1e3a5f;fontStyle=1;fontSize=14;"
    )


def _node_style(node: DrawNode, index: int) -> str:
    palette = _palette(index - 1)
    base = "whiteSpace=wrap;html=1;fontSize=13;fontColor=#1f3654;spacing=10;shadow=0;"
    if node.kind == "database":
        return f"shape=cylinder3;boundedLbl=1;backgroundOutline=1;size=15;{base}fillColor=#e7f3ff;strokeColor=#2563eb;"
    if node.kind == "queue":
        return f"rounded=1;arcSize=14;{base}fillColor=#f8fafc;strokeColor=#64748b;"
    if node.kind == "gateway":
        return f"shape=hexagon;perimeter=hexagonPerimeter2;{base}fillColor=#fff7ed;strokeColor=#f97316;"
    if node.kind == "external":
        return f"rounded=1;arcSize=10;dashed=1;{base}fillColor=#f8fafc;strokeColor=#94a3b8;"
    if node.kind == "decision":
        return f"rhombus;{base}fillColor=#fff7ed;strokeColor=#f97316;"
    if node.kind in {"start", "end"}:
        return f"ellipse;{base}fillColor=#ecfdf5;strokeColor=#10b981;fontStyle=1;"
    return f"rounded=1;arcSize=10;{base}fillColor={palette['fill']};strokeColor={palette['stroke']};"


def _edge_style(
    plan: DrawPlan,
    edge: DrawEdge,
    source: DrawNode,
    target: DrawNode,
    out_count: int,
    in_count: int,
    index: int,
    has_label: bool,
) -> str:
    sx, sy = _absolute_center(plan, source)
    tx, ty = _absolute_center(plan, target)
    horizontal = abs(tx - sx) >= abs(ty - sy)
    exit_x = 1 if tx >= sx else 0
    entry_x = 0 if tx >= sx else 1
    exit_y = 1 if ty >= sy else 0
    entry_y = 0 if ty >= sy else 1
    if horizontal:
        spread = _spread_point(index, out_count)
        entry_spread = _spread_point(index, in_count)
        exit = f"exitX={exit_x};exitY={spread};exitDx=0;exitDy=0;"
        entry = f"entryX={entry_x};entryY={entry_spread};entryDx=0;entryDy=0;"
    else:
        spread = _spread_point(index, out_count)
        entry_spread = _spread_point(index, in_count)
        exit = f"exitX={spread};exitY={exit_y};exitDx=0;exitDy=0;"
        entry = f"entryX={entry_spread};entryY={entry_y};entryDx=0;entryDy=0;"
    dashed = "dashed=1;" if edge.relation in {"data", "async", "backup"} else ""
    return (
        "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;"
        f"{exit}{entry}{dashed}strokeColor=#2563eb;strokeWidth=2;fontColor=#334155;fontSize=11;"
        f"endArrow=block;endFill=1;{'labelBackgroundColor=#f8fafc;labelBorderColor=#cbd5e1;' if has_label else ''}"
    )


def _edge_waypoints(plan: DrawPlan, source: DrawNode, target: DrawNode) -> list[tuple[int, int]]:
    sx, sy = _absolute_center(plan, source)
    tx, ty = _absolute_center(plan, target)
    if abs(tx - sx) < 80 or abs(ty - sy) < 80:
        return []
    if abs(tx - sx) >= abs(ty - sy):
        mid_x = _snap((sx + tx) / 2)
        return [(mid_x, sy), (mid_x, ty)]
    mid_y = _snap((sy + ty) / 2)
    return [(sx, mid_y), (tx, mid_y)]


def _edge_counts(edges: list[DrawEdge]) -> tuple[dict[str, int], dict[str, int]]:
    incoming: dict[str, int] = {}
    outgoing: dict[str, int] = {}
    for edge in edges:
        incoming[edge.target] = incoming.get(edge.target, 0) + 1
        outgoing[edge.source] = outgoing.get(edge.source, 0) + 1
    return incoming, outgoing


def _label_counts(edges: list[DrawEdge]) -> dict[str, int]:
    counts: dict[str, int] = {}
    for edge in edges:
        label = edge.label.strip()
        if label:
            counts[label] = counts.get(label, 0) + 1
    return counts


def _edge_label(edge: DrawEdge, label_counts: dict[str, int], index: int, edge_count: int) -> str:
    label = _compact_text(edge.label, 8)
    if not label:
        return ""
    if label in GENERIC_EDGE_LABELS:
        return ""
    if label_counts.get(label, 0) > 1 and not _looks_like_protocol(label):
        return ""
    if edge_count > 12 and index % 2 == 0 and not _looks_like_protocol(label):
        return ""
    return label


def _looks_like_protocol(label: str) -> bool:
    return bool(re.fullmatch(r"[A-Z0-9/._-]{2,12}", label))


def _spread_point(index: int, count: int) -> float:
    if count <= 1:
        return 0.5
    slots = [0.28, 0.5, 0.72, 0.18, 0.82]
    return slots[(index - 1) % len(slots)]


def _absolute_center(plan: DrawPlan, node: DrawNode) -> tuple[int, int]:
    x, y = node.x, node.y
    container = plan.container_by_id(node.parent)
    if container:
        x += container.x
        y += container.y
    return (x + node.width // 2, y + node.height // 2)


def _node_by_id(plan: DrawPlan, node_id: str) -> DrawNode | None:
    return next((node for node in plan.nodes if node.id == node_id), None)


def _cell_text(title: Any, subtitle: Any = "") -> str:
    title_text = _escape_label(str(title or ""))
    subtitle_text = _escape_label(str(subtitle or ""))
    if subtitle_text:
        return f"<b>{title_text}</b><br><font style=\"font-size: 11px\">{subtitle_text}</font>"
    return title_text


def _escape_label(value: str) -> str:
    return value.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\n", "&#xa;")


def _geometry(x: int | float, y: int | float, width: int | float, height: int | float) -> ET.Element:
    return ET.Element("mxGeometry", {
        "x": str(_snap(x)),
        "y": str(_snap(y)),
        "width": str(_snap(width)),
        "height": str(_snap(height)),
        "as": "geometry",
    })


def _snap(value: int | float) -> int:
    return int(round(float(value) / 10) * 10)


def _xml_id(value: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9_-]+", "_", value).strip("_")
    if not cleaned or not re.match(r"^[A-Za-z_]", cleaned):
        cleaned = f"N_{cleaned or 'node'}"
    return cleaned


def _safe_name(value: str) -> str:
    cleaned = "".join("_" if char in '<>:"/\\|?* ' else char for char in str(value))
    return cleaned.strip("._") or "diagram"


def _palette(index: int) -> dict[str, str]:
    palettes = [
        {"fill": "#eaf3ff", "stroke": "#2563eb", "container_fill": "#f3f8ff", "header_fill": "#dbeafe"},
        {"fill": "#eef6ff", "stroke": "#1d4ed8", "container_fill": "#f5f9ff", "header_fill": "#e0f2fe"},
        {"fill": "#f8fafc", "stroke": "#64748b", "container_fill": "#f8fbff", "header_fill": "#e2e8f0"},
        {"fill": "#ecfeff", "stroke": "#0891b2", "container_fill": "#f0fdff", "header_fill": "#cffafe"},
        {"fill": "#eff6ff", "stroke": "#3b82f6", "container_fill": "#f6faff", "header_fill": "#dbeafe"},
        {"fill": "#f1f5f9", "stroke": "#475569", "container_fill": "#f8fafc", "header_fill": "#e2e8f0"},
    ]
    return palettes[index % len(palettes)]


def _has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword.lower() in text for keyword in keywords)


def _find_drawio_command() -> list[str] | None:
    env_exe = os.environ.get("DRAWIO_EXE")
    if env_exe and Path(env_exe).exists():
        return [env_exe]

    repo_root = Path(__file__).resolve().parents[4]
    wrapper = repo_root / "tools" / "drawio.ps1"
    if wrapper.exists():
        return ["powershell", "-ExecutionPolicy", "Bypass", "-File", str(wrapper)]

    local_exe = repo_root / ".tools" / "drawio-msi" / "draw.io" / "draw.io.exe"
    if local_exe.exists():
        return [str(local_exe)]
    return None


def _export(command: list[str], source: Path, output: Path, fmt: str) -> bool:
    args = [*command, "--export", "--format", fmt]
    if fmt == "png":
        args.extend(["--width", "2000"])
    args.extend(["--output", str(output), str(source)])
    try:
        subprocess.run(args, check=False, capture_output=True, text=True, timeout=90)
    except Exception:
        return False
    return _wait_for_output(output)


def _wait_for_output(path: Path) -> bool:
    import time

    deadline = time.time() + 20
    while time.time() < deadline:
        if path.exists() and path.stat().st_size > 0:
            return True
        time.sleep(0.25)
    return False


def _validate_drawio_xml(xml: str) -> list[str]:
    try:
        root = ET.fromstring(xml)
    except ET.ParseError as exc:
        return [f"Draw.io XML 解析失败: {exc}"]
    warnings: list[str] = []
    for diagram in root.findall("diagram") or [root]:
        model = diagram.find("mxGraphModel")
        cells = model.find("root").findall("mxCell") if model is not None and model.find("root") is not None else []
        ids: dict[str, ET.Element] = {}
        parents = {cell.get("parent") for cell in cells}
        for cell in cells:
            cid = cell.get("id", "")
            if cid in ids:
                warnings.append(f"Draw.io lint: duplicate id {cid}")
            ids[cid] = cell
        for cell in cells:
            cid = cell.get("id", "")
            parent = cell.get("parent")
            if parent and parent not in ids:
                warnings.append(f"Draw.io lint: cell {cid} parent {parent} 不存在")
            for end in ("source", "target"):
                ref = cell.get(end)
                if ref and ref not in ids:
                    warnings.append(f"Draw.io lint: edge {cid} {end}={ref} 不存在")
            if cell.get("vertex") == "1":
                rect = _rect(cell)
                if rect is None:
                    warnings.append(f"Draw.io lint: vertex {cid} 缺少 geometry")
                elif rect[0] < 0 or rect[1] < 0:
                    warnings.append(f"Draw.io lint: vertex {cid} 位置为负数")
        boxes = [
            (cell.get("id", ""), cell.get("parent", ""), _rect(cell))
            for cell in cells
            if cell.get("vertex") == "1"
            and cell.get("id") not in parents
            and _rect(cell)
            and not _is_visual_overlay(cell)
        ]
        for idx, current in enumerate(boxes):
            for other in boxes[idx + 1:]:
                if current[1] == other[1] and _overlap(current[2], other[2]):
                    warnings.append(f"Draw.io lint: vertices {current[0]} and {other[0]} overlap")
    return warnings


def _rect(cell: ET.Element) -> tuple[float, float, float, float] | None:
    geometry = cell.find("mxGeometry")
    if geometry is None:
        return None
    try:
        return (
            float(geometry.get("x", "0")),
            float(geometry.get("y", "0")),
            float(geometry.get("width", "0")),
            float(geometry.get("height", "0")),
        )
    except ValueError:
        return None


def _is_visual_overlay(cell: ET.Element) -> bool:
    style = cell.get("style", "")
    cid = cell.get("id", "")
    return (
        cid in {"header_bg", "title"}
        or style.startswith("text;")
        or "pointerEvents=0" in style
        or "container=1" in style
    )


def _overlap(a: tuple[float, float, float, float] | None, b: tuple[float, float, float, float] | None) -> bool:
    if a is None or b is None:
        return False
    ax, ay, aw, ah = a
    bx, by, bw, bh = b
    return ax < bx + bw and bx < ax + aw and ay < by + bh and by < ay + ah
