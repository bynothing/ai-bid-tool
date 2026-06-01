"""Unified data normalization for the illustration platform.

All renderers receive data through this layer. The LLM generates content in a
flexible "v2" format; this module normalizes it to a canonical shape that every
renderer can consume without needing its own field-name translation.
"""
from __future__ import annotations

from typing import Any


# ── Public API ────────────────────────────────────────────────────────────────


def normalize(diagram_type: str, data: dict[str, Any]) -> dict[str, Any]:
    """Normalize LLM-generated diagram data to canonical renderer format.

    Returns a new dict with standardised field names and item shapes.  Callers
    (renderers) receive the normalised copy and can rely on consistent keys.
    """
    if not data:
        return {}
    out = dict(data)

    # ── 1.  Normalize top-level container fields ──
    out = _normalize_containers(diagram_type, out)

    # ── 2.  Normalize layered architecture items ──
    for key in ("layers",):
        if key in out:
            for layer in out[key]:
                if "items" in layer:
                    layer["items"] = _to_items(layer["items"])
    for key in ("actors", "integrations", "participants"):
        if key in out:
            out[key] = _to_items(out[key])

    # ── 3.  Normalize flowchart / swimlane items ──
    for key in ("nodes", "steps", "flows"):
        if key in out:
            out[key] = _to_flow_items(out[key])

    # ── 4.  Convert flows→nodes+edges for flowchart ──
    if diagram_type in ("process.flowchart", "flowchart"):
        if "nodes" not in out and "flows" in out:
            out = _flows_to_nodes(out)

    # ── 5.  Normalize relationship / topology nodes ──
    for key in ("containers",):
        if key in out:
            for container in out[key]:
                if "nodes" in container:
                    container["nodes"] = _to_items(container["nodes"])

    # ── 6.  Normalize gantt / milestone phases ──
    for key in ("phases",):
        if key in out:
            out[key] = _to_items(out[key])

    return out


# ── Field-name normalisation ──────────────────────────────────────────────────


def _normalize_containers(diagram_type: str, data: dict) -> dict:
    """Map LLM field names to canonical renderer field names."""
    ct = diagram_type

    # capability.map: "platforms" → "groups"
    if ct in ("capability.map", "capability_map"):
        if "groups" not in data:
            if "platforms" in data:
                data["groups"] = [
                    {"label": p.get("label", ""), "icon": p.get("icon", ""),
                     "items": _to_items(p.get("items", []))}
                    for p in data.pop("platforms")
                ]
            elif "trades" in data:
                data["groups"] = [
                    {"label": t.get("label", t) if isinstance(t, dict) else t,
                     "items": _to_items(t.get("items", [])) if isinstance(t, dict) else []}
                    for t in data.pop("trades")
                ]

    # Layered architecture: "categories" → "actors"
    if ct in ("architecture.layered", "layered_architecture"):
        if "actors" not in data and "categories" in data:
            data["actors"] = _to_items(data.pop("categories"))

    # Deployment / topology: ensure "zones" alias
    if ct in ("architecture.deployment", "network.topology"):
        if "zones" not in data and "platforms" in data:
            data["zones"] = data["platforms"]

    # Relationship map
    if ct in ("relationship.domain", "relationship_map"):
        if "containers" not in data:
            if "platforms" in data:
                data["containers"] = [
                    {"id": f"C{i:02d}", "title": p.get("label", ""),
                     "nodes": _to_items(p.get("items", [])), "row": i, "col": 0}
                    for i, p in enumerate(data.pop("platforms"))
                ]
            elif "groups" in data:
                data["containers"] = [
                    {"id": g.get("id", f"C{i:02d}"), "title": g.get("label", ""),
                     "nodes": _to_items(g.get("items", [])), "row": i, "col": 0}
                    for i, g in enumerate(data.pop("groups"))
                ]
        if "edges" not in data and len(data.get("containers", [])) > 1:
            edges = []
            for i in range(len(data["containers"]) - 1):
                src = data["containers"][i].get("nodes", [])
                dst = data["containers"][i + 1].get("nodes", [])
                if src and dst:
                    edges.append({"from": src[-1].get("id", f"n{i}"),
                                  "to": dst[0].get("id", f"n{i+1}"),
                                  "relation": "data"})
            if edges:
                data["edges"] = edges

    return data


# ── Item normalisation helpers ────────────────────────────────────────────────


def _to_items(items: list) -> list[dict]:
    """Convert mixed string/dict items → canonical [{title, desc, ...}]."""
    result = []
    for item in items or []:
        if isinstance(item, str):
            result.append({"title": item, "desc": ""})
        elif isinstance(item, dict):
            entry = {
                "title": _smart_truncate(
                    item.get("title") or item.get("label") or item.get("name") or "", max_len=20
                ),
                "desc": _extract_desc(item),
            }
            for k in ("icon", "style", "kind", "id", "row", "col", "order"):
                if k in item:
                    entry[k] = item[k]
            result.append(entry)
        else:
            result.append({"title": str(item), "desc": ""})
    return result


def _to_flow_items(items: list) -> list[dict]:
    """Convert flow items, enriching desc from content[] / output."""
    result = []
    for item in items or []:
        entry = dict(item) if isinstance(item, dict) else {"title": str(item)}
        if "title" not in entry:
            entry["title"] = _smart_truncate(
                entry.get("label") or entry.get("name") or "", max_len=20
            )
        else:
            entry["title"] = _smart_truncate(str(entry["title"]), max_len=20)
        if "desc" not in entry:
            entry["desc"] = _extract_desc(entry)
        # Map v2 style → v1 kind for compatibility
        if "style" in entry and "kind" not in entry:
            kind_map = {"default": "process", "success": "success",
                        "warning": "decision", "danger": "failure",
                        "accent": "external"}
            entry["kind"] = kind_map.get(entry["style"], "process")
        # Ensure id for SVG compatibility
        if "id" not in entry:
            entry["id"] = entry.get("id") or f"n{result.__len__():02d}"
        result.append(entry)
    return result


def _extract_desc(item: dict) -> str:
    """Extract description text from any known LLM field, with smart truncation."""
    desc = ""
    for key in ("desc", "subtitle", "description", "detail"):
        v = item.get(key)
        if v and isinstance(v, str) and v.strip():
            desc = v.strip()
            break
    if not desc:
        content = item.get("content")
        if isinstance(content, list) and content:
            desc = "；".join(str(c) for c in content[:3])
        elif isinstance(content, str) and content.strip():
            desc = content.strip()
    if not desc:
        output = item.get("output")
        if output and isinstance(output, str):
            desc = f"→{output.strip()}"

    if not desc:
        return ""

    # Smart truncation: keep desc readable and fitting within card constraints.
    # Chinese chars are roughly 1:1 with px at render font sizes, so 50 chars
    # is safe for most cards (even at 16px font, 50 chars = ~800px theoretical max
    # but cards are typically 180-350px wide, so we need to be conservative).
    return _smart_truncate(desc, max_len=50)


def _smart_truncate(text: str, max_len: int) -> str:
    """Truncate text at natural break points (punctuation) near max_len."""
    if len(text) <= max_len:
        return text
    # Try to break at last Chinese/English punctuation within limit
    for sep in ("；", ";", "，", ",", "。", ".", "、", "·", " "):
        pos = text.rfind(sep, 0, max_len)
        if pos > max_len // 2:
            return text[:pos + 1]
    # Fallback: hard truncate at max_len with ellipsis
    return text[:max_len - 1] + "…"


def _flows_to_nodes(data: dict) -> dict:
    """Convert flows[] → nodes[] + edges[].  """
    flows = data.pop("flows", [])
    nodes = _to_flow_items(flows)
    for i, n in enumerate(nodes):
        n.setdefault("row", i)
        n.setdefault("col", 0)
    data["nodes"] = nodes
    if len(nodes) > 1:
        data["edges"] = _linear_edges(nodes)
    return data


def _linear_edges(nodes: list[dict]) -> list[dict]:
    return [
        {"from": nodes[i]["id"], "to": nodes[i + 1]["id"], "relation": "flow"}
        for i in range(len(nodes) - 1)
    ]
