#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Workspace and project directory resolution for bid-tool.

Priority chain (highest to lowest):
  1. --project-dir CLI argument (explicit project directory path)
  2. BID_PROJECT_DIR environment variable
  3. Walk up from cwd looking for a .bid-project marker file
  4. cwd/output (backward compatible; emits deprecation warning)

Usage:
  from bid_tool.workspace import resolve_project_paths, init_project, migrate_cwd_output

  paths = resolve_project_paths(project_dir="/home/user/bid-workspace/甘肃放射源")
  print(paths.output)  # /home/user/bid-workspace/甘肃放射源/output
"""

from __future__ import annotations

import json
import os
import shutil
import warnings
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

MARKER_FILE = ".bid-project"
DEFAULT_WORKSPACE = Path.home() / "bid-workspace"


@dataclass
class ProjectPaths:
    """All canonical paths for a single bid project, resolved once."""
    root: Path           # e.g., ~/bid-workspace/甘肃放射源
    output: Path         # root / 'output'
    tender: Path         # root / 'tender'
    trace: Path          # output / 'trace.json'
    state: Path          # output / 'pipeline_state.json'
    context: Path        # root / 'context.md'
    marker: Path         # root / '.bid-project'


# ---------------------------------------------------------------------------
# Resolution
# ---------------------------------------------------------------------------

def resolve_project_paths(project_dir: str | Path | None = None) -> ProjectPaths:
    """One-stop resolution returning a fully populated ProjectPaths.

    If no project directory can be resolved, falls back to cwd/output
    (backward-compatible) and prints a deprecation warning.
    """
    root = _resolve_root(project_dir)
    return ProjectPaths(
        root=root,
        output=root / "output",
        tender=root / "tender",
        trace=root / "output" / "trace.json",
        state=root / "output" / "pipeline_state.json",
        context=root / "context.md",
        marker=root / MARKER_FILE,
    )


def _resolve_root(project_dir: str | Path | None) -> Path:
    """Apply the 4-tier priority chain to find the project root."""
    # 1. Explicit CLI argument
    if project_dir:
        p = Path(project_dir).expanduser().resolve()
        if _is_project_root(p):
            return p
        # Could be a workspace root containing a single project
        sub = _auto_discover_project(p)
        if sub:
            return sub
        return p

    # 2. Environment variable
    env_dir = os.environ.get("BID_PROJECT_DIR")
    if env_dir:
        p = Path(env_dir).expanduser().resolve()
        if p.exists():
            return p

    # 3. Walk up from cwd looking for .bid-project marker
    marker_root = _find_marker_upwards(Path.cwd())
    if marker_root:
        return marker_root

    # 4. Fallback: cwd/output (backward compatible)
    warnings.warn(
        "未配置项目目录，使用 cwd/output 作为输出目录。\n"
        "建议为项目设置独立目录: bid-tool init --project '项目名' --workspace ~/bid-workspace",
        FutureWarning,
    )
    return Path.cwd()


# ---------------------------------------------------------------------------
# Project initialization
# ---------------------------------------------------------------------------

def init_project(
    workspace: str | Path | None = None,
    project_name: str = "未命名项目",
    profile_type: str = "software",
    tender_path: str | Path | None = None,
) -> ProjectPaths:
    """Create a complete bid project directory structure.

    Args:
        workspace: Parent workspace directory. Defaults to ~/bid-workspace.
        project_name: Name of the bid project (used as directory name).
        profile_type: 'software' or 'construction'.
        tender_path: Optional path to tender document to copy into tender/.

    Returns:
        Resolved ProjectPaths for the newly created project.
    """
    ws = Path(workspace).expanduser().resolve() if workspace else DEFAULT_WORKSPACE
    safe_name = _safe_dirname(project_name)
    root = ws / safe_name

    # Create directory structure
    (root / "output").mkdir(parents=True, exist_ok=True)
    (root / "tender").mkdir(parents=True, exist_ok=True)

    # Write .bid-project marker
    marker_data = {
        "version": "1",
        "project": project_name,
        "profile_type": profile_type,
        "created_at": datetime.now().isoformat(),
        "workspace": str(ws),
    }
    (root / MARKER_FILE).write_text(
        json.dumps(marker_data, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )

    # Copy tender document if provided
    if tender_path:
        src = Path(tender_path).expanduser().resolve()
        if src.exists():
            dst = root / "tender" / src.name
            shutil.copy2(src, dst)

    # Initialize output/ with empty trace and state
    _init_trace(root, project_name)
    _init_state(root, project_name)

    # Initialize context.md
    _init_context(root, project_name, profile_type)

    return ProjectPaths(
        root=root,
        output=root / "output",
        tender=root / "tender",
        trace=root / "output" / "trace.json",
        state=root / "output" / "pipeline_state.json",
        context=root / "context.md",
        marker=root / MARKER_FILE,
    )


# ---------------------------------------------------------------------------
# Migration
# ---------------------------------------------------------------------------

def migrate_cwd_output(
    source_dir: str | Path,
    workspace: str | Path | None = None,
    project_name: str = "迁移项目",
) -> ProjectPaths:
    """Move an existing cwd/output directory into the workspace structure.

    Args:
        source_dir: Path to directory containing 'output/' (usually cwd).
        workspace: Target workspace root.
        project_name: Name for the migrated project.

    Returns:
        Resolved ProjectPaths for the migrated project.
    """
    src = Path(source_dir).expanduser().resolve()
    src_output = src / "output"
    if not src_output.exists():
        raise FileNotFoundError(f"未找到 output 目录: {src_output}")

    paths = init_project(workspace, project_name, "software")

    # Move output contents
    for item in src_output.iterdir():
        dst = paths.output / item.name
        if item.is_dir():
            if not dst.exists():
                shutil.copytree(str(item), str(dst))
        else:
            shutil.copy2(str(item), str(dst))

    # Copy tender docs if any
    for pattern in ["*.md", "*.txt", "*.docx"]:
        for f in src.glob(pattern):
            if f.name not in ("README.md",):
                shutil.copy2(str(f), str(paths.tender / f.name))

    print(f"已迁移 {project_name}: {paths.root}")
    return paths


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------

def _is_project_root(path: Path) -> bool:
    return (path / MARKER_FILE).exists()


def _find_marker_upwards(start: Path) -> Path | None:
    """Walk up from start looking for .bid-project marker."""
    current = start.resolve()
    for _ in range(10):  # max 10 levels up
        if (current / MARKER_FILE).exists():
            return current
        parent = current.parent
        if parent == current:
            break
        current = parent
    return None


def _auto_discover_project(workspace: Path) -> Path | None:
    """If workspace contains exactly one project subdir, return it."""
    if not workspace.exists() or not workspace.is_dir():
        return None
    projects = [
        p for p in workspace.iterdir()
        if p.is_dir() and _is_project_root(p)
    ]
    return projects[0] if len(projects) == 1 else None


def _safe_dirname(name: str) -> str:
    """Sanitize a project name into a safe directory name."""
    # Keep Chinese characters and alphanumeric, replace problematic chars
    safe = name.strip().replace("/", "-").replace("\\", "-").replace(":", "-")
    return safe or "未命名项目"


def _init_trace(root: Path, project_name: str) -> None:
    """Write an empty trace.json."""
    from .pipeline.trace import TEMPLATE
    trace = dict(TEMPLATE)
    trace["project"] = project_name
    trace["created_at"] = datetime.now().isoformat()
    tgt = root / "output" / "trace.json"
    tgt.parent.mkdir(parents=True, exist_ok=True)
    tgt.write_text(json.dumps(trace, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _init_state(root: Path, project_name: str) -> None:
    """Write an empty pipeline_state.json."""
    state = {
        "project": project_name,
        "current_stage": None,
        "stages": {},
        "created_at": datetime.now().isoformat(),
        "updated_at": datetime.now().isoformat(),
    }
    tgt = root / "output" / "pipeline_state.json"
    tgt.parent.mkdir(parents=True, exist_ok=True)
    tgt.write_text(json.dumps(state, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def _init_context(root: Path, project_name: str, profile_type: str) -> None:
    """Write the initial context.md."""
    from .context_writer import _ensure_sections, _append_section
    tgt = root / "context.md"
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = (
        f"# 项目上下文记录\n\n"
        f"**项目**: {project_name}\n"
        f"**类型**: {profile_type}\n"
        f"**创建时间**: {now}\n"
        f"**最后更新**: {now}\n\n"
    )
    tgt.write_text(header, encoding="utf-8")
    _ensure_sections(tgt)
    _append_section(tgt, "运行记录", f"- [{now}] 项目初始化完成 (类型: {profile_type})")
    _append_section(tgt, "状态快照", f"- 所有阶段: 待开始")
