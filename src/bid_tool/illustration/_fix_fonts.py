"""Fix SVG renderer: increase font sizes + layout dimensions for better readability."""
import re
from pathlib import Path

HERE = Path(__file__).resolve().parent
target = HERE / "svg_renderer.py"
content = target.read_text(encoding="utf-8")

# ── CSS font-size replacements ──
css_map = {
    'font:700 44px': 'font:700 60px',
    'font:500 23px': 'font:500 30px',
    'font:700 30px "Microsoft YaHei","Noto Sans SC",Arial,sans-serif; fill:{theme[\'label_text\']};': \
        'font:700 42px "Microsoft YaHei","SimHei","Noto Sans SC",Arial,sans-serif; fill:{theme[\'label_text\']};',
    'font:600 18px Arial': 'font:600 24px Arial',
    'font:600 30px "Microsoft YaHei","Noto Sans SC",Arial,sans-serif; fill:{theme[\'text\']};': \
        'font:600 40px "Microsoft YaHei","SimHei","Noto Sans SC",Arial,sans-serif; fill:{theme[\'text\']};',
    'font:700 33px': 'font:700 48px',
    'font:500 24px': 'font:500 30px',
    'font:600 30px "Microsoft YaHei","Noto Sans SC",Arial,sans-serif; fill:#fff;': \
        'font:600 40px "Microsoft YaHei","SimHei","Noto Sans SC",Arial,sans-serif; fill:#fff;',
    'font:500 20px': 'font:500 26px',
    'font:700 23px': 'font:700 30px',
}

for old, new in css_map.items():
    if old in content:
        content = content.replace(old, new)
        print(f"CSS: {old[:40]}... -> OK")
    else:
        print(f"CSS: {old[:40]}... -> NOT FOUND")

# Add SimHei as fallback font everywhere "Microsoft YaHei" appears in CSS
content = content.replace(
    '"Microsoft YaHei","Noto Sans SC",Arial,sans-serif;',
    '"Microsoft YaHei","SimHei","Noto Sans SC",Arial,sans-serif;'
)

# ── Layout dimension adjustments ──
# Increase card heights (86→120), layer row heights (92→130, 104→150)
dim_map = {
    # layer_heights formula: 46 + rows * 92 + (rows-1)*12 + 16
    'layer_heights.append(46 + rows * 92 + (rows - 1) * 12 + 16)':
        'layer_heights.append(60 + rows * 130 + (rows - 1) * 16 + 20)',

    # item_card: title_lh = 35, desc_lh = 29
    'title_lh = 35': 'title_lh = 45',
    'desc_lh = 29': 'desc_lh = 35',

    # item_card height constants in dark card rendering (cy = y + 24 + row * 104)
    'cy = y + 24 + row * 104':
        'cy = y + 30 + row * 150',

    # dark card height: 86 → 120
    'dark_w, 86, theme["dark_card"]':
        'dark_w, 120, theme["dark_card"]',

    # dark card vertical centering: (86 - total_h) / 2 + 29
    '(86 - total_h) / 2 + 29':
        '(120 - total_h) / 2 + 35',

    # item_card for actors: card_h 86 → 120
    'actor in enumerate(actors):\n            item_card(parts, card_x + index * (card_w + gap), y + 24, card_w, 86, actor, theme)':
        'actor in enumerate(actors):\n            item_card(parts, card_x + index * (card_w + gap), y + 30, card_w, 120, actor, theme)',

    # item_card in layered_architecture: card_w, 86, item, theme
    'item_card(parts, card_x + col * (card_w + gap), cy, card_w, 86, item, theme,':
        'item_card(parts, card_x + col * (card_w + gap), cy, card_w, 120, item, theme,',

    # actor_h = 136 → 170
    'actor_h = 136 if actors else 0':
        'actor_h = 170 if actors else 0',

    # content_h actor padding: 14 → 20
    'content_h = (actor_h + 14 if actors else 0)':
        'content_h = (actor_h + 20 if actors else 0)',

    # Header height: 96 → 120, accent bar y: 94 → 118
    'WIDTH, 96, "url(#header)"':
        'WIDTH, 120, "url(#header)"',
    'rect(0, 94, WIDTH, 3, theme["accent"]':
        'rect(0, 118, WIDTH, 3, theme["accent"]',

    # Title/subtitle positions in header
    'text(48, 48, title, "title")':
        'text(56, 58, title, "title")',
    'text(50, 78, subtitle, "subtitle")':
        'text(58, 98, subtitle, "subtitle")',

    # label_w = 220 → 260
    'label_w = 220':
        'label_w = 260',

    # section text positioning (x + 22, box_y + 38)
    'x + 22, box_y + 38, label, label_css':
        'x + 26, box_y + 48, label, label_css',
    'x + 22, box_y + 65, en, "section-en"':
        'x + 26, box_y + 80, en, "section-en"',

    # item_card icon positioning (pad_v, x + 15, icon size 31)
    'pad_v = 10': 'pad_v = 14',
    'x + 15, y + (h - 31) / 2, 31, icon_color':
        'x + 18, y + (h - 40) / 2, 40, icon_color',

    # text_x calculation in item_card
    'text_x = x + 56 if icon_name else x + w / 2':
        'text_x = x + 66 if icon_name else x + w / 2',

    # chars_per_line calculation
    '(w - (52 if icon_name else 32)) / 30))':
        '(w - (66 if icon_name else 40)) / 40))',

    # item_card title line offset (block_top + idx * title_lh + 29)
    'idx * title_lh + 29, line, "node"':
        'idx * title_lh + 36, line, "node"',

    # desc rendering y offset
    'desc_y = block_top + len(title_lines) * title_lh + text_gap + 23':
        'desc_y = block_top + len(title_lines) * title_lh + text_gap + 28',

    # section_box actor dimensions: y + 24 → y + 32
    'y + 24, card_w, 86, actor, theme)':
        'y + 30, card_w, 120, actor, theme)',

    # Layer gap: 12 → 16
    'y += h + 12\n':
        'y += h + 16\n',

    # Height min: 920 → 1100
    'max(920, 112 + 25 + content_h + 84)':
        'max(1200, 136 + 30 + content_h + 100)',

    # y start for layered: 122 → 150
    'y = 122\n':
        'y = 150\n',

    # y start for layered (inside layered_arch function, after page_start)
    # Actually above handles

    # Note bar positioning: y + 32 → y + 38, rect 50 → 60
    'y + 32, f"注：{value}", "note"':
        'y + 38, f"注：{value}", "note"',
    'rect(42, y, WIDTH - 84, 50, theme["card_alt"]':
        'rect(42, y, WIDTH - 84, 60, theme["card_alt"]',

    # Note bar bottom: height - 64 → height - 80
    'note_bar(parts, figure.get("note", "本图内容"), theme, height - 64)':
        'note_bar(parts, figure.get("note", "本图内容来源于文档已确认需求"), theme, height - 80)',

    # dark card text positioning
    'dark_x + 17, cy + 27, 31, "#ffffff"':
        'dark_x + 20, cy + 38, 40, "#ffffff"',
    'tx = dark_x + 58':
        'tx = dark_x + 70',
}

for old, new in dim_map.items():
    if old in content:
        content = content.replace(old, new)
        print(f"DIM: {old[:50]}... -> OK")
    else:
        print(f"DIM: {old[:50]}... -> NOT FOUND")

# ── Flowchart layout adjustments ──
flow_map = {
    'box_w, box_h = 240, 126': 'box_w, box_h = 300, 160',
    'col_gap, row_gap = 36, 62': 'col_gap, row_gap = 48, 80',
    'start_x = max(70, int((WIDTH - ((max_col + 1) * box_w + max_col * col_gap)) / 2))':
        'start_x = max(80, int((WIDTH - ((max_col + 1) * box_w + max_col * col_gap)) / 2))',
    'max(760, 166 + (max_row + 1) * box_h + max_row * row_gap + 112)':
        'max(1000, 200 + (max_row + 1) * box_h + max_row * row_gap + 130)',
    '160 + node.get("col", 0) * (box_w + col_gap)':
        '200 + node.get("col", 0) * (box_w + col_gap)',
    '160 + node.get("row", 0) * (box_h + row_gap)':
        '200 + node.get("row", 0) * (box_h + row_gap)',
    # decision node icon/line offsets
    'cy - 29, 24, theme["warn_stroke"]':
        'cy - 38, 32, theme["warn_stroke"]',
    'cy + 14 + line_index * 34':
        'cy + 18 + line_index * 44',
    'cy - (len(lines) - 1) * 17 + 10':
        'cy - (len(lines) - 1) * 22 + 12',
    'start_y + line_index * 34':
        'start_y + line_index * 44',
    # Edge label font: 15 → 20
    'label_w = max(52, len(edge["label"]) * 15 + 18)':
        'label_w = max(64, len(edge["label"]) * 20 + 24)',
    'rect(lx - label_w / 2, ly - 18, label_w, 25, theme["bg"]':
        'rect(lx - label_w / 2, ly - 22, label_w, 32, theme["bg"]',
    # Flowchart note bar
    '(figure.get("note", "流程节点和流向依据文档'), theme, height - 64)':
        '(figure.get("note", "流程节点和流向依据文档'), theme, height - 80)',
}

for old, new in flow_map.items():
    if old in content:
        content = content.replace(old, new)
        print(f"FLOW: {old[:50]}... -> OK")
    else:
        print(f"FLOW: {old[:50]}... -> NOT FOUND")

# ── Sequence diagram adjustments ──
seq_map = {
    'card_w = min(280, int((WIDTH - 100 - gap * (len(participants) - 1)) / len(participants)))':
        'card_w = min(340, int((WIDTH - 100 - gap * (len(participants) - 1)) / len(participants)))',
    'item_card(parts, int(x), 130, card_w, 96, participant, theme, style)':
        'item_card(parts, int(x), 150, card_w, 120, participant, theme, style)',
    'f\'<path d="M{{x + card_w / 2:g}} 240V{bottom_y:g}"\'':
        'f\'<path d="M{{x + card_w / 2:g}} 280V{bottom_y:g}"\'',
    'y = 270 + index * 70':
        'y = 320 + index * 90',
    'bottom_y = 264 + len(messages) * 66':
        'bottom_y = 310 + len(messages) * 90',
    'max(700, bottom_y + 122)':
        'max(900, bottom_y + 150)',
    'label_w = max(80, len(message.get("label", "")) * 25 + 28)':
        'label_w = max(100, len(message.get("label", "")) * 30 + 36)',
    'rect(label_x - label_w / 2, y - 36, label_w, 33':
        'rect(label_x - label_w / 2, y - 44, label_w, 40',
    'text(label_x, y - 12, message.get("label", "")':
        'text(label_x, y - 14, message.get("label", "")',
    '(figure.get("note", "虚线生命线表示交互参与方持续存在"), theme, height - 64)':
        '(figure.get("note", "虚线生命线表示交互参与方持续存在"), theme, height - 80)',
}

for old, new in seq_map.items():
    if old in content:
        content = content.replace(old, new)
        print(f"SEQ: {old[:50]}... -> OK")
    else:
        print(f"SEQ: {old[:50]}... -> NOT FOUND")

# ── Swimlane adjustments ──
swim_map = {
    'row_h, header_h = 128, 74': 'row_h, header_h = 160, 90',
    'body_y = 134': 'body_y = 160',
    'lane_h = header_h + (max_order + 1) * row_h + 25':
        'lane_h = header_h + (max_order + 1) * row_h + 30',
    'height = body_y + lane_h + 72':
        'height = body_y + lane_h + 90',
    'item_card(parts, x + 18, body_y + 20, 32, theme["accent"])':
        'lane["icon"]):\n            parts.append(icon(lane["icon"], x + 20, body_y + 24, 40, theme["accent"]))',
    'lane["icon"]):\n            parts.append(icon(lane["icon"], x + 18, body_y + 20, 32, theme["accent"]))\n            parts.append(text(x + 62, body_y + 46, lane["title"], "section"))\n        else:\n            parts.append(text(x + 20, body_y + 46, lane["title"], "section"))':
        'lane["icon"]):\n            parts.append(icon(lane["icon"], x + 20, body_y + 24, 40, theme["accent"]))\n            parts.append(text(x + 72, body_y + 56, lane["title"], "section"))\n        else:\n            parts.append(text(x + 24, body_y + 56, lane["title"], "section"))',
    'y = body_y + header_h + 20 + step.get("order", 0) * row_h':
        'y = body_y + header_h + 24 + step.get("order", 0) * row_h',
    'w, h = lane_w - 42, 96':
        'w, h = lane_w - 50, 120',
}

for old, new in swim_map.items():
    if old in content:
        content = content.replace(old, new)
        print(f"SWIM: {old[:50]}... -> OK")
    else:
        print(f"SWIM: {old[:50]}... -> NOT FOUND")

# ── Relationship map adjustments ──
rel_map = {
    'header_h, card_h, node_gap = 72, 92, 14':
        'header_h, card_h, node_gap = 88, 120, 18',
    'height = header_h + 20 + (max_node_row + 1) * card_h + max_node_row * node_gap + 18':
        'height = header_h + 24 + (max_node_row + 1) * card_h + max_node_row * node_gap + 22',
    'container["icon"]):\n            parts.append(icon(container["icon"], x + 18, y + 20, 32, theme["accent"]))\n            parts.append(text(x + 62, y + 39, container["title"], "section"))\n            parts.append(text(x + 62, y + 65, container.get("subtitle", "CONTAINER"), "section-en"))\n        else:\n            parts.append(text(x + 20, y + 39, container["title"], "section"))\n            parts.append(text(x + 20, y + 65, container.get("subtitle", "CONTAINER"), "section-en"))':
        'container["icon"]):\n            parts.append(icon(container["icon"], x + 22, y + 24, 40, theme["accent"]))\n            parts.append(text(x + 72, y + 48, container["title"], "section"))\n            parts.append(text(x + 72, y + 80, container.get("subtitle", "CONTAINER"), "section-en"))\n        else:\n            parts.append(text(x + 24, y + 48, container["title"], "section"))\n            parts.append(text(x + 24, y + 80, container.get("subtitle", "CONTAINER"), "section-en"))',
    # row_y cursor
    'cursor_y = 136': 'cursor_y = 170',
    'legend_y = cursor_y + 4': 'legend_y = cursor_y + 8',
    'max(640, legend_y + 76 + 51)': 'max(850, legend_y + 90 + 60)',
    # capability_map uses same layout
    'cursor_y = 136\n    for row in sorted(column_rows)':
        'cursor_y = 170\n    for row in sorted(column_rows)',
}

for old, new in rel_map.items():
    if old in content:
        content = content.replace(old, new)
        print(f"REL: {old[:50]}... -> OK")
    else:
        print(f"REL: {old[:50]}... -> NOT FOUND")

# ── Write back ──
target.write_text(content, encoding="utf-8")
print(f"\nDone. Written to {target}")
