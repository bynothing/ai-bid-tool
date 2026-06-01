"""Template-first decision layer with tiered fallback."""
from __future__ import annotations

from .models import CapabilityCatalog, IllustrationItem, IllustrationJob, PlanDecision, Template
from .validator import validate_item_for_template


def plan_job(job: IllustrationJob, catalog: CapabilityCatalog) -> list[PlanDecision]:
    theme = str(job.style.get("theme", "formal_blue"))
    return [_plan_item(item, catalog, theme) for item in job.illustrations]


def _plan_item(item: IllustrationItem, catalog: CapabilityCatalog, theme: str) -> PlanDecision:
    candidates = [template for template in catalog.templates if template.diagram_type == item.type]
    best_template, best_score, best_issues = _best_template(item, candidates)

    if best_template and best_score >= 0.82 and not best_issues:
        return PlanDecision(
            item=item,
            tier=1,
            renderer=best_template.renderer,
            template_id=best_template.id,
            theme=theme,
            fit_score=best_score,
            reasons=[
                "Tier 1 selected: item fits a frozen SVG template contract.",
                f"Template {best_template.id} contract violations: 0.",
            ],
        )

    if candidates:
        return PlanDecision(
            item=item,
            tier=2,
            renderer="structured_svg_fallback",
            template_id=None,
            theme=theme,
            fit_score=max(best_score, 0.0),
            degraded_from=candidates[0].id,
            fallback="template_contract_failed",
            reasons=[
                "Tier 2 selected: diagram type has templates, but content does not fit any contract.",
                *best_issues[:5],
            ],
        )

    return PlanDecision(
        item=item,
        tier=3,
        renderer="free_svg_floor",
        template_id=None,
        theme=theme,
        fit_score=0.0,
        fallback="no_registered_template",
        needs_human_review=True,
        reasons=[
            "Tier 3 selected: no frozen template is registered for this diagram type.",
            "Output is a review-marked floor artifact, not a polished bid figure.",
        ],
    )


def _best_template(
    item: IllustrationItem,
    candidates: list[Template],
) -> tuple[Template | None, float, list[str]]:
    if not candidates:
        return None, 0.0, []
    scored = []
    for template in candidates:
        issues = validate_item_for_template(item, template)
        score = _fit_score(item, template, issues)
        scored.append((template, score, issues))
    return max(scored, key=lambda row: row[1])


def _fit_score(item: IllustrationItem, template: Template, issues: list[str]) -> float:
    score = 1.0
    contract = template.contract
    layers = item.data.get("layers", [])
    if isinstance(layers, list):
        layer_span = max(1, contract.max_layers - contract.min_layers + 1)
        if contract.min_layers <= len(layers) <= contract.max_layers:
            score -= abs(contract.max_layers - len(layers)) * 0.03 / layer_span
        for layer in layers:
            items = layer.get("items", []) if isinstance(layer, dict) else []
            if isinstance(items, list) and items:
                target = min(contract.max_items_per_layer, 3)
                score -= abs(target - len(items)) * 0.015
    score -= min(0.75, len(issues) * 0.12)
    if item.visual.get("rendererPreference") == "template_svg":
        score += 0.04
    return max(0.0, min(1.0, score))
