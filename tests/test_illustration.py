"""Test illustration subsystem."""
import pytest


def test_icons_module():
    """icons module should have 46+ icons."""
    from bid_tool.illustration.icons import ICONS
    assert len(ICONS) >= 46
    # Check structure
    for key, (label, svg_path) in ICONS.items():
        assert isinstance(key, str)
        assert isinstance(label, str)
        assert isinstance(svg_path, str)
        assert '<path' in svg_path or '<circle' in svg_path or '<rect' in svg_path


def test_themes_module():
    """themes module should have 4 themes with expected color keys."""
    from bid_tool.illustration.themes import THEMES
    assert len(THEMES) == 4
    expected_themes = {'clarity_blue', 'navy_teal', 'royal_gold', 'slate_emerald'}
    assert set(THEMES.keys()) == expected_themes

    for name, theme in THEMES.items():
        assert 'bg' in theme, f"{name} missing 'bg'"
        assert 'header_a' in theme, f"{name} missing 'header_a'"
        assert 'header_b' in theme, f"{name} missing 'header_b'"
        assert 'accent' in theme, f"{name} missing 'accent'"
        assert 'text' in theme, f"{name} missing 'text'"


def test_toolkit_validate_job_valid():
    """validate_job should pass for a valid minimal job."""
    from bid_tool.illustration.toolkit import validate_job

    job = {
        "version": "1.0",
        "document": {"title": "Test Document"},
        "illustrations": [
            {
                "id": "test_01",
                "renderer": "svg",
                "insertion": {
                    "section": "第1章",
                    "caption": "Test Figure",
                },
                "spec": {
                    "type": "layered_architecture",
                    "title": "Test Architecture",
                    "layers": [
                        {
                            "label": "Layer 1",
                            "items": [
                                {"title": "Component A", "desc": "Description A"}
                            ]
                        }
                    ]
                }
            }
        ]
    }
    errors, svg_pkg, chart_pkg = validate_job(job)
    assert errors == [], f"Unexpected errors: {errors}"
    assert len(svg_pkg['figures']) == 1
    assert len(chart_pkg['charts']) == 0


def test_toolkit_validate_job_duplicate_id():
    """validate_job should catch duplicate illustration IDs."""
    from bid_tool.illustration.toolkit import validate_job

    spec = {
        "type": "layered_architecture",
        "title": "Test",
        "layers": [{"label": "L1", "items": [{"title": "A", "desc": "B"}]}]
    }
    insertion = {"section": "第1章", "caption": "Test"}
    job = {
        "version": "1.0",
        "document": {"title": "Test"},
        "illustrations": [
            {"id": "dup_id", "renderer": "svg", "insertion": dict(insertion), "spec": dict(spec)},
            {"id": "dup_id", "renderer": "svg", "insertion": dict(insertion), "spec": dict(spec)},
        ]
    }
    errors, _, _ = validate_job(job)
    assert any('必须唯一' in e for e in errors)


def test_svg_renderer_imports():
    """svg_renderer should import without errors."""
    from bid_tool.illustration.svg_renderer import (
        ICONS, THEMES, RENDERERS, WIDTH
    )
    assert len(RENDERERS) >= 6
    assert WIDTH > 0


def test_svg_renderer_has_all_diagram_types():
    """svg_renderer should support all 6 diagram types."""
    from bid_tool.illustration.svg_renderer import RENDERERS
    expected = {
        'layered_architecture', 'flowchart', 'sequence_diagram',
        'swimlane_flowchart', 'capability_map', 'relationship_map'
    }
    assert set(RENDERERS.keys()) == expected


def test_echarts_workbench_files():
    """echarts_workbench should have required files."""
    from bid_tool.illustration.toolkit import WEB_RUNTIME_DIR
    required = ['index.html', 'app.js', 'styles.css']
    for fname in required:
        assert (WEB_RUNTIME_DIR / fname).exists(), f"Missing: {fname}"
    assert (WEB_RUNTIME_DIR / 'vendor' / 'echarts.min.js').exists()
