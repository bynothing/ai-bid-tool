"""Manifest writer for illustration v2."""
from __future__ import annotations

import json
from dataclasses import asdict
from pathlib import Path

from .models import AssetRecord, IllustrationJob


def write_manifest(output: Path, job: IllustrationJob, records: list[AssetRecord]) -> None:
    output.mkdir(parents=True, exist_ok=True)
    payload = {
        "version": "2.0",
        "engine": "illustration_v2",
        "document": job.document,
        "sourceJob": str(job.source) if job.source else "",
        "illustrations": [asdict(record) for record in records],
    }
    (output / "illustration-manifest.json").write_text(
        json.dumps(payload, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    lines = [
        "# Illustration V2 Manifest",
        "",
        f"- Document: `{job.document.get('title', '-')}`",
        f"- Figures: `{len(records)}`",
        "",
        "| Section | Caption | Type | Tier | Template | Renderer | Human review | Outputs |",
        "| --- | --- | --- | ---: | --- | --- | --- | --- |",
    ]
    for record in records:
        outputs = " / ".join(f"`{key}`: <{value}>" for key, value in record.outputs.items()) or "-"
        review = "yes" if record.needs_human_review else "no"
        lines.append(
            f"| {record.section} | {record.caption} | `{record.type}` | {record.tier} | "
            f"`{record.template or '-'}` | `{record.renderer}` | {review} | {outputs} |"
        )
    (output / "generation-summary.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

