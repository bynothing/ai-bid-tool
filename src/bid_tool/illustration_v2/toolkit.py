"""Command-line toolkit for the active illustration_v2 engine."""
from __future__ import annotations

import argparse
from pathlib import Path

from . import api


SCHEMA_DIR = Path(__file__).resolve().parents[1] / "schemas"


def main() -> None:
    parser = argparse.ArgumentParser(description="Render Illustration Job v2 assets.")
    parser.add_argument("--job", type=Path, required=True, help="Illustration Job v2 JSON file")
    parser.add_argument("--output", type=Path, default=Path.cwd() / "output" / "illustrations", help="Output directory")
    parser.add_argument("--png", action="store_true", help="Also export PNG previews when supported")
    parser.add_argument("--png-scale", type=int, choices=(1, 2, 3), default=2, help="PNG output scale")
    parser.add_argument("--theme", default="formal_blue", help="Renderer theme id")
    parser.add_argument("--validate-only", action="store_true", help="Validate only; do not render")
    parser.add_argument(
        "--no-echarts-export",
        action="store_true",
        help="Compatibility flag from the retired engine; ignored by illustration_v2",
    )
    args = parser.parse_args()

    job = api.load_job(args.job)
    errors, warnings = api.validate(job)
    if errors:
        print("[illustration_v2] validation failed:")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(1)

    if warnings:
        print("[illustration_v2] validation warnings:")
        for warning in warnings:
            print(f"  - {warning}")

    print(f"[illustration_v2] job OK: {args.job}")
    if args.validate_only:
        return

    decisions = api.plan(job)
    for decision in decisions:
        template = decision["decision"].get("template") or "direct"
        print(f"  - {decision['id']}: {decision['type']} -> {decision['renderer']} ({template})")

    records = api.render(
        job,
        args.output,
        theme=args.theme,
        png=args.png,
        png_scale=args.png_scale,
        export_echarts=not args.no_echarts_export,
    )
    print(f"[illustration_v2] rendered {len(records)} asset(s): {args.output.resolve()}")


if __name__ == "__main__":
    main()
