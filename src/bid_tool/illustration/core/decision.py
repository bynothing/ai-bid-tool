"""Content analysis driven renderer decision layer.

`renderer=auto` should behave like a design reviewer: first understand the
diagram intent and content, then pick the renderer that expresses it best.
The implementation is deterministic, but the signals mirror the judgement an
LLM prompt should make before choosing a drawing technology.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from .job import IllustrationItem
from .registry import get_diagram_type, normalize_type

IMPLEMENTED_RENDERERS = {"html_css", "svg_native", "echarts_html", "mermaid", "graphviz"}


@dataclass(slots=True)
class RendererDecision:
    renderer: str
    reasons: list[str] = field(default_factory=list)


@dataclass(slots=True)
class ContentAnalysis:
    canonical_type: str
    intent_text: str
    item_count: int
    edge_count: int
    branch_count: int
    lane_count: int
    series_count: int
    categories_count: int
    is_data_chart: bool
    is_showcase: bool
    is_precise_structure: bool
    is_topology: bool
    is_bid_overview: bool
    requires_vector: bool
    requires_exact_connectors: bool
    has_security_or_interface_terms: bool
    summary: str


def decide_renderer(item: IllustrationItem) -> RendererDecision:
    """Choose the best renderer for one item when renderer=auto."""

    canonical = normalize_type(item.type)
    diagram = get_diagram_type(canonical)
    if diagram is None:
        raise ValueError(f"未注册的图型: {item.type}")

    analysis = analyze_content(item)
    data = item.data or {}
    visual = item.visual or {}
    explicit = visual.get("rendererPreference") or data.get("rendererPreference")
    if explicit in diagram.renderers:
        return RendererDecision(explicit, [analysis.summary, f"显式偏好 rendererPreference={explicit}"])

    scores = _score_renderers(analysis)
    supported_scores = {
        renderer: score
        for renderer, score in scores.items()
        if renderer in diagram.renderers and renderer in IMPLEMENTED_RENDERERS
    }
    if not supported_scores:
        return RendererDecision(diagram.default_renderer, [analysis.summary, "无可用评分项，使用图型注册表默认渲染器"])

    renderer = max(supported_scores, key=lambda key: (supported_scores[key], key == diagram.default_renderer))
    reasons = [analysis.summary, _explain_choice(renderer, analysis, supported_scores)]
    return RendererDecision(renderer, reasons)


def analyze_content(item: IllustrationItem) -> ContentAnalysis:
    """Extract semantic and structural signals from one diagram request."""

    canonical = normalize_type(item.type)
    data = item.data or {}
    visual = item.visual or {}
    intent_text = _collect_text(item)
    lowered = intent_text.lower()

    item_count = _count_items(data)
    edge_count = len(data.get("edges", []))
    branch_count = sum(1 for node in data.get("nodes", []) if node.get("kind") == "decision")
    lane_count = len(data.get("lanes", []))
    series_count = len(data.get("series", []))
    categories_count = len(data.get("categories", []))

    is_data_chart = canonical.startswith("chart.") or bool(series_count and categories_count)
    is_topology = canonical == "network.topology" or _has_any(lowered, ["拓扑", "网络", "链路", "交换机", "路由", "防火墙", "安全域"])
    is_bid_overview = canonical in {
        "timeline.gantt",
        "timeline.milestone",
        "matrix.risk",
        "matrix.scoring_response",
        "comparison.solution",
        "overview.one_page",
        "integration.interface_map",
        "architecture.deployment",
        "architecture.security",
    }
    has_security_or_interface_terms = _has_any(
        lowered,
        ["接口", "交互", "推送", "反馈", "ack", "https", "mqtt", "认证", "鉴权", "签名", "审计", "安全"],
    )
    requires_vector = bool(visual.get("editableVector") or _has_any(lowered, ["可编辑", "矢量", "svg"]))
    requires_exact_connectors = bool(
        visual.get("preciseConnectors")
        or _has_any(lowered, ["精确连线", "复杂连线", "回路", "依赖", "实体关系", "外键", "跨层"])
    )
    dense = item_count > 24 or edge_count > 10 or branch_count >= 3 or lane_count >= 5
    is_precise_structure = requires_vector or requires_exact_connectors or dense or is_topology
    is_showcase = (
        is_bid_overview
        or _has_any(lowered, ["总览", "说明", "展示", "亮点", "对比", "路线", "里程碑", "矩阵", "适配架构"])
        or (item_count <= 24 and edge_count <= 6 and not is_topology)
    )

    signals = []
    if is_data_chart:
        signals.append("数据图")
    if is_showcase:
        signals.append("展示型标书图")
    if is_precise_structure:
        signals.append("精确结构/复杂关系")
    if has_security_or_interface_terms:
        signals.append("接口/安全语义")
    signals_text = "、".join(signals) or "通用框图"
    summary = (
        f"内容分析: {signals_text}; 元素 {item_count}, 连线 {edge_count}, "
        f"分支 {branch_count}, 泳道 {lane_count}"
    )
    return ContentAnalysis(
        canonical_type=canonical,
        intent_text=intent_text,
        item_count=item_count,
        edge_count=edge_count,
        branch_count=branch_count,
        lane_count=lane_count,
        series_count=series_count,
        categories_count=categories_count,
        is_data_chart=is_data_chart,
        is_showcase=is_showcase,
        is_precise_structure=is_precise_structure,
        is_topology=is_topology,
        is_bid_overview=is_bid_overview,
        requires_vector=requires_vector,
        requires_exact_connectors=requires_exact_connectors,
        has_security_or_interface_terms=has_security_or_interface_terms,
        summary=summary,
    )


def _score_renderers(analysis: ContentAnalysis) -> dict[str, int]:
    scores = {"html_css": 0, "svg_native": 0, "echarts_html": 0, "graphviz": 0, "mermaid": 0}

    if analysis.is_data_chart:
        scores["echarts_html"] += 100
        scores["html_css"] -= 20
        scores["svg_native"] -= 10

    # SVG-native premium renderers: polished publication-quality output.
    # For these types, SVG is the default choice unless the diagram is tiny.
    _svg_premium_types = {
        "architecture.layered", "process.flowchart", "capability.map",
        "process.swimlane", "interaction.sequence", "relationship.domain",
        "integration.interface_map",
        "operation.inspection_taxonomy", "operation.incident_response",
        "architecture.security_ring",
    }
    if analysis.canonical_type in _svg_premium_types:
        scores["svg_native"] += 50  # strong preference for polished SVG renderers
        if analysis.item_count >= 8:
            scores["svg_native"] += 25  # rich diagrams benefit more from SVG
        if analysis.edge_count >= 3:
            scores["svg_native"] += 20

    if analysis.is_showcase:
        scores["html_css"] += 55
    if analysis.is_bid_overview:
        scores["html_css"] += 35

    if analysis.is_precise_structure:
        scores["svg_native"] += 55
    if analysis.requires_vector:
        scores["svg_native"] += 45
    if analysis.requires_exact_connectors:
        scores["svg_native"] += 40

    if analysis.is_topology:
        scores["graphviz"] += 120
        scores["svg_native"] += 35
        scores["html_css"] -= 10

    if analysis.has_security_or_interface_terms and analysis.item_count <= 28:
        scores["html_css"] += 25

    if analysis.item_count > 30:
        scores["svg_native"] += 35
        scores["html_css"] -= 15
    if analysis.edge_count > 10:
        scores["svg_native"] += 40
        scores["html_css"] -= 10
    if analysis.branch_count >= 3:
        scores["svg_native"] += 25
    if analysis.canonical_type in {"process.flowchart", "process.swimlane", "interaction.sequence"} and analysis.item_count <= 10:
        scores["html_css"] += 20
    if analysis.canonical_type in {"process.flowchart", "interaction.sequence"} and analysis.requires_exact_connectors:
        scores["mermaid"] += 45
    if analysis.canonical_type == "integration.interface_map":
        scores["html_css"] += 80
    return scores


def _explain_choice(renderer: str, analysis: ContentAnalysis, scores: dict[str, int]) -> str:
    score_text = ", ".join(f"{key}={value}" for key, value in sorted(scores.items()))
    if renderer == "echarts_html":
        reason = "选择 ECharts：内容以数值、序列或指标为主，ECharts 更适合坐标轴、图例和标签表达"
    elif renderer == "svg_native":
        reason = "选择 SVG：内容需要精确结构、矢量可编辑能力或复杂连线控制"
    elif renderer == "html_css":
        reason = "选择 HTML/CSS：内容偏正式标书展示，适合图3风格的标题栏、分区卡片、说明和结论条"
    elif renderer == "graphviz":
        reason = "选择 Graphviz：内容偏拓扑或复杂关系，自动布局更合适"
    else:
        reason = f"选择 {renderer}"
    return f"{reason}; 评分 {score_text}"


def _count_items(data: dict[str, Any]) -> int:
    total = 0
    total += len(data.get("actors", []))
    total += len(data.get("integrations", []))
    for layer in data.get("layers", []):
        total += len(layer.get("items", []))
    for group in data.get("groups", []):
        total += len(group.get("items", []))
    for container in data.get("containers", []):
        total += len(container.get("nodes", []))
    total += len(data.get("nodes", []))
    total += len(data.get("steps", []))
    total += len(data.get("messages", []))
    total += len(data.get("phases", []))
    total += len(data.get("risks", []))
    total += len(data.get("flows", []))
    return total


def _collect_text(item: IllustrationItem) -> str:
    chunks = [
        item.id,
        item.type,
        item.intent,
        item.insertion.get("caption", ""),
        item.insertion.get("purpose", ""),
        _stringify_text(item.data),
        _stringify_text(item.visual),
    ]
    return " ".join(chunk for chunk in chunks if chunk)


def _stringify_text(value: Any) -> str:
    if isinstance(value, dict):
        return " ".join(_stringify_text(item) for item in value.values())
    if isinstance(value, list):
        return " ".join(_stringify_text(item) for item in value)
    if isinstance(value, str):
        return value
    return ""


def _has_any(text: str, keywords: list[str]) -> bool:
    return any(keyword.lower() in text for keyword in keywords)
