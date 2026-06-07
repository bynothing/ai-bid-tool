"""Build a minimal standalone illustration_v2 toolkit bundle."""
from __future__ import annotations

import shutil
import zipfile
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent
BID_TOOL_ROOT = PACKAGE_ROOT.parent


def build_bundle(output: str | Path, *, include_examples: bool = True, make_zip: bool = False) -> Path:
    """Create a portable illustration_v2 source bundle."""

    output_dir = Path(output).resolve()
    if output_dir.exists():
        shutil.rmtree(output_dir)
    package_dir = output_dir / "bid_tool" / "illustration_v2"
    schema_dir = output_dir / "bid_tool" / "schemas"

    shutil.copytree(PACKAGE_ROOT, package_dir, ignore=shutil.ignore_patterns("__pycache__", "*.pyc"))
    schema_dir.mkdir(parents=True, exist_ok=True)
    for schema in BID_TOOL_ROOT.joinpath("schemas").glob("*.schema.json"):
        shutil.copy2(schema, schema_dir / schema.name)
    for doc in BID_TOOL_ROOT.joinpath("schemas").glob("AI_ILLUSTRATION_API*.md"):
        shutil.copy2(doc, schema_dir / doc.name)

    if not include_examples:
        shutil.rmtree(package_dir / "examples", ignore_errors=True)

    output_dir.joinpath("bid_tool", "__init__.py").write_text("", encoding="utf-8")
    _write_launcher(output_dir)
    _write_readme(output_dir)
    _write_pyproject(output_dir)

    if make_zip:
        zip_path = output_dir.with_suffix(".zip")
        if zip_path.exists():
            zip_path.unlink()
        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as archive:
            for path in output_dir.rglob("*"):
                if path.is_file():
                    archive.write(path, path.relative_to(output_dir.parent))

    return output_dir


def _write_launcher(output_dir: Path) -> None:
    output_dir.joinpath("run_illustration.py").write_text(
        """from bid_tool.illustration_v2.toolkit import main\n\nif __name__ == \"__main__\":\n    main()\n""",
        encoding="utf-8",
    )


def _write_readme(output_dir: Path) -> None:
    output_dir.joinpath("README.md").write_text(
        """# bid-tool illustration_v2 standalone\n\n"""
        """Run:\n\n"""
        """```bash\npython run_illustration.py --job path/to/job.json --output output/illustrations --png\n```\n""",
        encoding="utf-8",
    )


def _write_pyproject(output_dir: Path) -> None:
    output_dir.joinpath("pyproject.toml").write_text(
        """[build-system]\n"""
        """requires = [\"setuptools>=68.0\", \"wheel\"]\n"""
        """build-backend = \"setuptools.build_meta\"\n\n"""
        """[project]\n"""
        """name = \"bid-tool-illustration-v2-standalone\"\n"""
        """version = \"1.0.0\"\n"""
        """requires-python = \">=3.10\"\n"""
        """dependencies = [\"jsonschema>=4.17.0\"]\n\n"""
        """[project.optional-dependencies]\n"""
        """png = [\"cairosvg>=2.5.0\"]\n\n"""
        """[project.scripts]\n"""
        """bid-illustrate = \"bid_tool.illustration_v2.toolkit:main\"\n""",
        encoding="utf-8",
    )


def main() -> None:
    import argparse

    parser = argparse.ArgumentParser(description="Build standalone illustration_v2 bundle.")
    parser.add_argument("--output", type=Path, required=True)
    parser.add_argument("--no-examples", action="store_true")
    parser.add_argument("--zip", action="store_true")
    args = parser.parse_args()
    output = build_bundle(args.output, include_examples=not args.no_examples, make_zip=args.zip)
    print(output)


if __name__ == "__main__":
    main()
