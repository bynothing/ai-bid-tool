"""Stable SVG component primitives for illustration v2 templates."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from ..core.text_measure import TextSlot, emit_text, xml_escape


@dataclass(frozen=True, slots=True)
class Theme:
    primary: str
    primary_alt: str
    line: str
    wash: str
    text: str
    muted: str
    card: str = "#ffffff"

    @classmethod
    def from_dict(cls, value: dict[str, str]) -> "Theme":
        return cls(
            primary=value["primary"],
            primary_alt=value["primary_alt"],
            line=value["line"],
            wash=value["wash"],
            text=value["text"],
            muted=value["muted"],
            card=value.get("card", "#ffffff"),
        )


def text_box(
    value: Any,
    x: float,
    y: float,
    w: float,
    h: float,
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
            id="component-text",
            x=x,
            y=y,
            w=w,
            h=h,
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


def panel(
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    fill: str,
    stroke: str,
    rx: int = 8,
    stroke_width: float = 1.5,
    dashed: bool = False,
) -> str:
    dash = ' stroke-dasharray="7 5"' if dashed else ""
    return (
        f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="{rx}" '
        f'fill="{fill}" stroke="{stroke}" stroke-width="{stroke_width}"{dash}/>'
    )


def tab_label(
    label: Any,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    color: str,
    text_color: str = "#ffffff",
    size: int = 20,
) -> str:
    return "\n".join(
        [
            f'<rect x="{x}" y="{y}" width="{w}" height="{h}" rx="6" fill="{color}"/>',
            text_box(label, x + 10, y + 7, w - 20, h - 12, size, text_color, align="center", weight=700, min_size=12, max_lines=1),
        ]
    )


def numbered_badge(
    number: int | str,
    cx: float,
    cy: float,
    r: float,
    *,
    color: str,
    text_color: str = "#ffffff",
    size: int = 15,
) -> str:
    return (
        f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}"/>'
        f'<text x="{cx}" y="{cy + size * 0.34:.1f}" text-anchor="middle" '
        f'font-family="Microsoft YaHei, Arial" font-size="{size}" '
        f'font-weight="700" fill="{text_color}">{xml_escape(number)}</text>'
    )


def flow_step(
    step: dict[str, Any],
    number: int,
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    theme: Theme,
    color: str,
) -> str:
    return f'''<g>
{panel(x, y, w, h, fill="#f8fbff", stroke="#a9bfda", rx=7)}
{numbered_badge(number, x + 30, y + 30, 18, color=color, size=15)}
{text_box(step.get("title", ""), x + 58, y + 8, w - 72, 28, 16, theme.text, weight=700, min_size=12, max_lines=1)}
{text_box(step.get("desc", ""), x + 18, y + 50, w - 36, h - 56, 13, theme.muted, min_size=10, max_lines=2)}
</g>'''


def exception_card(
    entry: dict[str, Any],
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    theme: Theme,
    color: str,
) -> str:
    return f'''<g>
{panel(x, y, w, h, fill="#ffffff", stroke="#efc1b9", rx=7)}
<circle cx="{x + 34}" cy="{y + h / 2}" r="18" fill="#ffffff" stroke="{color}" stroke-width="3"/>
<text x="{x + 34}" y="{y + h / 2 + 7}" text-anchor="middle" font-family="Arial" font-size="17" font-weight="700" fill="{color}">!</text>
{text_box(entry.get("title", ""), x + 70, y + 9, w - 82, 22, 17, color, weight=700, min_size=12, max_lines=1)}
{text_box(entry.get("desc", ""), x + 70, y + 34, w - 82, 22, 13, theme.muted, min_size=10, max_lines=1)}
</g>'''


def process_node(
    entry: dict[str, Any],
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    color: str,
    theme: Theme,
) -> str:
    return f'''<g>
{panel(x, y, w, h, fill="#ffffff", stroke=color, rx=8, stroke_width=2)}
{text_box(entry.get("title", ""), x + 14, y + 12, w - 28, 26, 17, color, align="center", weight=700, min_size=12, max_lines=1)}
{text_box(entry.get("desc", ""), x + 16, y + 54, w - 32, h - 58, 13, theme.text, min_size=10, max_lines=2)}
</g>'''


def info_panel(
    panel_data: dict[str, Any],
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    color: str,
    theme: Theme,
) -> str:
    bullets = _as_list(panel_data.get("bullets"))[:4]
    return f'''<g>
{panel(x, y, w, h, fill="#fbfffb", stroke="#cbd9d0", rx=5)}
{text_box(panel_data.get("title", ""), x + 18, y + 12, w - 36, 30, 20, color, align="center", weight=700, min_size=14, max_lines=1)}
{bullet_list(bullets, x + 34, y + 64, w - 58, 15, theme.text, max_items=4, max_lines=1)}
</g>'''


def assurance_chip(item: Any, x: float, y: float, *, theme: Theme) -> str:
    title = item.get("title", item) if isinstance(item, dict) else item
    desc = item.get("desc", "") if isinstance(item, dict) else ""
    return f'''<g>
<circle cx="{x}" cy="{y}" r="14" fill="#39a86b"/>
<text x="{x}" y="{y + 5}" text-anchor="middle" font-family="Arial" font-size="10" font-weight="700" fill="#ffffff">OK</text>
{text_box(title, x + 26, y - 14, 118, 26, 17, theme.primary, weight=700, min_size=12, max_lines=1)}
{text_box(desc, x + 26, y + 10, 118, 22, 14, theme.muted, min_size=10, max_lines=1)}
</g>'''


def bullet_list(
    bullets: list[Any],
    x: float,
    y: float,
    w: float,
    size: int,
    color: str,
    *,
    bullet_color: str | None = None,
    max_items: int = 4,
    max_lines: int = 1,
) -> str:
    rows = []
    current_y = y
    step = size + 10 if max_lines == 1 else size + 16
    for bullet in bullets[:max_items]:
        rows.append(
            f'<text x="{x}" y="{current_y}" font-family="Microsoft YaHei, Arial" '
            f'font-size="{size}" fill="{bullet_color or color}">-</text>'
        )
        rows.append(
            text_box(
                bullet,
                x + 22,
                current_y - size,
                w - 22,
                size * (1.6 if max_lines == 1 else 2.5),
                size,
                color,
                min_size=max(9, size - 3),
                max_lines=max_lines,
            )
        )
        current_y += step
    return "".join(rows)


def connector(
    points: list[tuple[float, float]],
    *,
    color: str,
    marker_id: str = "arrow-0",
    width: float = 4,
    dashed: bool = False,
) -> str:
    if len(points) < 2:
        return ""
    d = f"M {points[0][0]} {points[0][1]} " + " ".join(f"L {x} {y}" for x, y in points[1:])
    dash = ' stroke-dasharray="8 7"' if dashed else ""
    return (
        f'<path d="{d}" fill="none" stroke="{color}" stroke-width="{width}"{dash} '
        f'marker-end="url(#{marker_id})"/>'
    )


def loop_connector(
    x: float,
    y: float,
    w: float,
    h: float,
    *,
    color: str,
    marker_id: str = "arrow-0",
) -> str:
    return (
        f'<path d="M {x + w * 0.1} {y + h * 0.45} '
        f'C {x + w * 0.22} {y - h * 0.22}, {x + w * 0.78} {y - h * 0.22}, {x + w * 0.9} {y + h * 0.45} '
        f'C {x + w * 0.98} {y + h * 0.96}, {x + w * 0.02} {y + h * 0.96}, {x + w * 0.1} {y + h * 0.45}" '
        f'fill="none" stroke="{color}" stroke-width="3" stroke-dasharray="9 8" marker-end="url(#{marker_id})"/>'
    )


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []
