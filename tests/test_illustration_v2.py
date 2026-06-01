"""Tests for the isolated illustration_v2 package."""
from pathlib import Path


EXAMPLE = Path("src/bid_tool/illustration_v2/examples/arch_layered_job.json")
REFERENCE_STYLE_EXAMPLE = Path("src/bid_tool/illustration_v2/examples/reference_style_job.json")


def test_illustration_v2_catalog_exposes_template():
    from bid_tool.illustration_v2 import api

    catalog = api.list_capabilities()

    assert catalog["templates"][0]["id"] == "arch.layered.v2"
    assert catalog["templates"][0]["diagram_type"] == "architecture.layered"
    assert {template["id"] for template in catalog["templates"]} >= {
        "platform.interface.v2",
        "process.resilience.v2",
        "inspection.cards.v2",
        "severity.closure.v2",
        "security.loop.v2",
    }
    assert catalog["renderers"][0]["id"] == "template_svg"


def test_illustration_v2_plans_tier1_template():
    from bid_tool.illustration_v2 import api

    errors, warnings = api.validate(EXAMPLE)
    decision = api.plan(EXAMPLE)[0]

    assert errors == []
    assert warnings == []
    assert decision["renderer"] == "template_svg"
    assert decision["decision"]["tier"] == 1
    assert decision["decision"]["template"] == "arch.layered.v2"
    assert decision["decision"]["fit_score"] == 1.0
    assert decision["decision"]["needs_human_review"] is False


def test_illustration_v2_renders_manifest(tmp_path):
    from bid_tool.illustration_v2 import api

    records = api.render(EXAMPLE, tmp_path)

    assert records[0].tier == 1
    assert records[0].template == "arch.layered.v2"
    assert (tmp_path / "illustration-manifest.json").exists()
    assert (tmp_path / records[0].outputs["svg"]).exists()


def test_illustration_v2_reference_style_templates_render(tmp_path):
    from bid_tool.illustration_v2 import api

    errors, warnings = api.validate(REFERENCE_STYLE_EXAMPLE)
    decisions = api.plan(REFERENCE_STYLE_EXAMPLE)
    records = api.render(REFERENCE_STYLE_EXAMPLE, tmp_path, png=True)

    assert errors == []
    assert warnings == []
    assert len(records) == 5
    assert {decision["decision"]["template"] for decision in decisions} == {
        "platform.interface.v2",
        "process.resilience.v2",
        "inspection.cards.v2",
        "severity.closure.v2",
        "security.loop.v2",
    }
    assert all(record.tier == 1 for record in records)
    assert all((tmp_path / record.outputs["svg"]).exists() for record in records)
    assert all((tmp_path / record.outputs["png"]).exists() for record in records)
    assert all(record.warnings == [] for record in records)
