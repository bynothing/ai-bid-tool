#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Auto-maintained project context log (context.md).

Design principles:
  - Append-only: each record_*() call appends a line to the appropriate section.
  - Idempotent: re-running the same stage doesn't create duplicate entries.
  - Machine-parseable sections, human-readable output.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any

# Section markers in context.md
SECTION_HEADERS = [
    "运行记录",
    "关键参数",
    "裁决与修改",
    "遇到的问题",
    "状态快照",
]

# Unique dedup keys: (section, normalized_prefix)
_DEDUP: set[tuple[str, str]] = set()


def record_stage_start(context_path: str | Path, stage_id: str, stage_name: str = "") -> None:
    """Record that a stage has started."""
    _ensure_file(context_path)
    now = _ts()
    label = f"{stage_id} {stage_name}".strip()
    key = (f"[{now}] 阶段 {label} 开始执行",)
    entry = f"- [{now}] 阶段 {label} 开始执行"
    _append_section(context_path, "运行记录", entry, dedup_key=str(key))


def record_stage_complete(
    context_path: str | Path,
    stage_id: str,
    gate_result: str = "",
    extra: str = "",
) -> None:
    """Record that a stage has completed, with gate result."""
    _ensure_file(context_path)
    now = _ts()
    gate_str = f", 门禁: {gate_result}" if gate_result else ""
    extra_str = f", {extra}" if extra else ""
    entry = f"- [{now}] 阶段 {stage_id} 完成{gate_str}{extra_str}"
    _append_section(context_path, "运行记录", entry, dedup_key=f"complete:{stage_id}")


def record_decision(
    context_path: str | Path,
    decision_type: str,
    value: str,
    reason: str = "",
) -> None:
    """Record a user decision or parameter choice."""
    _ensure_file(context_path)
    now = _ts()
    reason_str = f" — {reason}" if reason else ""
    entry = f"- [{now}] {decision_type}: {value}{reason_str}"
    _append_section(context_path, "裁决与修改", entry)


def record_issue(
    context_path: str | Path,
    stage_id: str,
    description: str,
    resolution: str = "",
) -> None:
    """Record an issue encountered and (optionally) its resolution."""
    _ensure_file(context_path)
    now = _ts()
    entry = f"- [{now}] [{stage_id}] {description}"
    if resolution:
        entry += f" → 解决: {resolution}"
    _append_section(context_path, "遇到的问题", entry)


def record_param(
    context_path: str | Path,
    param_name: str,
    value: Any,
    context: str = "",
) -> None:
    """Record a key parameter value."""
    _ensure_file(context_path)
    ctx = f" ({context})" if context else ""
    entry = f"- **{param_name}**: {value}{ctx}"
    _append_section(context_path, "关键参数", entry, dedup_key=f"param:{param_name}")


def update_status_snapshot(
    context_path: str | Path,
    stages_status: dict[str, str],
) -> None:
    """Replace the status snapshot section with current stage statuses."""
    _ensure_file(context_path)
    path = Path(context_path)
    lines = path.read_text(encoding="utf-8").split("\n")

    # Find and remove existing status snapshot section
    new_lines = []
    in_snapshot = False
    for line in lines:
        if line.strip().startswith("## 状态快照"):
            in_snapshot = True
            new_lines.append(line)
            new_lines.append(f"_(最后更新 {_ts()})_")
            new_lines.append("")
            for s_id, s_status in sorted(stages_status.items()):
                icon = _status_icon(s_status)
                new_lines.append(f"- {icon} {s_id}: {s_status}")
            new_lines.append("")
            continue
        if in_snapshot and line.strip().startswith("## "):
            in_snapshot = False
            new_lines.append(line)
            continue
        if in_snapshot:
            continue  # skip old snapshot lines
        new_lines.append(line)

    path.write_text("\n".join(new_lines), encoding="utf-8")

    # Also update the header timestamp
    content = path.read_text(encoding="utf-8")
    content = re.sub(
        r"\*\*最后更新\*\*: .*",
        f"**最后更新**: {_ts()}",
        content,
    )
    path.write_text(content, encoding="utf-8")


def read_context(context_path: str | Path) -> dict[str, list[str]]:
    """Parse existing context.md into a dict of section -> list of entry lines."""
    path = Path(context_path)
    if not path.exists():
        return {}
    result: dict[str, list[str]] = {}
    current_section = ""
    for line in path.read_text(encoding="utf-8").split("\n"):
        if line.startswith("## ") and line[3:].strip() in SECTION_HEADERS:
            current_section = line[3:].strip()
            result[current_section] = []
        elif current_section and line.strip():
            result[current_section].append(line)
    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _ts() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def _status_icon(status: str) -> str:
    icons = {
        "pending": "[ ]",
        "in_progress": "[>]",
        "completed": "[X]",
        "failed": "[!]",
    }
    return icons.get(status, "[?]")


def _ensure_file(context_path: str | Path) -> None:
    path = Path(context_path)
    if not path.exists():
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            f"# 项目上下文记录\n\n"
            f"**创建时间**: {_ts()}\n"
            f"**最后更新**: {_ts()}\n\n",
            encoding="utf-8",
        )
    _ensure_sections(path)


def _ensure_sections(path: Path) -> None:
    """Ensure all required section headers exist."""
    content = path.read_text(encoding="utf-8")
    for header in SECTION_HEADERS:
        if f"## {header}" not in content:
            content += f"\n## {header}\n\n"
    path.write_text(content, encoding="utf-8")


def _append_section(
    context_path: str | Path,
    section: str,
    entry: str,
    dedup_key: str = "",
) -> None:
    """Append an entry line to a named section. Skips if dedup_key already used."""
    global _DEDUP
    if dedup_key:
        full_key = (section, dedup_key)
        if full_key in _DEDUP:
            return
        _DEDUP.add(full_key)

    path = Path(context_path)
    lines = path.read_text(encoding="utf-8").split("\n")
    new_lines = []
    inserted = False
    for i, line in enumerate(lines):
        new_lines.append(line)
        if line.strip() == f"## {section}":
            # Insert after the section header (skip any existing content until next section or EOF)
            j = i + 1
            while j < len(lines):
                if lines[j].strip().startswith("## "):
                    break
                j += 1
            # Insert right after the section header (before any existing entries)
            insert_at = len(new_lines)
            new_lines.insert(insert_at, entry)
            inserted = True

    if not inserted:
        # Section not found, add it
        new_lines.append(f"## {section}")
        new_lines.append("")
        new_lines.append(entry)

    path.write_text("\n".join(new_lines), encoding="utf-8")
