"""Test illustration subsystem."""

import pytest


def test_icons_module():
    """icons module should have 46+ icons."""
    from bid_tool.illustration.icons import ICONS

    assert len(ICONS) >= 46
    for key, (label, svg_path) in ICONS.items():
        assert isinstance(key, str)
        assert isinstance(label, str)
        assert isinstance(svg_path, str)
        assert "<path" in svg_path or "<circle" in svg_path or "<rect" in svg_path


def test_themes_module():
    """themes module should have 4 legacy SVG themes with expected color keys."""
    from bid_tool.illustration.themes import THEMES

    expected_themes = {"clarity_blue", "navy_teal", "royal_gold", "slate_emerald"}
    assert set(THEMES.keys()) == expected_themes

    for name, theme in THEMES.items():
        for key in ("bg", "header_a", "header_b", "accent", "text"):
            assert key in theme, f"{name} missing {key!r}"


def test_v2_job_model_rejects_v1_jobs():
    """The public illustration platform should no longer accept v1 jobs."""
    from bid_tool.illustration.core.job import IllustrationJob

    with pytest.raises(ValueError, match="version '2.0'"):
        IllustrationJob.from_raw({
            "version": "1.0",
            "document": {"title": "Test"},
            "illustrations": [],
        })


def test_svg_renderer_imports():
    """svg_renderer should import without errors."""
    from bid_tool.illustration.svg_renderer import ICONS, RENDERERS, WIDTH

    assert ICONS
    assert len(RENDERERS) >= 6
    assert WIDTH > 0


def test_svg_renderer_has_all_diagram_types():
    """svg_renderer should support the core native diagram types."""
    from bid_tool.illustration.svg_renderer import RENDERERS

    expected = {
        "layered_architecture",
        "flowchart",
        "sequence_diagram",
        "swimlane_flowchart",
        "capability_map",
        "relationship_map",
    }
    assert expected.issubset(set(RENDERERS.keys()))


def test_echarts_workbench_files():
    """echarts_workbench should have required files."""
    from bid_tool.illustration.toolkit import WEB_RUNTIME_DIR

    for fname in ("index.html", "app.js", "styles.css"):
        assert (WEB_RUNTIME_DIR / fname).exists(), f"Missing: {fname}"
    assert (WEB_RUNTIME_DIR / "vendor" / "echarts.min.js").exists()


def test_platform_registry_contains_bid_diagrams():
    """Platform registry should expose semantic bid diagram types."""
    from bid_tool.illustration.core.registry import get_registry

    registry = get_registry()
    assert registry["architecture.layered"].default_renderer == "html_css"
    assert registry["timeline.gantt"].default_renderer == "html_css"
    assert registry["matrix.risk"].default_renderer == "html_css"
    assert registry["integration.interface_map"].default_renderer == "html_css"
    assert "mermaid" in registry["process.flowchart"].renderers
    assert registry["network.topology"].default_renderer == "graphviz"
    assert registry["chart.bar_line"].default_renderer == "echarts_html"


def test_platform_supports_mermaid_and_graphviz_renderers():
    """Platform should expose concrete adapters for Mermaid and Graphviz."""
    from bid_tool.illustration.platform import SUPPORTED_RENDERERS

    assert "mermaid" in SUPPORTED_RENDERERS
    assert "graphviz" in SUPPORTED_RENDERERS


def test_platform_routes_svg_aliases():
    """Router should still map SVG-native diagram ids to platform renderers."""
    from bid_tool.illustration.core.job import IllustrationItem
    from bid_tool.illustration.core.router import route_item

    item = IllustrationItem(
        id="arch",
        type="layered_architecture",
        renderer="auto",
        insertion={"caption": "Figure 1 Architecture"},
        data={"title": "Architecture"},
    )
    route = route_item(item)
    assert route.type == "architecture.layered"
    assert route.renderer == "html_css"
    assert route.legacy_type == "layered_architecture"


def test_platform_decides_svg_for_dense_or_precise_frames():
    """Auto routing should preserve SVG for dense or precise vector diagrams."""
    from bid_tool.illustration.core.job import IllustrationItem
    from bid_tool.illustration.core.router import route_item

    item = IllustrationItem(
        id="dense_arch",
        type="architecture.layered",
        renderer="auto",
        insertion={"caption": "Dense architecture"},
        data={
            "title": "Dense architecture",
            "layers": [
                {"label": "L1", "items": [{"title": f"N{i}"} for i in range(13)]},
                {"label": "L2", "items": [{"title": f"M{i}"} for i in range(13)]},
            ],
        },
    )
    route = route_item(item)
    assert route.renderer == "svg_native"
    assert route.reasons


def test_platform_decides_html_for_interface_map():
    """Interface maps should use the figure-3 bid style renderer."""
    from bid_tool.illustration.core.job import IllustrationItem
    from bid_tool.illustration.core.router import route_item

    item = IllustrationItem(
        id="interface_map",
        type="integration.interface_map",
        renderer="auto",
        insertion={"caption": "Interface map"},
        data={"title": "Interface map"},
    )
    assert route_item(item).renderer == "html_css"


def test_platform_v2_job_validation():
    """v2 semantic validation should pass for a minimal renderable job."""
    from bid_tool.illustration.core.job import IllustrationJob
    from bid_tool.illustration.core.validator import validate_platform_job

    job = IllustrationJob.from_raw({
        "version": "2.0",
        "document": {"title": "Test"},
        "illustrations": [
            {
                "id": "trend",
                "type": "chart.bar_line",
                "renderer": "auto",
                "intent": "show trend",
                "insertion": {"section": "1", "caption": "Figure 1 Trend"},
                "data": {
                    "source": "test data",
                    "categories": ["A", "B"],
                    "bar": {"name": "Count", "values": [1, 2]},
                    "line": {"name": "Rate", "values": [50, 80]},
                },
            }
        ],
    })
    assert validate_platform_job(job) == []


def test_public_api_facade_plans_job():
    """Public API should expose stable planning surface for external callers."""
    from bid_tool.illustration import api

    job = api.load("examples/示例_接口关系与数据交互图.json")
    errors, warnings = api.validate(job)
    decisions = api.plan(job)
    types = api.list_diagram_types()

    assert errors == []
    assert isinstance(warnings, list)
    assert decisions[0]["renderer"] == "html_css"
    assert any(item["id"] == "integration.interface_map" for item in types)


def test_standalone_bundle_builds_minimal_runtime(tmp_path):
    """Standalone bundle should contain the illustration runtime, not the full pipeline."""
    from bid_tool.illustration.standalone import build_bundle

    bundle = build_bundle(tmp_path / "bundle", include_examples=False)

    assert (bundle / "run_illustration.py").exists()
    assert (bundle / "requirements.txt").exists()
    assert (bundle / "src" / "bid_tool" / "illustration" / "toolkit.py").exists()
    assert (bundle / "src" / "bid_tool" / "schemas" / "illustration_job_v2.schema.json").exists()
    assert not (bundle / "src" / "bid_tool" / "pipeline").exists()
