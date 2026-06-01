"""Semantic validation for illustration platform jobs."""
from __future__ import annotations

import json
from pathlib import Path

from .job import IllustrationJob
from .registry import get_diagram_type, normalize_type

SCHEMA_DIR = Path(__file__).resolve().parents[2] / "schemas"


def validate_platform_job(job: IllustrationJob) -> list[str]:
    """Return non-schema semantic validation errors."""

    errors: list[str] = validate_platform_schema(job)
    ids: set[str] = set()
    for index, item in enumerate(job.illustrations):
        prefix = f"illustrations[{index}]"
        if item.id in ids:
            errors.append(f"{prefix}.id: 图件 id 必须唯一: {item.id}")
        ids.add(item.id)

        diagram = get_diagram_type(item.type)
        if diagram is None:
            errors.append(f"{prefix}.type: 未注册图型 `{item.type}`")
            continue
        if not item.intent and not item.insertion.get("purpose"):
            errors.append(f"{prefix}.intent: 建议说明图件表达目的，便于自动选择版式")
        if not item.insertion.get("caption"):
            errors.append(f"{prefix}.insertion.caption: 缺少图题")

        canonical = normalize_type(item.type)
        if canonical.startswith("chart."):
            source = item.data.get("source")
            if not source:
                errors.append(f"{prefix}.data.source: 数据图必须提供数据来源")
    return errors


def validate_platform_schema(job: IllustrationJob) -> list[str]:
    """Validate raw v2 job structure against the public JSON Schema."""

    schema_path = SCHEMA_DIR / "illustration_job_v2.schema.json"
    if not schema_path.exists():
        return []
    try:
        import jsonschema
    except ImportError:
        return []
    schema = json.loads(schema_path.read_text(encoding="utf-8"))
    validator = jsonschema.Draft202012Validator(schema)
    errors: list[str] = []
    for issue in sorted(validator.iter_errors(job.raw), key=lambda error: list(error.path)):
        location = ".".join(str(item) for item in issue.path) or "<root>"
        errors.append(f"schema.{location}: {issue.message}")
    return errors


def quality_warnings(job: IllustrationJob) -> list[str]:
    """Return warnings that should guide AI repair but not block rendering."""

    warnings: list[str] = []
    for index, item in enumerate(job.illustrations):
        caption = item.insertion.get("caption", "")
        if len(caption) > 45:
            warnings.append(f"illustrations[{index}].caption: 图题较长，建议控制在 45 字以内")
        if item.type.startswith("chart.") and item.data.get("dataNotice") and not item.visual.get("watermark"):
            warnings.append(f"illustrations[{index}].visual.watermark: 模拟数据建议设置水印或注释")
        node_like_count = 0
        for key in ("nodes", "items", "phases", "risks", "columns"):
            value = item.data.get(key)
            if isinstance(value, list):
                node_like_count += len(value)
        if node_like_count > 20:
            warnings.append(f"illustrations[{index}]: 元素数量为 {node_like_count}，建议拆成总览图和子图")
    return warnings
