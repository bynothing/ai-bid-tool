"""Diagram type registry.

The registry decouples semantic diagram types from concrete renderers. AI jobs
can request `renderer=auto`; the router then uses this table to pick a renderer.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True, slots=True)
class DiagramType:
    id: str
    label: str
    default_renderer: str
    renderers: tuple[str, ...]
    legacy_type: str | None = None
    description: str = ""


def _diagram(
    id: str,
    label: str,
    default_renderer: str,
    *renderers: str,
    legacy_type: str | None = None,
    description: str = "",
) -> DiagramType:
    supported = (default_renderer, *renderers)
    return DiagramType(id, label, default_renderer, supported, legacy_type, description)


_REGISTRY: dict[str, DiagramType] = {
    # Existing SVG-native capabilities.
    "architecture.layered": _diagram(
        "architecture.layered", "分层架构图", "svg_native", legacy_type="layered_architecture",
        description="系统总体架构、技术架构、能力分层。"
    ),
    "process.flowchart": _diagram(
        "process.flowchart", "流程图", "svg_native", "mermaid", legacy_type="flowchart",
        description="业务、服务、运维、处置流程。"
    ),
    "process.swimlane": _diagram(
        "process.swimlane", "泳道流程图", "svg_native", legacy_type="swimlane_flowchart",
        description="多角色、多部门、多系统协同。"
    ),
    "interaction.sequence": _diagram(
        "interaction.sequence", "时序图", "svg_native", "mermaid", legacy_type="sequence_diagram",
        description="接口调用、消息传递、事件交互。"
    ),
    "capability.map": _diagram(
        "capability.map", "能力地图", "svg_native", legacy_type="capability_map",
        description="功能模块、服务能力、响应能力分组。"
    ),
    "relationship.domain": _diagram(
        "relationship.domain", "关系图", "svg_native", "graphviz", legacy_type="relationship_map",
        description="系统、组件、实体、数据表关系。"
    ),
    # Planned formal bid diagrams.
    "architecture.deployment": _diagram(
        "architecture.deployment", "部署架构图", "html_css", "svg_native", "graphviz",
        description="服务器、网络域、安全域、终端部署。"
    ),
    "architecture.security": _diagram(
        "architecture.security", "安全体系图", "html_css", "svg_native",
        description="边界防护、访问控制、审计、备份、应急。"
    ),
    "network.topology": _diagram(
        "network.topology", "网络拓扑图", "graphviz", "html_css", "svg_native",
        description="网络设备、链路、区域、访问方向。"
    ),
    "timeline.gantt": _diagram(
        "timeline.gantt", "甘特图", "html_css", "mermaid",
        description="实施计划、阶段周期、交付节奏。"
    ),
    "timeline.milestone": _diagram(
        "timeline.milestone", "里程碑图", "html_css", "svg_native",
        description="关键节点、交付成果、评审窗口。"
    ),
    "matrix.risk": _diagram(
        "matrix.risk", "风险矩阵", "html_css", "svg_native",
        description="概率 x 影响的风险等级表达。"
    ),
    "matrix.scoring_response": _diagram(
        "matrix.scoring_response", "评分响应矩阵", "html_css",
        description="评分项、响应章节、证明材料覆盖。"
    ),
    "comparison.solution": _diagram(
        "comparison.solution", "方案对比图", "html_css", "svg_native",
        description="我方方案与常规/替代方案的对比。"
    ),
    "overview.one_page": _diagram(
        "overview.one_page", "一页式总览图", "html_css",
        description="问题、方案、路径、价值的一页式表达。"
    ),
}

_LEGACY_ALIASES = {
    "layered_architecture": "architecture.layered",
    "flowchart": "process.flowchart",
    "swimlane_flowchart": "process.swimlane",
    "sequence_diagram": "interaction.sequence",
    "capability_map": "capability.map",
    "relationship_map": "relationship.domain",
    "bar_line": "chart.bar_line",
    "radar": "chart.radar",
    "sankey": "chart.sankey",
    "pie_donut": "chart.pie_donut",
    "stacked_bar": "chart.stacked_bar",
    "line_multi": "chart.line_multi",
    "funnel": "chart.funnel",
    "gauge": "chart.gauge",
}

for chart_type, label in {
    "chart.bar_line": "柱线组合图",
    "chart.radar": "雷达图",
    "chart.sankey": "桑基图",
    "chart.pie_donut": "饼/环图",
    "chart.stacked_bar": "堆叠柱状图",
    "chart.line_multi": "多折线图",
    "chart.funnel": "漏斗图",
    "chart.gauge": "仪表盘",
    "chart.heatmap": "热力图",
}.items():
    legacy = chart_type.removeprefix("chart.")
    _REGISTRY[chart_type] = _diagram(
        chart_type, label, "echarts_html", legacy_type=legacy,
        description="投标文档中的数据统计和指标展示。"
    )


def normalize_type(type_id: str) -> str:
    """Return the canonical v2 type id for a v1/v2 diagram type."""

    return _LEGACY_ALIASES.get(type_id, type_id)


def get_registry() -> dict[str, DiagramType]:
    return dict(_REGISTRY)


def get_diagram_type(type_id: str) -> DiagramType | None:
    return _REGISTRY.get(normalize_type(type_id))
