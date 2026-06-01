"""Job model helpers for illustration platform v2.

The model intentionally stays lightweight: schemas remain the formal contract,
while these classes make routing and validation code easier to read.
"""
from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any


@dataclass(slots=True)
class IllustrationItem:
    """One requested figure in an illustration job."""

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
            id=raw["id"],
            type=raw["type"],
            renderer=raw.get("renderer", "auto"),
            insertion=raw.get("insertion", {}),
            intent=raw.get("intent", ""),
            data=raw.get("data", {}),
            visual=raw.get("visual", {}),
        )


@dataclass(slots=True)
class IllustrationJob:
    """Normalized v2 job object."""

    version: str
    document: dict[str, Any]
    style: dict[str, Any]
    illustrations: list[IllustrationItem]
    raw: dict[str, Any]
    source: Path | None = None

    @classmethod
    def from_raw(cls, raw: dict[str, Any], source: Path | None = None) -> "IllustrationJob":
        version = str(raw.get("version", "2.0"))
        if version != "2.0":
            raise ValueError(
                "Illustration platform now accepts only version '2.0'. "
                "Please migrate the job to illustration_job_v2.schema.json."
            )
        return cls(
            version=version,
            document=raw.get("document", {}),
            style=raw.get("style", {}),
            illustrations=[IllustrationItem.from_raw(item) for item in raw.get("illustrations", [])],
            raw=raw,
            source=source,
        )


def load_job(path: Path) -> IllustrationJob:
    """Load and normalize an illustration job from JSON."""

    raw = json.loads(path.read_text(encoding="utf-8"))
    return IllustrationJob.from_raw(raw, source=path)
