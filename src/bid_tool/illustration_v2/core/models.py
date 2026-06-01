"""Domain models for the isolated illustration v2 engine."""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class IllustrationItem:
    id: str
    type: str
    renderer: str
    insertion: dict[str, Any]
    intent: str = ""
    data: dict[str, Any] = field(default_factory=dict)
    visual: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_raw(cls, raw: dict[str, Any]) -> "IllustrationItem":
        return cls(
            id=str(raw["id"]),
            type=str(raw["type"]),
            renderer=str(raw.get("renderer", "auto")),
            insertion=dict(raw.get("insertion", {})),
            intent=str(raw.get("intent", "")),
            data=dict(raw.get("data", {})),
            visual=dict(raw.get("visual", {})),
        )


@dataclass(slots=True)
class IllustrationJob:
    version: str
    document: dict[str, Any]
    style: dict[str, Any]
    illustrations: list[IllustrationItem]
    raw: dict[str, Any]
    source: Path | None = None

    @classmethod
    def from_raw(cls, raw: dict[str, Any], source: Path | None = None) -> "IllustrationJob":
        version = str(raw.get("version", "2.0"))
        return cls(
            version=version,
            document=dict(raw.get("document", {})),
            style=dict(raw.get("style", {})),
            illustrations=[IllustrationItem.from_raw(item) for item in raw.get("illustrations", [])],
            raw=raw,
            source=source,
        )


@dataclass(frozen=True, slots=True)
class TextLimit:
    field: str
    max_chars: int


@dataclass(frozen=True, slots=True)
class TemplateContract:
    schema_kind: str
    paradigm: str
    min_layers: int
    max_layers: int
    min_items_per_layer: int
    max_items_per_layer: int
    text_limits: tuple[TextLimit, ...]
    icon_whitelist: tuple[str, ...]
    required_data_fields: tuple[str, ...] = ("layers",)


@dataclass(frozen=True, slots=True)
class Template:
    id: str
    diagram_type: str
    variant_of: str
    renderer: str
    svg_template: str
    summary: str
    contract: TemplateContract
    theme_vars: dict[str, str]

    def to_summary(self) -> dict[str, Any]:
        return {
            "id": self.id,
            "diagram_type": self.diagram_type,
            "variant_of": self.variant_of,
            "renderer": self.renderer,
            "svg_template": self.svg_template,
            "summary": self.summary,
            "paradigm": self.contract.paradigm,
            "capacity": {
                "layers": [self.contract.min_layers, self.contract.max_layers],
                "items_per_layer": [
                    self.contract.min_items_per_layer,
                    self.contract.max_items_per_layer,
                ],
            },
        }


@dataclass(frozen=True, slots=True)
class RendererCapability:
    id: str
    tier: int
    strengths: tuple[str, ...]
    weaknesses: tuple[str, ...]


@dataclass(slots=True)
class CapabilityCatalog:
    templates: list[Template]
    renderers: list[RendererCapability]

    def to_dict(self) -> dict[str, Any]:
        return {
            "templates": [template.to_summary() for template in self.templates],
            "renderers": [asdict(renderer) for renderer in self.renderers],
        }


@dataclass(slots=True)
class PlanDecision:
    item: IllustrationItem
    tier: int
    renderer: str
    template_id: str | None
    theme: str
    fit_score: float
    reasons: list[str] = field(default_factory=list)
    degraded_from: str | None = None
    fallback: str | None = None
    needs_human_review: bool = False

    def to_dict(self) -> dict[str, Any]:
        decision: dict[str, Any] = {
            "tier": self.tier,
            "template": self.template_id,
            "renderer": self.renderer,
            "theme": self.theme,
            "fit_score": round(self.fit_score, 4),
            "reasons": list(self.reasons),
        }
        if self.degraded_from:
            decision["degraded_from"] = self.degraded_from
        if self.fallback:
            decision["fallback"] = self.fallback
        decision["needs_human_review"] = self.needs_human_review
        return {
            "id": self.item.id,
            "type": self.item.type,
            "renderer": self.renderer,
            "decision": decision,
        }


@dataclass(slots=True)
class AssetRecord:
    id: str
    type: str
    renderer: str
    section: str
    caption: str
    outputs: dict[str, str]
    template: str | None
    theme: str
    fit_score: float
    tier: int
    degraded_from: str | None = None
    needs_human_review: bool = False
    warnings: list[str] = field(default_factory=list)
    decision: dict[str, Any] = field(default_factory=dict)
