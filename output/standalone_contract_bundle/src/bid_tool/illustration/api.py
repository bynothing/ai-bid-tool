"""Public API facade for the illustration platform.

External callers should use this module instead of importing renderer internals.
It keeps CLI, pipeline stages, future HTTP/MCP services, and tests on one stable
contract.
"""
from __future__ import annotations

from dataclasses import asdict
from pathlib import Path
from typing import Any

from .core.job import IllustrationJob, load_job
from .core.manifest import AssetRecord
from .core.registry import get_registry
from .core.router import route_item
from .core.validator import quality_warnings, validate_platform_job
from .platform import render_job, render_job_file


def load(path: str | Path) -> IllustrationJob:
    """Load an illustration job file."""

    return load_job(Path(path))


def validate(path_or_job: str | Path | IllustrationJob) -> tuple[list[str], list[str]]:
    """Validate a v2 job and return (errors, warnings)."""

    job = _ensure_job(path_or_job)
    return validate_platform_job(job), quality_warnings(job)


def plan(path_or_job: str | Path | IllustrationJob) -> list[dict[str, Any]]:
    """Return routing decisions without rendering files."""

    job = _ensure_job(path_or_job)
    decisions: list[dict[str, Any]] = []
    for item in job.illustrations:
        route = route_item(item)
        decisions.append({
            "id": item.id,
            "type": route.type,
            "renderer": route.renderer,
            "decision": list(route.reasons),
        })
    return decisions


def render(
    path_or_job: str | Path | IllustrationJob,
    output: str | Path,
    *,
    png: bool = False,
    png_scale: int = 2,
    export_echarts: bool = True,
) -> list[AssetRecord]:
    """Render a job through the platform and return manifest records."""

    output_path = Path(output)
    if isinstance(path_or_job, IllustrationJob):
        return render_job(path_or_job, output_path, png=png, png_scale=png_scale, export_echarts=export_echarts)
    return render_job_file(Path(path_or_job), output_path, png=png, png_scale=png_scale, export_echarts=export_echarts)


def list_diagram_types() -> list[dict[str, Any]]:
    """Return registered diagram types for UI/API discovery."""

    return [asdict(diagram) for diagram in get_registry().values()]


def _ensure_job(value: str | Path | IllustrationJob) -> IllustrationJob:
    if isinstance(value, IllustrationJob):
        return value
    return load_job(Path(value))
