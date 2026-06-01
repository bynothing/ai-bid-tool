"""[DEPRECATED] Legacy adapter — replaced by SvgRenderer + EChartsRenderer.

This module is kept for backward compatibility only.  New code should use
``svg_v2.SvgRenderer`` and ``echarts_v2.EChartsRenderer`` instead.
The platform no longer routes items through this adapter.
"""
from __future__ import annotations

from pathlib import Path

from ..core.job import IllustrationJob, IllustrationItem
from ..core.registry import get_diagram_type, normalize_type
from ..palettes import select_palette_for_item
from .base import RenderContext, RenderResult


class LegacyToolkitAdapter:
    """Render v2 items through the existing SVG/ECharts helper functions."""

    name = "legacy_toolkit"

    def render(self, job: IllustrationJob, items: list[IllustrationItem], context: RenderContext) -> list[RenderResult]:
        from .. import toolkit

        adapter_job = self._to_legacy_job(job, items)
        # Validation already done by platform v2; skip re-validation via legacy validate_job
        _, svg_package, chart_package = toolkit.validate_job(adapter_job)

        context.output.mkdir(parents=True, exist_ok=True)
        svg_file, _ = toolkit.write_input_packages(context.output, svg_package, chart_package)
        svg_results = toolkit.render_svg(svg_file, context.output, context.theme, context.png, context.png_scale)
        review_page = toolkit.create_echarts_review_page(chart_package, context.output)
        chart_exports: dict[str, dict[str, str]] = {}
        if review_page and context.export_echarts:
            try:
                chart_exports = toolkit.export_echarts_images(review_page, chart_package["charts"], context.output, context.png)
            except Exception as exc:
                print(f"  [WARN] ECharts export failed (review page still available): {exc}")

        records = toolkit.make_records(adapter_job, svg_results, chart_exports, review_page, context.output)
        return [
            RenderResult(
                item_id=record["id"],
                renderer=record["renderer"],
                outputs=record.get("outputs", {}),
            )
            for record in records
        ]

    def _to_legacy_job(self, job: IllustrationJob, items: list[IllustrationItem]) -> dict:
        legacy_items = []
        for item in items:
            spec = dict(item.data)
            spec.setdefault("id", item.id)
            spec.setdefault("palette", select_palette_for_item(job, item))
            diagram = get_diagram_type(item.type)
            if diagram and diagram.legacy_type:
                spec["type"] = diagram.legacy_type
            elif item.type.startswith("chart."):
                spec["type"] = item.type.removeprefix("chart.")
            else:
                spec["type"] = normalize_type(item.type)
            spec.setdefault("title", item.insertion.get("caption", item.id))

            # Convert v2 LLM data format → v1 SVG renderer format
            spec = _convert_v2_to_v1(spec)

            renderer = "echarts_html" if normalize_type(item.type).startswith("chart.") else "svg"
            if item.renderer in {"echarts_html", "echarts"}:
                renderer = "echarts_html"
            elif item.renderer in {"svg", "svg_native"}:
                renderer = "svg"

            legacy_items.append({
                "id": item.id,
                "renderer": renderer,
                "insertion": item.insertion,
                "spec": spec,
            })
        return {
            "document": job.document,
            "style": {
                "theme": _theme_for_legacy(job.style.get("theme", "clarity_blue")),
                "preferredFormat": job.style.get("preferredFormat", "both"),
            },
            "illustrations": legacy_items,
        }


def _convert_v2_to_v1(spec: dict) -> dict:
    """Convert v2 LLM data format to v1 SVG renderer format.

    The LLM generates v2-format data with field names like 'flows', 'platforms',
    string items, etc. The SVG renderer (v1) expects 'nodes'+'edges', 'groups',
    dict items with title/desc, etc. This function bridges the two.
    """
    spec_type = spec.get("type", "")

    # ── flowchart: flows[] → nodes[] + edges[] ──
    if spec_type == "flowchart" and "flows" in spec and "nodes" not in spec:
        spec = _convert_flowchart(spec)

    # ── layered_architecture / swimlane: string items → {title} objects ──
    if spec_type in ("layered_architecture", "interface_map"):
        if "layers" in spec:
            for layer in spec.get("layers", []):
                if "items" in layer:
                    layer["items"] = _to_item_dicts(layer["items"])

    # ── capability_map: platforms[] → groups[] + string items → objects ──
    if spec_type == "capability_map":
        if "groups" not in spec and "platforms" in spec:
            spec["groups"] = [
                {
                    "label": p.get("label", ""),
                    "icon": p.get("icon", ""),
                    "items": _to_item_dicts(p.get("items", [])),
                }
                for p in spec.pop("platforms")
            ]
        elif "groups" in spec:
            for g in spec["groups"]:
                if "items" in g:
                    g["items"] = _to_item_dicts(g["items"])

    # ── relationship_map: string items → objects ──
    if spec_type == "relationship_map":
        for container in spec.get("containers", []):
            if "nodes" in container:
                container["nodes"] = _to_item_dicts(container["nodes"])
        # Also convert top-level keywords: platforms → containers if needed
        if "containers" not in spec and "platforms" in spec:
            spec["containers"] = [
                {
                    "id": f"C{i:02d}",
                    "title": p.get("label", ""),
                    "nodes": _to_item_dicts(p.get("items", [])),
                    "row": i, "col": 0,
                }
                for i, p in enumerate(spec.pop("platforms"))
            ]
        # Generate edges if missing
        if "edges" not in spec and len(spec.get("containers", [])) > 1:
            edges = []
            for i in range(len(spec["containers"]) - 1):
                src_nodes = spec["containers"][i].get("nodes", [])
                dst_nodes = spec["containers"][i + 1].get("nodes", [])
                if src_nodes and dst_nodes:
                    edges.append({
                        "from": src_nodes[-1].get("id", f"n{i}"),
                        "to": dst_nodes[0].get("id", f"n{i+1}"),
                        "relation": "data",
                    })
            if edges:
                spec["edges"] = edges

    # ── swimlane_flowchart: string items → objects ──
    if spec_type == "swimlane_flowchart":
        for step in spec.get("steps", []):
            if isinstance(step, dict):
                if "title" not in step and "label" in step:
                    step["title"] = step["label"]

    # ── Generic: convert any remaining string items ──
    for key in ("actors", "integrations", "participants"):
        if key in spec:
            spec[key] = _to_item_dicts(spec[key])

    return spec


def _to_item_dicts(items: list) -> list:
    """Convert mixed string/dict items to [{title, desc}] dicts."""
    result = []
    for item in items:
        if isinstance(item, str):
            result.append({"title": item})
        elif isinstance(item, dict):
            entry = {"title": item.get("title", item.get("label", item.get("name", "")))}
            desc = item.get("desc") or item.get("subtitle") or item.get("description") or ""
            if not desc and "content" in item:
                content = item["content"]
                desc = "；".join(str(c) for c in content[:3]) if isinstance(content, list) else str(content)
            if not desc:
                desc = item.get("output", "")
            entry["desc"] = str(desc) if desc else ""
            for k in ("icon", "style", "kind", "id"):
                if k in item:
                    entry[k] = item[k]
            result.append(entry)
        else:
            result.append({"title": str(item)})
    return result


def _convert_flowchart(spec: dict) -> dict:
    """Convert v2 flows[] → v1 nodes[] + edges[].  """
    flows = spec.pop("flows", [])
    nodes = []
    edges = []
    for i, flow in enumerate(flows):
        nid = flow.get("id", f"n{i:02d}")
        # Build desc from content + output
        desc_parts = []
        content = flow.get("content", [])
        if isinstance(content, list) and content:
            desc_parts.extend(content[:3])
        elif isinstance(content, str) and content:
            desc_parts.append(content)
        output = flow.get("output", "")
        if output:
            desc_parts.append(f"→{output}")
        desc = "；".join(str(p) for p in desc_parts) if desc_parts else ""
        # Map v2 style → v1 kind
        style = flow.get("style", "default")
        kind_map = {"default": "process", "success": "success", "warning": "decision",
                     "danger": "failure", "accent": "external"}
        kind = flow.get("kind") or kind_map.get(style, "process")
        # Get icon
        icon = flow.get("icon", "")
        nodes.append({
            "id": nid,
            "row": i,
            "col": 0,
            "title": flow.get("title", ""),
            "desc": desc,
            "kind": kind,
            "icon": icon,
        })
        if i > 0:
            edges.append({
                "from": f"n{i-1:02d}",
                "to": nid,
                "label": flow.get("ackLabel", ""),
                "relation": "flow",
            })
    spec["nodes"] = nodes
    spec["edges"] = edges
    return spec


def _theme_for_legacy(theme: str) -> str:
    aliases = {
        "formal_blue": "clarity_blue",
        "formal_teal": "navy_teal",
        "formal_gold": "royal_gold",
    }
    return aliases.get(theme, theme)
