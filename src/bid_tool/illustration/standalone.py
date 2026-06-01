"""Build a standalone distribution for the illustration platform.

The bundle intentionally contains only the illustration runtime, schemas,
examples, and documentation. It can be unzipped and run with:

    python run_illustration.py --job examples/<job>.json --output output/demo
"""
from __future__ import annotations

import argparse
import shutil
import zipfile
from pathlib import Path
from typing import Iterable


ILLUSTRATION_SCHEMA_FILES = {
    "__init__.py",
    "illustration_job_v2.schema.json",
    "svg_diagram.schema.json",
    "echarts_diagram.schema.json",
    "AI_ILLUSTRATION_API_V2.md",
}

DOC_FILES = {
    "ILLUSTRATION_EXTERNAL_INTERFACE.md",
    "ILLUSTRATION_CLI_USAGE.md",
    "ILLUSTRATION_PLATFORM_DESIGN.md",
    "ILLUSTRATION_SOFTWARE_ARCHITECTURE.md",
}

LAUNCHER = '''#!/usr/bin/env python3
"""Standalone launcher for the bid illustration platform."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bid_tool.illustration.toolkit import main

if __name__ == "__main__":
    main()
'''

README = """# Bid Illustration Standalone

This directory is a standalone runtime for the bid illustration platform V2.
It does not include the full bid-tool pipeline.

## Quick Start

```powershell
python run_illustration.py --job examples\\示例_统一文档配图任务.json --validate-only
python run_illustration.py --job examples\\示例_统一文档配图任务.json --output output\\illustrations --png
```

## Dependencies

Minimum:

```powershell
pip install jsonschema pyyaml
```

Optional PNG and ECharts export:

```powershell
pip install cairosvg playwright
playwright install chromium
```

## Public Contract

External jobs must use `version: "2.0"` and the schema:

`src/bid_tool/schemas/illustration_job_v2.schema.json`

Use `renderer: "auto"` unless a specific renderer is required. The platform
will choose from `html_css`, `svg_native`, `echarts_html`, `mermaid`, and
`graphviz`.
"""

REQUIREMENTS = """jsonschema>=4.17.0
pyyaml>=6.0
"""

PYPROJECT = """[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.build_meta"

[project]
name = "bid-illustration-standalone"
version = "2.0.0"
description = "Standalone bid illustration platform runtime"
requires-python = ">=3.10"
dependencies = [
    "jsonschema>=4.17.0",
    "pyyaml>=6.0",
]

[project.optional-dependencies]
png = ["cairosvg>=2.5.0"]
echarts_export = ["playwright>=1.30.0"]
full = ["bid-illustration-standalone[png,echarts_export]"]

[project.scripts]
bid-illustrate = "bid_tool.illustration.toolkit:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.setuptools.package-data]
"bid_tool.schemas" = ["*.json", "*.md"]
"bid_tool.illustration" = ["*.md", "echarts_workbench/**/*"]
"""


def build_bundle(
    output: Path,
    *,
    include_examples: bool = True,
    make_zip: bool = False,
) -> Path:
    """Create a standalone illustration bundle directory."""

    source_file = Path(__file__).resolve()
    source_src = source_file.parents[2]
    source_bid_tool = source_file.parents[1]
    source_repo = source_file.parents[3]

    output = output.resolve()
    output.mkdir(parents=True, exist_ok=True)

    package_root = output / "src" / "bid_tool"
    package_root.mkdir(parents=True, exist_ok=True)
    (package_root / "__init__.py").write_text(
        '"""Standalone bid illustration runtime."""\n__version__ = "2.0.0"\n',
        encoding="utf-8",
    )

    _copy_tree(source_bid_tool / "illustration", package_root / "illustration")
    _copy_schema_files(source_bid_tool / "schemas", package_root / "schemas")
    _write_docs(output, package_root)

    if include_examples and (source_repo / "examples").exists():
        _copy_tree(source_repo / "examples", output / "examples")

    (output / "run_illustration.py").write_text(LAUNCHER, encoding="utf-8")
    (output / "README.md").write_text(README, encoding="utf-8")
    (output / "requirements.txt").write_text(REQUIREMENTS, encoding="utf-8")
    (output / "pyproject.toml").write_text(PYPROJECT, encoding="utf-8")

    if make_zip:
        zip_path = output.with_suffix(".zip")
        _zip_dir(output, zip_path)
    return output


def _copy_tree(source: Path, target: Path) -> None:
    shutil.copytree(source, target, dirs_exist_ok=True, ignore=_ignore_runtime_files)


def _ignore_runtime_files(_: str, names: list[str]) -> set[str]:
    ignored = {"__pycache__", ".pytest_cache"}
    ignored.update(name for name in names if name.endswith((".pyc", ".pyo")))
    return ignored


def _copy_schema_files(source: Path, target: Path) -> None:
    target.mkdir(parents=True, exist_ok=True)
    for name in ILLUSTRATION_SCHEMA_FILES:
        src = source / name
        if src.exists():
            shutil.copy2(src, target / name)


def _write_docs(output: Path, package_root: Path) -> None:
    docs = output / "docs"
    docs.mkdir(parents=True, exist_ok=True)
    illustration_dir = package_root / "illustration"
    schema_dir = package_root / "schemas"
    for name in DOC_FILES:
        src = illustration_dir / name
        if src.exists():
            shutil.copy2(src, docs / name)
    api_doc = schema_dir / "AI_ILLUSTRATION_API_V2.md"
    if api_doc.exists():
        shutil.copy2(api_doc, docs / "AI_ILLUSTRATION_API_V2.md")


def _zip_dir(source: Path, zip_path: Path) -> None:
    if zip_path.exists():
        zip_path.unlink()
    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        for file in _iter_files(source):
            archive.write(file, file.relative_to(source.parent))


def _iter_files(root: Path) -> Iterable[Path]:
    for file in root.rglob("*"):
        if file.is_file():
            yield file


def main() -> None:
    parser = argparse.ArgumentParser(description="Build standalone bid illustration runtime")
    parser.add_argument(
        "--output",
        type=Path,
        default=Path.cwd() / "dist" / "bid-illustration-standalone",
        help="Standalone bundle output directory",
    )
    parser.add_argument("--no-examples", action="store_true", help="Do not copy examples")
    parser.add_argument("--zip", action="store_true", help="Also create a .zip archive beside the output directory")
    args = parser.parse_args()

    output = build_bundle(args.output, include_examples=not args.no_examples, make_zip=args.zip)
    print(f"Standalone illustration bundle created: {output}")
    print(f"Launcher: {output / 'run_illustration.py'}")
    if args.zip:
        print(f"Zip: {output.with_suffix('.zip')}")


if __name__ == "__main__":
    main()
