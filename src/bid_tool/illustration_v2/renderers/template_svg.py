"""Frozen-template SVG renderer for illustration v2."""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from ..core.catalog import build_capability_catalog
from ..core.models import AssetRecord, IllustrationJob, PlanDecision, Template
from ..core.text_measure import TextSlot, emit_text, xml_escape
from . import components as ui


WIDTH = 1600
HEIGHT = 980
PACKAGE_DIR = Path(__file__).resolve().parents[1]

THEMES = {
    "formal_blue": {
        "primary": "#123f6d",
        "primary_alt": "#1f78a8",
        "line": "#c9d8e8",
        "wash": "#f4f8fc",
        "text": "#10253f",
        "muted": "#55708c",
        "card": "#ffffff",
    },
    "formal_green": {
        "primary": "#155f50",
        "primary_alt": "#26826f",
        "line": "#c8ded8",
        "wash": "#f2faf7",
        "text": "#12352f",
        "muted": "#587870",
        "card": "#ffffff",
    },
}


def render_decision(
    job: IllustrationJob,
    decision: PlanDecision,
    output: Path,
    *,
    theme: str,
    png: bool = False,
    png_scale: int = 2,
) -> AssetRecord:
    output_dir = output / "assets" / "svg"
    output_dir.mkdir(parents=True, exist_ok=True)

    if decision.renderer == "template_svg" and decision.template_id == "arch.layered.v2":
        template = _find_template(decision.template_id)
        svg = _render_arch_layered(decision, template, job, theme)
    elif decision.renderer == "template_svg" and decision.template_id == "platform.interface.v2":
        svg = _render_platform_interface(decision, job, theme)
    elif decision.renderer == "template_svg" and decision.template_id == "process.resilience.v2":
        svg = _render_resilience_flow(decision, job, theme)
    elif decision.renderer == "template_svg" and decision.template_id == "inspection.cards.v2":
        svg = _render_inspection_cards(decision, job, theme)
    elif decision.renderer == "template_svg" and decision.template_id == "severity.closure.v2":
        svg = _render_severity_closure(decision, job, theme)
    elif decision.renderer == "template_svg" and decision.template_id == "security.loop.v2":
        svg = _render_security_loop(decision, job, theme)
    elif decision.renderer == "structured_svg_fallback":
        svg = _render_structured_fallback(decision, job, theme)
    else:
        svg = _render_free_floor(decision, job, theme)

    svg_path = output_dir / f"{_safe_name(decision.item.id)}.svg"
    svg_path.write_text(svg, encoding="utf-8")
    outputs = {"svg": svg_path.relative_to(output).as_posix()}
    warnings: list[str] = []
    if png:
        png_dir = output / "assets" / "png"
        png_dir.mkdir(parents=True, exist_ok=True)
        png_path = png_dir / f"{_safe_name(decision.item.id)}.png"
        if _svg_to_png(svg, png_path, png_scale):
            outputs["png"] = png_path.relative_to(output).as_posix()
        else:
            warnings.append("PNG export failed; SVG output is still available.")
    return AssetRecord(
        id=decision.item.id,
        type=decision.item.type,
        renderer=decision.renderer,
        section=str(decision.item.insertion.get("section", "")),
        caption=str(decision.item.insertion.get("caption", decision.item.id)),
        outputs=outputs,
        template=decision.template_id,
        theme=theme,
        fit_score=decision.fit_score,
        tier=decision.tier,
        degraded_from=decision.degraded_from,
        needs_human_review=decision.needs_human_review,
        warnings=warnings,
        decision=decision.to_dict()["decision"],
    )


def _render_arch_layered(
    decision: PlanDecision,
    template: Template,
    job: IllustrationJob,
    theme_name: str,
) -> str:
    item = decision.item
    data = item.data
    theme = _theme(theme_name, template.theme_vars)
    svg = _load_template(template)
    return _apply_tokens(svg, _arch_layered_tokens(item, job, theme))


def _layer_svg(layer: dict[str, Any], layer_index: int, y: int, theme: dict[str, str]) -> str:
    label = str(layer.get("label", layer.get("title", f"Layer {layer_index + 1}")))
    items = layer.get("items", [])[:4]
    x = 64
    width = 1472
    header_h = 46
    card_y = y + 70
    slot_w = 342
    gap = 20
    cards = []
    for index, node in enumerate(items):
        cx = 92 + index * (slot_w + gap)
        cards.append(_card_svg(node, cx, card_y, slot_w, 112, theme, index))
    return f'''<g>
<rect x="{x}" y="{y}" width="{width}" height="210" rx="12" fill="{theme["wash"]}" stroke="{theme["line"]}" stroke-width="1.5"/>
<rect x="{x}" y="{y}" width="{width}" height="{header_h}" rx="12" fill="{theme["primary"]}"/>
<rect x="{x}" y="{y + 34}" width="{width}" height="14" fill="{theme["primary"]}"/>
<text x="{x + 24}" y="{y + 31}" font-family="Microsoft YaHei, Arial" font-size="22" font-weight="700" fill="#ffffff">{_xml(label)}</text>
{''.join(cards)}
</g>'''


def _card_svg(
    node: dict[str, Any],
    x: int,
    y: int,
    width: int,
    height: int,
    theme: dict[str, str],
    index: int,
) -> str:
    title = str(node.get("title", f"Node {index + 1}"))[:16]
    desc = str(node.get("desc", ""))[:42]
    icon = str(node.get("icon", "server"))[:18]
    style = str(node.get("style", "default"))
    accent = _style_color(style, theme)
    return f'''<g>
<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="10" fill="{theme["card"]}" stroke="{accent}" stroke-width="1.8"/>
<circle cx="{x + 36}" cy="{y + 35}" r="18" fill="{accent}"/>
<text x="{x + 36}" y="{y + 41}" text-anchor="middle" font-family="Arial" font-size="14" font-weight="700" fill="#ffffff">{_xml(icon[:2].upper())}</text>
<text x="{x + 68}" y="{y + 34}" font-family="Microsoft YaHei, Arial" font-size="20" font-weight="700" fill="{theme["text"]}">{_xml(title)}</text>
<text x="{x + 22}" y="{y + 78}" font-family="Microsoft YaHei, Arial" font-size="16" fill="{theme["muted"]}">{_xml(desc)}</text>
</g>'''


def _render_platform_interface(decision: PlanDecision, job: IllustrationJob, theme_name: str) -> str:
    item = decision.item
    data = item.data
    theme = _theme(theme_name, _template_theme(decision))
    left = data.get("left", {})
    right = data.get("right", {})
    flows = _as_list(data.get("flows"))[:5]
    requirements = _as_list(data.get("requirements"))[:6]
    flow_svg = []
    colors = ["#1f78b4", "#3f8f5f", "#ef7d22", "#7357a6", "#2c7a7b"]
    for index, flow in enumerate(flows):
        y = 230 + index * 104
        color = str(flow.get("color", colors[index % len(colors)]))
        reverse = flow.get("direction") == "right_to_left"
        x1, x2 = (1000, 600) if reverse else (600, 1000)
        flow_svg.append(
            f'''<g>
<text x="800" y="{y - 22}" text-anchor="middle" font-family="Microsoft YaHei, Arial" font-size="21" font-weight="700" fill="{color}">{index + 1}. {_xml(flow.get("label", ""))}</text>
<line x1="{x1}" y1="{y}" x2="{x2}" y2="{y}" stroke="{color}" stroke-width="6" marker-end="url(#arrow-{index})"/>
<text x="800" y="{y + 38}" text-anchor="middle" font-family="Microsoft YaHei, Arial" font-size="18" fill="{theme["text"]}">{_xml(flow.get("protocol", ""))}</text>
<line x1="{x2}" y1="{y + 54}" x2="{x1}" y2="{y + 54}" stroke="{color}" stroke-width="2" stroke-dasharray="8 7" marker-end="url(#arrow-dash-{index})"/>
</g>'''
        )
    req_svg = []
    for index, req in enumerate(requirements):
        x = 186 + index * 216
        req_svg.append(
            f'''<g>
<circle cx="{x}" cy="842" r="23" fill="#ffffff" stroke="{theme["primary_alt"]}" stroke-width="3"/>
<text x="{x}" y="850" text-anchor="middle" font-family="Arial" font-size="17" font-weight="700" fill="{theme["primary_alt"]}">{_xml(req.get("icon", "OK")[:2].upper())}</text>
<text x="{x + 38}" y="833" font-family="Microsoft YaHei, Arial" font-size="19" font-weight="700" fill="{theme["primary"]}">{_xml(req.get("title", ""))}</text>
<text x="{x + 38}" y="861" font-family="Microsoft YaHei, Arial" font-size="15" fill="{theme["muted"]}">{_xml(req.get("desc", ""))}</text>
</g>'''
        )
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
{_defs(colors)}
<rect width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>
{_title_block(data, item, job, theme)}
{_platform_box(left, 28, 130, 540, 612, "#2b7fc8", theme)}
{_platform_box(right, 1032, 130, 540, 612, "#5a8f45", theme)}
{''.join(flow_svg)}
<rect x="28" y="782" width="1544" height="112" rx="8" fill="#f7fbff" stroke="{theme["line"]}" stroke-dasharray="4 4"/>
<rect x="44" y="802" width="102" height="72" rx="6" fill="{theme["primary_alt"]}"/>
<text x="95" y="832" text-anchor="middle" font-family="Microsoft YaHei, Arial" font-size="19" font-weight="700" fill="#ffffff">{_xml(data.get("requirementsTitle", "Requirements"))}</text>
<text x="95" y="858" text-anchor="middle" font-family="Microsoft YaHei, Arial" font-size="19" font-weight="700" fill="#ffffff">{_xml(data.get("requirementsSubtitle", ""))}</text>
{''.join(req_svg)}
<rect x="616" y="916" width="368" height="38" rx="6" fill="#eef8ff" stroke="#9dcced"/>
<text x="800" y="941" text-anchor="middle" font-family="Microsoft YaHei, Arial" font-size="19" font-weight="700" fill="{theme["primary_alt"]}">{_xml(data.get("footer", "Traceable, auditable, closed-loop data exchange"))}</text>
</svg>'''


def _render_resilience_flow(decision: PlanDecision, job: IllustrationJob, theme_name: str) -> str:
    item = decision.item
    data = item.data
    theme = _theme(theme_name, _template_theme(decision))
    component_theme = ui.Theme.from_dict(theme)
    steps = _as_list(data.get("steps"))[:8]
    exceptions = _as_list(data.get("exceptions"))[:6]
    mechanisms = _as_list(data.get("mechanisms"))[:4]
    side_panels = _as_list(data.get("sidePanels"))[:2]
    assurance = _as_list(data.get("assurance"))[:5]
    step_svg = []
    for index, step in enumerate(steps):
        x = 32 + index * 187
        step_svg.append(ui.flow_step(step, index + 1, x, 150, 154, 82, theme=component_theme, color="#2b7fc8"))
        if index < len(steps) - 1:
            step_svg.append(ui.connector([(x + 154, 191), (x + 184, 191)], color="#2b7fc8", width=3))
    exception_svg = []
    for index, ex in enumerate(exceptions):
        y = 310 + index * 80
        exception_svg.append(ui.exception_card(ex, 36, y, 286, 64, theme=component_theme, color="#d64b3b"))
    mech_svg = _resilience_loop_components(mechanisms, component_theme)
    side_svg = []
    for index, panel in enumerate(side_panels):
        side_svg.append(ui.info_panel(panel, 1240, 298 + index * 190, 306, 154, color=["#3f8f5f", "#7357a6"][index % 2], theme=component_theme))
    ass_svg = []
    for index, item_data in enumerate(assurance):
        x = 260 + index * 270
        ass_svg.append(ui.assurance_chip(item_data, x, 842, theme=component_theme))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
{_defs(["#2b7fc8", "#d64b3b", "#f6a126", "#41a56a", "#7357a6"])}
<rect width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>
{_title_block(data, item, job, theme)}
{ui.panel(22, 126, 1556, 126, fill="#f7fbff", stroke="#9db8d6")}
{ui.tab_label(data.get("normalTitle", "Normal Flow"), 30, 116, 250, 42, color=theme["primary_alt"], size=20)}
{''.join(step_svg)}
{ui.panel(24, 286, 312, 478, fill="#fffafa", stroke="#efb4a7", rx=10)}
{ui.tab_label(data.get("exceptionTitle", "Exception Scenarios"), 40, 270, 220, 44, color="#f0523d", size=20)}
{''.join(exception_svg)}
{ui.panel(370, 286, 820, 478, fill="#fffdf8", stroke="#efcc84", rx=10)}
{ui.tab_label(data.get("mechanismTitle", "Handling And Compensation"), 388, 270, 368, 44, color="#f59b23", size=19)}
{''.join(mech_svg)}
{''.join(side_svg)}
{ui.panel(24, 812, 1552, 76, fill="#f7fbff", stroke="#9dcced", rx=4)}
{_text(data.get("assuranceTitle", "Assurance Points"), 58, 832, 170, 34, 19, theme["primary"], weight=700, min_size=13, max_lines=1)}
{''.join(ass_svg)}
{_text(data.get("legend", "实线：正常流程；虚线：异常与重试流程"), 60, 918, 900, 28, 15, theme["muted"], min_size=11, max_lines=1)}
</svg>'''


def _render_inspection_cards(decision: PlanDecision, job: IllustrationJob, theme_name: str) -> str:
    item = decision.item
    data = item.data
    theme = _theme(theme_name, _template_theme(decision))
    categories = _as_list(data.get("categories"))[:4]
    colors = ["#2fa45a", "#2777bf", "#ef7d22", "#7357a6"]
    card_w = 478 if len(categories) <= 3 else 360
    gap = 44 if len(categories) <= 3 else 30
    start_x = int((WIDTH - len(categories) * card_w - (len(categories) - 1) * gap) / 2)
    cards = []
    for index, category in enumerate(categories):
        cards.append(_inspection_card(category, index + 1, start_x + index * (card_w + gap), 220, card_w, 546, colors[index % 4], theme))
    outputs = _as_list(data.get("outputs"))[:4]
    output_svg = []
    for index, output in enumerate(outputs):
        x = 430 + index * 260
        output_svg.append(_text(f"- {output}", x, 818, 238, 34, 18, theme["text"], min_size=12, max_lines=1))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
<rect width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>
{_title_block(data, item, job, theme, top=42)}
<rect x="168" y="112" width="1264" height="64" rx="8" fill="#f7fbff" stroke="#95bce5"/>
<text x="800" y="152" text-anchor="middle" font-family="Microsoft YaHei, Arial" font-size="23" font-weight="700" fill="{theme["text"]}">{_xml(data.get("summary", ""))}</text>
<line x1="800" y1="176" x2="800" y2="210" stroke="{theme["primary"]}" stroke-width="2"/>
{''.join(cards)}
<rect x="78" y="806" width="1444" height="58" rx="8" fill="#f7fbff" stroke="#9dcced"/>
<text x="130" y="843" font-family="Microsoft YaHei, Arial" font-size="24" font-weight="700" fill="{theme["primary"]}">{_xml(data.get("outputTitle", "Overall Output"))}</text>
{''.join(output_svg)}
<rect x="78" y="902" width="1444" height="48" rx="6" fill="#ffffff" stroke="#9dcced" stroke-dasharray="7 5"/>
<text x="168" y="932" font-family="Microsoft YaHei, Arial" font-size="20" font-weight="700" fill="{theme["primary"]}">{_xml(data.get("principleTitle", "Principle"))}</text>
<text x="300" y="932" font-family="Microsoft YaHei, Arial" font-size="19" fill="{theme["text"]}">{_xml(data.get("principle", ""))}</text>
</svg>'''


def _resilience_loop_components(mechanisms: list[Any], theme: ui.Theme) -> str:
    defaults = [
        {"title": "异常捕获", "desc": "记录原因时间来源"},
        {"title": "自动重试", "desc": "按策略重试上报"},
        {"title": "补传成功？", "desc": "核验补传结果"},
        {"title": "人工复核", "desc": "修正后重新提交"},
    ]
    nodes = [(item if isinstance(item, dict) else {}) for item in mechanisms[:4]]
    while len(nodes) < 4:
        nodes.append(defaults[len(nodes)])

    colors = ["#f59b23", "#41a56a", "#7357a6", "#2b7fc8"]
    slots = [
        (488, 432, 188, 92),
        (690, 330, 188, 92),
        (894, 432, 188, 92),
        (690, 562, 188, 92),
    ]
    parts = [
        ui.loop_connector(505, 358, 560, 280, color="#8aa7c8", marker_id="arrow-dash-0"),
    ]
    for index, node in enumerate(nodes):
        x, y, w, h = slots[index]
        parts.append(ui.process_node(node, x, y, w, h, color=colors[index], theme=theme))

    parts.extend(
        [
            ui.connector([(676, 468), (690, 390)], color="#41a56a", marker_id="arrow-3", width=4),
            ui.connector([(878, 390), (894, 468)], color="#41a56a", marker_id="arrow-3", width=4),
            ui.connector([(988, 524), (878, 608)], color="#d64b3b", marker_id="arrow-1", width=4),
            ui.connector([(690, 608), (676, 508)], color="#7357a6", marker_id="arrow-4", width=4),
            ui.connector([(600, 524), (600, 676), (784, 676), (784, 654)], color="#2b7fc8", marker_id="arrow-0", width=3, dashed=True),
        ]
    )
    return "".join(parts)


def _render_severity_closure(decision: PlanDecision, job: IllustrationJob, theme_name: str) -> str:
    item = decision.item
    data = item.data
    theme = _theme(theme_name, _template_theme(decision))
    levels = _as_list(data.get("levels"))[:4]
    steps = _as_list(data.get("steps"))[:8]
    measures = _as_list(data.get("measures"))[:5]
    row_svg = []
    row_h = 102
    headers = ["Level", "Definition", "Scenario", "Response", "Handling", "Service", "Escalation"]
    col_x = [22, 186, 380, 704, 888, 1080, 1274]
    col_w = [164, 194, 324, 184, 192, 194, 282]
    for index, header in enumerate(headers):
        row_svg.append(f'''<rect x="{col_x[index]}" y="106" width="{col_w[index]}" height="44" fill="{theme["primary"]}" stroke="#ffffff"/><text x="{col_x[index] + col_w[index] / 2}" y="134" text-anchor="middle" font-family="Microsoft YaHei, Arial" font-size="18" font-weight="700" fill="#ffffff">{_xml(header)}</text>''')
    sev_colors = ["#d9363e", "#f58a23", "#4ba34f", "#2b7fc8"]
    for index, level in enumerate(levels):
        y = 150 + index * row_h
        fill = "#fffafa" if index == 0 else "#fffdf7" if index == 1 else "#f8fff8"
        for col, width in zip(col_x, col_w):
            row_svg.append(f'''<rect x="{col}" y="{y}" width="{width}" height="{row_h}" fill="{fill}" stroke="#c8c8c8"/>''')
        row_svg.append(f'''<circle cx="72" cy="{y + 51}" r="24" fill="{sev_colors[index % 4]}"/><text x="72" y="{y + 60}" text-anchor="middle" font-family="Arial" font-size="18" font-weight="700" fill="#ffffff">{index + 1}</text>''')
        values = [
            level.get("title", ""),
            level.get("definition", ""),
            " / ".join(_as_list(level.get("scenarios"))[:3]),
            level.get("response", ""),
            level.get("handling", ""),
            level.get("service", ""),
            level.get("escalation", ""),
        ]
        for cell_index, value in enumerate(values):
            x = col_x[cell_index] + (70 if cell_index == 0 else 12)
            row_svg.append(_wrapped_text(value, x, y + 34, col_w[cell_index] - (82 if cell_index == 0 else 24), 17, theme["text"], weight="700" if cell_index == 0 else "400"))
    step_svg = []
    for index, step in enumerate(steps):
        x = 34 + index * 194
        step_svg.append(_flow_step(step, index + 1, x, 616, 154, 140, theme, "#2b72c4"))
        if index < len(steps) - 1:
            step_svg.append(_arrow(x + 154, 686, x + 188, 686, "#2b72c4"))
    measure_svg = []
    for index, measure in enumerate(measures):
        x = 250 + index * 270
        measure_svg.append(_assurance_chip(measure, x, 860, theme))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
{_defs(["#2b72c4", "#d9363e", "#f58a23", "#4ba34f"])}
<rect width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>
{_title_block(data, item, job, theme, top=42)}
<text x="28" y="82" font-family="Microsoft YaHei, Arial" font-size="22" font-weight="700" fill="{theme["primary"]}">{_xml(data.get("matrixTitle", "Severity Response Standard"))}</text>
{''.join(row_svg)}
<text x="28" y="584" font-family="Microsoft YaHei, Arial" font-size="22" font-weight="700" fill="{theme["primary"]}">{_xml(data.get("processTitle", "Issue Closure Process"))}</text>
{''.join(step_svg)}
<path d="M 1340 778 C 1000 824 560 824 214 778" fill="none" stroke="#2b72c4" stroke-width="3" stroke-dasharray="9 8" marker-end="url(#arrow-dash-0)"/>
<rect x="30" y="836" width="1540" height="70" rx="8" fill="#f7fbff" stroke="#9dcced"/>
<text x="58" y="878" font-family="Microsoft YaHei, Arial" font-size="19" font-weight="700" fill="{theme["primary"]}">{_xml(data.get("measureTitle", "Key Measures"))}</text>
{''.join(measure_svg)}
</svg>'''


def _render_security_loop(decision: PlanDecision, job: IllustrationJob, theme_name: str) -> str:
    item = decision.item
    data = item.data
    theme = _theme(theme_name, _template_theme(decision))
    center = data.get("center", {})
    controls = _as_list(data.get("controls"))[:5]
    loop = _as_list(data.get("loop"))[:5]
    colors = ["#0b6be8", "#35a960", "#f28a10", "#7c46c7", "#00a5b5"]
    positions = [(670, 148), (1120, 360), (870, 604), (470, 604), (210, 360)]
    control_svg = []
    for index, control in enumerate(controls):
        x, y = positions[index]
        control_svg.append(_radial_control(control, index + 1, x, y, 260, 188, colors[index], theme))
    loop_svg = []
    for index, entry in enumerate(loop):
        x = 148 + index * 276
        loop_svg.append(f'''<g><circle cx="{x}" cy="872" r="24" fill="#ffffff" stroke="{theme["primary_alt"]}" stroke-width="3"/><text x="{x}" y="880" text-anchor="middle" font-family="Arial" font-size="16" font-weight="700" fill="{theme["primary_alt"]}">{index + 1}</text><text x="{x + 38}" y="864" font-family="Microsoft YaHei, Arial" font-size="18" font-weight="700" fill="{theme["primary"]}">{_xml(entry.get("title", ""))}</text><text x="{x + 38}" y="892" font-family="Microsoft YaHei, Arial" font-size="15" fill="{theme["muted"]}">{_xml(entry.get("desc", ""))}</text></g>''')
        if index < len(loop) - 1:
            loop_svg.append(_arrow(x + 188, 872, x + 248, 872, theme["primary_alt"]))
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
{_defs(colors)}
<rect width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>
{_title_block(data, item, job, theme, top=42)}
<circle cx="800" cy="492" r="330" fill="none" stroke="#5b8ee6" stroke-width="12" opacity="0.75"/>
<circle cx="800" cy="492" r="390" fill="none" stroke="#5b8ee6" stroke-width="2" stroke-dasharray="10 10" opacity="0.85"/>
<path d="M 800 286 L 980 420 L 912 638 L 688 638 L 620 420 Z" fill="#eef6ff" stroke="#0758bd" stroke-width="6"/>
<circle cx="800" cy="390" r="52" fill="#ffffff" stroke="#0758bd" stroke-width="4"/>
<text x="800" y="410" text-anchor="middle" font-family="Arial" font-size="42" font-weight="700" fill="#0758bd">{_xml(center.get("icon", "S")[:2].upper())}</text>
{_text(center.get("title", ""), 650, 444, 300, 78, 31, theme["primary"], align="center", weight=700, min_size=22, max_lines=2)}
{_text(center.get("desc", ""), 630, 528, 340, 44, 18, theme["primary_alt"], align="center", weight=700, min_size=13, max_lines=2)}
{''.join(control_svg)}
<rect x="120" y="832" width="1360" height="92" rx="10" fill="#ffffff" stroke="#5b8ee6" stroke-width="2"/>
<text x="800" y="816" text-anchor="middle" font-family="Microsoft YaHei, Arial" font-size="23" font-weight="700" fill="{theme["primary_alt"]}">{_xml(data.get("loopTitle", "Management Closed Loop"))}</text>
{''.join(loop_svg)}
<text x="800" y="954" text-anchor="middle" font-family="Microsoft YaHei, Arial" font-size="17" fill="{theme["primary"]}">{_xml(data.get("footer", ""))}</text>
</svg>'''


def _render_structured_fallback(decision: PlanDecision, job: IllustrationJob, theme_name: str) -> str:
    theme = _theme(theme_name, {})
    item = decision.item
    title = item.data.get("title") or item.insertion.get("caption") or item.id
    reason = "; ".join(decision.reasons[:3])
    return _simple_svg(title, job.document.get("title", ""), "Tier 2 structured fallback", reason, theme)


def _render_free_floor(decision: PlanDecision, job: IllustrationJob, theme_name: str) -> str:
    theme = _theme(theme_name, {})
    item = decision.item
    title = item.data.get("title") or item.insertion.get("caption") or item.id
    reason = "; ".join(decision.reasons[:3])
    return _simple_svg(title, job.document.get("title", ""), "Tier 3 floor output - human review required", reason, theme)


def _simple_svg(title: str, doc_title: str, badge: str, reason: str, theme: dict[str, str]) -> str:
    return f'''<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">
<rect width="{WIDTH}" height="{HEIGHT}" fill="#ffffff"/>
<rect x="0" y="0" width="{WIDTH}" height="116" fill="{theme["primary"]}"/>
<text x="52" y="68" font-family="Microsoft YaHei, Arial" font-size="38" font-weight="700" fill="#ffffff">{_xml(title)}</text>
<text x="1548" y="48" text-anchor="end" font-family="Microsoft YaHei, Arial" font-size="17" fill="#dbeefa">{_xml(doc_title)}</text>
<rect x="120" y="220" width="1360" height="420" rx="16" fill="{theme["wash"]}" stroke="{theme["line"]}" stroke-width="2"/>
<text x="800" y="338" text-anchor="middle" font-family="Microsoft YaHei, Arial" font-size="34" font-weight="700" fill="{theme["primary"]}">{_xml(badge)}</text>
<text x="800" y="410" text-anchor="middle" font-family="Microsoft YaHei, Arial" font-size="20" fill="{theme["muted"]}">{_xml(reason[:120])}</text>
<text x="800" y="516" text-anchor="middle" font-family="Microsoft YaHei, Arial" font-size="18" fill="{theme["muted"]}">This artifact is generated by isolated illustration_v2 and does not depend on legacy renderers.</text>
</svg>'''


def _template_theme(decision: PlanDecision) -> dict[str, str]:
    if not decision.template_id:
        return {}
    return _find_template(decision.template_id).theme_vars


def _title_block(
    data: dict[str, Any],
    item: Any,
    job: IllustrationJob,
    theme: dict[str, str],
    *,
    top: int = 46,
) -> str:
    title = data.get("title") or item.insertion.get("caption") or item.id
    subtitle = data.get("subtitle") or item.intent
    return "\n".join([
        _text(title, 260, top - 38, 1080, 48, 38, theme["text"], align="center", weight=800, min_size=28, max_lines=1),
        _text(subtitle, 300, top + 4, 1000, 32, 20, theme["primary_alt"], align="center", weight=700, min_size=15, max_lines=1),
        _text(job.document.get("title", ""), 1230, top - 20, 310, 26, 14, theme["muted"], align="right", min_size=11, max_lines=1),
    ])


def _defs(colors: list[str]) -> str:
    markers = []
    for index, color in enumerate(colors):
        markers.append(
            f'''<marker id="arrow-{index}" markerWidth="12" markerHeight="8" refX="11" refY="4" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L12,4 L0,8 Z" fill="{color}"/></marker>
<marker id="arrow-dash-{index}" markerWidth="12" markerHeight="8" refX="11" refY="4" orient="auto" markerUnits="userSpaceOnUse"><path d="M0,0 L12,4 L0,8 Z" fill="{color}"/></marker>'''
        )
    return "<defs>" + "".join(markers) + "</defs>"


def _platform_box(platform: dict[str, Any], x: int, y: int, width: int, height: int, color: str, theme: dict[str, str]) -> str:
    layers = _as_list(platform.get("layers"))[:4]
    layer_h = int((height - 88) / max(1, len(layers)))
    layer_svg = []
    for index, layer in enumerate(layers):
        ly = y + 70 + index * layer_h
        layer_svg.append(
            f'''<g>
<rect x="{x + 22}" y="{ly}" width="{width - 44}" height="{layer_h - 18}" rx="5" fill="#fbfdff" stroke="{color}" opacity="0.9"/>
{_text(layer.get("label", ""), x + 42, ly + 8, width - 84, 30, 19, color, align="center", weight=700, min_size=14, max_lines=1)}
{_mini_items(_as_list(layer.get("items"))[:5], x + 38, ly + 52, width - 76, layer_h - 76, color, theme)}
</g>'''
        )
    return f'''<g>
<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="6" fill="#fbfdff" stroke="{color}" stroke-width="2"/>
<rect x="{x + 22}" y="{y}" width="{width - 44}" height="48" rx="5" fill="{color}"/>
{_text(platform.get("title", ""), x + 46, y + 9, width - 92, 32, 22, "#ffffff", align="center", weight=700, min_size=15, max_lines=1)}
{''.join(layer_svg)}
</g>'''


def _mini_items(items: list[Any], x: int, y: int, width: int, height: int, color: str, theme: dict[str, str]) -> str:
    if not items:
        return ""
    gap = 10
    item_w = int((width - gap * (len(items) - 1)) / len(items))
    chunks = []
    for index, item in enumerate(items):
        ix = x + index * (item_w + gap)
        chunks.append(
            f'''<rect x="{ix}" y="{y}" width="{item_w}" height="{height}" rx="6" fill="#ffffff" stroke="{color}" opacity="0.95"/>
{_text(item, ix + 8, y + 6, item_w - 16, height - 12, 15, theme["text"], align="center", min_size=11, max_lines=2)}'''
        )
    return "".join(chunks)


def _flow_step(step: dict[str, Any], number: int, x: int, y: int, width: int, height: int, theme: dict[str, str], color: str) -> str:
    return f'''<g>
<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="7" fill="#f8fbff" stroke="#a9bfda"/>
<circle cx="{x + 30}" cy="{y + 30}" r="18" fill="{color}"/>
<text x="{x + 30}" y="{y + 37}" text-anchor="middle" font-family="Arial" font-size="15" font-weight="700" fill="#ffffff">{number}</text>
{_text(step.get("title", ""), x + 56, y + 8, width - 66, 26, 16, theme["text"], weight=700, min_size=12, max_lines=1)}
{_wrapped_text(step.get("desc", ""), x + 16, y + 58, width - 32, 13, theme["muted"])}
</g>'''


def _small_alert(entry: dict[str, Any], x: int, y: int, width: int, height: int, color: str, theme: dict[str, str]) -> str:
    return f'''<g>
<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="7" fill="#ffffff" stroke="#efc1b9"/>
<circle cx="{x + 34}" cy="{y + 32}" r="18" fill="#ffffff" stroke="{color}" stroke-width="3"/>
<text x="{x + 34}" y="{y + 39}" text-anchor="middle" font-family="Arial" font-size="17" font-weight="700" fill="{color}">!</text>
{_text(entry.get("title", ""), x + 70, y + 8, width - 82, 24, 17, color, weight=700, min_size=12, max_lines=1)}
{_text(entry.get("desc", ""), x + 70, y + 34, width - 82, 22, 13, theme["muted"], min_size=10, max_lines=1)}
</g>'''


def _process_node(entry: dict[str, Any], x: int, y: int, width: int, height: int, *, colors: str, theme: dict[str, str]) -> str:
    return f'''<g>
<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="8" fill="#ffffff" stroke="{colors}" stroke-width="2"/>
{_text(entry.get("title", ""), x + 14, y + 12, width - 28, 26, 17, colors, align="center", weight=700, min_size=12, max_lines=1)}
{_wrapped_text(entry.get("desc", ""), x + 16, y + 58, width - 32, 13, theme["text"])}
</g>'''


def _info_panel(panel: dict[str, Any], x: int, y: int, width: int, height: int, color: str, theme: dict[str, str]) -> str:
    bullets = _as_list(panel.get("bullets"))[:4]
    return f'''<g>
<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="4" fill="#fbfffb" stroke="#cbd9d0"/>
{_text(panel.get("title", ""), x + 18, y + 10, width - 36, 32, 20, color, align="center", weight=700, min_size=14, max_lines=1)}
{_bullet_lines(bullets, x + 34, y + 66, width - 58, 16, theme["text"])}
</g>'''


def _assurance_chip(item: Any, x: int, y: int, theme: dict[str, str]) -> str:
    title = item.get("title", item) if isinstance(item, dict) else item
    desc = item.get("desc", "") if isinstance(item, dict) else ""
    return f'''<g>
<circle cx="{x}" cy="{y}" r="14" fill="#39a86b"/>
<text x="{x}" y="{y + 5}" text-anchor="middle" font-family="Arial" font-size="10" font-weight="700" fill="#ffffff">OK</text>
{_text(title, x + 26, y - 14, 118, 26, 17, theme["primary"], weight=700, min_size=12, max_lines=1)}
{_text(desc, x + 26, y + 10, 118, 22, 14, theme["muted"], min_size=10, max_lines=1)}
</g>'''


def _inspection_card(category: dict[str, Any], number: int, x: int, y: int, width: int, height: int, color: str, theme: dict[str, str]) -> str:
    sections = _as_list(category.get("sections"))[:3]
    section_h = 96
    section_svg = []
    for index, section in enumerate(sections):
        sy = y + 185 + index * section_h
        section_svg.append(
            f'''<g>
<rect x="{x + 40}" y="{sy}" width="{width - 72}" height="{section_h - 12}" rx="5" fill="#ffffff" stroke="#ccd9d0"/>
<rect x="{x + 20}" y="{sy + 12}" width="38" height="44" rx="6" fill="{color}"/>
<text x="{x + 39}" y="{sy + 41}" text-anchor="middle" font-family="Arial" font-size="16" font-weight="700" fill="#ffffff">{index + 1}</text>
{_text(section.get("title", ""), x + 78, sy + 12, width - 126, 30, 18, color, weight=700, min_size=13, max_lines=1)}
{_compact_bullet_lines(_as_list(section.get("bullets"))[:3], x + 88, sy + 56, width - 116, 14, theme["text"])}
</g>'''
        )
    return f'''<g>
<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="10" fill="#fbfffb" stroke="{color}" stroke-width="2"/>
<rect x="{x}" y="{y}" width="{width}" height="86" rx="10" fill="{color}"/>
<rect x="{x}" y="{y + 72}" width="{width}" height="18" fill="{color}"/>
<circle cx="{x + 92}" cy="{y + 30}" r="20" fill="#ffffff"/>
<text x="{x + 92}" y="{y + 38}" text-anchor="middle" font-family="Arial" font-size="22" font-weight="700" fill="{color}">{number}</text>
{_text(category.get("title", ""), x + 118, y + 10, width - 142, 34, 25, "#ffffff", align="center", weight=800, min_size=17, max_lines=1)}
{_text(category.get("subtitle", ""), x + 118, y + 45, width - 142, 26, 18, "#ffffff", align="center", weight=700, min_size=13, max_lines=1)}
<rect x="{x + 70}" y="{y + 104}" width="{width - 140}" height="54" rx="6" fill="#ffffff" stroke="{color}" stroke-dasharray="5 4"/>
{_text(category.get("triggerTitle", "Trigger"), x + 78, y + 110, width - 156, 22, 17, color, align="center", weight=700, min_size=12, max_lines=1)}
{_text(category.get("trigger", ""), x + 78, y + 132, width - 156, 24, 16, theme["text"], align="center", min_size=11, max_lines=1)}
{''.join(section_svg)}
<rect x="{x + 28}" y="{y + height - 76}" width="{width - 56}" height="48" rx="7" fill="#ffffff" stroke="{color}" stroke-width="1.5"/>
{_text(category.get("outputTitle", "Output"), x + 74, y + height - 64, 90, 30, 18, color, weight=700, min_size=13, max_lines=1)}
{_text(category.get("output", ""), x + 170, y + height - 64, width - 210, 30, 17, theme["text"], min_size=12, max_lines=1)}
</g>'''


def _radial_control(control: dict[str, Any], number: int, x: int, y: int, width: int, height: int, color: str, theme: dict[str, str]) -> str:
    bullets = _as_list(control.get("bullets"))[:4]
    return f'''<g>
<rect x="{x}" y="{y}" width="{width}" height="{height}" rx="18" fill="#ffffff" stroke="{color}" stroke-width="2"/>
<rect x="{x + 16}" y="{y + 16}" width="{width - 32}" height="58" rx="8" fill="{color}"/>
<circle cx="{x + width / 2}" cy="{y - 2}" r="28" fill="{color}"/>
<text x="{x + width / 2}" y="{y + 8}" text-anchor="middle" font-family="Arial" font-size="26" font-weight="700" fill="#ffffff">{number}</text>
{_text(control.get("title", ""), x + 28, y + 28, width - 56, 34, 23, "#ffffff", align="center", weight=800, min_size=16, max_lines=1)}
{_compact_bullet_lines(bullets, x + 34, y + 104, width - 58, 15, theme["text"], bullet_color=color)}
</g>'''


def _arrow(x1: int, y1: int, x2: int, y2: int, color: str) -> str:
    return f'''<line x1="{x1}" y1="{y1}" x2="{x2}" y2="{y2}" stroke="{color}" stroke-width="4" marker-end="url(#arrow-0)"/>'''


def _wrapped_text(
    value: Any,
    x: float,
    y: float,
    width: float,
    size: int,
    color: str,
    *,
    weight: str = "400",
) -> str:
    return _text(
        value,
        x,
        y - size,
        width,
        max(size + 4, 72),
        size,
        color,
        weight=int(weight),
        min_size=max(9, size - 3),
        max_lines=4,
    )


def _bullet_lines(
    bullets: list[Any],
    x: float,
    y: float,
    width: float,
    size: int,
    color: str,
    *,
    bullet_color: str | None = None,
) -> str:
    rows = []
    current_y = y
    for bullet in bullets:
        rows.append(
            f'''<text x="{x}" y="{current_y}" font-family="Microsoft YaHei, Arial" font-size="{size}" fill="{bullet_color or color}">•</text>'''
        )
        rows.append(_wrapped_text(str(bullet), x + 22, current_y, width - 22, size, color))
        current_y += size + 16
    return "".join(rows)


def _compact_bullet_lines(
    bullets: list[Any],
    x: float,
    y: float,
    width: float,
    size: int,
    color: str,
    *,
    bullet_color: str | None = None,
) -> str:
    rows = []
    current_y = y
    for bullet in bullets:
        rows.append(
            f'<text x="{x}" y="{current_y}" font-family="Microsoft YaHei, Arial" '
            f'font-size="{size}" fill="{bullet_color or color}">-</text>'
        )
        rows.append(
            _text(
                bullet,
                x + 22,
                current_y - size,
                width - 22,
                size * 1.55,
                size,
                color,
                min_size=max(10, size - 2),
                max_lines=1,
            )
        )
        current_y += size + 10
    return "".join(rows)


def _split_text(text: str, max_chars: int) -> list[str]:
    if not text:
        return [""]
    return [text[index : index + max_chars] for index in range(0, len(text), max_chars)]


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _find_template(template_id: str) -> Template:
    for template in build_capability_catalog().templates:
        if template.id == template_id:
            return template
    raise KeyError(template_id)


def _load_template(template: Template) -> str:
    template_path = PACKAGE_DIR / template.svg_template
    return template_path.read_text(encoding="utf-8")


def _arch_layered_tokens(item: Any, job: IllustrationJob, theme: dict[str, str]) -> dict[str, str]:
    data = item.data
    tokens = _theme_tokens(theme)
    tokens.update({
        "TITLE": _xml(data.get("title") or item.insertion.get("caption") or item.id),
        "SUBTITLE": _xml(data.get("subtitle") or item.intent),
        "DOCUMENT_TITLE": _xml(job.document.get("title", "")),
        "NOTE": _xml(data.get("note") or "Template arch.layered.v2: frozen geometry, contract-first content injection."),
    })
    layers = data.get("layers", [])
    for layer_number in range(1, 4):
        layer = layers[layer_number - 1] if layer_number <= len(layers) else {}
        tokens[f"L{layer_number}_VISIBLE"] = "inline" if layer else "none"
        tokens[f"L{layer_number}_LABEL"] = _xml(layer.get("label", layer.get("title", ""))) if layer else ""
        items = layer.get("items", []) if isinstance(layer, dict) else []
        for item_number in range(1, 5):
            node = items[item_number - 1] if item_number <= len(items) else {}
            prefix = f"L{layer_number}I{item_number}"
            tokens[f"{prefix}_VISIBLE"] = "inline" if node else "none"
            tokens[f"{prefix}_TITLE"] = _xml(str(node.get("title", ""))[:16]) if node else ""
            tokens[f"{prefix}_DESC"] = _xml(str(node.get("desc", ""))[:42]) if node else ""
            icon = str(node.get("icon", "server")) if node else ""
            tokens[f"{prefix}_ICON"] = _xml(icon[:2].upper())
            tokens[f"{prefix}_ACCENT"] = _style_color(str(node.get("style", "default")), theme) if node else theme["primary_alt"]
    return tokens


def _theme_tokens(theme: dict[str, str]) -> dict[str, str]:
    return {
        "THEME_PRIMARY": theme["primary"],
        "THEME_PRIMARY_ALT": theme["primary_alt"],
        "THEME_LINE": theme["line"],
        "THEME_WASH": theme["wash"],
        "THEME_TEXT": theme["text"],
        "THEME_MUTED": theme["muted"],
        "THEME_CARD": theme["card"],
    }


def _apply_tokens(svg: str, tokens: dict[str, str]) -> str:
    for key, value in tokens.items():
        svg = svg.replace("{{" + key + "}}", value)
    return re.sub(r"\{\{[A-Z0-9_]+\}\}", "", svg)


def _theme(theme_name: str, overrides: dict[str, str]) -> dict[str, str]:
    theme = dict(THEMES.get(theme_name, THEMES["formal_blue"]))
    theme.update({key: value for key, value in overrides.items() if value})
    return theme


def _style_color(style: str, theme: dict[str, str]) -> str:
    return {
        "accent": theme["primary_alt"],
        "success": "#3f8f5f",
        "warning": "#b7791f",
        "danger": "#c2414a",
        "purple": "#7357a6",
        "cyan": "#218aa5",
    }.get(style, theme["primary_alt"])


def _safe_name(value: str) -> str:
    cleaned = "".join(ch if ch.isalnum() or ch in {"-", "_"} else "_" for ch in value)
    return cleaned or "illustration"


def _xml(value: Any) -> str:
    return xml_escape(value)


def _text(
    value: Any,
    x: float,
    y: float,
    width: float,
    height: float,
    size: int,
    color: str,
    *,
    align: str = "left",
    weight: int = 400,
    min_size: int | None = None,
    max_lines: int | None = None,
    line_height: float = 1.28,
    language: str = "auto",
) -> str:
    return emit_text(
        value,
        TextSlot(
            id="inline",
            x=x,
            y=y,
            w=width,
            h=height,
            align=align,
            weight=weight,
            font_max=size,
            font_min=min_size if min_size is not None else max(9, size - 4),
            line_height=line_height,
            max_lines=max_lines,
            color=color,
            language=language,
        ),
    )


def _bullet_lines(
    bullets: list[Any],
    x: float,
    y: float,
    width: float,
    size: int,
    color: str,
    *,
    bullet_color: str | None = None,
) -> str:
    rows = []
    current_y = y
    for bullet in bullets:
        rows.append(
            f'<text x="{x}" y="{current_y}" font-family="Microsoft YaHei, Arial" '
            f'font-size="{size}" fill="{bullet_color or color}">-</text>'
        )
        rows.append(
            _text(
                bullet,
                x + 22,
                current_y - size,
                width - 22,
                size * 2.5,
                size,
                color,
                min_size=max(9, size - 3),
                max_lines=2,
            )
        )
        current_y += size + 16
    return "".join(rows)


def _svg_to_png(svg: str, png_path: Path, scale: int) -> bool:
    try:
        import cairosvg  # type: ignore

        cairosvg.svg2png(
            bytestring=svg.encode("utf-8"),
            write_to=str(png_path),
            output_width=WIDTH * scale,
            output_height=HEIGHT * scale,
        )
        return True
    except Exception:
        pass
    try:
        from playwright.sync_api import sync_playwright

        with sync_playwright() as playwright:
            browser = playwright.chromium.launch()
            page = browser.new_page(
                viewport={"width": WIDTH, "height": HEIGHT},
                device_scale_factor=scale,
            )
            page.set_content(f'<html><body style="margin:0">{svg}</body></html>')
            page.locator("svg").screenshot(path=str(png_path), animations="disabled", timeout=60000)
            browser.close()
        return True
    except Exception:
        return False
