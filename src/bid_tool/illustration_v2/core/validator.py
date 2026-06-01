"""Validation for illustration v2 jobs and template contracts."""
from __future__ import annotations

from typing import Any

from .catalog import build_capability_catalog
from .models import IllustrationItem, IllustrationJob, Template


def validate_job(job: IllustrationJob) -> tuple[list[str], list[str]]:
    errors: list[str] = []
    warnings: list[str] = []

    if job.version != "2.0":
        errors.append("version must be '2.0'")
    if not job.document.get("title"):
        errors.append("document.title is required")
    if not job.illustrations:
        errors.append("illustrations must contain at least one item")

    seen: set[str] = set()
    for index, item in enumerate(job.illustrations):
        prefix = f"illustrations[{index}]"
        if not item.id:
            errors.append(f"{prefix}.id is required")
        if item.id in seen:
            errors.append(f"{prefix}.id duplicates {item.id!r}")
        seen.add(item.id)
        if not item.type:
            errors.append(f"{prefix}.type is required")
        if not item.intent:
            warnings.append(f"{prefix}.intent is empty; template selection may be weaker")
        if not item.insertion.get("section"):
            errors.append(f"{prefix}.insertion.section is required")
        if not item.insertion.get("caption"):
            errors.append(f"{prefix}.insertion.caption is required")
        if not isinstance(item.data, dict):
            errors.append(f"{prefix}.data must be an object")

    return errors, warnings


def validate_item_for_template(item: IllustrationItem, template: Template) -> list[str]:
    contract = template.contract
    data = item.data
    issues: list[str] = []

    for field in contract.required_data_fields:
        if field not in data:
            issues.append(f"data.{field} is required by template {template.id}")

    if contract.schema_kind == "layered":
        return issues + _validate_layered(item, template)
    if contract.schema_kind == "platform_interface":
        return issues + _validate_platform_interface(item, template)
    if contract.schema_kind == "resilience_flow":
        return issues + _validate_collection_template(item, template, "steps", 4, 8) + _validate_collection_template(
            item, template, "exceptions", 3, 7
        )
    if contract.schema_kind == "inspection_cards":
        return issues + _validate_collection_template(item, template, "categories", 2, 4)
    if contract.schema_kind == "severity_closure":
        return issues + _validate_collection_template(item, template, "levels", 2, 4) + _validate_collection_template(
            item, template, "steps", 4, 8
        )
    if contract.schema_kind == "security_loop":
        return issues + _validate_collection_template(item, template, "controls", 4, 6)

    return issues


def _validate_layered(item: IllustrationItem, template: Template) -> list[str]:
    contract = template.contract
    data = item.data
    issues: list[str] = []
    layers = data.get("layers", [])
    if not isinstance(layers, list):
        return ["data.layers must be a list"]

    if not contract.min_layers <= len(layers) <= contract.max_layers:
        issues.append(
            f"data.layers count {len(layers)} outside "
            f"{contract.min_layers}-{contract.max_layers}"
        )

    for layer_index, layer in enumerate(layers):
        label = str(layer.get("label", layer.get("title", "")))
        _check_text(issues, f"layers[{layer_index}].label", label, _limit(contract, "label"))
        items = layer.get("items", [])
        if not isinstance(items, list):
            issues.append(f"layers[{layer_index}].items must be a list")
            continue
        if not contract.min_items_per_layer <= len(items) <= contract.max_items_per_layer:
            issues.append(
                f"layers[{layer_index}].items count {len(items)} outside "
                f"{contract.min_items_per_layer}-{contract.max_items_per_layer}"
            )
        for item_index, node in enumerate(items):
            title = str(node.get("title", ""))
            desc = str(node.get("desc", ""))
            icon = str(node.get("icon", "server"))
            if not title:
                issues.append(f"layers[{layer_index}].items[{item_index}].title is required")
            _check_text(
                issues,
                f"layers[{layer_index}].items[{item_index}].title",
                title,
                _limit(contract, "title"),
            )
            _check_text(
                issues,
                f"layers[{layer_index}].items[{item_index}].desc",
                desc,
                _limit(contract, "desc"),
            )
            if icon not in contract.icon_whitelist:
                issues.append(
                    f"layers[{layer_index}].items[{item_index}].icon {icon!r} "
                    f"is not in template whitelist"
                )

    _check_text(issues, "data.subtitle", str(data.get("subtitle", "")), _limit(contract, "subtitle"))
    return issues


def _validate_platform_interface(item: IllustrationItem, template: Template) -> list[str]:
    issues: list[str] = []
    data = item.data
    for side in ("left", "right"):
        platform = data.get(side, {})
        if not isinstance(platform, dict):
            issues.append(f"data.{side} must be an object")
            continue
        _check_text(issues, f"data.{side}.title", str(platform.get("title", "")), _limit(template.contract, "title"))
        layers = platform.get("layers", [])
        if not isinstance(layers, list):
            issues.append(f"data.{side}.layers must be a list")
            continue
        if not 2 <= len(layers) <= 4:
            issues.append(f"data.{side}.layers count {len(layers)} outside 2-4")
        for layer_index, layer in enumerate(layers):
            _check_text(
                issues,
                f"data.{side}.layers[{layer_index}].label",
                str(layer.get("label", "")),
                _limit(template.contract, "label"),
            )
            items = layer.get("items", [])
            if not isinstance(items, list) or not 1 <= len(items) <= 5:
                issues.append(f"data.{side}.layers[{layer_index}].items count must be 1-5")
    flows = data.get("flows", [])
    if not isinstance(flows, list) or not 2 <= len(flows) <= 5:
        issues.append(f"data.flows count {len(flows) if isinstance(flows, list) else 'invalid'} outside 2-5")
    for index, flow in enumerate(flows if isinstance(flows, list) else []):
        _check_text(issues, f"data.flows[{index}].label", str(flow.get("label", "")), _limit(template.contract, "label"))
        _check_text(issues, f"data.flows[{index}].protocol", str(flow.get("protocol", "")), _limit(template.contract, "desc"))
    return issues


def _validate_collection_template(
    item: IllustrationItem,
    template: Template,
    field: str,
    minimum: int,
    maximum: int,
) -> list[str]:
    issues: list[str] = []
    collection = item.data.get(field, [])
    if not isinstance(collection, list):
        return [f"data.{field} must be a list"]
    if not minimum <= len(collection) <= maximum:
        issues.append(f"data.{field} count {len(collection)} outside {minimum}-{maximum}")
    for index, entry in enumerate(collection):
        if not isinstance(entry, dict):
            issues.append(f"data.{field}[{index}] must be an object")
            continue
        _check_text(
            issues,
            f"data.{field}[{index}].title",
            str(entry.get("title", entry.get("label", ""))),
            _limit(template.contract, "title"),
        )
        _check_text(
            issues,
            f"data.{field}[{index}].desc",
            str(entry.get("desc", "")),
            _limit(template.contract, "desc"),
        )
        bullets = entry.get("bullets", [])
        if bullets and not isinstance(bullets, list):
            issues.append(f"data.{field}[{index}].bullets must be a list")
    return issues


def known_diagram_types() -> set[str]:
    return {template.diagram_type for template in build_capability_catalog().templates}


def _limit(contract: Any, field: str) -> int:
    for item in contract.text_limits:
        if item.field == field:
            return item.max_chars
    return 9999


def _check_text(issues: list[str], location: str, value: str, max_chars: int) -> None:
    if value and len(value) > max_chars:
        issues.append(f"{location} length {len(value)} exceeds {max_chars}")
