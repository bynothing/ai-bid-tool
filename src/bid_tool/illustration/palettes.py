"""Shared color palettes for bid illustration renderers.

The default palette is distilled from the example 3-6 diagrams: deep blue
headers, white cards, thin borders, and semantic accents for normal flow,
verification, exception handling, closed-loop review, and risk levels.
"""
from __future__ import annotations

import json
from contextlib import contextmanager
from contextvars import ContextVar
from typing import Any, Iterator


DEFAULT_PALETTE = "engineering_blue"
_CURRENT_PALETTE: ContextVar[str] = ContextVar("bid_illustration_palette", default=DEFAULT_PALETTE)


PALETTES: dict[str, dict[str, Any]] = {
    "engineering_blue": {
        "name": "工程蓝灰",
        "header": {"main": "#12324f", "alt": "#1f5f8b", "soft": "#eef5fb"},
        "text": "#1e293b",
        "subtext": "#526173",
        "line": "#cbd8e6",
        "wash": "#f6f9fc",
        "roles": {
            "primary": {"main": "#1f5f8b", "light": "#f3f7fb", "soft": "#dbe8f3"},
            "success": {"main": "#3f7d62", "light": "#f4faf7", "soft": "#dcece5"},
            "warning": {"main": "#9a6a24", "light": "#fbf8f1", "soft": "#efe1c8"},
            "danger": {"main": "#9b3434", "light": "#fbf4f4", "soft": "#efd7d7"},
            "teal": {"main": "#3b7280", "light": "#f3f8fa", "soft": "#d8e8ec"},
            "cyan": {"main": "#456f96", "light": "#f3f7fb", "soft": "#dbe7f2"},
            "purple": {"main": "#5d6680", "light": "#f6f7fa", "soft": "#e2e5ec"},
            "gold": {"main": "#8a7245", "light": "#faf8f2", "soft": "#e9dfca"},
        },
        "sequence": ["primary", "cyan", "teal", "purple", "primary", "cyan", "teal", "purple"],
        "relations": {
            "flow": "primary",
            "data": "cyan",
            "sync": "teal",
            "control": "purple",
            "alert": "danger",
            "risk": "warning",
            "feedback": "gold",
        },
    },
    "example_formal": {
        "name": "图3-6正式标书蓝",
        "header": {"main": "#073b72", "alt": "#006ea8", "soft": "#e9f5ff"},
        "text": "#062b52",
        "subtext": "#365b82",
        "line": "#d3e3f2",
        "wash": "#f5fbff",
        "roles": {
            "primary": {"main": "#2563eb", "light": "#eff6ff", "soft": "#dbeafe"},
            "success": {"main": "#16a34a", "light": "#f0fdf4", "soft": "#dcfce7"},
            "warning": {"main": "#f97316", "light": "#fff7ed", "soft": "#ffedd5"},
            "danger": {"main": "#dc2626", "light": "#fef2f2", "soft": "#fee2e2"},
            "teal": {"main": "#0f766e", "light": "#ecfdf5", "soft": "#ccfbf1"},
            "cyan": {"main": "#0891b2", "light": "#ecfeff", "soft": "#cffafe"},
            "purple": {"main": "#7c3aed", "light": "#f5f3ff", "soft": "#ede9fe"},
            "gold": {"main": "#ca8a04", "light": "#fefce8", "soft": "#fef3c7"},
        },
        "sequence": ["primary", "success", "warning", "purple", "teal", "cyan", "danger", "gold"],
        "relations": {
            "flow": "primary",
            "data": "teal",
            "sync": "success",
            "control": "purple",
            "alert": "danger",
            "risk": "warning",
            "feedback": "gold",
        },
    },
    "data_cyan": {
        "name": "数据接口青蓝",
        "header": {"main": "#064e5f", "alt": "#0891b2", "soft": "#ecfeff"},
        "text": "#083344",
        "subtext": "#365b82",
        "line": "#bae6fd",
        "wash": "#f0f9ff",
        "roles": {
            "primary": {"main": "#0284c7", "light": "#f0f9ff", "soft": "#bae6fd"},
            "success": {"main": "#059669", "light": "#ecfdf5", "soft": "#a7f3d0"},
            "warning": {"main": "#f59e0b", "light": "#fffbeb", "soft": "#fde68a"},
            "danger": {"main": "#e11d48", "light": "#fff1f2", "soft": "#fecdd3"},
            "teal": {"main": "#0f766e", "light": "#ecfdf5", "soft": "#ccfbf1"},
            "cyan": {"main": "#06b6d4", "light": "#ecfeff", "soft": "#cffafe"},
            "purple": {"main": "#6366f1", "light": "#eef2ff", "soft": "#c7d2fe"},
            "gold": {"main": "#ca8a04", "light": "#fefce8", "soft": "#fef3c7"},
        },
        "sequence": ["primary", "teal", "success", "cyan", "warning", "purple", "danger", "gold"],
        "relations": {"flow": "primary", "data": "cyan", "sync": "success", "control": "purple", "alert": "danger", "risk": "warning", "feedback": "gold"},
    },
    "ops_indigo": {
        "name": "operations indigo",
        "header": {"main": "#312e81", "alt": "#4f46e5", "soft": "#eef2ff"},
        "text": "#1e1b4b",
        "subtext": "#475569",
        "line": "#c7d2fe",
        "wash": "#f8fafc",
        "roles": {
            "primary": {"main": "#4f46e5", "light": "#eef2ff", "soft": "#c7d2fe"},
            "success": {"main": "#059669", "light": "#ecfdf5", "soft": "#a7f3d0"},
            "warning": {"main": "#d97706", "light": "#fffbeb", "soft": "#fde68a"},
            "danger": {"main": "#dc2626", "light": "#fef2f2", "soft": "#fecaca"},
            "teal": {"main": "#0f766e", "light": "#f0fdfa", "soft": "#ccfbf1"},
            "cyan": {"main": "#0284c7", "light": "#f0f9ff", "soft": "#bae6fd"},
            "purple": {"main": "#7c3aed", "light": "#f5f3ff", "soft": "#ddd6fe"},
            "gold": {"main": "#b45309", "light": "#fffbeb", "soft": "#fde68a"},
        },
        "sequence": ["primary", "cyan", "teal", "success", "warning", "purple", "gold", "danger"],
        "relations": {"flow": "primary", "data": "cyan", "sync": "success", "control": "purple", "alert": "danger", "risk": "warning", "feedback": "gold"},
    },
    "process_violet": {
        "name": "process violet",
        "header": {"main": "#4c1d95", "alt": "#7c3aed", "soft": "#f5f3ff"},
        "text": "#2e1065",
        "subtext": "#5b4b76",
        "line": "#ddd6fe",
        "wash": "#faf5ff",
        "roles": {
            "primary": {"main": "#7c3aed", "light": "#f5f3ff", "soft": "#ddd6fe"},
            "success": {"main": "#16a34a", "light": "#f0fdf4", "soft": "#bbf7d0"},
            "warning": {"main": "#f59e0b", "light": "#fffbeb", "soft": "#fde68a"},
            "danger": {"main": "#e11d48", "light": "#fff1f2", "soft": "#fecdd3"},
            "teal": {"main": "#0f766e", "light": "#ecfdf5", "soft": "#ccfbf1"},
            "cyan": {"main": "#0891b2", "light": "#ecfeff", "soft": "#cffafe"},
            "purple": {"main": "#9333ea", "light": "#faf5ff", "soft": "#e9d5ff"},
            "gold": {"main": "#ca8a04", "light": "#fefce8", "soft": "#fef3c7"},
        },
        "sequence": ["primary", "purple", "cyan", "teal", "success", "warning", "danger", "gold"],
        "relations": {"flow": "primary", "data": "cyan", "sync": "success", "control": "purple", "alert": "danger", "risk": "warning", "feedback": "gold"},
    },
    "infra_slate": {
        "name": "infrastructure slate",
        "header": {"main": "#0f172a", "alt": "#334155", "soft": "#f1f5f9"},
        "text": "#0f172a",
        "subtext": "#475569",
        "line": "#cbd5e1",
        "wash": "#f8fafc",
        "roles": {
            "primary": {"main": "#334155", "light": "#f8fafc", "soft": "#e2e8f0"},
            "success": {"main": "#15803d", "light": "#f0fdf4", "soft": "#bbf7d0"},
            "warning": {"main": "#b45309", "light": "#fffbeb", "soft": "#fde68a"},
            "danger": {"main": "#b91c1c", "light": "#fef2f2", "soft": "#fecaca"},
            "teal": {"main": "#0f766e", "light": "#f0fdfa", "soft": "#ccfbf1"},
            "cyan": {"main": "#0369a1", "light": "#f0f9ff", "soft": "#bae6fd"},
            "purple": {"main": "#6d28d9", "light": "#f5f3ff", "soft": "#ddd6fe"},
            "gold": {"main": "#a16207", "light": "#fefce8", "soft": "#fef3c7"},
        },
        "sequence": ["primary", "cyan", "teal", "success", "gold", "purple", "warning", "danger"],
        "relations": {"flow": "primary", "data": "cyan", "sync": "success", "control": "purple", "alert": "danger", "risk": "warning", "feedback": "gold"},
    },
    "service_emerald": {
        "name": "service emerald",
        "header": {"main": "#064e3b", "alt": "#10b981", "soft": "#ecfdf5"},
        "text": "#052e2b",
        "subtext": "#3f6b63",
        "line": "#a7f3d0",
        "wash": "#f0fdfa",
        "roles": {
            "primary": {"main": "#059669", "light": "#ecfdf5", "soft": "#a7f3d0"},
            "success": {"main": "#16a34a", "light": "#f0fdf4", "soft": "#bbf7d0"},
            "warning": {"main": "#d97706", "light": "#fffbeb", "soft": "#fde68a"},
            "danger": {"main": "#dc2626", "light": "#fef2f2", "soft": "#fecaca"},
            "teal": {"main": "#0f766e", "light": "#f0fdfa", "soft": "#ccfbf1"},
            "cyan": {"main": "#0891b2", "light": "#ecfeff", "soft": "#cffafe"},
            "purple": {"main": "#7c3aed", "light": "#f5f3ff", "soft": "#ddd6fe"},
            "gold": {"main": "#b45309", "light": "#fffbeb", "soft": "#fde68a"},
        },
        "sequence": ["primary", "success", "teal", "cyan", "gold", "warning", "purple", "danger"],
        "relations": {"flow": "primary", "data": "cyan", "sync": "success", "control": "purple", "alert": "danger", "risk": "warning", "feedback": "gold"},
    },
    "innovation_royal": {
        "name": "innovation royal",
        "header": {"main": "#1e1b4b", "alt": "#2563eb", "soft": "#eef2ff"},
        "text": "#172554",
        "subtext": "#475569",
        "line": "#bfdbfe",
        "wash": "#f8fafc",
        "roles": {
            "primary": {"main": "#2563eb", "light": "#eff6ff", "soft": "#bfdbfe"},
            "success": {"main": "#059669", "light": "#ecfdf5", "soft": "#a7f3d0"},
            "warning": {"main": "#f59e0b", "light": "#fffbeb", "soft": "#fde68a"},
            "danger": {"main": "#e11d48", "light": "#fff1f2", "soft": "#fecdd3"},
            "teal": {"main": "#0f766e", "light": "#f0fdfa", "soft": "#ccfbf1"},
            "cyan": {"main": "#06b6d4", "light": "#ecfeff", "soft": "#cffafe"},
            "purple": {"main": "#7c3aed", "light": "#f5f3ff", "soft": "#ddd6fe"},
            "gold": {"main": "#ca8a04", "light": "#fefce8", "soft": "#fef3c7"},
        },
        "sequence": ["primary", "cyan", "purple", "teal", "success", "gold", "warning", "danger"],
        "relations": {"flow": "primary", "data": "cyan", "sync": "success", "control": "purple", "alert": "danger", "risk": "warning", "feedback": "gold"},
    },
    "quality_mint": {
        "name": "quality mint",
        "header": {"main": "#134e4a", "alt": "#14b8a6", "soft": "#f0fdfa"},
        "text": "#042f2e",
        "subtext": "#3f6b63",
        "line": "#99f6e4",
        "wash": "#f0fdfa",
        "roles": {
            "primary": {"main": "#0f766e", "light": "#f0fdfa", "soft": "#99f6e4"},
            "success": {"main": "#16a34a", "light": "#f0fdf4", "soft": "#bbf7d0"},
            "warning": {"main": "#ca8a04", "light": "#fefce8", "soft": "#fef3c7"},
            "danger": {"main": "#dc2626", "light": "#fef2f2", "soft": "#fecaca"},
            "teal": {"main": "#0d9488", "light": "#f0fdfa", "soft": "#ccfbf1"},
            "cyan": {"main": "#0891b2", "light": "#ecfeff", "soft": "#cffafe"},
            "purple": {"main": "#6d28d9", "light": "#f5f3ff", "soft": "#ddd6fe"},
            "gold": {"main": "#b45309", "light": "#fffbeb", "soft": "#fde68a"},
        },
        "sequence": ["primary", "success", "teal", "cyan", "warning", "purple", "gold", "danger"],
        "relations": {"flow": "primary", "data": "cyan", "sync": "success", "control": "purple", "alert": "danger", "risk": "warning", "feedback": "gold"},
    },
    "security_green": {
        "name": "安全合规绿蓝",
        "header": {"main": "#064e3b", "alt": "#047857", "soft": "#ecfdf5"},
        "text": "#063b33",
        "subtext": "#3f6b63",
        "line": "#bbf7d0",
        "wash": "#f0fdf4",
        "roles": {
            "primary": {"main": "#047857", "light": "#ecfdf5", "soft": "#bbf7d0"},
            "success": {"main": "#16a34a", "light": "#f0fdf4", "soft": "#dcfce7"},
            "warning": {"main": "#d97706", "light": "#fffbeb", "soft": "#fde68a"},
            "danger": {"main": "#dc2626", "light": "#fef2f2", "soft": "#fee2e2"},
            "teal": {"main": "#0f766e", "light": "#f0fdfa", "soft": "#ccfbf1"},
            "cyan": {"main": "#0891b2", "light": "#ecfeff", "soft": "#cffafe"},
            "purple": {"main": "#6d28d9", "light": "#f5f3ff", "soft": "#ddd6fe"},
            "gold": {"main": "#a16207", "light": "#fefce8", "soft": "#fef3c7"},
        },
        "sequence": ["primary", "success", "teal", "cyan", "warning", "purple", "danger", "gold"],
        "relations": {"flow": "primary", "data": "teal", "sync": "success", "control": "purple", "alert": "danger", "risk": "warning", "feedback": "gold"},
    },
    "risk_orange": {
        "name": "风险故障橙红",
        "header": {"main": "#7c2d12", "alt": "#ea580c", "soft": "#fff7ed"},
        "text": "#431407",
        "subtext": "#7c4a2d",
        "line": "#fed7aa",
        "wash": "#fff7ed",
        "roles": {
            "primary": {"main": "#f97316", "light": "#fff7ed", "soft": "#ffedd5"},
            "success": {"main": "#16a34a", "light": "#f0fdf4", "soft": "#dcfce7"},
            "warning": {"main": "#ea580c", "light": "#fff7ed", "soft": "#fed7aa"},
            "danger": {"main": "#dc2626", "light": "#fef2f2", "soft": "#fecaca"},
            "teal": {"main": "#0f766e", "light": "#ecfdf5", "soft": "#ccfbf1"},
            "cyan": {"main": "#0284c7", "light": "#f0f9ff", "soft": "#bae6fd"},
            "purple": {"main": "#7c3aed", "light": "#f5f3ff", "soft": "#ddd6fe"},
            "gold": {"main": "#ca8a04", "light": "#fefce8", "soft": "#fef3c7"},
        },
        "sequence": ["danger", "warning", "primary", "purple", "cyan", "teal", "success", "gold"],
        "relations": {"flow": "primary", "data": "cyan", "sync": "success", "control": "purple", "alert": "danger", "risk": "warning", "feedback": "gold"},
    },
    "executive_gold": {
        "name": "汇报里程碑蓝金",
        "header": {"main": "#172554", "alt": "#1d4ed8", "soft": "#eff6ff"},
        "text": "#172554",
        "subtext": "#475569",
        "line": "#dbeafe",
        "wash": "#f8fafc",
        "roles": {
            "primary": {"main": "#1d4ed8", "light": "#eff6ff", "soft": "#dbeafe"},
            "success": {"main": "#15803d", "light": "#f0fdf4", "soft": "#bbf7d0"},
            "warning": {"main": "#d97706", "light": "#fffbeb", "soft": "#fde68a"},
            "danger": {"main": "#b91c1c", "light": "#fef2f2", "soft": "#fecaca"},
            "teal": {"main": "#0f766e", "light": "#f0fdfa", "soft": "#ccfbf1"},
            "cyan": {"main": "#0369a1", "light": "#f0f9ff", "soft": "#bae6fd"},
            "purple": {"main": "#6d28d9", "light": "#f5f3ff", "soft": "#ddd6fe"},
            "gold": {"main": "#b45309", "light": "#fffbeb", "soft": "#fde68a"},
        },
        "sequence": ["primary", "gold", "success", "cyan", "purple", "warning", "teal", "danger"],
        "relations": {"flow": "primary", "data": "cyan", "sync": "success", "control": "purple", "alert": "danger", "risk": "warning", "feedback": "gold"},
    },
}


ALIASES = {
    "default": "primary",
    "accent": "teal",
    "blue": "primary",
    "green": "success",
    "orange": "warning",
    "red": "danger",
    "yellow": "gold",
}


def get_palette(name: str | None = None) -> dict[str, Any]:
    """Return a named palette, falling back to the bid example palette."""

    return PALETTES.get(name or _CURRENT_PALETTE.get(), PALETTES[DEFAULT_PALETTE])


@contextmanager
def use_palette(name: str | None) -> Iterator[None]:
    token = _CURRENT_PALETTE.set(name if name in PALETTES else DEFAULT_PALETTE)
    try:
        yield
    finally:
        _CURRENT_PALETTE.reset(token)


def normalize_style(style: Any, default: str = "primary") -> str:
    key = str(style or default).strip().lower()
    return ALIASES.get(key, key)


def role(style: Any = None, palette_name: str | None = None) -> dict[str, str]:
    palette = get_palette(palette_name)
    roles = palette["roles"]
    key = normalize_style(style)
    return roles.get(key, roles["primary"])


def triplet(style: Any = None, palette_name: str | None = None) -> tuple[str, str, str]:
    item = role(style, palette_name)
    return item["main"], item["light"], item["soft"]


def role_for_index(index: int, palette_name: str | None = None) -> str:
    palette = get_palette(palette_name)
    sequence = palette["sequence"]
    return sequence[index % len(sequence)]


def triplet_for_index(index: int, palette_name: str | None = None) -> tuple[str, str, str]:
    return triplet(role_for_index(index, palette_name), palette_name)


def style_from_item(item: Any, index: int = 0, palette_name: str | None = None) -> str:
    if isinstance(item, dict) and item.get("style"):
        return normalize_style(item.get("style"))
    return role_for_index(index, palette_name)


def relation_color(relation: Any = None, palette_name: str | None = None) -> str:
    palette = get_palette(palette_name)
    style = palette["relations"].get(str(relation or "flow").lower(), "primary")
    return role(style, palette_name)["main"]


def select_palette_for_item(job: Any, item: Any) -> str:
    """Pick a palette from explicit hints or by reading the diagram content."""

    explicit = _explicit_palette(
        getattr(item, "visual", None),
        getattr(item, "data", None),
        getattr(job, "style", None),
    )
    if explicit:
        return explicit
    payload = {
        "type": getattr(item, "type", ""),
        "intent": getattr(item, "intent", ""),
        "insertion": getattr(item, "insertion", {}),
        "data": getattr(item, "data", {}),
    }
    return select_palette_for_payload(payload, payload.get("type", ""))


def select_palette_for_payload(payload: dict[str, Any], diagram_type: str = "") -> str:
    """Select the visual palette for a render job.

    The platform default is intentionally stable and engineering-oriented. A
    caller may still opt into a named palette with ``style.palette`` or
    ``visual.palette``, but automatic per-diagram palette switching is avoided
    because it makes one document look like several unrelated design systems.
    """

    explicit = _explicit_palette(payload, payload.get("visual"), payload.get("style"))
    if explicit:
        return explicit
    return DEFAULT_PALETTE


def _explicit_palette(*sources: Any) -> str | None:
    keys = ("palette", "colorScheme", "color_scheme", "themePalette")
    for source in sources:
        if not isinstance(source, dict):
            continue
        for key in keys:
            value = source.get(key)
            if isinstance(value, str) and value in PALETTES:
                return value
        style = source.get("style")
        if isinstance(style, dict):
            for key in keys:
                value = style.get(key)
                if value in PALETTES:
                    return value
    return None


def _payload_text(payload: Any) -> str:
    try:
        return json.dumps(payload, ensure_ascii=False).lower()
    except TypeError:
        return str(payload).lower()


def _has_any(text: str, words: list[str]) -> bool:
    return any(word.lower() in text for word in words)
