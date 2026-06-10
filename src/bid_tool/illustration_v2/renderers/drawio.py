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
from hashlib import sha1
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
    color_role: str = ""


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
    color_role: str = ""


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
            warnings.extend(_quality_warnings(item))

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
        points = _edge_waypoints(plan, source, target, edge)
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
    if item.type in {"architecture.layered_explainer", "methodology.layered_stack"}:
        return _plan_layered_explainer(title, subtitle, item)
    if item.type in {"architecture.deployment", "network.topology"} and item.data.get("zones"):
        return _plan_zones(title, subtitle, item)
    if item.type == "integration.interface_map":
        return _plan_interface(title, subtitle, item)
    if item.type in {"process.interaction_map", "process.system_interaction"} or (
        item.data.get("sections") and (item.data.get("primary_flow") or item.data.get("support_flows"))
    ):
        return _plan_process_interaction(title, subtitle, item)
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


def _plan_layered_explainer(title: str, subtitle: str, item: IllustrationItem) -> DrawPlan:
    levels = item.data.get("levels") or item.data.get("layers") or []
    if not isinstance(levels, list) or not levels:
        return _plan_general(title, subtitle, item)

    width = 1240
    left = 60
    top_y = 126
    row_h = 78
    gap_y = 8
    badge_w = 82
    card_x = left + badge_w + 18
    card_w = 410
    icon_size = 72
    icon_x = card_x + card_w - 34
    note_x = icon_x + icon_size + 88
    note_w = width - note_x - 70

    nodes: list[DrawNode] = []
    edges: list[DrawEdge] = []
    normalized_levels = [_normalize_level(level, index) for index, level in enumerate(levels, start=1)]

    for row_idx, level in enumerate(normalized_levels, start=1):
        y = top_y + (row_idx - 1) * (row_h + gap_y)
        role = _layer_explainer_role(level, row_idx, len(normalized_levels))
        badge_id = _xml_id(f"{level['id']}_badge")
        card_id = _xml_id(f"{level['id']}_card")
        icon_id = _xml_id(f"{level['id']}_icon")
        note_id = _xml_id(f"{level['id']}_note")

        nodes.append(DrawNode(
            badge_id,
            str(level["number"]),
            kind="layer_badge",
            x=left,
            y=y,
            width=badge_w,
            height=row_h,
            color_role=role,
        ))
        nodes.append(DrawNode(
            card_id,
            str(level["title"]),
            str(level.get("subtitle") or ""),
            kind="layer_card",
            x=card_x,
            y=y + 3,
            width=card_w,
            height=row_h - 6,
            color_role=role,
        ))
        nodes.append(DrawNode(
            icon_id,
            _layer_icon_text(level),
            kind="layer_icon",
            x=icon_x,
            y=y + 3,
            width=icon_size,
            height=icon_size,
            color_role=role,
        ))
        nodes.append(DrawNode(
            note_id,
            str(level.get("description") or level.get("desc") or ""),
            kind="layer_note",
            x=note_x,
            y=y + 9,
            width=note_w,
            height=row_h - 18,
            color_role=role,
        ))
        edges.append(DrawEdge(
            id=f"EDGE_CALLOUT_{row_idx}",
            source=icon_id,
            target=note_id,
            relation="callout",
        ))

    analogy_items = item.data.get("analogies") or [
        {
            "number": level["number"],
            "title": level["title"],
            "description": level.get("analogy") or level.get("subtitle") or "",
            "color_role": _layer_explainer_role(level, idx, len(normalized_levels)),
        }
        for idx, level in enumerate(normalized_levels, start=1)
    ]
    if isinstance(analogy_items, list) and analogy_items:
        analogy_items = _sort_analogy_items(analogy_items)
        bottom_y = top_y + len(normalized_levels) * (row_h + gap_y) + 18
        bottom_h = 138
        containers = [DrawContainer(
            "C_analogy",
            str(item.data.get("analogyTitle") or "通俗理解 · 一句话类比"),
            38,
            bottom_y,
            width - 76,
            bottom_h,
            0,
            "box",
            "legend",
        )]
        cols = min(7, len(analogy_items))
        card_wide = (width - 112 - (cols - 1) * 10) // cols
        for idx, raw in enumerate(analogy_items, start=1):
            if not isinstance(raw, dict):
                raw = {"title": str(raw)}
            col = (idx - 1) % cols
            row = (idx - 1) // cols
            role = str(raw.get("color_role") or _layer_explainer_role(normalized_levels[min(idx - 1, len(normalized_levels) - 1)], idx, len(normalized_levels)))
            nodes.append(DrawNode(
                _xml_id(f"analogy_{idx}"),
                f"{raw.get('number') or idx}  {raw.get('title') or ''}",
                str(raw.get("description") or raw.get("desc") or raw.get("analogy") or ""),
                kind="analogy_item",
                parent="C_analogy",
                x=24 + col * (card_wide + 10),
                y=42 + row * 78,
                width=card_wide,
                height=66,
                color_role=role,
            ))
        height = bottom_y + bottom_h + 46
        return DrawPlan(title, subtitle, width, height, nodes, edges, containers)

    return DrawPlan(title, subtitle, width, top_y + len(normalized_levels) * (row_h + gap_y) + 52, nodes, edges, [])


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


def _plan_process_interaction(title: str, subtitle: str, item: IllustrationItem) -> DrawPlan:
    sections = item.data.get("sections", [])
    if not isinstance(sections, list) or not sections:
        return _plan_general(title, subtitle, item)

    section_count = len(sections)
    legend_entries = _legend_entries(item)
    bottom_legend = len(legend_entries) > 5
    legend_w = 280 if legend_entries and not bottom_legend else 0
    width = max(1280, 120 + section_count * 240 + legend_w)
    left, gap_x, top_y = 56, 22, 130
    available_w = width - left * 2 - legend_w - (28 if legend_w else 0) - gap_x * max(0, section_count - 1)
    container_w = max(210, min(270, available_w // max(section_count, 1)))
    max_steps = max([len(section.get("steps", [])) for section in sections if isinstance(section, dict)] or [1])
    container_h = max(292, 76 + max_steps * 76)

    nodes: list[DrawNode] = []
    containers: list[DrawContainer] = []
    first_by_section: dict[str, str] = {}
    last_by_section: dict[str, str] = {}

    for section_idx, section in enumerate(sections, start=1):
        if not isinstance(section, dict):
            continue
        section_id = str(section.get("id") or f"S{section_idx}")
        cid = _xml_id(f"C_{section_id}")
        x = left + (section_idx - 1) * (container_w + gap_x)
        title_text = str(section.get("title") or section.get("label") or f"工艺段 {section_idx}")
        subtitle_text = str(section.get("subtitle") or "")
        container_title = title_text if not subtitle_text else f"{title_text}\n{subtitle_text}"
        containers.append(DrawContainer(
            cid,
            container_title,
            x,
            top_y,
            container_w,
            container_h,
            section_idx - 1,
            color_role=_process_section_role(section, section_idx),
        ))

        steps = section.get("steps", [])
        if not isinstance(steps, list) or not steps:
            steps = [{"id": f"{section_id}_summary", "title": title_text, "description": subtitle_text}]
        for step_idx, step in enumerate(steps, start=1):
            node = _node(step, len(nodes) + 1)
            node.parent = cid
            node.group = cid
            node.x = 24
            node.y = 46 + (step_idx - 1) * 72
            node.width = container_w - 48
            node.height = 58
            node.subtitle = node.subtitle or str(step.get("output") or step.get("interaction_type") or "")
            node.kind = _process_step_kind(step)
            nodes.append(node)
            first_by_section.setdefault(section_id, node.id)
            last_by_section[section_id] = node.id

    edges = _interaction_edges(item, first_by_section, last_by_section)

    legend_h = 0
    if legend_entries and bottom_legend:
        legend_x = left
        legend_y = top_y + container_h + 20
        legend_wide = width - left * 2
        legend_cols = 4 if len(legend_entries) >= 6 else 3
        legend_rows = math.ceil(len(legend_entries) / legend_cols)
        legend_h = max(126, 48 + legend_rows * 46)
        legend_id = "C_legend"
        containers.append(DrawContainer(legend_id, "图例与术语", legend_x, legend_y, legend_wide, legend_h, section_count, "box", "legend"))
        card_w = max(210, (legend_wide - 44 - (legend_cols - 1) * 18) // legend_cols)
        for index, entry in enumerate(legend_entries, start=1):
            node = _node(entry, len(nodes) + 1)
            node.parent = legend_id
            col = (index - 1) % legend_cols
            row = (index - 1) // legend_cols
            node.x = 22 + col * (card_w + 18)
            node.y = 38 + row * 44
            node.width = card_w
            node.height = 36
            nodes.append(node)
    elif legend_entries:
        legend_x = left + section_count * (container_w + gap_x) + 6
        legend_h = max(240, 70 + len(legend_entries) * 58)
        legend_id = "C_legend"
        containers.append(DrawContainer(legend_id, "图例与术语", legend_x, top_y, legend_w, legend_h, section_count, "box", "legend"))
        for index, entry in enumerate(legend_entries, start=1):
            node = _node(entry, len(nodes) + 1)
            node.parent = legend_id
            node.x = 22
            node.y = 42 + (index - 1) * 54
            node.width = legend_w - 44
            node.height = 42
            nodes.append(node)

    if bottom_legend:
        height = top_y + container_h + 20 + legend_h + 44
    else:
        height = top_y + max(container_h, legend_h) + 80
    return DrawPlan(title, subtitle, width, height, nodes, edges, containers)


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
        if node.kind == "layer_note":
            node.title = _compact_text(node.title, 46)
            node.subtitle = ""
        elif node.kind == "analogy_item":
            node.title = _compact_text(node.title, 18)
            node.subtitle = _compact_text(node.subtitle, 16)
        elif node.kind in {"layer_card", "layer_icon", "layer_badge"}:
            node.title = _compact_text(node.title, 18)
            node.subtitle = _normalize_subtitle(node.subtitle, parent_title)
        else:
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


def _sort_analogy_items(items: list[Any]) -> list[Any]:
    def key(value: Any) -> tuple[int, int]:
        if not isinstance(value, dict):
            return (1, 0)
        raw = value.get("number") or value.get("level") or 0
        try:
            return (0, int(raw))
        except (TypeError, ValueError):
            return (1, 0)

    return sorted(items, key=key)


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
                id=f"EDGE_{index}",
                source=_xml_id(source),
                target=_xml_id(target),
                label=str(edge.get("label") or edge.get("title") or ""),
                relation=str(edge.get("relation") or ""),
            ))
    return edges


def _interaction_edges(
    item: IllustrationItem,
    first_by_section: dict[str, str],
    last_by_section: dict[str, str],
) -> list[DrawEdge]:
    data = item.data or {}
    edges: list[DrawEdge] = []
    edge_index = 1

    for flow in data.get("primary_flow") or []:
        edge = _flow_edge(flow, edge_index, first_by_section, last_by_section, default_relation="primary")
        if edge:
            edges.append(edge)
            edge_index += 1

    for flow in data.get("support_flows") or []:
        edge = _flow_edge(flow, edge_index, first_by_section, last_by_section, default_relation="support")
        if edge:
            edges.append(edge)
            edge_index += 1

    if not edges:
        edges = _edges(item)

    return edges


def _flow_edge(
    raw: Any,
    index: int,
    first_by_section: dict[str, str],
    last_by_section: dict[str, str],
    *,
    default_relation: str,
) -> DrawEdge | None:
    if not isinstance(raw, dict):
        return None
    source = str(raw.get("from") or raw.get("source") or "")
    target = str(raw.get("to") or raw.get("target") or "")
    if not source or not target:
        return None
    source_id = _resolve_interaction_endpoint(source, last_by_section, first_by_section)
    target_id = _resolve_interaction_endpoint(target, first_by_section, last_by_section)
    return DrawEdge(
        id=f"EDGE_{index}",
        source=source_id,
        target=target_id,
        label=str(raw.get("label") or raw.get("title") or ""),
        relation=str(raw.get("relation") or raw.get("type") or default_relation),
    )


def _resolve_interaction_endpoint(value: str, preferred: dict[str, str], fallback: dict[str, str]) -> str:
    if value in preferred:
        return preferred[value]
    if value in fallback:
        return fallback[value]
    return _xml_id(value)


def _legend_entries(item: IllustrationItem) -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for raw in item.data.get("interaction_types") or []:
        if isinstance(raw, dict):
            entries.append({
                "id": raw.get("id") or raw.get("title") or raw.get("label") or f"legend_{len(entries) + 1}",
                "title": raw.get("title") or raw.get("label") or raw.get("id") or "交互点",
                "description": raw.get("description") or raw.get("desc") or raw.get("meaning") or "",
                "kind": "legend",
            })
    legend = item.data.get("legend")
    if isinstance(legend, list):
        for raw in legend:
            if isinstance(raw, dict):
                entries.append({
                    "id": raw.get("id") or raw.get("title") or raw.get("label") or f"legend_{len(entries) + 1}",
                    "title": raw.get("title") or raw.get("label") or "图例",
                    "description": raw.get("description") or raw.get("desc") or "",
                    "kind": "legend",
                })
            else:
                entries.append({"id": f"legend_{len(entries) + 1}", "title": str(raw), "kind": "legend"})
    glossary = item.data.get("glossary")
    if isinstance(glossary, list):
        for raw in glossary:
            if isinstance(raw, dict):
                entries.append({
                    "id": raw.get("term") or raw.get("id") or f"term_{len(entries) + 1}",
                    "title": raw.get("term") or raw.get("title") or "术语",
                    "description": raw.get("definition") or raw.get("description") or "",
                    "kind": "legend",
                })
    return entries[:8]


def _node(value: Any, index: int) -> DrawNode:
    if isinstance(value, dict):
        raw = dict(value)
    else:
        raw = {"title": str(value)}
    title = str(raw.get("title") or raw.get("label") or raw.get("name") or f"节点{index}")
    subtitle = str(raw.get("subtitle") or raw.get("description") or raw.get("desc") or "")
    node_id = _xml_id(str(raw.get("id") or f"N{index}"))
    return DrawNode(node_id, title, subtitle, _infer_kind(title, subtitle, raw))


def _process_section_role(section: dict[str, Any], index: int) -> str:
    role = str(section.get("color_role") or section.get("role") or "").strip().lower()
    if role:
        return role
    title = str(section.get("title") or section.get("label") or "")
    if _has_any(title, ["上线", "准备", "计划"]):
        return "process_planning"
    if _has_any(title, ["装配", "工位", "生产"]):
        return "process_assembly"
    if _has_any(title, ["电检", "标定", "检测"]):
        return "process_validation"
    if _has_any(title, ["质量", "返修", "问题"]):
        return "process_quality"
    if _has_any(title, ["下线", "入库", "交付"]):
        return "process_delivery"
    roles = ["process_planning", "process_assembly", "process_validation", "process_quality", "process_delivery"]
    return roles[(index - 1) % len(roles)]


def _process_step_kind(step: Any) -> str:
    if not isinstance(step, dict):
        return "service"
    text = " ".join(
        str(step.get(key) or "")
        for key in ("title", "description", "desc", "interaction_type", "output")
    )
    if _has_any(text, ["QMS", "质量", "缺陷", "返修", "放行"]):
        return "system_qms"
    if _has_any(text, ["WMS", "物料", "齐套", "配送", "入库"]):
        return "system_wms"
    if _has_any(text, ["刷写", "电检", "扭矩", "设备", "ECU"]):
        return "system_device"
    if _has_any(text, ["MES", "工单", "排产", "工艺参数"]):
        return "system_mes"
    if _has_any(text, ["VIN", "扫码"]):
        return "system_id"
    return "service"


def _normalize_level(level: Any, index: int) -> dict[str, Any]:
    if isinstance(level, dict):
        raw = dict(level)
    else:
        raw = {"title": str(level)}
    number = raw.get("number") or raw.get("level") or index
    title = raw.get("title") or raw.get("label") or raw.get("name") or f"Layer {number}"
    raw["number"] = number
    raw["title"] = title
    raw["id"] = str(raw.get("id") or f"L{number}_{title}")
    return raw


def _layer_explainer_role(level: dict[str, Any], index: int, total: int) -> str:
    role = str(level.get("color_role") or level.get("role") or "").strip().lower()
    if role:
        return role
    title = str(level.get("title") or "")
    if _has_any(title, ["Token", "提示", "Prompt", "Context", "上下文"]):
        return "layer_blue"
    if _has_any(title, ["Agent", "Harness"]):
        return "layer_gold"
    if _has_any(title, ["MCP", "Skills", "技能"]):
        return "layer_red"
    midpoint = max(1, total // 2)
    if index <= midpoint:
        return "layer_red"
    if index == midpoint + 1:
        return "layer_gold"
    return "layer_blue"


def _layer_icon_text(level: dict[str, Any]) -> str:
    icon = str(level.get("icon") or "").strip()
    if icon:
        return icon[:4]
    title = str(level.get("title") or "")
    if _has_any(title, ["Skills", "技能"]):
        return "SK"
    if _has_any(title, ["MCP"]):
        return "IO"
    if _has_any(title, ["Harness"]):
        return "HF"
    if _has_any(title, ["Agent"]):
        return "AI"
    if _has_any(title, ["Context", "上下文"]):
        return "CTX"
    if _has_any(title, ["Prompt", "提示"]):
        return "PT"
    if _has_any(title, ["Token"]):
        return "TK"
    return str(level.get("number") or "")[:3]


def _ordered_nodes(nodes: list[DrawNode], preferred: list[str]) -> list[DrawNode]:
    by_id = {node.id: node for node in nodes}
    ordered = [by_id[item] for item in preferred if item in by_id]
    ordered.extend(node for node in nodes if node not in ordered)
    return ordered


def _infer_kind(title: str, subtitle: str, raw: dict[str, Any]) -> str:
    text = f"{title} {subtitle} {raw.get('kind', '')} {raw.get('type', '')}".lower()
    raw_kind = str(raw.get("kind") or "").lower()
    if raw_kind in {"start", "end", "decision", "gateway", "external", "database", "queue", "legend"}:
        return raw_kind
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
    palette = _container_palette(container)
    if container.kind == "box":
        return (
            "rounded=1;whiteSpace=wrap;html=1;container=1;pointerEvents=0;arcSize=4;"
            f"fillColor={palette['container_fill']};strokeColor={palette['stroke']};"
            f"fontStyle=1;fontSize=14;fontColor={palette.get('text', '#1e3a5f')};"
            "align=left;verticalAlign=top;spacingLeft=12;spacingTop=8;dashed=1;"
        )
    return (
        "swimlane;whiteSpace=wrap;html=1;startSize=34;container=1;recursiveResize=0;collapsible=0;"
        f"fillColor={palette['container_fill']};strokeColor={palette['stroke']};"
        f"swimlaneFillColor={palette['header_fill']};fontColor={palette.get('text', '#1e3a5f')};fontStyle=1;fontSize=14;"
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
    if node.kind == "legend":
        return f"rounded=1;arcSize=8;{base}fillColor=#ffffff;strokeColor=#cbd5e1;fontSize=12;"
    if node.kind == "layer_badge":
        palette = _layer_palette(node.color_role)
        return (
            "rounded=1;arcSize=12;whiteSpace=wrap;html=1;shadow=1;"
            f"fillColor={palette['strong']};strokeColor={palette['stroke']};"
            "fontColor=#ffffff;fontStyle=1;fontSize=30;align=center;verticalAlign=middle;"
        )
    if node.kind == "layer_card":
        palette = _layer_palette(node.color_role)
        return (
            "rounded=1;arcSize=10;whiteSpace=wrap;html=1;shadow=1;"
            f"fillColor=#ffffff;strokeColor={palette['light_stroke']};"
            f"fontColor={palette['text']};fontSize=18;fontStyle=1;spacing=12;align=left;verticalAlign=middle;"
        )
    if node.kind == "layer_icon":
        palette = _layer_palette(node.color_role)
        return (
            "ellipse;whiteSpace=wrap;html=1;shadow=1;"
            f"fillColor={palette['pale']};strokeColor={palette['stroke']};"
            f"fontColor={palette['strong']};fontStyle=1;fontSize=20;align=center;verticalAlign=middle;"
        )
    if node.kind == "layer_note":
        palette = _layer_palette(node.color_role)
        return (
            "rounded=1;arcSize=8;whiteSpace=wrap;html=1;"
            f"fillColor=#ffffff;strokeColor={palette['light_stroke']};"
            "fontColor=#1f2937;fontSize=13;spacing=12;align=left;verticalAlign=middle;"
        )
    if node.kind == "analogy_item":
        palette = _layer_palette(node.color_role)
        return (
            "rounded=1;arcSize=6;whiteSpace=wrap;html=1;"
            f"fillColor={palette['pale']};strokeColor={palette['light_stroke']};"
            f"fontColor={palette['text']};fontSize=12;spacing=8;"
        )
    if node.kind == "system_mes":
        return f"rounded=1;arcSize=8;{base}fillColor=#eef6ff;strokeColor=#2563eb;"
    if node.kind == "system_wms":
        return f"rounded=1;arcSize=8;{base}fillColor=#ecfdf5;strokeColor=#0f766e;"
    if node.kind == "system_qms":
        return f"rounded=1;arcSize=8;{base}fillColor=#fff7ed;strokeColor=#b45309;"
    if node.kind == "system_device":
        return f"rounded=1;arcSize=8;{base}fillColor=#eef2ff;strokeColor=#4f46e5;"
    if node.kind == "system_id":
        return f"rounded=1;arcSize=8;{base}fillColor=#f8fafc;strokeColor=#64748b;"
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
    relation = edge.relation.lower()
    horizontal = abs(tx - sx) >= abs(ty - sy)
    exit_x = 1 if tx >= sx else 0
    entry_x = 0 if tx >= sx else 1
    exit_y = 1 if ty >= sy else 0
    entry_y = 0 if ty >= sy else 1
    if relation == "rework":
        exit_x = 0 if tx >= sx else 1
        entry_x = 1 if tx >= sx else 0
        exit = f"exitX={exit_x};exitY=0.5;exitDx=0;exitDy=0;"
        entry = f"entryX={entry_x};entryY=0.5;entryDx=0;entryDy=0;"
    elif relation in {"support", "auxiliary", "material"}:
        exit = "exitX=0.5;exitY=1;exitDx=0;exitDy=0;"
        entry = "entryX=0.5;entryY=1;entryDx=0;entryDy=0;"
    elif horizontal:
        spread = _spread_point(index, out_count)
        entry_spread = _spread_point(index, in_count)
        exit = f"exitX={exit_x};exitY={spread};exitDx=0;exitDy=0;"
        entry = f"entryX={entry_x};entryY={entry_spread};entryDx=0;entryDy=0;"
    else:
        spread = _spread_point(index, out_count)
        entry_spread = _spread_point(index, in_count)
        exit = f"exitX={spread};exitY={exit_y};exitDx=0;exitDy=0;"
        entry = f"entryX={entry_spread};entryY={entry_y};entryDx=0;entryDy=0;"
    dashed = "dashed=1;" if relation in {"data", "async", "backup", "support", "auxiliary", "material", "rework", "callout"} else ""
    color = _edge_color(relation, dashed=bool(dashed))
    width = "3" if relation == "primary" else "2"
    arrow = "none" if relation == "callout" else "block"
    fill = "0" if relation == "callout" else "1"
    return (
        "edgeStyle=orthogonalEdgeStyle;rounded=1;orthogonalLoop=1;jettySize=auto;html=1;"
        f"{exit}{entry}{dashed}strokeColor=#2563eb;strokeWidth=2;fontColor=#334155;fontSize=11;"
        f"endArrow={arrow};endFill={fill};{'labelBackgroundColor=#f8fafc;labelBorderColor=#cbd5e1;' if has_label else ''}"
    ).replace("strokeColor=#2563eb;strokeWidth=2;", f"strokeColor={color};strokeWidth={width};")


def _edge_color(relation: str, *, dashed: bool) -> str:
    if relation == "material":
        return "#0f766e"
    if relation == "rework":
        return "#b45309"
    if relation == "callout":
        return "#94a3b8"
    if relation in {"support", "auxiliary"}:
        return "#64748b"
    return "#64748b" if dashed else "#2563eb"


def _edge_waypoints(
    plan: DrawPlan,
    source: DrawNode,
    target: DrawNode,
    edge: DrawEdge | None = None,
) -> list[tuple[int, int]]:
    sx, sy = _absolute_center(plan, source)
    tx, ty = _absolute_center(plan, target)
    relation = (edge.relation.lower() if edge else "")
    if relation == "rework":
        return _rework_edge_waypoints(plan, source, target)
    if relation == "callout":
        sx, sy = _absolute_center(plan, source)
        tx, ty = _absolute_center(plan, target)
        mid_x = _snap((sx + tx) / 2)
        return [(mid_x, sy), (mid_x, ty)]
    if relation in {"support", "auxiliary", "material"}:
        return _secondary_edge_waypoints(plan, sx, sy, tx, ty, relation)
    if abs(tx - sx) < 80 or abs(ty - sy) < 80:
        return []
    if abs(tx - sx) >= abs(ty - sy):
        mid_x = _snap((sx + tx) / 2)
        return [(mid_x, sy), (mid_x, ty)]
    mid_y = _snap((sy + ty) / 2)
    return [(sx, mid_y), (tx, mid_y)]


def _rework_edge_waypoints(plan: DrawPlan, source: DrawNode, target: DrawNode) -> list[tuple[int, int]]:
    sx, sy = _absolute_center(plan, source)
    tx, ty = _absolute_center(plan, target)
    section_top = min([container.y for container in plan.containers if container.id != "C_legend"] or [130])
    corridor_y = _snap(max(108, section_top - 18))
    source_container = plan.container_by_id(source.parent)
    target_container = plan.container_by_id(target.parent)

    if tx < sx:
        source_lane = _snap((source_container.x + source_container.width if source_container else sx + source.width // 2) + 18)
        target_lane = _snap((target_container.x if target_container else tx - target.width // 2) - 18)
    else:
        source_lane = _snap((source_container.x if source_container else sx - source.width // 2) - 18)
        target_lane = _snap((target_container.x + target_container.width if target_container else tx + target.width // 2) + 18)

    return [
        (source_lane, sy),
        (source_lane, corridor_y),
        (target_lane, corridor_y),
        (target_lane, ty),
    ]


def _secondary_edge_waypoints(
    plan: DrawPlan,
    sx: int,
    sy: int,
    tx: int,
    ty: int,
    relation: str,
) -> list[tuple[int, int]]:
    if relation == "rework" or tx < sx:
        section_top = min(
            [container.y for container in plan.containers if container.id != "C_legend"] or [130]
        )
        corridor_y = max(108, section_top - 18)
    else:
        corridor_y = min(plan.height - 80, max(sy, ty) + 86)
    corridor_y = _snap(corridor_y)
    if abs(tx - sx) < 80:
        corridor_x = _snap(max(sx, tx) + 80)
        return [(corridor_x, sy), (corridor_x, corridor_y), (tx, corridor_y)]
    return [(sx, corridor_y), (tx, corridor_y)]


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
    if not cleaned:
        cleaned = f"N_{sha1(value.encode('utf-8')).hexdigest()[:8]}"
    elif not re.match(r"^[A-Za-z_]", cleaned):
        cleaned = f"N_{cleaned}"
    return cleaned


def _safe_name(value: str) -> str:
    cleaned = "".join("_" if char in '<>:"/\\|?* ' else char for char in str(value))
    return cleaned.strip("._") or "diagram"


def _container_palette(container: DrawContainer) -> dict[str, str]:
    role_palettes = {
        "process_planning": {
            "fill": "#eef6ff",
            "stroke": "#2563eb",
            "container_fill": "#f4f8ff",
            "header_fill": "#dbeafe",
            "text": "#17345f",
        },
        "process_assembly": {
            "fill": "#ecfdf5",
            "stroke": "#0f766e",
            "container_fill": "#f2fbf8",
            "header_fill": "#ccfbf1",
            "text": "#164e63",
        },
        "process_validation": {
            "fill": "#f8fafc",
            "stroke": "#64748b",
            "container_fill": "#f7f9fc",
            "header_fill": "#e2e8f0",
            "text": "#334155",
        },
        "process_quality": {
            "fill": "#fff7ed",
            "stroke": "#b45309",
            "container_fill": "#fffaf2",
            "header_fill": "#fed7aa",
            "text": "#713f12",
        },
        "process_delivery": {
            "fill": "#eef2ff",
            "stroke": "#4f46e5",
            "container_fill": "#f5f6ff",
            "header_fill": "#e0e7ff",
            "text": "#312e81",
        },
        "legend": {
            "fill": "#ffffff",
            "stroke": "#64748b",
            "container_fill": "#f8fafc",
            "header_fill": "#e2e8f0",
            "text": "#1e293b",
        },
    }
    return role_palettes.get(container.color_role, _palette(container.color_index))


def _layer_palette(role: str) -> dict[str, str]:
    palettes = {
        "layer_red": {
            "strong": "#dc2626",
            "stroke": "#b91c1c",
            "light_stroke": "#fecaca",
            "pale": "#fff1f2",
            "text": "#991b1b",
        },
        "layer_orange": {
            "strong": "#ea580c",
            "stroke": "#c2410c",
            "light_stroke": "#fed7aa",
            "pale": "#fff7ed",
            "text": "#9a3412",
        },
        "layer_gold": {
            "strong": "#d97706",
            "stroke": "#b45309",
            "light_stroke": "#fde68a",
            "pale": "#fffbeb",
            "text": "#92400e",
        },
        "layer_blue": {
            "strong": "#0f5fb8",
            "stroke": "#1d4ed8",
            "light_stroke": "#bfdbfe",
            "pale": "#eff6ff",
            "text": "#1e3a8a",
        },
    }
    return palettes.get(role, palettes["layer_blue"])


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


def _quality_warnings(item: IllustrationItem) -> list[str]:
    warnings: list[str] = []
    if item.type not in {"process.interaction_map", "process.system_interaction"}:
        return warnings

    sections = item.data.get("sections") or []
    primary = item.data.get("primary_flow") or []
    support = item.data.get("support_flows") or []
    step_count = sum(len(section.get("steps", [])) for section in sections if isinstance(section, dict))
    edge_count = len(primary) + len(support)

    if not primary:
        warnings.append("quality: process interaction map 缺少 primary_flow，主路径不可验证")
    if item.visual.get("legend") and not _legend_entries(item):
        warnings.append("quality: 已要求图例但缺少 legend / interaction_types")
    if step_count > 24:
        warnings.append(f"quality: step_count={step_count} 超过 24，建议拆图或摘要")
    if edge_count > 14:
        warnings.append(f"quality: edge_count={edge_count} 超过 14，箭头复杂度偏高")
    if len(support) > 6:
        warnings.append(f"quality: support_flow_count={len(support)} 超过 6，辅助关系应转说明区或拆图")
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
