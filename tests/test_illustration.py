"""Compatibility tests for the active illustration_v2 drawing interfaces."""
from pathlib import Path


def _drawio_job():
    return {
        "version": "2.0",
        "document": {"title": "Draw.io 迁移测试"},
        "illustrations": [
            {
                "id": "drawio_arch",
                "type": "architecture.layered",
                "renderer": "drawio",
                "intent": "验证 Draw.io 已注册到 illustration_v2",
                "insertion": {"section": "测试章节", "caption": "Draw.io 系统框图"},
                "data": {
                    "title": "系统框图",
                    "layers": [
                        {
                            "title": "接入层",
                            "items": [
                                {"id": "portal", "title": "门户"},
                                {"id": "gateway", "title": "API 网关"},
                            ],
                        },
                        {
                            "title": "服务层",
                            "items": [
                                {"id": "service", "title": "业务服务"},
                                {"id": "db", "title": "数据仓库"},
                            ],
                        },
                    ],
                    "edges": [
                        {"from": "portal", "to": "gateway", "label": "请求"},
                        {"from": "gateway", "to": "service", "label": "编排"},
                        {"from": "service", "to": "db", "label": "读写"},
                    ],
                },
            }
        ],
    }


def test_illustration_v2_exports_drawing_tools():
    from bid_tool.illustration_v2 import list_drawing_tools

    tools = list_drawing_tools()

    assert any(tool["name"] == "drawio" and tool["kind"] == "external_cli" for tool in tools)


def test_illustration_v2_plans_explicit_drawio_renderer():
    from bid_tool.illustration_v2 import api
    from bid_tool.illustration_v2.core.models import IllustrationJob

    decision = api.plan(IllustrationJob.from_raw(_drawio_job()))[0]

    assert decision["renderer"] == "drawio"
    assert decision["decision"]["tier"] == 2
    assert decision["decision"]["template"] is None


def test_illustration_v2_drawio_renders_editable_source(tmp_path, monkeypatch):
    from bid_tool.illustration_v2 import api
    from bid_tool.illustration_v2.core.models import IllustrationJob
    from bid_tool.illustration_v2.renderers import drawio

    monkeypatch.setattr(drawio, "_find_drawio_command", lambda: None)

    records = api.render(IllustrationJob.from_raw(_drawio_job()), tmp_path, png=True)

    assert records[0].renderer == "drawio"
    assert records[0].outputs["drawio"].endswith(".drawio")
    assert "png" not in records[0].outputs
    assert (tmp_path / records[0].outputs["drawio"]).exists()
    assert (tmp_path / "illustration-manifest.json").exists()


def test_illustration_v2_toolkit_schema_dir_exists():
    from bid_tool.illustration_v2.toolkit import SCHEMA_DIR

    assert Path(SCHEMA_DIR, "illustration_job_v2.schema.json").exists()


def test_drawio_content_standard_normalizes_labels_and_subtitles():
    from bid_tool.illustration_v2.core.models import IllustrationJob
    from bid_tool.illustration_v2.renderers.drawio import _drawio_xml

    raw = _drawio_job()
    raw["illustrations"][0]["data"]["layers"][0]["items"][0]["description"] = "接入层"
    raw["illustrations"][0]["data"]["edges"] = [
        {"from": "portal", "to": "gateway", "label": "请求"},
        {"from": "gateway", "to": "service", "label": "请求"},
        {"from": "service", "to": "db", "label": "HTTPS"},
    ]
    item = IllustrationJob.from_raw(raw).illustrations[0]
    xml = _drawio_xml(IllustrationJob.from_raw(raw), item)

    assert "请求" not in xml
    assert "HTTPS" in xml
    assert "门户&lt;/b&gt;&lt;br&gt;" not in xml
    assert 'fillColor=#eaf3ff' in xml


def test_drawio_router_uses_container_absolute_coordinates():
    from bid_tool.illustration_v2.renderers.drawio import (
        DrawContainer,
        DrawNode,
        DrawPlan,
        _edge_waypoints,
    )

    plan = DrawPlan(
        "测试图",
        "",
        900,
        600,
        nodes=[
            DrawNode("a", "A", parent="c1", x=30, y=40, width=120, height=60),
            DrawNode("b", "B", parent="c2", x=30, y=40, width=120, height=60),
        ],
        containers=[
            DrawContainer("c1", "左区", 60, 120, 240, 180, 0),
            DrawContainer("c2", "右区", 560, 360, 240, 180, 1),
        ],
    )

    assert _edge_waypoints(plan, plan.nodes[0], plan.nodes[1]) == [(400, 190), (400, 430)]


def test_process_interaction_map_auto_routes_to_drawio():
    from bid_tool.illustration_v2 import api

    job = Path("tests/fixtures/illustration_cases/process_interaction_map/job.json")
    decision = api.plan(job)[0]

    assert decision["renderer"] == "drawio"
    assert decision["decision"]["tier"] == 2
    assert decision["decision"]["fallback"] == "auto_structured_drawio"
    assert decision["decision"]["needs_human_review"] is True


def test_process_interaction_map_drawio_outputs_sections_and_legend(tmp_path, monkeypatch):
    from bid_tool.illustration_v2 import api
    from bid_tool.illustration_v2.renderers import drawio

    monkeypatch.setattr(drawio, "_find_drawio_command", lambda: None)

    job = Path("tests/fixtures/illustration_cases/process_interaction_map/job.json")
    records = api.render(job, tmp_path, png=True)
    drawio_file = tmp_path / records[0].outputs["drawio"]
    xml = drawio_file.read_text(encoding="utf-8")

    assert records[0].renderer == "drawio"
    assert records[0].tier == 2
    assert records[0].needs_human_review is True
    assert records[0].warnings == ["未检测到 Draw.io CLI；已生成可编辑 .drawio 源文件，跳过 SVG/PNG 导出"]
    assert "A 上线准备" in xml
    assert "图例与术语" in xml
    assert "dashed=1" in xml
    assert "strokeWidth=3" in xml


def test_process_interaction_map_uses_bottom_legend_and_secondary_lanes():
    from bid_tool.illustration_v2 import api
    from bid_tool.illustration_v2.renderers.drawio import _drawio_xml

    job = api.load_job("tests/fixtures/illustration_cases/process_interaction_map/job.json")
    xml = _drawio_xml(job, job.illustrations[0])

    legend_start = xml.index('<mxCell id="C_legend"')
    legend_end = xml.index("</mxCell>", legend_start)
    legend_cell = xml[legend_start:legend_end]

    assert 'y="440"' in legend_cell
    assert 'width="1210"' in legend_cell
    assert 'height="140"' in legend_cell
    assert "fillColor=#fffaf2" in xml
    assert "fillColor=#f5f6ff" in xml
    assert "fillColor=#f2fbf8" in xml
    assert "strokeColor=#0f766e" in xml
    assert "strokeColor=#b45309" in xml
    assert "strokeColor=#4f46e5" in xml
    assert "exitX=0.5;exitY=1" in xml
    assert "exitX=1;exitY=0.5" in xml
    assert "entryX=0;entryY=0.5" in xml
    assert '<mxPoint x="414" y="360"' in xml
    assert '<mxPoint x="1040" y="110"' in xml
    assert '<mxPoint x="530" y="110"' in xml
