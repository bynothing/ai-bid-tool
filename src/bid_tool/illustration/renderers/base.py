"""Renderer adapter protocol."""
from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path
from typing import Protocol

from ..core.job import IllustrationJob, IllustrationItem


@dataclass(slots=True)
class RenderContext:
    output: Path
    theme: str
    png: bool = False
    png_scale: int = 2


@dataclass(slots=True)
class RenderResult:
    item_id: str
    renderer: str
    outputs: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


class RendererAdapter(Protocol):
    name: str

    def render(self, job: IllustrationJob, items: list[IllustrationItem], context: RenderContext) -> list[RenderResult]:
        """Render selected items and return output records."""
