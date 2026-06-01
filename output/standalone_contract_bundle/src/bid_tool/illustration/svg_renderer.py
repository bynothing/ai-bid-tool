# -*- coding: utf-8 -*-
r"""Document-driven SVG diagram generator for proposal documents.

The tool reads a Markdown document containing one fenced ``svg-diagrams`` JSON
block, then generates polished SVG/PNG figures and an output manifest.

Usage:
    python .\src\generate_architecture_diagram.py
    python .\src\generate_architecture_diagram.py --document .\examples\标书示例_图示需求.md --png
    python .\src\generate_architecture_diagram.py --spec .\examples\示例_主流图型描述.json --png
"""
from __future__ import annotations

import argparse
import html
import json
import math
import re
from pathlib import Path
from typing import Any

from .icons import ICONS
from .palettes import get_palette, role_for_index, select_palette_for_payload, style_from_item, triplet, use_palette
from .themes import THEMES

WIDTH = 1600

# ── Configurable layout parameters ──
# Adjust these values to tune font sizes and spacing globally.
LAYOUT = {
    # ── Font sizes (px) ──
    "title":        56,
    "subtitle":     28,
    "section":      39,
    "section_en":   23,
    "node":         38,
    "node_lg":      45,
    "desc":         28,
    "dark_node":    38,
    "note":         24,
    "edge_label":   28,

    # ── Spacing & dimensions ──
    "header_h":         116,
    "header_accent_y":  114,
    "title_x":          50,
    "title_y":          57,
    "subtitle_x":       52,
    "subtitle_y":       92,

    "note_bar_h":       60,
    "note_bar_text_y":  38,

    "label_w":          255,
    "actor_h":          165,

    # item_card internals
    "card_pad_v":       13,
    "card_title_lh":    43,
    "card_desc_lh":     34,
    "card_text_gap":    4,
    "card_icon_size":   38,
    "card_icon_x":      16,
    "card_text_x_icon": 64,
    "card_text_x_no_icon_margin": 38,
    "card_chars_div":   36,
    "card_title_baseline": 34,
    "card_desc_baseline":  27,

    # Layered architecture
    "layer_base":       56,
    "layer_per_row":    124,
    "layer_gap":        14,
    "layer_extra":      18,
    "layer_row_h":      144,
    "layer_dark_card_h": 116,
    "layer_dark_text_lh": 43,
    "layer_dark_baseline": 34,
    "layer_dark_icon_size": 38,
    "layer_dark_icon_x": 18,
    "layer_dark_icon_y_offset": 38,
    "layer_dark_text_x": 72,
    "layer_dark_chars_div": 36,
    "layer_dark_icon_margin": 64,

    "section_label_x":  24,
    "section_label_y":  47,
    "section_en_y":     77,
    "actor_y_offset":   28,
    "actor_gap":        16,
    "y_start":          148,
    "layer_y_gap":      14,
    "integration_y":    148,
    "content_h_extra":  16,
    "height_min":       1080,
    "height_base":      136,
    "height_pad_top":   28,
    "height_pad_bottom": 96,

    # Flowchart
    "flow_box_w":       310,
    "flow_box_h":       160,
    "flow_col_gap":     48,
    "flow_row_gap":     78,
    "flow_height_min":  900,
    "flow_height_base": 200,
    "flow_height_extra": 130,
    "flow_start_x_min": 80,
    "flow_node_x_base": 200,
    "flow_decision_icon_size": 30,
    "flow_decision_icon_cy": 34,
    "flow_decision_line_lh": 43,
    "flow_decision_text_y": 18,
    "flow_decision_start_y_base": 22,
    "flow_edge_label_chars": 20,
    "flow_edge_label_pad": 24,
    "flow_edge_rect_h": 32,
    "flow_edge_rect_y": 22,

    # Sequence diagram
    "seq_card_w_min":   360,
    "seq_card_h":       116,
    "seq_card_y":       148,
    "seq_lifeline_y":   276,
    "seq_msg_y_start":  318,
    "seq_msg_step":     86,
    "seq_bottom_y_base": 310,
    "seq_bottom_y_step": 86,
    "seq_height_min":   800,
    "seq_height_pad":   150,
    "seq_label_w_chars": 30,
    "seq_label_w_pad":  36,
    "seq_label_rect_h": 40,
    "seq_label_rect_y": 43,
    "seq_label_text_y": 13,

    # Swimlane
    "swim_row_h":       160,
    "swim_header_h":    88,
    "swim_body_y":      160,
    "swim_lane_extra":  30,
    "swim_height_pad":  88,
    "swim_icon_size":   38,
    "swim_icon_x":      20,
    "swim_icon_y":      24,
    "swim_text_x_icon": 72,
    "swim_text_x":      24,
    "swim_text_y":      54,
    "swim_step_y_off":  24,
    "swim_step_w_margin": 50,
    "swim_step_h":      116,

    # Relationship map
    "rel_header_h":     88,
    "rel_card_h":       116,
    "rel_node_gap":     16,
    "rel_container_pad_top": 24,
    "rel_container_pad_bottom": 22,
    "rel_cursor_y":     168,
    "rel_gap_y":        56,
    "rel_legend_extra": 4,
    "rel_height_min":   780,
    "rel_height_extra": 78,
    "rel_icon_size":    38,
    "rel_icon_x":       22,
    "rel_icon_y":       24,
    "rel_text_x_icon":  72,
    "rel_text_x":       24,
    "rel_text_y":       48,
    "rel_en_y":         77,
    "rel_node_y_off":   18,

    # Capability map
    "cap_row_h":        278,
    "cap_height_base":  200,
    "cap_height_extra": 96,
    "cap_y_start":      168,
    "cap_card_h":       258,
    "cap_header_h":     80,
    "cap_header_split": 64,
    "cap_icon_size":    38,
    "cap_icon_x":       24,
    "cap_icon_y":       22,
    "cap_text_x_icon":  72,
    "cap_text_x":       26,
    "cap_text_y":       52,
    "cap_item_y_start": 120,
    "cap_item_step":    50,
    "cap_item_x_margin": 10,
    "cap_item_icon_size": 30,
    "cap_item_icon_cy": 26,
    "cap_item_text_x":  38,

    # Note bar bottom offset
    "note_bar_bottom":  78,

    # item_card default heights per context
    "card_h":           116,
    "dark_card_h":      116,
    "flow_card_h":      160,
    "seq_card_h":       116,
    "swim_card_h":      116,
    "rel_card_h":       116,
}
LAYOUT["flow_card_h"] = LAYOUT["flow_box_h"]  # same as box height


def apply_font_scale(scale: float) -> None:
    """Multiply all LAYOUT values by *scale* so the entire diagram scales proportionally."""
    for key in LAYOUT:
        LAYOUT[key] = round(LAYOUT[key] * scale)


def esc(value: Any) -> str:
    return html.escape(str(value), quote=True)


def slug(value: str) -> str:
    cleaned = re.sub(r'[<>:"/\\|?*\s]+', "_", value.strip())
    return cleaned.strip("_.") or "diagram"


def text(x: float, y: float, value: str, css: str, anchor: str = "start") -> str:
    return f'<text x="{x:g}" y="{y:g}" class="{css}" text-anchor="{anchor}">{esc(value)}</text>'


def rect(x: float, y: float, w: float, h: float, fill: str, stroke: str = "none",
         radius: float = 10, extra: str = "") -> str:
    return (
        f'<rect x="{x:g}" y="{y:g}" width="{w:g}" height="{h:g}" rx="{radius:g}" '
        f'fill="{fill}" stroke="{stroke}" {extra}/>'
    )


def wrap_lines(value: str, max_chars: int) -> list[str]:
    """Split text into lines, preferring breaks at punctuation or spaces."""
    if not value:
        return [""]
    if len(value) <= max_chars:
        return [value]
    lines = []
    remaining = value
    while remaining:
        if len(remaining) <= max_chars:
            lines.append(remaining)
            break
        chunk = remaining[:max_chars]
        # Prefer breaking at Chinese/English punctuation
        for sep in ['；', ';', '，', ',', '。', '.', '、', '）', ')', '：', ':']:
            pos = chunk.rfind(sep)
            if pos > max_chars // 2:
                lines.append(remaining[:pos + 1])
                remaining = remaining[pos + 1:]
                break
        else:
            # Try space (for English words)
            pos = chunk.rfind(' ')
            if pos > max_chars // 2:
                lines.append(remaining[:pos])
                remaining = remaining[pos + 1:]
            else:
                lines.append(chunk)
                remaining = remaining[max_chars:]
    return lines


def icon_symbols() -> str:
    symbols = []
    for key, (_, content) in ICONS.items():
        symbols.append(
            f'<symbol id="ico-{key}" viewBox="0 0 24 24" fill="none" '
            f'stroke="currentColor" stroke-width="1.8" stroke-linecap="round" '
            f'stroke-linejoin="round">{content}</symbol>'
        )
    return "\n  ".join(symbols)


def icon(name: str | None, x: float, y: float, size: float, color: str) -> str:
    if not name:
        return ""
    if name not in ICONS:
        return ""
    return (
        f'<g color="{color}"><use href="#ico-{esc(name)}" '
        f'x="{x:g}" y="{y:g}" width="{size:g}" height="{size:g}"/></g>'
    )


def defs(theme: dict[str, str]) -> str:
    L = LAYOUT
    theme = _theme_with_palette(theme)
    return f"""<defs>
  <linearGradient id="header" x2="1"><stop stop-color="{theme['header_a']}"/><stop offset="1" stop-color="{theme['header_b']}"/></linearGradient>
  <filter id="shadow" x="-8%" y="-12%" width="116%" height="130%"><feDropShadow dx="0" dy="1" stdDeviation="1.5" flood-color="#183652" flood-opacity=".035"/></filter>
  <pattern id="grid" width="32" height="32" patternUnits="userSpaceOnUse"><circle cx="16" cy="16" r="1" fill="{theme['line']}" opacity=".35"/></pattern>
  <marker id="arrow" markerWidth="9" markerHeight="9" refX="8" refY="4.5" orient="auto"><path d="M0 0L9 4.5L0 9Z" fill="{theme['subtext']}"/></marker>
  <marker id="arrow-flow" markerWidth="10" markerHeight="10" refX="8.5" refY="5" orient="auto"><path d="M0 0L10 5L0 10Z" fill="{theme['flow']}"/></marker>
  <marker id="arrow-data" markerWidth="10" markerHeight="10" refX="8.5" refY="5" orient="auto"><path d="M0 0L10 5L0 10Z" fill="{theme['data']}"/></marker>
  <marker id="arrow-control" markerWidth="10" markerHeight="10" refX="8.5" refY="5" orient="auto"><path d="M0 0L10 5L0 10Z" fill="{theme['control']}"/></marker>
  <marker id="arrow-alert" markerWidth="10" markerHeight="10" refX="8.5" refY="5" orient="auto"><path d="M0 0L10 5L0 10Z" fill="{theme['alert']}"/></marker>
  <marker id="arrow-sync" markerWidth="10" markerHeight="10" refX="8.5" refY="5" orient="auto"><path d="M0 0L10 5L0 10Z" fill="{theme['sync']}"/></marker>
  {icon_symbols()}
  <style>
    .fm {{ font-family:"SimHei","Microsoft YaHei","Noto Sans SC",sans-serif; }}
    .title {{ font-weight:700; font-size:{L["title"]}px; font-family:"SimHei","Microsoft YaHei","Noto Sans SC",sans-serif; fill:#fff; letter-spacing:1px; }}
    .subtitle {{ font-weight:500; font-size:{L["subtitle"]}px; font-family:"SimHei","Microsoft YaHei","Noto Sans SC",sans-serif; fill:#e8f2fb; }}
    .section {{ font-weight:700; font-size:{L["section"]}px; font-family:"SimHei","Microsoft YaHei","Noto Sans SC",sans-serif; fill:{theme['label_text']}; }}
    .section-en {{ font-weight:600; font-size:{L["section_en"]}px; font-family:Arial,sans-serif; fill:{theme['subtext']}; letter-spacing:1.3px; }}
    .node {{ font-weight:600; font-size:{L["node"]}px; font-family:"SimHei","Microsoft YaHei","Noto Sans SC",sans-serif; fill:{theme['text']}; }}
    .node-lg {{ font-weight:700; font-size:{L["node_lg"]}px; font-family:"SimHei","Microsoft YaHei","Noto Sans SC",sans-serif; fill:{theme['text']}; }}
    .desc {{ font-weight:500; font-size:{L["desc"]}px; font-family:"SimHei","Microsoft YaHei","Noto Sans SC",sans-serif; fill:{theme['subtext']}; }}
    .dark-node {{ font-weight:600; font-size:{L["dark_node"]}px; font-family:"SimHei","Microsoft YaHei","Noto Sans SC",sans-serif; fill:#fff; }}
    .note {{ font-weight:500; font-size:{L["note"]}px; font-family:"SimHei","Microsoft YaHei","Noto Sans SC",sans-serif; fill:{theme['subtext']}; }}
    .edge-label {{ font-weight:700; font-size:{L["edge_label"]}px; font-family:"SimHei","Microsoft YaHei","Noto Sans SC",sans-serif; fill:{theme['text']}; }}
  </style>
</defs>"""


def page_start(title: str, subtitle: str, theme: dict[str, str], height: int) -> list[str]:
    L = LAYOUT
    theme = _theme_with_palette(theme)
    return [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{height}" viewBox="0 0 {WIDTH} {height}">',
        defs(theme),
        rect(0, 0, WIDTH, height, theme["bg"], radius=0),
        f'<rect width="{WIDTH}" height="{height}" fill="url(#grid)" opacity="{theme.get("grid_opacity", "0.38")}"/>',
        rect(0, 0, WIDTH, L["header_h"], "url(#header)", radius=0),
        rect(0, L["header_accent_y"], WIDTH, 3, theme["accent"], radius=0),
        text(L["title_x"], L["title_y"], title, "title"),
        text(L["subtitle_x"], L["subtitle_y"], subtitle, "subtitle"),
    ]


def _theme_with_palette(theme: dict[str, str]) -> dict[str, str]:
    palette = get_palette()
    roles = palette["roles"]
    header = palette["header"]
    merged = dict(theme)
    merged.update({
        "header_a": header["main"],
        "header_b": header["alt"],
        "accent": roles["primary"]["main"],
        "accent_light": roles["primary"]["light"],
        "label_bg": palette["wash"],
        "label_text": palette["text"],
        "card_alt": palette["wash"],
        "line": palette["line"],
        "text": palette["text"],
        "subtext": palette["subtext"],
        "dark": header["main"],
        "dark_card": header["main"],
        "success": roles["success"]["light"],
        "success_stroke": roles["success"]["main"],
        "warn": roles["warning"]["light"],
        "warn_stroke": roles["warning"]["main"],
        "danger": roles["danger"]["light"],
        "danger_stroke": roles["danger"]["main"],
        "flow": roles["primary"]["main"],
        "data": roles["teal"]["main"],
        "control": roles["purple"]["main"],
        "alert": roles["danger"]["main"],
        "sync": roles["gold"]["main"],
    })
    return merged


def note_bar(parts: list[str], value: str, theme: dict[str, str], y: int) -> None:
    L = LAYOUT
    parts.append(rect(42, y, WIDTH - 84, L["note_bar_h"], theme["card_alt"], theme["line"], 8))
    parts.append(text(59, y + L["note_bar_text_y"], f"注：{value}", "note"))


def item_card(parts: list[str], x: int, y: int, w: int, h: int, item: dict[str, Any],
              theme: dict[str, str], kind: str = "default") -> None:
    L = LAYOUT
    fill = theme["card"]
    stroke = theme["line"]
    if kind == "success":
        fill, stroke = theme["success"], theme["success_stroke"]
    elif kind == "warning":
        fill, stroke = theme["warn"], theme["warn_stroke"]
    elif kind == "danger":
        fill, stroke = theme["danger"], theme["danger_stroke"]
    elif kind == "accent":
        fill, stroke = theme["accent_light"], theme["accent"]
    parts.append(rect(x, y, w, h, fill, stroke, 9, 'filter="url(#shadow)"'))
    parts.append(rect(x, y + 9, 4, h - 18, stroke, radius=2))
    title = str(item.get("title", item) if isinstance(item, dict) else item)
    desc = item.get("desc", "") if isinstance(item, dict) else ""
    icon_name = item.get("icon") if isinstance(item, dict) else None
    if icon_name:
        icon_color = theme["accent"] if kind == "default" else stroke
        parts.append(icon(icon_name, x + L["card_icon_x"], y + (h - L["card_icon_size"]) / 2, L["card_icon_size"], icon_color))

    pad_v = L["card_pad_v"]
    title_lh = L["card_title_lh"]
    desc_lh = L["card_desc_lh"]
    text_gap = L["card_text_gap"]

    avail_h = h - pad_v * 2
    text_x = x + L["card_text_x_icon"] if icon_name else x + w / 2
    anchor = "start" if icon_name else "middle"
    chars_per_line = max(4, int((w - (L["card_text_x_icon"] if icon_name else L["card_text_x_no_icon_margin"])) / L["card_chars_div"]))

    all_title_lines = wrap_lines(title, chars_per_line)

    desc_h = desc_lh + text_gap if desc else 0
    max_title_lines = max(1, int((avail_h - desc_h) / title_lh))

    title_lines = all_title_lines[:max_title_lines]
    if len(title_lines) < len(all_title_lines) and title_lines:
        last = title_lines[-1]
        if len(last) > 1:
            title_lines[-1] = last[:-1] + '…'

    text_block_h = len(title_lines) * title_lh + desc_h
    block_top = y + pad_v + (avail_h - text_block_h) / 2

    for idx, line in enumerate(title_lines):
        parts.append(text(text_x, block_top + idx * title_lh + L["card_title_baseline"], line, "node", anchor))

    if desc:
        desc_y = block_top + len(title_lines) * title_lh + text_gap + L["card_desc_baseline"]
        desc_max = max(6, int((w - 30) / 23))
        if len(desc) > desc_max:
            desc = desc[:desc_max - 1] + '…'
        parts.append(text(text_x, desc_y, desc, "desc", anchor))


def edge_visual(edge: dict[str, Any], theme: dict[str, str]) -> tuple[str, str, str, float]:
    relation = edge.get("relation", "flow")
    colors = {
        "flow": theme["flow"],
        "data": theme["data"],
        "control": theme["control"],
        "alert": theme["alert"],
        "sync": theme["sync"],
    }
    dashes = {
        "flow": "",
        "data": "7 4",
        "control": "10 4",
        "alert": "",
        "sync": "3 4",
    }
    width = 2.7 if relation == "alert" else 2.1
    return colors.get(relation, theme["flow"]), f"arrow-{relation}", dashes.get(relation, ""), width


def append_semantic_edge(parts: list[str], d: str, edge: dict[str, Any],
                         theme: dict[str, str]) -> None:
    color, marker, dash, width = edge_visual(edge, theme)
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    start_attr = f' marker-start="url(#{marker})"' if edge.get("bidirectional") else ""
    parts.append(
        f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width:g}"'
        f'{dash_attr}{start_attr} marker-end="url(#{marker})"/>'
    )


def append_edge_tip(parts: list[str], d: str, edge: dict[str, Any],
                    theme: dict[str, str], start: bool = False) -> None:
    color, marker, dash, width = edge_visual(edge, theme)
    dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
    marker_attr = f'marker-start="url(#{marker})"' if start else f'marker-end="url(#{marker})"'
    parts.append(
        f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width:g}"'
        f'{dash_attr} {marker_attr}/>'
    )


def render_layered_architecture(figure: dict[str, Any], theme: dict[str, str]) -> str:
    L = LAYOUT
    actors = figure.get("actors", [])
    layers = figure.get("layers", [])
    integrations = figure.get("integrations", [])
    side_w = 320 if integrations else 0
    main_w = 1520 - side_w - (18 if integrations else 0)
    x = 42
    label_w = L["label_w"]
    actor_h = L["actor_h"] if actors else 0
    layer_heights: list[int] = []
    for layer in layers:
        count = len(layer.get("items", []))
        cols = min(count, layer.get("columns", 5))
        rows = max(1, math.ceil(count / max(cols, 1)))
        layer_heights.append(L["layer_base"] + rows * L["layer_per_row"] + (rows - 1) * L["layer_gap"] + L["layer_extra"])
    content_h = (actor_h + L["actor_gap"] if actors else 0) + sum(layer_heights) + max(0, len(layers) - 1) * L["layer_y_gap"]
    height = max(L["height_min"], L["height_base"] + L["height_pad_top"] + content_h + L["height_pad_bottom"])
    title = figure["title"]
    subtitle = figure.get("subtitle", "总体技术方案 / 系统总体架构设计")
    parts = page_start(title, subtitle, theme, height)
    y = L["y_start"]
    layer_mids: list[int] = []
    blocks: list[tuple[int, int]] = []

    def section_box(label: str, en: str, box_y: int, box_h: int, dark: bool = False) -> None:
        fill = theme["dark"] if dark else theme["card"]
        label_fill = theme["dark"] if dark else theme["label_bg"]
        stroke = theme["dark"] if dark else theme["line"]
        parts.append(rect(x, box_y, main_w, box_h, fill, stroke, 12, 'filter="url(#shadow)"'))
        parts.append(rect(x, box_y, label_w, box_h, label_fill, stroke, 12))
        label_css = "dark-node" if dark else "section"
        parts.append(text(x + L["section_label_x"], box_y + L["section_label_y"], label, label_css))
        parts.append(text(x + L["section_label_x"], box_y + L["section_en_y"], en, "section-en"))

    if actors:
        section_box(figure.get("actors_label", "服务对象"), "USERS & ACCESS", y, actor_h)
        card_x = x + label_w + 34
        available = main_w - label_w - 60
        gap = L["actor_gap"]
        card_w = int((available - gap * (len(actors) - 1)) / len(actors))
        for index, actor in enumerate(actors):
            item_card(parts, card_x + index * (card_w + gap), y + L["actor_y_offset"], card_w, L["card_h"], actor, theme)
        layer_mids.append(y + actor_h // 2)
        blocks.append((y, y + actor_h))
        y += actor_h + L["actor_gap"]

    for number, layer in enumerate(layers):
        h = layer_heights[number]
        dark = layer.get("style") == "dark"
        section_box(layer["label"], layer.get("en", ""), y, h, dark)
        items = layer.get("items", [])
        cols = min(len(items), layer.get("columns", 5))
        rows = max(1, math.ceil(len(items) / cols))
        gap = L["layer_gap"]
        available = main_w - label_w - 40
        card_w = int((available - gap * (cols - 1)) / cols)
        card_x = x + label_w + 20
        for index, item in enumerate(items):
            row, col = divmod(index, cols)
            cy = y + L["actor_y_offset"] + row * L["layer_row_h"]
            if dark:
                dark_w = card_w
                dark_x = card_x + col * (card_w + gap)
                dch = L["layer_dark_card_h"]
                parts.append(rect(dark_x, cy, dark_w, dch, theme["dark_card"], "#4f7296", 8))
                title_value = item.get("title", item) if isinstance(item, dict) else item
                icon_name = item.get("icon") if isinstance(item, dict) else None
                max_chars = max(4, int((dark_w - (L["layer_dark_icon_margin"] if icon_name else 40)) / L["layer_dark_chars_div"]))
                dark_lines = wrap_lines(title_value, max_chars)[:2]
                if len(dark_lines) < len(wrap_lines(title_value, max_chars)):
                    dark_lines[-1] = dark_lines[-1][:-1] + '…' if len(dark_lines[-1]) > 1 else dark_lines[-1]
                total_h = len(dark_lines) * L["layer_dark_text_lh"]
                start_y = cy + (dch - total_h) / 2 + L["layer_dark_baseline"]
                if icon_name:
                    icon_size = L["layer_dark_icon_size"]
                    parts.append(icon(icon_name, dark_x + L["layer_dark_icon_x"], cy + L["layer_dark_icon_y_offset"], icon_size, "#ffffff"))
                    tx = dark_x + L["layer_dark_text_x"]
                    for idx, line in enumerate(dark_lines):
                        parts.append(text(tx, start_y + idx * (L["layer_dark_text_lh"] + 5), line, "dark-node"))
                else:
                    tx = dark_x + dark_w / 2
                    for idx, line in enumerate(dark_lines):
                        parts.append(text(tx, start_y + idx * (L["layer_dark_text_lh"] + 5), line, "dark-node", "middle"))
            else:
                item_card(parts, card_x + col * (card_w + gap), cy, card_w, L["layer_dark_card_h"] + 12, item, theme,
                          item.get("style", "default") if isinstance(item, dict) else "default")
        layer_mids.append(y + h // 2)
        blocks.append((y, y + h))
        y += h + L["layer_gap"]

    for (_, bottom), (top, _) in zip(blocks, blocks[1:]):
        mid_x = x + main_w / 2
        parts.append(f'<path d="M{mid_x:g} {bottom + 2:g}V{top - 4:g}" stroke="{theme["subtext"]}" stroke-width="1.5" stroke-dasharray="4 3" marker-end="url(#arrow)"/>')

    if integrations:
        sx = x + main_w + 18
        sy = L["integration_y"] + (actor_h + 20 if actors else 0)
        sh = y - sy - 12
        parts.append(rect(sx, sy, side_w, sh, theme["card_alt"], theme["line"], 12, 'filter="url(#shadow)"'))
        parts.append(rect(sx, sy, side_w, 94, theme["header_b"], radius=12))
        parts.append(text(sx + side_w / 2, sy + 39, figure.get("integration_label", "外部协同与交换"), "dark-node", "middle"))
        parts.append(text(sx + side_w / 2, sy + 70, "INTEGRATION", "subtitle", "middle"))
        iy = sy + 112
        for item in integrations:
            item_card(parts, sx + 20, iy, side_w - 40, L["layer_dark_card_h"] + 12, item, theme)
            iy += 112
        for mid in layer_mids[1:]:
            parts.append(f'<path d="M{x + main_w:g} {mid:g}H{sx - 5:g}" stroke="{theme["subtext"]}" stroke-width="1.3" marker-end="url(#arrow)"/>')

    note_bar(parts, figure.get("note", "本图内容来源于文档已确认需求，未确认的实现细节需在深化设计阶段确认。"), theme, height - L["note_bar_bottom"])
    parts.append("</svg>")
    return "\n".join(parts)


def render_flowchart(figure: dict[str, Any], theme: dict[str, str]) -> str:
    L = LAYOUT
    nodes = figure.get("nodes", [])
    edges = figure.get("edges", [])
    if not nodes:
        raise ValueError(f"{figure['title']} 未定义 nodes")
    positions: dict[str, tuple[int, int, int, int]] = {}
    max_row = max(node.get("row", 0) for node in nodes)
    max_col = max(node.get("col", 0) for node in nodes)
    box_w, box_h = L["flow_box_w"], L["flow_box_h"]
    col_gap, row_gap = L["flow_col_gap"], L["flow_row_gap"]
    cols = max_col + 1
    usable_w = WIDTH - 84
    total_w = cols * box_w + max_col * col_gap
    if total_w > usable_w:
        col_gap = min(col_gap, 36)
        box_w = max(220, int((usable_w - max_col * col_gap) / cols))
        total_w = cols * box_w + max_col * col_gap
    start_x = max(42, int((WIDTH - total_w) / 2))
    height = max(L["flow_height_min"], L["flow_height_base"] + (max_row + 1) * box_h + max_row * row_gap + L["flow_height_extra"])
    parts = page_start(figure["title"], figure.get("subtitle", "业务流程图"), theme, height)
    for node in nodes:
        positions[node["id"]] = (
            start_x + node.get("col", 0) * (box_w + col_gap),
            L["flow_node_x_base"] + node.get("row", 0) * (box_h + row_gap),
            box_w,
            box_h,
        )

    edge_parts: list[str] = []
    edge_labels: list[str] = []
    edge_tips: list[str] = []
    for edge in edges:
        ax, ay, aw, ah = positions[edge["from"]]
        bx, by, bw, bh = positions[edge["to"]]
        x1, y1 = ax + aw, ay + ah / 2
        x2, y2 = bx, by + bh / 2
        if bx <= ax:
            x1, y1 = ax + aw / 2, ay + ah
            x2, y2 = bx + bw / 2, by
            d = f"M{x1:g} {y1:g}V{(y1 + y2) / 2:g}H{x2:g}V{y2:g}"
            direction = 1 if y2 >= y1 else -1
            append_edge_tip(edge_tips, f"M{x2:g} {y2 - direction * 18:g}V{y2:g}", edge, theme)
        else:
            d = f"M{x1:g} {y1:g}H{(x1 + x2) / 2:g}V{y2:g}H{x2:g}"
            append_edge_tip(edge_tips, f"M{x2 - 18:g} {y2:g}H{x2:g}", edge, theme)
        append_semantic_edge(edge_parts, d, edge, theme)
        if edge.get("label"):
            lx = (x1 + x2) / 2
            ly = min(y1, y2) - 8 if y1 != y2 else y1 - 10
            label_w = max(64, len(edge["label"]) * L["flow_edge_label_chars"] + L["flow_edge_label_pad"])
            edge_labels.append(rect(lx - label_w / 2, ly - L["flow_edge_rect_y"], label_w, L["flow_edge_rect_h"], theme["bg"], theme["line"], 5))
            edge_labels.append(text(lx, ly, edge["label"], "edge-label", "middle"))

    parts.extend(edge_parts)
    for node in nodes:
        x0, y0, w, h = positions[node["id"]]
        kind = node.get("kind", "process")
        if kind == "decision":
            cx, cy = x0 + w / 2, y0 + h / 2
            parts.append(f'<path d="M{cx:g} {y0:g}L{x0 + w:g} {cy:g}L{cx:g} {y0 + h:g}L{x0:g} {cy:g}Z" fill="{theme["warn"]}" stroke="{theme["warn_stroke"]}" filter="url(#shadow)"/>')
            dics = L["flow_decision_icon_size"]
            if node.get("icon"):
                parts.append(icon(node["icon"], cx - dics // 2, cy - dics - 6, dics, theme["warn_stroke"]))
                lines = wrap_lines(node["title"], 6)[:2]
                for line_index, line in enumerate(lines):
                    parts.append(text(cx, cy + L["flow_decision_text_y"] + line_index * L["flow_decision_line_lh"], line, "node", "middle"))
            else:
                lines = wrap_lines(node["title"], 6)[:2]
                start_y = cy - (len(lines) - 1) * (L["flow_decision_line_lh"] // 2) + L["flow_decision_start_y_base"]
                for line_index, line in enumerate(lines):
                    parts.append(text(cx, start_y + line_index * L["flow_decision_line_lh"], line, "node", "middle"))
        else:
            style = "success" if kind == "success" else "danger" if kind == "failure" else "accent" if kind == "external" else "default"
            item_card(parts, x0, y0, w, h, node, theme, style)
    parts.extend(edge_tips)
    parts.extend(edge_labels)
    note_bar(parts, figure.get("note", "流程节点和流向依据文档业务描述整理。"), theme, height - L["note_bar_bottom"])
    parts.append("</svg>")
    return "\n".join(parts)


def render_sequence_diagram(figure: dict[str, Any], theme: dict[str, str]) -> str:
    L = LAYOUT
    participants = figure.get("participants", [])
    messages = figure.get("messages", [])
    if len(participants) < 2:
        raise ValueError(f"{figure['title']} 至少需要两个 participants")
    gap = 24
    card_w = min(L["seq_card_w_min"], int((WIDTH - 100 - gap * (len(participants) - 1)) / len(participants)))
    total_w = len(participants) * card_w + (len(participants) - 1) * gap
    start_x = (WIDTH - total_w) / 2
    bottom_y = L["seq_bottom_y_base"] + len(messages) * L["seq_bottom_y_step"]
    height = max(L["seq_height_min"], bottom_y + L["seq_height_pad"])
    parts = page_start(figure["title"], figure.get("subtitle", "系统交互时序图"), theme, height)
    centers: dict[str, float] = {}

    for index, participant in enumerate(participants):
        x = start_x + index * (card_w + gap)
        centers[participant["id"]] = x + card_w / 2
        style = participant.get("style", "default")
        item_card(parts, int(x), L["seq_card_y"], card_w, L["seq_card_h"], participant, theme, style)
        parts.append(
            f'<path d="M{x + card_w / 2:g} {L["seq_lifeline_y"]}V{bottom_y:g}" stroke="{theme["line"]}" '
            'stroke-width="1.5" stroke-dasharray="6 5"/>'
        )

    for index, message in enumerate(messages):
        y = L["seq_msg_y_start"] + index * L["seq_msg_step"]
        x1 = centers[message["from"]]
        x2 = centers[message["to"]]
        if message.get("activate"):
            parts.append(rect(x2 - 7, y + 7, 14, 42, theme["accent_light"], theme["accent"], 3))
        if x1 == x2:
            d = f"M{x1:g} {y:g}H{x1 + 55:g}V{y + 26:g}H{x1 + 8:g}"
            label_x = x1 + 32
        else:
            d = f"M{x1:g} {y:g}H{x2:g}"
            label_x = (x1 + x2) / 2
        append_semantic_edge(parts, d, message, theme)
        label_w = max(100, len(message.get("label", "")) * L["seq_label_w_chars"] + L["seq_label_w_pad"])
        parts.append(rect(label_x - label_w / 2, y - L["seq_label_rect_y"], label_w, L["seq_label_rect_h"], theme["bg"], radius=4))
        parts.append(text(label_x, y - L["seq_label_text_y"], message.get("label", ""), "edge-label", "middle"))

    note_bar(parts, figure.get("note", "虚线生命线表示交互参与方持续存在，箭头颜色对应消息语义。"), theme, height - L["note_bar_bottom"])
    parts.append("</svg>")
    return "\n".join(parts)


def render_swimlane_flowchart(figure: dict[str, Any], theme: dict[str, str]) -> str:
    L = LAYOUT
    lanes = figure.get("lanes", [])
    steps = figure.get("steps", [])
    edges = figure.get("edges", [])
    if not lanes or not steps:
        raise ValueError(f"{figure['title']} 需要定义 lanes 与 steps")
    gap = 14
    lane_w = int((WIDTH - 84 - gap * (len(lanes) - 1)) / len(lanes))
    max_order = max(step.get("order", 0) for step in steps)
    row_h, header_h = L["swim_row_h"], L["swim_header_h"]
    body_y = L["swim_body_y"]
    lane_h = header_h + (max_order + 1) * row_h + L["swim_lane_extra"]
    height = body_y + lane_h + L["swim_height_pad"]
    parts = page_start(figure["title"], figure.get("subtitle", "跨角色泳道流程图"), theme, height)
    lane_x: dict[str, int] = {}
    positions: dict[str, tuple[int, int, int, int]] = {}

    for index, lane in enumerate(lanes):
        x = 42 + index * (lane_w + gap)
        lane_x[lane["id"]] = x
        parts.append(rect(x, body_y, lane_w, lane_h, theme["card"], theme["line"], 10))
        parts.append(rect(x, body_y, lane_w, header_h, theme["accent_light"], theme["accent"], 10))
        parts.append(rect(x, body_y + header_h - 10, lane_w, 10, theme["accent_light"], radius=0))
        if lane.get("icon"):
            parts.append(icon(lane["icon"], x + L["swim_icon_x"], body_y + L["swim_icon_y"], L["swim_icon_size"], theme["accent"]))
            parts.append(text(x + L["swim_text_x_icon"], body_y + L["swim_text_y"], lane["title"], "section"))
        else:
            parts.append(text(x + L["swim_text_x"], body_y + L["swim_text_y"], lane["title"], "section"))

    for step in steps:
        x = lane_x[step["lane"]] + 21
        y = body_y + header_h + L["swim_step_y_off"] + step.get("order", 0) * row_h
        w, h = lane_w - L["swim_step_w_margin"], L["swim_step_h"]
        positions[step["id"]] = (x, y, w, h)
        kind = step.get("kind", "process")
        style = "success" if kind == "success" else "danger" if kind == "failure" else "warning" if kind == "decision" else step.get("style", "default")
        item_card(parts, x, y, w, h, step, theme, style)

    edge_parts: list[str] = []
    label_parts: list[str] = []
    for edge in edges:
        ax, ay, aw, ah = positions[edge["from"]]
        bx, by, bw, bh = positions[edge["to"]]
        if by > ay:
            x1, y1, x2, y2 = ax + aw / 2, ay + ah, bx + bw / 2, by
            mid_y = (y1 + y2) / 2
            d = f"M{x1:g} {y1:g}V{mid_y:g}H{x2:g}V{y2:g}"
            lx, ly = (x1 + x2) / 2, mid_y - 8
        else:
            x1, y1, x2, y2 = ax + aw, ay + ah / 2, bx, by + bh / 2
            mid_x = (x1 + x2) / 2
            d = f"M{x1:g} {y1:g}H{mid_x:g}V{y2:g}H{x2:g}"
            lx, ly = mid_x, min(y1, y2) - 9
        append_semantic_edge(edge_parts, d, edge, theme)
        if edge.get("label"):
            label_w = max(68, len(edge["label"]) * 24 + 24)
            label_parts.append(rect(lx - label_w / 2, ly - 27, label_w, 34, theme["bg"], theme["line"], 5))
            label_parts.append(text(lx, ly, edge["label"], "edge-label", "middle"))
    parts.extend(edge_parts)
    parts.extend(label_parts)
    note_bar(parts, figure.get("note", "泳道区分责任主体，连线表达跨角色流转和反馈。"), theme, height - L["note_bar_bottom"])
    parts.append("</svg>")
    return "\n".join(parts)


def render_relationship_map(figure: dict[str, Any], theme: dict[str, str]) -> str:
    L = LAYOUT
    containers = figure.get("containers", [])
    edges = figure.get("edges", [])
    if not containers:
        raise ValueError(f"{figure['title']} 未定义 containers")
    columns = max(1, min(4, figure.get("columns", 3)))
    gap_x, gap_y = L["rel_node_gap"] * 3, L["rel_gap_y"]
    left, usable_w = 42, WIDTH - 84
    container_w = int((usable_w - gap_x * (columns - 1)) / columns)
    header_h, card_h, node_gap = L["rel_header_h"], L["rel_card_h"], L["rel_node_gap"]
    container_rows: dict[int, int] = {}
    measured: dict[str, tuple[int, int, int]] = {}

    for container in containers:
        node_cols = max(1, min(2, container.get("columns", 2)))
        nodes = container.get("nodes", [])
        max_node_row = max((node.get("row", idx // node_cols) for idx, node in enumerate(nodes)), default=0)
        height = header_h + L["rel_container_pad_top"] + (max_node_row + 1) * card_h + max_node_row * node_gap + L["rel_container_pad_bottom"]
        row = container.get("row", 0)
        measured[container["id"]] = (node_cols, max_node_row, height)
        container_rows[row] = max(container_rows.get(row, 0), height)

    row_y: dict[int, int] = {}
    cursor_y = L["rel_cursor_y"]
    for row in sorted(container_rows):
        row_y[row] = cursor_y
        cursor_y += container_rows[row] + gap_y
    legend_y = cursor_y + L["rel_legend_extra"]
    height = max(L["rel_height_min"], legend_y + L["rel_height_extra"] + 60)
    parts = page_start(figure["title"], figure.get("subtitle", "复杂关系与包含架构图"), theme, height)
    node_positions: dict[str, tuple[float, float, float, float]] = {}

    for container in containers:
        row, col = container.get("row", 0), container.get("col", 0)
        x, y = left + col * (container_w + gap_x), row_y[row]
        container_h = container_rows[row]
        style = container.get("style", "default")
        border = theme["accent"] if style == "accent" else theme["line"]
        heading = theme["accent_light"] if style == "accent" else theme["label_bg"]
        parts.append(rect(x, y, container_w, container_h, theme["card_alt"], border, 12, 'filter="url(#shadow)"'))
        parts.append(rect(x, y, container_w, header_h, heading, border, 12))
        parts.append(rect(x, y + header_h - 12, container_w, 12, heading, radius=0))
        if container.get("icon"):
            parts.append(icon(container["icon"], x + L["rel_icon_x"], y + L["rel_icon_y"], L["rel_icon_size"], theme["accent"]))
            parts.append(text(x + L["rel_text_x_icon"], y + L["rel_text_y"], container["title"], "section"))
            parts.append(text(x + L["rel_text_x_icon"], y + L["rel_en_y"], container.get("subtitle", "CONTAINER"), "section-en"))
        else:
            parts.append(text(x + L["rel_text_x"], y + L["rel_text_y"], container["title"], "section"))
            parts.append(text(x + L["rel_text_x"], y + L["rel_en_y"], container.get("subtitle", "CONTAINER"), "section-en"))
        nodes = container.get("nodes", [])
        node_cols = measured[container["id"]][0]
        inner_gap = 10
        inner_w = container_w - 32
        node_w = int((inner_w - inner_gap * (node_cols - 1)) / node_cols)
        for index, node in enumerate(nodes):
            nrow = node.get("row", index // node_cols)
            ncol = node.get("col", index % node_cols)
            nx = x + 16 + ncol * (node_w + inner_gap)
            ny = y + header_h + L["rel_node_y_off"] + nrow * (card_h + node_gap)
            node_positions[node["id"]] = (nx, ny, node_w, card_h)

    edge_parts: list[str] = []
    edge_labels: list[str] = []
    edge_tips: list[str] = []
    for edge in edges:
        ax, ay, aw, ah = node_positions[edge["from"]]
        bx, by, bw, bh = node_positions[edge["to"]]
        acx, bcx = ax + aw / 2, bx + bw / 2
        acy, bcy = ay + ah / 2, by + bh / 2
        if abs(bcx - acx) >= abs(bcy - acy):
            if bcx >= acx:
                x1, y1, x2, y2 = ax + aw, acy, bx, bcy
                direction = 1
            else:
                x1, y1, x2, y2 = ax, acy, bx + bw, bcy
                direction = -1
            middle = (x1 + x2) / 2
            d = f"M{x1:g} {y1:g}H{middle:g}V{y2:g}H{x2:g}"
            append_edge_tip(edge_tips, f"M{x2 - direction * 18:g} {y2:g}H{x2:g}", edge, theme)
            if edge.get("bidirectional"):
                append_edge_tip(edge_tips, f"M{x1:g} {y1:g}H{x1 + direction * 18:g}", edge, theme, start=True)
            lx, ly = middle, (y1 + y2) / 2 - 10
        else:
            if bcy >= acy:
                x1, y1, x2, y2 = acx, ay + ah, bcx, by
                direction = 1
            else:
                x1, y1, x2, y2 = acx, ay, bcx, by + bh
                direction = -1
            middle = (y1 + y2) / 2
            d = f"M{x1:g} {y1:g}V{middle:g}H{x2:g}V{y2:g}"
            append_edge_tip(edge_tips, f"M{x2:g} {y2 - direction * 18:g}V{y2:g}", edge, theme)
            if edge.get("bidirectional"):
                append_edge_tip(edge_tips, f"M{x1:g} {y1:g}V{y1 + direction * 18:g}", edge, theme, start=True)
            lx, ly = (x1 + x2) / 2, middle - 10
        append_semantic_edge(edge_parts, d, edge, theme)
        if edge.get("label"):
            label_w = max(76, len(edge["label"]) * 24 + 24)
            edge_labels.append(rect(lx - label_w / 2, ly - 28, label_w, 36, theme["bg"], theme["line"], 5))
            edge_labels.append(text(lx, ly, edge["label"], "edge-label", "middle"))

    parts.extend(edge_parts)
    for container in containers:
        for node in container.get("nodes", []):
            nx, ny, nw, nh = node_positions[node["id"]]
            item_card(parts, int(nx), int(ny), int(nw), int(nh), node, theme, node.get("style", "default"))
    parts.extend(edge_tips)
    parts.extend(edge_labels)

    legend = [
        ("业务流", "flow"), ("数据流", "data"), ("控制流", "control"),
        ("告警流", "alert"), ("同步/反馈", "sync"),
    ]
    parts.append(text(42, legend_y + 36, "连线语义", "section"))
    legend_x = 190
    for label, relation in legend:
        edge = {"relation": relation}
        color, marker, dash, width = edge_visual(edge, theme)
        dash_attr = f' stroke-dasharray="{dash}"' if dash else ""
        parts.append(f'<path d="M{legend_x:g} {legend_y + 29:g}H{legend_x + 58:g}" stroke="{color}" stroke-width="{width:g}"{dash_attr} marker-end="url(#{marker})"/>')
        parts.append(text(legend_x + 76, legend_y + 36, label, "desc"))
        legend_x += 235
    note_bar(parts, figure.get("note", "容器表示所属域，彩色连线表示跨域数据和业务协同关系。"), theme, height - L["note_bar_bottom"])
    parts.append("</svg>")
    return "\n".join(parts)


def render_capability_map(figure: dict[str, Any], theme: dict[str, str]) -> str:
    L = LAYOUT
    groups = figure.get("groups", [])
    cols = figure.get("columns", 3)
    card_w = int((1516 - (cols - 1) * 18) / cols)
    row_h = L["cap_row_h"]
    rows = max(1, math.ceil(len(groups) / cols))
    height = L["cap_height_base"] + rows * row_h + L["cap_height_extra"]
    parts = page_start(figure["title"], figure.get("subtitle", "功能能力框图"), theme, height)
    for index, group in enumerate(groups):
        row, col = divmod(index, cols)
        x = 42 + col * (card_w + 18)
        y = L["cap_y_start"] + row * row_h
        ch = L["cap_card_h"]
        parts.append(rect(x, y, card_w, ch, theme["card"], theme["line"], 12, 'filter="url(#shadow)"'))
        parts.append(rect(x, y, card_w, L["cap_header_h"], theme["label_bg"], theme["line"], 12))
        parts.append(rect(x, y + L["cap_header_split"], card_w, 14, theme["label_bg"], radius=0))
        group_icon = group.get("icon")
        if group_icon:
            parts.append(icon(group_icon, x + L["cap_icon_x"], y + L["cap_icon_y"], L["cap_icon_size"], theme["accent"]))
            parts.append(text(x + L["cap_text_x_icon"], y + L["cap_text_y"], group["label"], "section"))
        else:
            parts.append(text(x + L["cap_text_x"], y + L["cap_text_y"], group["label"], "section"))
        items = group.get("items", [])
        for item_index, item in enumerate(items[:6]):
            iy = y + L["cap_item_y_start"] + (item_index // 2) * L["cap_item_step"]
            ix = x + L["cap_item_x_margin"] + (item_index % 2) * (card_w / 2 - 12)
            item_title = item.get("title", "") if isinstance(item, dict) else item
            item_icon = item.get("icon") if isinstance(item, dict) else None
            cis = L["cap_item_icon_size"]
            if item_icon:
                parts.append(icon(item_icon, ix - 2, iy - cis, cis, theme["accent"]))
                parts.append(text(ix + L["cap_item_text_x"], iy, item_title, "node"))
            else:
                parts.append(f'<circle cx="{ix:g}" cy="{iy - L["cap_item_icon_cy"] + cis:g}" r="4" fill="{theme["accent"]}"/>')
                parts.append(text(ix + 18, iy, item_title, "node"))
    note_bar(parts, figure.get("note", "能力模块可根据需求章节继续细化到功能清单。"), theme, height - L["note_bar_bottom"])
    parts.append("</svg>")
    return "\n".join(parts)


def style_color(style: str | None, theme: dict[str, str]) -> tuple[str, str, str]:
    return triplet(style)


def formal_bid_css(parts: list[str]) -> None:
    parts.append("""
<style>
  .title { font-size:46px; letter-spacing:0; }
  .subtitle { font-size:24px; }
  .section { font-size:28px; }
  .node-lg { font-size:28px; }
  .node { font-size:24px; }
  .desc { font-size:20px; }
  .dark-node { font-size:26px; }
  .note { font-size:18px; }
  .edge-label { font-size:21px; }
</style>""")


def svg_text_block(
    parts: list[str],
    x: float,
    y: float,
    lines: list[str] | str,
    css: str,
    max_chars: int,
    line_h: int,
    anchor: str = "start",
    limit: int | None = None,
) -> float:
    if isinstance(lines, str):
        source = [lines]
    else:
        source = [str(line) for line in lines if str(line)]
    wrapped: list[str] = []
    for line in source:
        wrapped.extend(wrap_lines(line, max_chars))
    if limit is not None:
        wrapped = wrapped[:limit]
    for index, line in enumerate(wrapped):
        parts.append(text(x, y + index * line_h, line, css, anchor))
    return y + max(0, len(wrapped)) * line_h


def bullet_list(parts: list[str], x: float, y: float, items: list[Any], color: str, max_chars: int, limit: int = 6) -> float:
    cursor = y
    for item in items[:limit]:
        value = item.get("title", item) if isinstance(item, dict) else item
        lines = wrap_lines(str(value), max_chars)
        parts.append(f'<circle cx="{x:g}" cy="{cursor - 7:g}" r="4" fill="{color}"/>')
        for idx, line in enumerate(lines[:2]):
            parts.append(text(x + 18, cursor + idx * 28, line, "desc"))
        cursor += max(1, min(2, len(lines))) * 28 + 8
    return cursor


def formal_panel(
    parts: list[str],
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    style: str,
    theme: dict[str, str],
    subtitle: str = "",
    icon_name: str | None = None,
    index: str | int | None = None,
) -> tuple[str, str, str, int]:
    color, light, soft = style_color(style, theme)
    parts.append(rect(x, y, w, h, "#ffffff", color, 14, 'filter="url(#shadow)"'))
    parts.append(rect(x, y, w, 86, color, color, 14))
    parts.append(rect(x, y + 62, w, 26, color, color, 0))
    if index is not None:
        parts.append(f'<circle cx="{x + 42:g}" cy="{y + 42:g}" r="21" fill="#fff"/>')
        parts.append(text(x + 42, y + 53, str(index), "section", "middle"))
    if icon_name:
        parts.append(icon(icon_name, x + 22, y + 22, 38, "#ffffff"))
    title_x = x + (76 if (icon_name or index is not None) else 24)
    parts.append(text(title_x, y + 42, title, "dark-node"))
    if subtitle:
        parts.append(text(title_x, y + 72, subtitle, "subtitle"))
    return color, light, soft, y + 112


def section_box(
    parts: list[str],
    x: int,
    y: int,
    w: int,
    h: int,
    title: str,
    items: list[Any],
    style: str,
    theme: dict[str, str],
    icon_name: str | None = None,
    max_chars: int = 20,
    limit: int = 6,
) -> None:
    color, light, _ = style_color(style, theme)
    parts.append(rect(x, y, w, h, light, color, 8))
    if icon_name:
        parts.append(rect(x - 18, y + 18, 48, 48, color, color, 8))
        parts.append(icon(icon_name, x - 7, y + 29, 26, "#ffffff"))
        title_x = x + 42
    else:
        title_x = x + 20
    parts.append(text(title_x, y + 42, title, "node"))
    bullet_list(parts, x + 32, y + 78, items, color, max_chars, limit=limit)


def render_interface_map(figure: dict[str, Any], theme: dict[str, str]) -> str:
    """SVG version of the bid-friendly interface relationship style from example figure 3."""

    height = 1160
    parts = page_start(figure["title"], figure.get("subtitle", "数据交互规则、接口链路与安全约束"), theme, height)
    formal_bid_css(parts)
    left = figure.get("leftPlatform") or figure.get("left") or {}
    right = figure.get("rightPlatform") or figure.get("right") or {}
    flows = figure.get("flows", [])
    requirements = figure.get("requirements", [])
    notes = figure.get("notes", [])

    def platform(x: int, data: dict[str, Any], style: str) -> None:
        color, light, _ = style_color(style, theme)
        parts.append(rect(x, 150, 480, 560, "#ffffff", color, 16, 'filter="url(#shadow)"'))
        parts.append(rect(x, 150, 480, 84, color, color, 16))
        parts.append(rect(x, 212, 480, 24, color, color, 0))
        parts.append(icon(data.get("icon", "server"), x + 28, 176, 40, "#ffffff"))
        parts.append(text(x + 84, 200, data.get("title", "业务平台"), "dark-node"))
        if data.get("subtitle"):
            parts.append(text(x + 84, 226, data["subtitle"], "subtitle"))
        y = 258
        for layer in data.get("layers", [])[:4]:
            parts.append(rect(x + 28, y, 424, 96, light, color, 8))
            parts.append(text(x + 48, y + 38, layer.get("title", layer.get("label", "能力层")), "node"))
            items = layer.get("items", [])
            label = "、".join(str(item.get("title", item) if isinstance(item, dict) else item) for item in items[:4])
            svg_text_block(parts, x + 48, y + 68, label, "desc", 24, 28, limit=2)
            y += 112

    platform(48, left, "default")
    platform(1072, right, "success")

    # Central bidirectional data links.
    flow_y = 210
    for idx, flow in enumerate(flows[:6], start=1):
        color, _, _ = style_color(style_from_item(flow, idx - 1), theme)
        y = flow_y + (idx - 1) * 82
        parts.append(f'<path d="M548 {y} C 672 {y - 26}, 844 {y - 26}, 1052 {y}" fill="none" stroke="{color}" stroke-width="4" marker-end="url(#arrow-data)"/>')
        parts.append(rect(660, y - 42, 280, 42, "#ffffff", color, 21))
        parts.append(text(800, y - 14, flow.get("label", flow.get("title", f"接口链路{idx}")), "edge-label", "middle"))
        detail = flow.get("protocol") or flow.get("desc") or ""
        if detail:
            parts.append(text(800, y + 28, detail, "note", "middle"))
        if flow.get("ack", True):
            parts.append(f'<path d="M1052 {y + 32} C 902 {y + 72}, 700 {y + 72}, 548 {y + 32}" fill="none" stroke="{theme["sync"]}" stroke-width="2.4" stroke-dasharray="9 6" marker-end="url(#arrow-sync)"/>')
            parts.append(text(800, y + 72, flow.get("ackLabel", "ACK/校验反馈"), "note", "middle"))

    # Requirements and conclusion band.
    parts.append(rect(48, 740, 1504, 124, "#ffffff", theme["line"], 12, 'filter="url(#shadow)"'))
    parts.append(rect(48, 740, 230, 124, theme["accent_light"], theme["accent"], 12))
    parts.append(icon("shield", 86, 774, 50, theme["accent"]))
    parts.append(text(154, 810, figure.get("requirementsTitle", "接口约束"), "section"))
    req_x = 310
    for idx, req in enumerate(requirements[:4]):
        color, light, _ = style_color(style_from_item(req, idx), theme)
        parts.append(rect(req_x, 766, 280, 72, light, color, 8))
        title = req.get("title", req) if isinstance(req, dict) else req
        parts.append(text(req_x + 140, 810, str(title), "node", "middle"))
        req_x += 300

    if notes:
        note_w = 460
        for idx, note in enumerate(notes[:3]):
            x = 64 + idx * 500
            note.setdefault("style", style_from_item(note, idx))
            section_box(parts, x, 890, note_w, 112, note.get("title", f"说明{idx + 1}"), note.get("items", []), note.get("style", "default"), theme, note.get("icon"), 24, limit=2)

    note_bar(parts, figure.get("note", "接口关系图应同时表达链路方向、反馈机制、安全校验和异常处置边界。"), theme, height - 78)
    parts.append("</svg>")
    return "\n".join(parts)


def render_inspection_taxonomy(figure: dict[str, Any], theme: dict[str, str]) -> str:
    """Three-column inspection/category cards in the style of example figure 5."""

    categories = figure.get("categories", [])
    height = 1080
    parts = page_start(figure["title"], figure.get("subtitle", "例行巡检、专项巡检和异常触发巡检分类表达"), theme, height)
    formal_bid_css(parts)
    summary = figure.get("summary", "通过分类巡检机制，保障系统稳定运行、数据质量达标、接口畅通、终端在线可用。")
    parts.append(rect(110, 140, 1380, 64, theme["accent_light"], theme["line"], 8))
    parts.append(text(800, 182, summary, "node", "middle"))

    col_w, gap = 470, 38
    y = 250
    for idx, cat in enumerate(categories[:3], start=1):
        x = 52 + (idx - 1) * (col_w + gap)
        cat.setdefault("style", style_from_item(cat, idx - 1))
        color, _, _, body_y = formal_panel(
            parts, x, y, col_w, 680, cat.get("title", f"分类{idx}"), cat.get("style", "default"), theme,
            subtitle=cat.get("subtitle", ""), icon_name=cat.get("icon"), index=cat.get("index", idx)
        )
        if cat.get("trigger"):
            parts.append(rect(x + 176, body_y - 2, col_w - 206, 96, "#ffffff", color, 8, 'stroke-dasharray="6 4"'))
            parts.append(text(x + col_w - 168, body_y + 34, "触发方式", "node", "middle"))
            svg_text_block(parts, x + col_w - 168, body_y + 66, cat["trigger"], "desc", 16, 28, "middle", limit=2)
        if cat.get("icon"):
            parts.append(icon(cat["icon"], x + 52, body_y + 8, 82, color))
        section_box(parts, x + 38, body_y + 120, col_w - 76, 170, "巡检内容", cat.get("content", []), cat.get("style", "default"), theme, "search", 22, limit=3)
        section_box(parts, x + 38, body_y + 296, col_w - 76, 148, "核查要点", cat.get("checks", []), cat.get("style", "default"), theme, "form", 22, limit=3)
        section_box(parts, x + 38, body_y + 452, col_w - 76, 70, "输出成果", [cat.get("output", "巡检报告与整改建议")], cat.get("style", "default"), theme, "report", 22)

    outputs = figure.get("outputs", [])
    parts.append(rect(84, 956, 1432, 66, theme["accent_light"], theme["line"], 8))
    parts.append(icon("dashboard", 120, 970, 36, theme["accent"]))
    parts.append(text(178, 998, figure.get("outputsTitle", "总体输出"), "section"))
    for idx, value in enumerate(outputs[:4]):
        x = 400 + idx * 270
        parts.append(icon("check", x, 976, 26, theme["flow"]))
        parts.append(text(x + 40, 998, str(value), "node"))

    note_bar(parts, figure.get("note", "巡检发现的问题必须闭环管理，形成发现-处理-验证-归档-改进的持续优化机制。"), theme, height - 78)
    parts.append("</svg>")
    return "\n".join(parts)


def render_incident_response(figure: dict[str, Any], theme: dict[str, str]) -> str:
    """Fault severity table plus closed-loop handling flow, based on example figure 6."""

    levels = figure.get("levels", [])
    steps = figure.get("steps", [])
    safeguards = figure.get("safeguards", [])
    height = 1120
    parts = page_start(figure["title"], figure.get("subtitle", "故障分级响应标准与问题闭环处理流程"), theme, height)
    formal_bid_css(parts)
    parts.append("<style>.desc{font-size:17px}.note{font-size:16px}.node{font-size:22px}.section{font-size:27px}</style>")

    headers = figure.get("headers", ["级别", "故障定义", "典型场景示例", "响应时限", "处理时限", "服务方式", "升级条件"])
    col_x = [44, 190, 392, 760, 940, 1120, 1350]
    col_w = [146, 202, 368, 180, 180, 230, 206]
    table_y, row_h = 166, 116
    parts.append(text(44, 148, "【一】故障分级响应标准", "section"))
    for i, h in enumerate(headers):
        parts.append(rect(col_x[i], table_y, col_w[i], 46, theme["dark_card"], theme["dark_card"], 0))
        parts.append(text(col_x[i] + col_w[i] / 2, table_y + 31, h, "dark-node", "middle"))
    for r, level in enumerate(levels[:3]):
        y = table_y + 46 + r * row_h
        style = level.get("style", ["danger", "warning", "success"][min(r, 2)])
        color, light, _ = style_color(style, theme)
        for i in range(len(headers)):
            parts.append(rect(col_x[i], y, col_w[i], row_h, light if i == 0 else "#ffffff", theme["line"], 0))
        parts.append(icon(level.get("icon", "alert"), col_x[0] + 18, y + 34, 42, color))
        parts.append(text(col_x[0] + 92, y + 46, level.get("level", f"{r + 1}级"), "node", "middle"))
        parts.append(text(col_x[0] + 92, y + 78, level.get("name", ""), "node", "middle"))
        cells = [level.get("definition", ""), level.get("scenes", []), level.get("response", ""), level.get("handling", ""), level.get("service", ""), level.get("upgrade", "")]
        for i, cell in enumerate(cells, start=1):
            content = cell if isinstance(cell, list) else [cell]
            svg_text_block(parts, col_x[i] + 18, y + 34, [f"• {line}" for line in content] if i == 2 else content, "desc", max(8, int(col_w[i] / 28)), 24, limit=3)

    flow_y = 640
    parts.append(text(44, flow_y - 34, "【二】问题闭环处理流程", "section"))
    step_w, step_gap = 162, 32
    for idx, step in enumerate(steps[:7], start=1):
        x = 44 + (idx - 1) * (step_w + step_gap)
        step.setdefault("style", style_from_item(step, idx - 1))
        color, light, _ = style_color(step.get("style", "default"), theme)
        parts.append(rect(x, flow_y, step_w, 218, light, color, 10, 'filter="url(#shadow)"'))
        parts.append(text(x + step_w / 2, flow_y + 34, f"{idx}.{step.get('title', '')}", "node", "middle"))
        parts.append(f'<circle cx="{x + step_w / 2:g}" cy="{flow_y + 82:g}" r="30" fill="{color}"/>')
        parts.append(icon(step.get("icon", "workflow"), x + step_w / 2 - 18, flow_y + 64, 36, "#ffffff"))
        svg_text_block(parts, x + 18, flow_y + 132, step.get("desc", ""), "note", 9, 25, limit=3)
        parts.append(rect(x, flow_y + 184, step_w, 34, "#ffffff", color, 0))
        parts.append(text(x + step_w / 2, flow_y + 208, "输出：" + step.get("output", ""), "note", "middle"))
        if idx < min(7, len(steps)):
            ax = x + step_w + 6
            parts.append(f'<path d="M{ax} {flow_y + 104} H{ax + step_gap - 12}" fill="none" stroke="{theme["flow"]}" stroke-width="4" marker-end="url(#arrow-flow)"/>')

    if len(steps) > 1:
        parts.append(f'<path d="M{44 + 6 * (step_w + step_gap) + step_w / 2:g} {flow_y + 250} H{44 + step_w / 2:g} V{flow_y + 228}" fill="none" stroke="{theme["flow"]}" stroke-width="3" stroke-dasharray="10 7" marker-end="url(#arrow-flow)"/>')
        parts.append(text(800, flow_y + 274, figure.get("loopLabel", "持续改进，形成闭环"), "edge-label", "middle"))

    parts.append(rect(44, 980, 1512, 74, theme["accent_light"], theme["line"], 8))
    parts.append(rect(70, 998, 154, 38, theme["accent"], theme["accent"], 5))
    parts.append(text(147, 1025, "关键保障措施", "dark-node", "middle"))
    for idx, item in enumerate(safeguards[:5]):
        x = 286 + idx * 250
        parts.append(icon(item.get("icon", "shield") if isinstance(item, dict) else "shield", x, 1000, 36, theme["flow"]))
        title = item.get("title", item) if isinstance(item, dict) else item
        desc = item.get("desc", "") if isinstance(item, dict) else ""
        parts.append(text(x + 50, 1018, str(title), "node"))
        if desc:
            parts.append(text(x + 50, 1043, desc, "note"))

    parts.append("</svg>")
    return "\n".join(parts)


def render_security_ring(figure: dict[str, Any], theme: dict[str, str]) -> str:
    """Central core with five surrounding assurance measures, matching example figure 7 style."""

    measures = figure.get("measures", [])
    height = 1180
    parts = page_start(figure["title"], figure.get("subtitle", "多层协同防护 · 全流程闭环管理"), theme, height)
    formal_bid_css(parts)
    parts.append("<style>.node{font-size:21px}.desc{font-size:18px}.dark-node{font-size:23px}.section{font-size:27px}</style>")
    cx, cy = 800, 590
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="360" fill="none" stroke="{theme["flow"]}" stroke-width="18" opacity="0.55"/>')
    parts.append(f'<circle cx="{cx}" cy="{cy}" r="418" fill="none" stroke="{theme["flow"]}" stroke-width="2.4" stroke-dasharray="12 10" opacity="0.75"/>')
    points = [(800, 230), (1165, 430), (1035, 790), (565, 790), (435, 430)]
    for idx, measure in enumerate(measures[:5], start=1):
        x, y = points[idx - 1]
        style = measure.get("style", role_for_index(idx - 1))
        color, light, _ = style_color(style, theme)
        w, h = 300, 196
        px, py = x - w / 2, y - h / 2
        parts.append(rect(px, py, w, h, "#ffffff", color, 14, 'filter="url(#shadow)"'))
        parts.append(rect(px + 16, py + 16, w - 32, 70, color, color, 8))
        parts.append(f'<circle cx="{px + 48:g}" cy="{py + 14:g}" r="26" fill="{color}"/>')
        parts.append(text(px + 48, py + 26, str(measure.get("index", idx)), "dark-node", "middle"))
        parts.append(text(px + w / 2, py + 59, measure.get("title", f"措施{idx}"), "dark-node", "middle"))
        bullet_list(parts, px + 42, py + 108, measure.get("items", []), color, 14, limit=3)
        parts.append(f'<path d="M{x} {y + (h / 2 if y < cy else -h / 2)} L{cx} {cy}" fill="none" stroke="{color}" stroke-width="2.5" stroke-dasharray="8 7" marker-end="url(#arrow-data)"/>')

    core = figure.get("core", {})
    parts.append(f'<path d="M{cx} {cy - 160} L{cx + 188} {cy - 22} L{cx + 116} {cy + 196} H{cx - 116} L{cx - 188} {cy - 22} Z" fill="#f2f7ff" stroke="{theme["flow"]}" stroke-width="5" filter="url(#shadow)"/>')
    parts.append(icon(core.get("icon", "lock"), cx - 54, cy - 100, 108, theme["flow"]))
    svg_text_block(parts, cx, cy + 20, core.get("title", "数据安全保密\n保障体系").split("\n"), "section", 12, 44, "middle", limit=3)
    svg_text_block(parts, cx, cy + 120, core.get("desc", "合规为基 · 技术为盾 · 管理为纲 · 闭环可控"), "node", 14, 30, "middle", limit=2)

    loop = figure.get("loop", [])
    parts.append(text(cx, 1032, figure.get("loopTitle", "管理闭环"), "section", "middle"))
    parts.append(rect(112, 1050, 1376, 82, "#ffffff", theme["line"], 10))
    for idx, item in enumerate(loop[:6]):
        x = 160 + idx * 218
        parts.append(icon(item.get("icon", "check") if isinstance(item, dict) else "check", x, 1074, 40, theme["flow"]))
        title = item.get("title", item) if isinstance(item, dict) else item
        parts.append(text(x + 54, 1098, str(title), "node"))
        if idx < min(6, len(loop)) - 1:
            parts.append(f'<path d="M{x + 164} 1092 H{x + 196}" fill="none" stroke="{theme["flow"]}" stroke-width="3" marker-end="url(#arrow-flow)"/>')

    parts.append("</svg>")
    return "\n".join(parts)


RENDERERS = {
    "layered_architecture": render_layered_architecture,
    "flowchart": render_flowchart,
    "sequence_diagram": render_sequence_diagram,
    "swimlane_flowchart": render_swimlane_flowchart,
    "capability_map": render_capability_map,
    "relationship_map": render_relationship_map,
    "interface_map": render_interface_map,
    "inspection_taxonomy": render_inspection_taxonomy,
    "incident_response": render_incident_response,
    "security_ring": render_security_ring,
}


def render_icon_catalog(theme: dict[str, str]) -> str:
    columns = 4
    card_w, card_h = 355, 72
    gap_x, gap_y = 16, 14
    rows = math.ceil(len(ICONS) / columns)
    height = 145 + rows * (card_h + gap_y) + 58
    parts = page_start("内置 SVG 图标语义目录", "供大模型在绘图描述中引用 / icon identifier catalog", theme, height)
    for index, (key, (label, _)) in enumerate(ICONS.items()):
        row, col = divmod(index, columns)
        x = 58 + col * (card_w + gap_x)
        y = 122 + row * (card_h + gap_y)
        parts.append(rect(x, y, card_w, card_h, theme["card"], theme["line"], 10, 'filter="url(#shadow)"'))
        parts.append(icon(key, x + 18, y + 22, 28, theme["accent"]))
        parts.append(text(x + 60, y + 30, label, "node-lg"))
        parts.append(text(x + 60, y + 53, key, "desc"))
    note_bar(parts, "大模型仅需输出 icon 标识，渲染器统一生成矢量图标并保持整本文档风格一致。", theme, height - 48)
    parts.append("</svg>")
    return "\n".join(parts)


def load_spec(document: Path | None, spec_file: Path | None) -> tuple[dict[str, Any], str]:
    if spec_file:
        return json.loads(spec_file.read_text(encoding="utf-8")), str(spec_file)
    if not document:
        raise ValueError("必须提供 --document 或 --spec 参数")
    content = document.read_text(encoding="utf-8")
    match = re.search(r"```svg-diagrams\s*\n(.*?)\n```", content, re.DOTALL)
    if not match:
        raise ValueError(f"文档未包含 ```svg-diagrams JSON 配置块: {document}")
    return json.loads(match.group(1)), str(document)


def validate_spec(spec: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    try:
        import jsonschema
        schema_file = Path(__file__).resolve().parent.parent / "schemas" / "svg_diagram.schema.json"
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
        validator = jsonschema.Draft202012Validator(schema)
        for issue in sorted(validator.iter_errors(spec), key=lambda err: list(err.path)):
            position = ".".join(str(value) for value in issue.path) or "<root>"
            errors.append(f"{position}: {issue.message}")
    except ImportError:
        pass
    figures = spec.get("figures", [])
    for index, figure in enumerate(figures, start=1):
        prefix = f"figures[{index - 1}]"
        diagram_type = figure.get("type")
        if diagram_type not in RENDERERS:
            errors.append(f"{prefix}.type: 不支持的图型 {diagram_type}")
        used_icons: list[str] = []
        for key in ("actors", "integrations", "nodes", "participants", "steps"):
            used_icons.extend(item.get("icon") for item in figure.get(key, []) if isinstance(item, dict) and item.get("icon"))
        used_icons.extend(lane.get("icon") for lane in figure.get("lanes", []) if lane.get("icon"))
        for layer in figure.get("layers", []):
            used_icons.extend(item.get("icon") for item in layer.get("items", []) if isinstance(item, dict) and item.get("icon"))
        for group in figure.get("groups", []):
            if group.get("icon"):
                used_icons.append(group["icon"])
            used_icons.extend(item.get("icon") for item in group.get("items", []) if isinstance(item, dict) and item.get("icon"))
        for container in figure.get("containers", []):
            if container.get("icon"):
                used_icons.append(container["icon"])
            used_icons.extend(item.get("icon") for item in container.get("nodes", []) if isinstance(item, dict) and item.get("icon"))
        for icon_name in used_icons:
            if icon_name not in ICONS:
                errors.append(f"{prefix}: 未知图标 `{icon_name}`")
        if diagram_type in ("flowchart", "relationship_map"):
            if diagram_type == "flowchart":
                node_ids = [node.get("id") for node in figure.get("nodes", [])]
                node_path = "nodes"
            else:
                node_ids = [
                    node.get("id")
                    for container in figure.get("containers", [])
                    for node in container.get("nodes", [])
                ]
                node_path = "containers.nodes"
            if len(node_ids) != len(set(node_ids)):
                errors.append(f"{prefix}.{node_path}: 节点 id 必须唯一")
            for edge in figure.get("edges", []):
                for endpoint in ("from", "to"):
                    if edge.get(endpoint) not in node_ids:
                        errors.append(f"{prefix}.edges: 连线引用未知节点 `{edge.get(endpoint)}`")
        if diagram_type == "sequence_diagram":
            participant_ids = [participant.get("id") for participant in figure.get("participants", [])]
            if len(participant_ids) != len(set(participant_ids)):
                errors.append(f"{prefix}.participants: 参与方 id 必须唯一")
            for message in figure.get("messages", []):
                for endpoint in ("from", "to"):
                    if message.get(endpoint) not in participant_ids:
                        errors.append(f"{prefix}.messages: 消息引用未知参与方 `{message.get(endpoint)}`")
        if diagram_type == "swimlane_flowchart":
            lane_ids = [lane.get("id") for lane in figure.get("lanes", [])]
            step_ids = [step.get("id") for step in figure.get("steps", [])]
            if len(lane_ids) != len(set(lane_ids)):
                errors.append(f"{prefix}.lanes: 泳道 id 必须唯一")
            if len(step_ids) != len(set(step_ids)):
                errors.append(f"{prefix}.steps: 步骤 id 必须唯一")
            for step in figure.get("steps", []):
                if step.get("lane") not in lane_ids:
                    errors.append(f"{prefix}.steps: 步骤引用未知泳道 `{step.get('lane')}`")
            for edge in figure.get("edges", []):
                for endpoint in ("from", "to"):
                    if edge.get(endpoint) not in step_ids:
                        errors.append(f"{prefix}.edges: 连线引用未知步骤 `{edge.get(endpoint)}`")
    return errors


def quality_warnings(spec: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    for index, figure in enumerate(spec.get("figures", [])):
        diagram_type = figure.get("type")
        if diagram_type == "flowchart":
            nodes = figure.get("nodes", [])
            rows = {node.get("row", 0) for node in nodes}
            if len(nodes) > 16:
                warnings.append(f"figures[{index}]: 流程节点数为 {len(nodes)}，建议拆分为总览图和子流程图")
            if len(rows) > 5:
                warnings.append(f"figures[{index}]: 流程层级为 {len(rows)} 行，正式文档中可能需要分页或拆图")
        if diagram_type == "relationship_map" and len(figure.get("edges", [])) > 12:
            warnings.append(f"figures[{index}]: 关系连线超过 12 条，建议拆分域间关系和域内关系")
    return warnings


def render_png(svg: str, target: Path, width: int, height: int, scale: int = 2) -> bool:
    try:
        import cairosvg  # type: ignore
        cairosvg.svg2png(bytestring=svg.encode("utf-8"), write_to=str(target),
                          output_width=width * scale, output_height=height * scale)
        return True
    except (ImportError, OSError):
        pass
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": width, "height": height},
                device_scale_factor=scale,
            )
            page.set_content(f'<html><body style="margin:0">{svg}</body></html>', wait_until="domcontentloaded")
            page.locator("svg").screenshot(path=str(target), timeout=120000, animations="disabled")
            browser.close()
        return True
    except Exception as exc:
        print(f"  PNG 渲染失败: {exc}")
        return False


def write_manifest(output: Path, source: str, theme_results: list[dict[str, Any]]) -> None:
    lines = [
        "# SVG 框图生成清单",
        "",
        f"- 输入来源：`{source}`",
        f"- 生成图数：`{len(theme_results)}`",
        "",
        "| 建议插入位置 | 图题 | 类型 | 主题 | SVG | PNG |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for result in theme_results:
        png = f"[查看](<{result['png']}>)" if result.get("png") else "-"
        lines.append(
            f"| {result.get('placement', '-')} | {result['title']} | `{result['type']}` | {result['theme']} | "
            f"[查看](<{result['svg']}>) | {png} |"
        )
    lines.extend(["", "## 预览", ""])
    for result in theme_results:
        if result.get("png"):
            lines.extend([f"### {result['title']}（{result['theme']}）", "", f"![{result['title']}](<{result['png']}>)", ""])
    (output / "生成清单.md").write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="从标书文档中的图示配置生成专业 SVG 框图")
    parser.add_argument("--document", type=Path, help="包含 svg-diagrams JSON 配置块的 Markdown 文档")
    parser.add_argument("--spec", type=Path, help="独立 JSON 图示规范文件")
    parser.add_argument("--output", type=Path, default=Path.cwd() / "output" / "svg_diagrams", help="输出目录")
    parser.add_argument("--theme", choices=THEMES.keys(), default="clarity_blue", help="配色主题")
    parser.add_argument("--all-themes", action="store_true", help="按全部主题生成配色对比")
    parser.add_argument("--png", action="store_true", help="同时生成 PNG 预览")
    parser.add_argument("--png-scale", type=int, choices=(1, 2, 3), default=2, help="PNG 栅格输出倍率，正式文档推荐 2 或 3")
    parser.add_argument("--validate-only", action="store_true", help="仅校验绘图描述，不生成文件")
    parser.add_argument("--list-icons", action="store_true", help="输出可供 AI 使用的内置图标目录")
    parser.add_argument("--render-icon-catalog", action="store_true", help="生成内置图标的 SVG/PNG 预览目录")
    parser.add_argument("--font-scale", type=float, default=1.0, help="全局字体和布局缩放比例 (默认 1.0，如 0.88 缩小 12%%)")
    args = parser.parse_args()

    if args.list_icons:
        print("内置图标标识：")
        for key, (label, _) in ICONS.items():
            print(f"  {key:<14} {label}")
        return
    if args.render_icon_catalog:
        output = args.output.resolve()
        output.mkdir(parents=True, exist_ok=True)
        theme = THEMES[args.theme]
        svg = render_icon_catalog(theme)
        svg_path = output / "内置SVG图标目录.svg"
        svg_path.write_text(svg, encoding="utf-8")
        height_match = re.search(r'height="(\d+)"', svg)
        height = int(height_match.group(1)) if height_match else 700
        if args.png:
            render_png(svg, output / "内置SVG图标目录.png", WIDTH, height)
        print(f"图标目录已生成: {svg_path}")
        return

    spec, source = load_spec(args.document, args.spec)
    errors = validate_spec(spec)
    if errors:
        print(f"图示描述校验失败: {source}")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(2)
    warnings = quality_warnings(spec)
    if warnings:
        print("图件可读性提示:")
        for warning in warnings:
            print(f"  - {warning}")
    if args.validate_only:
        print(f"图示描述校验通过: {source} ({len(spec.get('figures', []))} 张图)")
        return
    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    if args.font_scale != 1.0:
        apply_font_scale(args.font_scale)
        print(f"字体缩放: {args.font_scale}x")

    themes = list(THEMES) if args.all_themes else [args.theme]
    results: list[dict[str, Any]] = []

    figures = spec.get("figures", [])
    if not figures:
        raise ValueError("图示配置中未定义 figures")
    print(f"输入: {source}")
    print(f"输出: {output}")
    for figure_index, figure in enumerate(figures, start=1):
        diagram_type = figure.get("type")
        if diagram_type not in RENDERERS:
            raise ValueError(f"不支持的图型: {diagram_type}; 可选 {', '.join(RENDERERS)}")
        for theme_key in themes:
            theme = THEMES[theme_key]
            palette_name = figure.get("palette") or select_palette_for_payload(figure, diagram_type)
            with use_palette(palette_name):
                svg = RENDERERS[diagram_type](figure, _theme_with_palette(theme))
            suffix = f"_{theme_key}" if args.all_themes else ""
            filename = f"{figure_index:02d}_{slug(figure['title'])}{suffix}"
            svg_name = f"{filename}.svg"
            (output / svg_name).write_text(svg, encoding="utf-8")
            height_match = re.search(r'height="(\d+)"', svg)
            height = int(height_match.group(1)) if height_match else 1000
            png_output_dir = output / "png"
            png_output_dir.mkdir(parents=True, exist_ok=True)
            png_name = f"{filename}.png" if args.png and render_png(svg, png_output_dir / f"{filename}.png", WIDTH, height, args.png_scale) else None
            results.append({
                "title": figure["title"],
                "type": diagram_type,
                "placement": figure.get("placement", "-"),
                "theme": theme["name"],
                "svg": svg_name,
                "png": png_name,
            })
            print(f"  {figure_index:02d}. {figure['title']} [{theme['name']}] -> {svg_name}")
    write_manifest(output, source, results)
    (output / "result.json").write_text(json.dumps(results, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"完成: {output / '生成清单.md'}")


if __name__ == "__main__":
    main()
