"""Deterministic text measurement and SVG text emission for v2 templates."""
from __future__ import annotations

from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import Any


@dataclass(frozen=True, slots=True)
class TextSlot:
    id: str
    x: float
    y: float
    w: float
    h: float
    align: str = "left"
    weight: int = 400
    font_max: int = 16
    font_min: int = 12
    font_step: int = 1
    line_height: float = 1.28
    max_lines: int | None = None
    color: str = "#10253f"


@dataclass(frozen=True, slots=True)
class TextLayout:
    lines: tuple[str, ...]
    size: int
    ok: bool
    width: float
    height: float


class MeasureEngine:
    """Measure text with a stable local font when Pillow is available.

    The SVG still declares a font stack, but layout decisions use this single
    engine instead of scattered character-count guesses.  If no local TrueType
    font can be loaded, the fallback width model is deliberately conservative.
    """

    def width(self, text: str, size: int, weight: int = 400) -> float:
        font = _font(size, weight)
        if font is not None:
            try:
                return float(font.getlength(text))
            except Exception:
                pass
        return sum(_fallback_char_width(ch, size) for ch in text)

    def ascent(self, size: int, weight: int = 400) -> float:
        font = _font(size, weight)
        if font is not None:
            try:
                return float(font.getmetrics()[0])
            except Exception:
                pass
        return size * 0.86


DEFAULT_MEASURE = MeasureEngine()


def fit_text(text: Any, slot: TextSlot, measure: MeasureEngine = DEFAULT_MEASURE) -> TextLayout:
    value = _normalize_text(text)
    for size in range(slot.font_max, slot.font_min - 1, -max(1, slot.font_step)):
        lines = _wrap(value, slot.w, size, slot.weight, measure)
        if slot.max_lines is not None and len(lines) > slot.max_lines:
            continue
        line_height = size * slot.line_height
        height = len(lines) * line_height
        width = max((measure.width(line, size, slot.weight) for line in lines), default=0.0)
        if height <= slot.h and width <= slot.w:
            return TextLayout(tuple(lines), size, True, width, height)

    size = slot.font_min
    lines = _wrap(value, slot.w, size, slot.weight, measure)
    if slot.max_lines is not None and len(lines) > slot.max_lines:
        lines = lines[: slot.max_lines]
        if lines:
            lines[-1] = _ellipsize(lines[-1], slot.w, size, slot.weight, measure)
    line_height = size * slot.line_height
    width = max((measure.width(line, size, slot.weight) for line in lines), default=0.0)
    return TextLayout(tuple(lines), size, False, width, len(lines) * line_height)


def emit_text(text: Any, slot: TextSlot, measure: MeasureEngine = DEFAULT_MEASURE) -> str:
    layout = fit_text(text, slot, measure)
    line_height = layout.size * slot.line_height
    total_h = len(layout.lines) * line_height
    top = slot.y + max(0.0, (slot.h - total_h) / 2)
    baseline = top + measure.ascent(layout.size, slot.weight)
    x = {
        "left": slot.x,
        "center": slot.x + slot.w / 2,
        "right": slot.x + slot.w,
    }.get(slot.align, slot.x)
    anchor = {
        "left": "start",
        "center": "middle",
        "right": "end",
    }.get(slot.align, "start")
    lines = layout.lines or ("",)
    tspans = []
    for index, line in enumerate(lines):
        dy = 0 if index == 0 else line_height
        tspans.append(f'<tspan x="{x:.1f}" dy="{dy:.1f}">{xml_escape(line)}</tspan>')
    fit_attr = "true" if layout.ok else "false"
    return (
        f'<text data-fit="{fit_attr}" x="{x:.1f}" y="{baseline:.1f}" '
        f'text-anchor="{anchor}" font-family="Microsoft YaHei, Noto Sans CJK SC, Arial, sans-serif" '
        f'font-size="{layout.size}" font-weight="{slot.weight}" fill="{slot.color}">'
        f'{"".join(tspans)}</text>'
    )


def xml_escape(value: Any) -> str:
    text = str(value or "")
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def _wrap(text: str, max_w: float, size: int, weight: int, measure: MeasureEngine) -> list[str]:
    tokens = _tokenize(text)
    lines: list[str] = []
    current = ""
    for token in tokens:
        if token == "\n":
            if current.strip():
                lines.append(current.strip())
            current = ""
            continue
        trial = current + token
        if not current.strip() or measure.width(trial.strip(), size, weight) <= max_w:
            current = trial
            continue
        if current.strip():
            lines.append(current.strip())
        current = token if token.strip() else ""
        if measure.width(current.strip(), size, weight) > max_w:
            if current.strip():
                lines.append(_ellipsize(current.strip(), max_w, size, weight, measure))
            current = ""
    if current.strip():
        lines.append(current.strip())
    return lines or [""]


def _tokenize(text: str) -> list[str]:
    tokens: list[str] = []
    buffer = ""
    for ch in text:
        if ch == "\n":
            if buffer:
                tokens.append(buffer)
                buffer = ""
            tokens.append("\n")
        elif _is_cjk(ch):
            if buffer:
                tokens.append(buffer)
                buffer = ""
            tokens.append(ch)
        elif ch.isspace():
            if buffer:
                tokens.append(buffer)
                buffer = ""
            tokens.append(" ")
        elif ch in {"/", "-", ":", "(", ")", ","}:
            buffer += ch
            tokens.append(buffer)
            buffer = ""
        else:
            buffer += ch
    if buffer:
        tokens.append(buffer)
    return tokens


def _ellipsize(text: str, max_w: float, size: int, weight: int, measure: MeasureEngine) -> str:
    suffix = "..."
    if measure.width(text, size, weight) <= max_w:
        return text
    result = text
    while result and measure.width(result + suffix, size, weight) > max_w:
        result = result[:-1]
    return (result + suffix) if result else suffix


def _normalize_text(text: Any) -> str:
    return " ".join(str(text or "").replace("\r", "\n").split())


def _is_cjk(ch: str) -> bool:
    code = ord(ch)
    return (
        0x3400 <= code <= 0x4DBF
        or 0x4E00 <= code <= 0x9FFF
        or 0xF900 <= code <= 0xFAFF
    )


def _fallback_char_width(ch: str, size: int) -> float:
    if _is_cjk(ch):
        return size
    if ch.isspace():
        return size * 0.34
    if ch in "ilI.,:;|!":
        return size * 0.32
    if ch in "mwMW@#":
        return size * 0.86
    return size * 0.58


@lru_cache(maxsize=32)
def _font(size: int, weight: int):
    try:
        from PIL import ImageFont
    except Exception:
        return None

    for path in _font_candidates(weight):
        if path.exists():
            try:
                return ImageFont.truetype(str(path), size)
            except Exception:
                continue
    try:
        return ImageFont.load_default()
    except Exception:
        return None


def _font_candidates(weight: int) -> tuple[Path, ...]:
    windows = Path("C:/Windows/Fonts")
    if weight >= 600:
        return (
            windows / "msyhbd.ttc",
            windows / "simhei.ttf",
            windows / "arialbd.ttf",
            windows / "segoeuib.ttf",
        )
    return (
        windows / "msyh.ttc",
        windows / "simsun.ttc",
        windows / "arial.ttf",
        windows / "segoeui.ttf",
    )
