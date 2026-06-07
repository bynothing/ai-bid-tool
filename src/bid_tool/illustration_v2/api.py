"""Public API for the isolated illustration v2 engine."""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from .core.catalog import build_capability_catalog
from .core.decision import plan_job
from .core.manifest import write_manifest
from .core.models import AssetRecord, IllustrationJob
from .core.validator import validate_job
from .renderers.drawio import render_decision as render_drawio_decision
from .renderers.template_svg import render_decision as render_template_decision


def load_job(path: str | Path) -> IllustrationJob:
    """Load an illustration job from JSON."""

    source = Path(path)
    raw = json.loads(source.read_text(encoding="utf-8"))
    return IllustrationJob.from_raw(raw, source=source)


load = load_job


def validate(path_or_job: str | Path | IllustrationJob) -> tuple[list[str], list[str]]:
    """Validate a job and return ``(errors, warnings)``."""

    job = _ensure_job(path_or_job)
    return validate_job(job)


def plan(path_or_job: str | Path | IllustrationJob) -> list[dict[str, Any]]:
    """Return deterministic routing decisions without writing files."""

    job = _ensure_job(path_or_job)
    decisions = plan_job(job, build_capability_catalog())
    return [decision.to_dict() for decision in decisions]


def render(
    path_or_job: str | Path | IllustrationJob,
    output: str | Path,
    *,
    theme: str = "formal_blue",
    png: bool = False,
    png_scale: int = 2,
    export_echarts: bool = True,
) -> list[AssetRecord]:
    """Render a job through the isolated v2 engine."""

    job = _ensure_job(path_or_job)
    errors, warnings = validate_job(job)
    if errors:
        raise ValueError("illustration_v2 job validation failed:\n" + "\n".join(f"- {e}" for e in errors))

    output_dir = Path(output).resolve()
    decisions = plan_job(job, build_capability_catalog())
    records = [
        _render_decision(job, decision, output_dir, theme=theme, png=png, png_scale=png_scale)
        for decision in decisions
    ]
    if warnings and records:
        records[0].warnings.extend(warnings)
    write_manifest(output_dir, job, records)
    return records


def list_capabilities() -> dict[str, Any]:
    """Return the template and renderer capability catalog."""

    return build_capability_catalog().to_dict()


def list_drawing_tools() -> list[dict[str, Any]]:
    """Return renderer capabilities in a drawing-tool friendly shape."""

    return [
        {
            "name": renderer["id"],
            "kind": "external_cli" if renderer["id"] == "drawio" else "v2_renderer",
            "tier": renderer["tier"],
            "strengths": renderer["strengths"],
            "weaknesses": renderer["weaknesses"],
        }
        for renderer in list_capabilities()["renderers"]
    ]


def _render_decision(
    job: IllustrationJob,
    decision,
    output_dir: Path,
    *,
    theme: str,
    png: bool,
    png_scale: int,
) -> AssetRecord:
    if decision.renderer == "drawio":
        return render_drawio_decision(job, decision, output_dir, theme=theme, png=png, png_scale=png_scale)
    return render_template_decision(job, decision, output_dir, theme=theme, png=png, png_scale=png_scale)


def _ensure_job(value: str | Path | IllustrationJob) -> IllustrationJob:
    if isinstance(value, IllustrationJob):
        return value
    return load_job(value)
