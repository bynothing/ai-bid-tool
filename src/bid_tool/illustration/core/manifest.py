"""Manifest helpers for rendered illustration assets."""
from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass(slots=True)
class AssetRecord:
    id: str
    type: str
    renderer: str
    section: str
    caption: str
    purpose: str = ""
    outputs: dict[str, str] = field(default_factory=dict)
    warnings: list[str] = field(default_factory=list)


def write_platform_manifest(
    output: Path,
    document: dict,
    records: list[AssetRecord],
    source_job: Path | None = None,
) -> None:
    output.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": "2.0",
        "document": document,
        "sourceJob": str(source_job) if source_job else "",
        "illustrations": [asdict(record) for record in records],
    }
    (output / "illustration-manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# 标书配图生成清单",
        "",
        f"- 文档：`{document.get('title', '-')}`",
        f"- 图件数量：`{len(records)}`",
        "",
        "| 章节位置 | 图题 | 图型 | 渲染器 | 输出 |",
        "| --- | --- | --- | --- | --- |",
    ]
    for record in records:
        outputs = " / ".join(f"`{key}`: <{value}>" for key, value in record.outputs.items()) or "-"
        lines.append(f"| {record.section} | {record.caption} | `{record.type}` | `{record.renderer}` | {outputs} |")
    warnings = [warning for record in records for warning in record.warnings]
    if warnings:
        lines.extend(["", "## 质量提示", ""])
        lines.extend(f"- {warning}" for warning in warnings)
    (output / "生成清单.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
