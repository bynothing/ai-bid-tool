"""HTML/CSS renderer for presentation-quality bid diagrams."""
from __future__ import annotations

import html
import json
from pathlib import Path

from ..core.job import IllustrationJob, IllustrationItem
from ..palettes import get_palette, relation_color, select_palette_for_item, style_from_item, use_palette
from .base import RenderContext, RenderResult


class HtmlCssRenderer:
    """Render high-visual bid diagrams as self-contained HTML."""

    name = "html_css"

    def render(self, job: IllustrationJob, items: list[IllustrationItem], context: RenderContext) -> list[RenderResult]:
        output_dir = context.output / "assets" / "html"
        output_dir.mkdir(parents=True, exist_ok=True)
        results: list[RenderResult] = []
        for item in items:
            palette_name = select_palette_for_item(job, item)
            with use_palette(palette_name):
                html_text = self._render_item(job, item)
            html_path = output_dir / f"{_safe_name(item.id)}.html"
            html_path.write_text(html_text, encoding="utf-8")
            outputs = {"html": html_path.relative_to(context.output).as_posix()}
            warnings: list[str] = []
            if context.png:
                png_path = output_dir / f"{_safe_name(item.id)}.png"
                if _screenshot_html(html_path, png_path):
                    outputs["png"] = png_path.relative_to(context.output).as_posix()
                else:
                    warnings.append("HTML 图件 PNG 导出失败，请安装 playwright 并执行 playwright install chromium")
            results.append(RenderResult(item.id, self.name, outputs, warnings))
        return results

    def _render_item(self, job: IllustrationJob, item: IllustrationItem) -> str:
        data = item.data
        title = data.get("title") or item.insertion.get("caption") or item.id
        subtitle = data.get("subtitle") or item.intent
        body = self._body(item)
        note = data.get("note") or data.get("dataNotice") or ""
        watermark = item.visual.get("watermark", "")
        return _page(title, subtitle, body, note, watermark, job.document.get("title", ""))

    def _body(self, item: IllustrationItem) -> str:
        if item.type in {"architecture.layered", "layered_architecture"}:
            return _layered_architecture(item.data)
        if item.type in {"capability.map", "capability_map"}:
            return _capability_map(item.data)
        if item.type in {"process.flowchart", "flowchart"}:
            return _flowchart_map(item.data)
        if item.type in {"process.swimlane", "swimlane_flowchart"}:
            return _swimlane_map(item.data)
        if item.type in {"relationship.domain", "relationship_map"}:
            return _relationship_map(item.data)
        if item.type in {"interaction.sequence", "sequence_diagram"}:
            return _sequence_map(item.data)
        if item.type in {"architecture.deployment", "network.topology"}:
            return _platform_cards(item.data)
        if item.type == "architecture.security_ring":
            return _security_ring(item.data)
        if item.type == "operation.incident_response":
            return _incident_response(item.data)
        if item.type == "timeline.gantt":
            return _gantt(item.data)
        if item.type == "timeline.milestone":
            return _milestones(item.data)
        if item.type == "matrix.risk":
            return _risk_matrix(item.data)
        if item.type in {"comparison.solution", "comparison.advantage"}:
            return _comparison(item.data)
        if item.type == "integration.interface_map":
            return _interface_map(item.data)
        return _generic_cards(item.data)


def _page(title: str, subtitle: str, body: str, note: str, watermark: str, doc_title: str) -> str:
    palette = get_palette()
    roles = palette["roles"]
    header = palette["header"]
    return f"""<!doctype html>
<html lang="zh-CN">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>{_e(title)}</title>
  <style>
    :root {{
      --navy:{header["main"]}; --blue:{header["alt"]}; --teal:#00877c; --gold:#ba7000;
      --red:#c9363e; --text:{palette["text"]}; --sub:{palette["subtext"]}; --line:{palette["line"]};
      --wash:{palette["wash"]}; --soft:{header["soft"]};
      --primary:{roles["primary"]["main"]}; --primary-light:{roles["primary"]["light"]};
      --success:{roles["success"]["main"]}; --success-light:{roles["success"]["light"]};
      --warning:{roles["warning"]["main"]}; --warning-light:{roles["warning"]["light"]};
      --purple:{roles["purple"]["main"]}; --purple-light:{roles["purple"]["light"]};
      --cyan:{roles["cyan"]["main"]}; --cyan-light:{roles["cyan"]["light"]};
      --danger:{roles["danger"]["main"]}; --danger-light:{roles["danger"]["light"]};
      --teal2:{roles["teal"]["main"]}; --teal2-light:{roles["teal"]["light"]};
      --gold2:{roles["gold"]["main"]}; --gold2-light:{roles["gold"]["light"]};
    }}
    * {{ box-sizing:border-box; }}
    body {{ margin:0; background:#fff; font-family:"Microsoft YaHei","Noto Sans SC",Arial,sans-serif; color:var(--text); }}
    .canvas {{ position:relative; width:1600px; min-height:960px; padding:0 42px 34px; background:#fff; overflow:hidden; }}
    .header {{ height:118px; margin:0 -42px 30px; padding:28px 52px; color:#fff; background:linear-gradient(90deg,var(--navy),#006ea8); border-bottom:4px solid #4db3d9; }}
    h1 {{ margin:0; font-size:42px; line-height:1.18; letter-spacing:0; }}
    .subtitle {{ margin-top:10px; font-size:21px; color:#e9f5ff; }}
    .doc {{ position:absolute; top:32px; right:52px; max-width:430px; text-align:right; font-size:16px; color:#d8ecfb; }}
    .note {{ margin-top:24px; padding:14px 18px; border:1px solid var(--line); border-radius:8px; color:var(--sub); font-size:18px; background:#fff; }}
    .watermark {{ position:absolute; right:68px; bottom:88px; font-size:56px; font-weight:700; color:#dcecf8; transform:rotate(-18deg); pointer-events:none; }}
    .grid {{ display:grid; gap:18px; }}
    .card {{ background:#fff; border:1px solid var(--line); border-radius:8px; box-shadow:0 2px 8px rgba(7,59,114,.06); }}
    .card-h {{ padding:18px 20px; border-bottom:1px solid var(--line); background:var(--wash); font-size:25px; font-weight:700; color:var(--navy); }}
    .tone-primary {{ --tone:var(--primary); --tone-light:var(--primary-light); }}
    .tone-success {{ --tone:var(--success); --tone-light:var(--success-light); }}
    .tone-warning {{ --tone:var(--warning); --tone-light:var(--warning-light); }}
    .tone-purple {{ --tone:var(--purple); --tone-light:var(--purple-light); }}
    .tone-cyan {{ --tone:var(--cyan); --tone-light:var(--cyan-light); }}
    .tone-danger {{ --tone:var(--danger); --tone-light:var(--danger-light); }}
    .tone-teal {{ --tone:var(--teal2); --tone-light:var(--teal2-light); }}
    .tone-gold {{ --tone:var(--gold2); --tone-light:var(--gold2-light); }}
    .card.tone-primary, .card.tone-success, .card.tone-warning, .card.tone-purple, .card.tone-cyan, .card.tone-danger, .card.tone-teal, .card.tone-gold {{ border-color:var(--tone); }}
    .card.tone-primary .card-h, .card.tone-success .card-h, .card.tone-warning .card-h, .card.tone-purple .card-h, .card.tone-cyan .card-h, .card.tone-danger .card-h, .card.tone-teal .card-h, .card.tone-gold .card-h {{ background:linear-gradient(90deg,var(--tone),color-mix(in srgb,var(--tone) 72%,#fff)); color:#fff; }}
    .card-b {{ padding:18px 20px; }}
    .pill {{ display:inline-block; padding:6px 12px; border-radius:999px; background:var(--soft); color:var(--blue); font-weight:700; }}
    .muted {{ color:var(--sub); }}
    .bar-bg {{ height:28px; border-radius:999px; background:#edf3f9; overflow:hidden; }}
    .bar {{ height:100%; border-radius:999px; background:linear-gradient(90deg,var(--blue),var(--teal)); }}
    .axis {{ display:grid; grid-template-columns:repeat(12,1fr); margin:10px 0 18px 260px; color:var(--sub); font-size:16px; }}
    .gantt-row {{ display:grid; grid-template-columns:240px 1fr; gap:20px; align-items:center; margin:16px 0; }}
    .risk-grid {{ display:grid; grid-template-columns:90px repeat(5,1fr); grid-template-rows:repeat(6,102px); gap:8px; }}
    .risk-cell {{ border:1px solid var(--line); border-radius:8px; padding:10px; background:#f8fbff; font-size:17px; }}
    .risk-head {{ display:flex; align-items:center; justify-content:center; color:var(--sub); font-weight:700; }}
    .risk-low {{ background:#e8fff3; }} .risk-medium {{ background:#fff8e7; }}
    .risk-high {{ background:#fff0f0; }} .risk-critical {{ background:#ffe6e8; border-color:#e89aa0; }}
    .compare {{ grid-template-columns:repeat(auto-fit,minmax(280px,1fr)); }}
    .compare ul {{ margin:0; padding-left:22px; font-size:22px; line-height:1.8; }}
    .milestones {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(240px,1fr)); gap:18px; margin-top:28px; }}
    .milestone {{ min-height:220px; padding:22px; border-top:6px solid var(--blue); }}
    .milestone[class*="tone-"] {{ border-top-color:var(--tone); background:linear-gradient(180deg,var(--tone-light),#fff 46%); }}
    .num {{ width:38px; height:38px; border-radius:50%; display:inline-flex; align-items:center; justify-content:center; background:var(--blue); color:#fff; font-weight:700; margin-right:10px; }}
    [class*="tone-"] > .num, [class*="tone-"] .num {{ background:var(--tone); }}
    .imap {{ display:grid; grid-template-columns:540px 430px 540px; gap:20px; align-items:start; }}
    .platform {{ border:2px solid var(--blue); border-radius:8px; padding:14px 18px; background:#fbfdff; }}
    .platform.green {{ border-color:#6a9c56; background:#fbfff9; }}
    .platform-title {{ margin:-14px 0 18px; padding:14px; border-radius:0 0 6px 6px; text-align:center; color:#fff; font-size:25px; font-weight:700; background:linear-gradient(90deg,var(--blue),#2e88c2); }}
    .green .platform-title {{ background:linear-gradient(90deg,#6a9c56,#4f8440); }}
    .layer {{ margin:14px 0; padding:12px; border:1px solid #9bc3df; border-radius:8px; background:#fff; }}
    .green .layer {{ border-color:#abc99c; }}
    .layer-title {{ text-align:center; color:var(--navy); font-size:21px; font-weight:700; margin-bottom:12px; }}
    .green .layer-title {{ color:#2d6d31; }}
    .layer-items {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(92px,1fr)); gap:10px; }}
    .mini {{ min-height:62px; display:flex; align-items:center; justify-content:center; padding:8px; border:1px solid #86b7d9; border-radius:7px; text-align:center; font-size:17px; line-height:1.25; background:#fff; }}
    .mini[class*="tone-"] {{ border-color:var(--tone); background:var(--tone-light); color:var(--text); }}
    .green .mini {{ border-color:#9fc394; }}
    .exchange {{ padding-top:54px; }}
    .flow {{ margin:16px 0 22px; text-align:center; }}
    .flow-title {{ font-size:20px; font-weight:700; margin-bottom:8px; }}
    .flow-line {{ position:relative; height:10px; border-radius:999px; background:var(--blue); }}
    .flow-line.left::before, .flow-line.right::after {{ content:""; position:absolute; top:-9px; border-top:14px solid transparent; border-bottom:14px solid transparent; }}
    .flow-line.right::after {{ right:-2px; border-left:24px solid currentColor; }}
    .flow-line.left::before {{ left:-2px; border-right:24px solid currentColor; }}
    .flow-sub {{ margin-top:9px; font-size:18px; }}
    .ack {{ margin-top:8px; border-top:2px dashed currentColor; color:#477a42; font-size:17px; padding-top:8px; }}
    .requirements {{ display:grid; grid-template-columns:150px repeat(6,1fr); gap:0; margin-top:22px; border:1px dashed #78a9c8; border-radius:8px; overflow:hidden; }}
    .req-title {{ display:flex; align-items:center; justify-content:center; padding:14px; background:#2f86bd; color:#fff; font-size:24px; font-weight:700; text-align:center; }}
    .req {{ min-height:106px; padding:14px; border-left:1px solid #d8e7f2; background:#fff; }}
    .req[class*="tone-"] {{ border-left:4px solid var(--tone); background:var(--tone-light); }}
    .req strong {{ display:block; color:var(--navy); font-size:20px; margin-bottom:8px; }}
    .explain {{ display:grid; grid-template-columns:1.3fr 1fr; gap:22px; margin-top:18px; }}
    .explain .card-b {{ font-size:18px; line-height:1.7; }}
    .conclusion {{ margin-top:14px; padding:12px; text-align:center; border:1px solid #9ecae1; border-radius:8px; background:#f1fbff; color:#1173a5; font-size:25px; font-weight:700; }}
    .bid-block {{ display:grid; gap:18px; }}
    .bid-cols-2 {{ grid-template-columns:1fr 1fr; }}
    .bid-cols-3 {{ grid-template-columns:repeat(3,1fr); }}
    .wide-panel {{ border:2px solid var(--blue); border-radius:8px; padding:14px 18px; background:#fbfdff; }}
    .panel-title {{ margin:-14px 0 18px; padding:14px; border-radius:0 0 6px 6px; text-align:center; color:#fff; font-size:25px; font-weight:700; background:linear-gradient(90deg,var(--blue),#2e88c2); }}
    .stage-line {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(170px,1fr)); gap:14px; align-items:stretch; }}
    .stage {{ position:relative; padding:16px; min-height:108px; border:1px solid #9bc3df; border-radius:8px; background:#fff; text-align:center; }}
    .stage[class*="tone-"] {{ border-color:var(--tone); background:var(--tone-light); }}
    .stage[class*="tone-"] strong {{ color:var(--tone); }}
    .stage strong {{ display:block; color:var(--navy); font-size:20px; margin-bottom:8px; }}
    .stage .muted {{ font-size:16px; line-height:1.45; }}
    .stage:not(:last-child)::after {{ content:""; position:absolute; right:-20px; top:45%; border-left:20px solid var(--blue); border-top:12px solid transparent; border-bottom:12px solid transparent; }}
    .domain-grid {{ display:grid; grid-template-columns:repeat(auto-fit,minmax(300px,1fr)); gap:18px; }}
    .domain {{ border:1px solid var(--line); border-radius:8px; background:#fff; overflow:hidden; }}
    .domain-title {{ padding:14px 16px; background:var(--wash); color:var(--navy); font-size:22px; font-weight:700; }}
    .domain[class*="tone-"] {{ border-color:var(--tone); }}
    .domain[class*="tone-"] .domain-title {{ background:linear-gradient(90deg,var(--tone),color-mix(in srgb,var(--tone) 72%,#fff)); color:#fff; }}
    .domain-body {{ padding:14px; display:grid; grid-template-columns:repeat(auto-fit,minmax(120px,1fr)); gap:10px; }}
  </style>
</head>
<body>
  <main class="canvas">
    <section class="header">
      <h1>{_e(title)}</h1>
      <div class="subtitle">{_e(subtitle)}</div>
      <div class="doc">{_e(doc_title)}</div>
    </section>
    {body}
    {f'<div class="note">注：{_e(note)}</div>' if note else ''}
    {f'<div class="watermark">{_e(watermark)}</div>' if watermark else ''}
  </main>
</body>
</html>
"""


def _gantt(data: dict) -> str:
    total = int(data.get("total") or 12)
    unit = data.get("unit", "月")
    axis = "".join(f"<div>{i + 1}{_e(unit)}</div>" for i in range(total))
    rows = []
    for phase in data.get("phases", []):
        start = float(phase.get("start", 0))
        end = float(phase.get("end", start + 1))
        left = max(0, min(100, start / total * 100))
        width = max(4, min(100 - left, (end - start) / total * 100))
        label = f"{_e(phase.get('title', '阶段'))}<div class='muted'>{_e(phase.get('desc', ''))}</div>"
        marker = " <span class='pill'>里程碑</span>" if phase.get("milestone") else ""
        rows.append(
            f"<div class='gantt-row'><div>{label}{marker}</div>"
            f"<div class='bar-bg'><div class='bar' style='margin-left:{left:.2f}%;width:{width:.2f}%'></div></div></div>"
        )
    return f"<div class='axis'>{axis}</div><div>{''.join(rows)}</div>"


def _layered_architecture(data: dict) -> str:
    actors = data.get("actors", [])
    integrations = data.get("integrations", [])
    layers = data.get("layers", [])
    actor_panel = _small_panel("服务对象", actors) if actors else ""
    integration_panel = _small_panel("外部协同", integrations) if integrations else ""
    layer_html = "".join(_interface_layer({"title": layer.get("label", layer.get("title", "分层")), "items": layer.get("items", [])}) for layer in layers)
    support = ""
    if actor_panel or integration_panel:
        support = f"<div class='grid bid-cols-2'>{actor_panel}{integration_panel}</div>"
    return (
        "<section class='bid-block'>"
        f"{support}"
        "<section class='wide-panel'>"
        "<div class='panel-title'>总体分层架构</div>"
        f"{layer_html}"
        "</section>"
        f"{_requirements(data.get('requirements', []))}"
        f"{_conclusion(data)}"
        "</section>"
    )


def _capability_map(data: dict) -> str:
    groups = data.get("groups", [])
    cards = []
    for index, group in enumerate(groups):
        items = group.get("items", [])
        tone = _tone_class(group, index)
        cards.append(
            f"<div class='domain {tone}'>"
            f"<div class='domain-title'>{_e(group.get('label', group.get('title', '能力分组')))}</div>"
            f"<div class='domain-body'>{''.join(_mini_item(item, item_index) for item_index, item in enumerate(items))}</div>"
            "</div>"
        )
    return f"<section class='domain-grid'>{''.join(cards)}</section>{_conclusion(data)}"


def _flowchart_map(data: dict) -> str:
    nodes = data.get("nodes") or data.get("steps") or data.get("flows") or []
    nodes = sorted(nodes, key=lambda node: (node.get("row", 0), node.get("col", node.get("order", 0))))
    return (
        "<section class='wide-panel'>"
        "<div class='panel-title'>流程主线</div>"
        f"<div class='stage-line'>{''.join(_stage(node, index) for index, node in enumerate(nodes))}</div>"
        "</section>"
        f"{_conclusion(data)}"
    )


def _swimlane_map(data: dict) -> str:
    lanes = {lane.get("id"): lane for lane in data.get("lanes", [])}
    steps_by_lane: dict[str, list[dict]] = {lane_id: [] for lane_id in lanes}
    for step in data.get("steps", []):
        steps_by_lane.setdefault(step.get("lane", ""), []).append(step)
    rows = []
    for lane_id, lane in lanes.items():
        steps = sorted(steps_by_lane.get(lane_id, []), key=lambda step: step.get("order", 0))
        rows.append(
            "<div class='card'>"
            f"<div class='card-h'>{_e(lane.get('title', lane_id))}</div>"
            f"<div class='card-b stage-line'>{''.join(_stage(step, index) for index, step in enumerate(steps))}</div>"
            "</div>"
        )
    return f"<section class='bid-block'>{''.join(rows)}</section>{_conclusion(data)}"


def _relationship_map(data: dict) -> str:
    containers = data.get("containers", [])
    cards = []
    for index, container in enumerate(containers):
        tone = _tone_class(container, index)
        cards.append(
            f"<div class='domain {tone}'>"
            f"<div class='domain-title'>{_e(container.get('title', '关系域'))}</div>"
            f"<div class='domain-body'>{''.join(_mini_item(node, node_index) for node_index, node in enumerate(container.get('nodes', [])))}</div>"
            "</div>"
        )
    return f"<section class='domain-grid'>{''.join(cards)}</section>{_conclusion(data)}"


def _sequence_map(data: dict) -> str:
    participants = {item.get("id"): item.get("title", item.get("id", "")) for item in data.get("participants", [])}
    stages = []
    for index, message in enumerate(data.get("messages", []), 1):
        label = f"{participants.get(message.get('from'), message.get('from'))} → {participants.get(message.get('to'), message.get('to'))}"
        stages.append({"title": f"{index}. {message.get('label', '交互')}", "desc": label})
    return (
        "<section class='wide-panel'>"
        "<div class='panel-title'>交互时序</div>"
        f"<div class='stage-line'>{''.join(_stage(stage, index) for index, stage in enumerate(stages))}</div>"
        "</section>"
        f"{_conclusion(data)}"
    )


def _milestones(data: dict) -> str:
    phases = data.get("phases") or data.get("milestones") or []
    cards = []
    for index, phase in enumerate(phases, 1):
        cards.append(
            f"<div class='card milestone {_tone_class(phase, index - 1)}'>"
            f"<div><span class='num'>{index}</span><span class='pill'>{_e(phase.get('time', '关键节点'))}</span></div>"
            f"<h2>{_e(phase.get('title', '里程碑'))}</h2>"
            f"<p class='muted'>{_e(phase.get('desc', ''))}</p>"
            "</div>"
        )
    return f"<div class='milestones'>{''.join(cards)}</div>"


def _risk_matrix(data: dict) -> str:
    buckets: dict[tuple[int, int], list[str]] = {}
    for risk in data.get("risks", []):
        buckets.setdefault((int(risk.get("impact", 1)), int(risk.get("probability", 1))), []).append(risk.get("title", "风险"))
    cells = ["<div class='risk-head'>影响/概率</div>"]
    cells.extend(f"<div class='risk-head'>{i}</div>" for i in range(1, 6))
    for impact in range(5, 0, -1):
        cells.append(f"<div class='risk-head'>影响 {impact}</div>")
        for probability in range(1, 6):
            score = impact * probability
            css = "risk-low" if score <= 6 else "risk-medium" if score <= 12 else "risk-high" if score <= 19 else "risk-critical"
            content = "<br>".join(_e(title) for title in buckets.get((impact, probability), []))
            cells.append(f"<div class='risk-cell {css}'>{content}</div>")
    return f"<div class='risk-grid'>{''.join(cells)}</div>"


def _comparison(data: dict) -> str:
    cards = []
    for index, column in enumerate(data.get("columns", [])):
        items = column.get("items", [])
        lis = "".join(f"<li>{_e(item.get('title', ''))}</li>" if isinstance(item, dict) else f"<li>{_e(item)}</li>" for item in items)
        cards.append(
            f"<div class='card {_tone_class(column, index)}'>"
            f"<div class='card-h'>{_e(column.get('title', '对比项'))}</div>"
            f"<div class='card-b'><div class='muted'>{_e(column.get('subtitle', ''))}</div><ul>{lis}</ul></div>"
            "</div>"
        )
    return f"<div class='grid compare'>{''.join(cards)}</div>"


def _interface_map(data: dict) -> str:
    left = data.get("leftPlatform", {})
    right = data.get("rightPlatform", {})
    flows = data.get("flows", [])
    requirements = data.get("requirements", [])
    notes = data.get("notes", [])
    legend = data.get("legend", [])
    conclusion = data.get("conclusion", "所有数据交互均需留痕、可追溯、可审计")
    return (
        "<section class='imap'>"
        f"{_platform(left, 'blue')}"
        f"<div class='exchange'>{''.join(_flow(flow, index) for index, flow in enumerate(flows))}</div>"
        f"{_platform(right, 'green')}"
        "</section>"
        f"{_requirements(requirements)}"
        f"{_explain(notes, legend)}"
        f"<div class='conclusion'>{_e(conclusion)}</div>"
    )


def _platform(platform: dict, color: str) -> str:
    css = "platform green" if color == "green" else "platform"
    layers = "".join(_interface_layer(layer, index) for index, layer in enumerate(platform.get("layers", [])))
    return (
        f"<section class='{css}'>"
        f"<div class='platform-title'>{_e(platform.get('title', '平台'))}</div>"
        f"{layers}"
        "</section>"
    )


def _interface_layer(layer: dict, index: int = 0) -> str:
    items = "".join(_mini_item(item, item_index) for item_index, item in enumerate(layer.get("items", [])))
    return (
        "<div class='layer'>"
        f"<div class='layer-title'>{_e(layer.get('title', layer.get('label', '分层')))}</div>"
        f"<div class='layer-items'>{items}</div>"
        "</div>"
    )


def _flow(flow: dict, index: int = 0) -> str:
    direction = flow.get("direction", "right")
    if flow.get("color"):
        color = flow["color"]
    elif flow.get("relation"):
        color = relation_color(flow.get("relation"))
    else:
        color = get_palette()["roles"][style_from_item(flow, index)]["main"]
    line_class = "right" if direction == "right" else "left"
    ack = flow.get("ack") or flow.get("ackLabel") or ""
    label = flow.get("label") or flow.get("title") or "数据交互"
    return (
        f"<div class='flow' style='color:{_e(color)}'>"
        f"<div class='flow-title'>{_e(label)}</div>"
        f"<div class='flow-line {line_class}'></div>"
        f"<div class='flow-sub'>{_e(flow.get('protocol', 'HTTPS / JSON'))}</div>"
        f"{f'<div class=\"ack\">{_e(ack)}</div>' if ack else ''}"
        "</div>"
    )


def _requirements(requirements: list) -> str:
    if not requirements:
        return ""
    reqs = []
    for index, req in enumerate(requirements[:6]):
        tone = _tone_class(req, index)
        reqs.append(
            f"<div class='req {tone}'>"
            f"<strong>{_e(req.get('title', '要求'))}</strong>"
            f"<div class='muted'>{_e(req.get('desc', ''))}</div>"
            "</div>"
        )
    return "<section class='requirements'><div class='req-title'>通信与<br>安全要求</div>" + "".join(reqs) + "</section>"


def _explain(notes: list, legend: list) -> str:
    note_html = "".join(f"<div>{_e(note)}</div>" for note in notes)
    legend_html = "".join(f"<div><span class='pill'>{_e(item.get('label', '图例'))}</span> {_e(item.get('desc', ''))}</div>" for item in legend)
    return (
        "<section class='explain'>"
        f"<div class='card'><div class='card-h'>说明</div><div class='card-b'>{note_html}</div></div>"
        f"<div class='card'><div class='card-h'>图例</div><div class='card-b'>{legend_html}</div></div>"
        "</section>"
    )


def _small_panel(title: str, items: list) -> str:
    return (
        "<div class='card'>"
        f"<div class='card-h'>{_e(title)}</div>"
            f"<div class='card-b layer-items'>{''.join(_mini_item(item, index) for index, item in enumerate(items))}</div>"
        "</div>"
    )


def _mini_item(item: object, index: int = 0) -> str:
    if isinstance(item, dict):
        title = item.get("title", item.get("name", ""))
        desc = item.get("desc", item.get("subtitle", ""))
    else:
        title, desc = item, ""
    return f"<div class='mini {_tone_class(item, index)}'>{_e(title)}{f'<br><span class=\"muted\">{_e(desc)}</span>' if desc else ''}</div>"


def _stage(item: dict, index: int = 0) -> str:
    title = item.get("title", item.get("label", "步骤"))
    desc = item.get("desc", item.get("subtitle", ""))
    return f"<div class='stage {_tone_class(item, index)}'><strong>{_e(title)}</strong><div class='muted'>{_e(desc)}</div></div>"


def _tone_class(item: object, index: int = 0) -> str:
    return f"tone-{style_from_item(item, index)}"


def _conclusion(data: dict) -> str:
    value = data.get("conclusion")
    if not value:
        return ""
    return f"<div class='conclusion'>{_e(value)}</div>"


def _generic_cards(data: dict) -> str:
    groups = data.get("groups") or data.get("columns") or data.get("platforms") or data.get("levels") or data.get("measures") or []
    cards = []
    for index, group in enumerate(groups):
        title = group.get("title") or group.get("label") or "分组"
        items = _as_items(group.get("items") or group.get("content") or group.get("scenes") or group.get("checks") or [])
        if not items and group.get("desc"):
            items = [group.get("desc")]
        body = _mini_grid(items) if items else f"<div class='muted'>{_e(json.dumps(group, ensure_ascii=False))}</div>"
        cards.append(f"<div class='card {_tone_class(group, index)}'><div class='card-h'>{_e(title)}</div><div class='card-b'>{body}</div></div>")
    sections = [f"<div class='grid compare'>{''.join(cards)}</div>" if cards else ""]
    sections.append(_summary_panels(data))
    return "".join(sections) or "<div></div>"


def _platform_cards(data: dict) -> str:
    platforms = data.get("platforms") or data.get("zones") or data.get("areas") or data.get("nodes") or []
    cards = []
    for index, platform in enumerate(platforms):
        items = _as_items(platform.get("items") or platform.get("content") or platform.get("children") or [])
        cards.append(
            f"<div class='domain {_tone_class(platform, index)}'>"
            f"<div class='domain-title'>{_e(platform.get('title', platform.get('label', '功能分区')))}</div>"
            f"<div class='domain-body'>{''.join(_mini_item(item, item_index) for item_index, item in enumerate(items))}</div>"
            "</div>"
        )
    body = f"<section class='domain-grid'>{''.join(cards)}</section>" if cards else _generic_cards(data)
    return body + _summary_panels(data) + _conclusion(data)


def _incident_response(data: dict) -> str:
    levels = data.get("levels", [])
    steps = data.get("steps", [])
    level_cards = []
    for index, level in enumerate(levels):
        items = [
            f"响应：{level.get('response', '-')}",
            f"处置：{level.get('handling', '-')}",
            f"服务：{level.get('service', '-')}",
        ]
        items.extend(_as_items(level.get("scenes", []))[:3])
        level_cards.append(
            f"<div class='card {_tone_class(level, index)}'><div class='card-h'>{_e(level.get('level', '级别'))} {_e(level.get('name', ''))}</div>"
            f"<div class='card-b'>{_mini_grid(items)}</div></div>"
        )
    return (
        f"<section class='grid bid-cols-3'>{''.join(level_cards)}</section>"
        "<section class='wide-panel' style='margin-top:18px'><div class='panel-title'>问题闭环流程</div>"
        f"<div class='stage-line'>{''.join(_stage(step, index) for index, step in enumerate(steps))}</div></section>"
        f"{_summary_panels(data)}{_conclusion(data)}"
    )


def _security_ring(data: dict) -> str:
    core = data.get("core", {})
    measures = data.get("measures", [])
    loop = data.get("loop", [])
    measure_cards = []
    for index, measure in enumerate(measures):
        measure_cards.append(
            f"<div class='domain {_tone_class(measure, index)}'>"
            f"<div class='domain-title'>{_e(measure.get('title', '安全措施'))}</div>"
            f"<div class='domain-body'>{''.join(_mini_item(item, item_index) for item_index, item in enumerate(_as_items(measure.get('items', []))))}</div>"
            "</div>"
        )
    core_html = ""
    if core:
        core_html = (
            "<section class='wide-panel' style='margin-bottom:18px'>"
            f"<div class='panel-title'>{_e(core.get('title', '安全保障体系'))}</div>"
            f"<div class='conclusion'>{_e(core.get('desc', data.get('summary', '')))}</div>"
            "</section>"
        )
    loop_html = ""
    if loop:
        loop_html = (
            "<section class='wide-panel' style='margin-top:18px'><div class='panel-title'>管理闭环</div>"
            f"<div class='stage-line'>{''.join(_stage(step, index) for index, step in enumerate(loop))}</div></section>"
        )
    return core_html + f"<section class='domain-grid'>{''.join(measure_cards)}</section>" + loop_html + _summary_panels(data) + _conclusion(data)


def _summary_panels(data: dict) -> str:
    panels = []
    for title, key in [("关键内容", "content"), ("检查要点", "checks"), ("保障措施", "safeguards"), ("原则要求", "requirements"), ("说明", "notes")]:
        items = _as_items(data.get(key, []))
        if items:
            panels.append(f"<div class='card'><div class='card-h'>{title}</div><div class='card-b'>{_mini_grid(items[:8])}</div></div>")
    return f"<section class='grid compare' style='margin-top:18px'>{''.join(panels)}</section>" if panels else ""


def _mini_grid(items: list) -> str:
    return "<div class='layer-items'>" + "".join(_mini_item(item, index) for index, item in enumerate(items)) + "</div>"


def _as_items(value: object) -> list:
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        return [value]
    return []


def _screenshot_html(html_path: Path, png_path: Path) -> bool:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        return False
    try:
        with sync_playwright() as playwright:
            browser = playwright.chromium.launch(headless=True)
            page = browser.new_page(viewport={"width": 1600, "height": 960}, device_scale_factor=2)
            page.goto(html_path.as_uri(), wait_until="load")
            page.locator(".canvas").screenshot(path=str(png_path), animations="disabled")
            browser.close()
        return True
    except Exception:
        return False


def _safe_name(value: str) -> str:
    return "".join("_" if char in '<>:"/\\|?* ' else char for char in value).strip("_") or "diagram"


def _e(value: object) -> str:
    return html.escape(str(value or ""), quote=True)
