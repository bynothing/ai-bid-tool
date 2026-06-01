"""Renderer routing for illustration jobs."""
from __future__ import annotations

from dataclasses import dataclass

from .decision import decide_renderer
from .job import IllustrationItem
from .registry import get_diagram_type, normalize_type


@dataclass(frozen=True, slots=True)
class Route:
    item_id: str
    type: str
    renderer: str
    legacy_type: str | None = None
    reasons: tuple[str, ...] = ()


def route_item(item: IllustrationItem) -> Route:
    """Resolve one item to a concrete renderer."""

    canonical_type = normalize_type(item.type)
    diagram = get_diagram_type(canonical_type)
    if diagram is None:
        raise ValueError(f"未注册的图型: {item.type}")

    renderer = item.renderer
    if renderer == "svg":
        renderer = "svg_native"
    elif renderer == "echarts":
        renderer = "echarts_html"

    reasons: tuple[str, ...] = ()
    if renderer == "auto":
        decision = decide_renderer(item)
        renderer = decision.renderer
        reasons = tuple(decision.reasons)
    if renderer not in diagram.renderers:
        supported = ", ".join(diagram.renderers)
        raise ValueError(f"{item.id}: 图型 {canonical_type} 不支持渲染器 {renderer}; 可选 {supported}")
    return Route(item.id, canonical_type, renderer, diagram.legacy_type, reasons)
