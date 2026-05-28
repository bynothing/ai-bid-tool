# -*- coding: utf-8 -*-
"""Unified illustration toolkit entrypoint for proposal documents.

The toolkit accepts one document-oriented job description, routes structured
framework diagrams to the SVG renderer, and routes data charts to an offline
ECharts HTML review package with optional automatic SVG/PNG export.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any

PROJECT_DIR = Path(__file__).resolve().parent
SCHEMA_DIR = PROJECT_DIR.parent / "schemas"
WEB_RUNTIME_DIR = PROJECT_DIR / "echarts_workbench"
SVG_SCRIPT = PROJECT_DIR / "svg_renderer.py"
DEFAULT_JOB = None  # --job is required; kept for API compat

# Package root for running svg_renderer as a module
_PACKAGE_ROOT = PROJECT_DIR.parent.parent  # bid-tool/


def read_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def validate_schema(instance: dict[str, Any], schema_file: Path, label: str) -> list[str]:
    try:
        import jsonschema
    except ImportError:
        return [f"{label}: 缺少 jsonschema 依赖，无法执行 Schema 校验"]
    schema = read_json(schema_file)
    validator = jsonschema.Draft202012Validator(schema)
    errors: list[str] = []
    for issue in sorted(validator.iter_errors(instance), key=lambda error: list(error.path)):
        location = ".".join(str(item) for item in issue.path) or "<root>"
        errors.append(f"{label}.{location}: {issue.message}")
    return errors


def split_specs(job: dict[str, Any]) -> tuple[dict[str, Any], dict[str, Any]]:
    title = job["document"]["title"]
    svg_figures: list[dict[str, Any]] = []
    chart_specs: list[dict[str, Any]] = []
    for item in job["illustrations"]:
        spec = dict(item["spec"])
        section = item["insertion"]["section"]
        spec.setdefault("placement", section)
        if item["renderer"] == "svg":
            svg_figures.append(spec)
        elif item["renderer"] == "echarts_html":
            chart_specs.append(spec)
    return (
        {"documentTitle": title, "figures": svg_figures},
        {"documentTitle": title, "charts": chart_specs},
    )


def validate_echarts_semantics(package: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    seen: set[str] = set()
    for index, chart in enumerate(package.get("charts", [])):
        prefix = f"echarts.charts[{index}]"
        chart_id = chart.get("id")
        if chart_id in seen:
            errors.append(f"{prefix}.id: 图件 id 重复 `{chart_id}`")
        seen.add(chart_id)
        if chart.get("type") == "bar_line":
            count = len(chart.get("categories", []))
            if len(chart.get("bar", {}).get("values", [])) != count or len(chart.get("line", {}).get("values", [])) != count:
                errors.append(f"{prefix}: categories、bar.values 与 line.values 数量必须一致")
        elif chart.get("type") == "radar":
            count = len(chart.get("indicators", []))
            for series in chart.get("series", []):
                if len(series.get("values", [])) != count:
                    errors.append(f"{prefix}: series.values 数量必须与 indicators 一致")
        elif chart.get("type") == "sankey":
            nodes = {node.get("name") for node in chart.get("nodes", [])}
            for link in chart.get("links", []):
                if link.get("source") not in nodes or link.get("target") not in nodes:
                    errors.append(f"{prefix}: link 引用了不存在的节点")
    return errors


def validate_job(job: dict[str, Any]) -> tuple[list[str], dict[str, Any], dict[str, Any]]:
    errors = validate_schema(job, SCHEMA_DIR / "proposal_illustration_job.schema.json", "job")
    svg_package, chart_package = split_specs(job) if not errors else ({"figures": []}, {"charts": []})
    if svg_package["figures"]:
        errors.extend(validate_schema(svg_package, SCHEMA_DIR / "svg_diagram.schema.json", "svg"))
    if chart_package["charts"]:
        errors.extend(validate_schema(chart_package, SCHEMA_DIR / "echarts_diagram.schema.json", "echarts"))
        errors.extend(validate_echarts_semantics(chart_package))
    ids = [item.get("id") for item in job.get("illustrations", [])]
    if len(ids) != len(set(ids)):
        errors.append("job.illustrations: 插图 id 必须唯一")
    return errors, svg_package, chart_package


def write_input_packages(output: Path, svg_package: dict[str, Any], chart_package: dict[str, Any]) -> tuple[Path, Path]:
    input_dir = output / "inputs"
    input_dir.mkdir(parents=True, exist_ok=True)
    svg_file = input_dir / "svg-diagrams.json"
    charts_file = input_dir / "echarts-diagrams.json"
    svg_file.write_text(json.dumps(svg_package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    charts_file.write_text(json.dumps(chart_package, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    return svg_file, charts_file


def render_svg(svg_file: Path, output: Path, theme: str, png: bool, png_scale: int) -> list[dict[str, Any]]:
    if not read_json(svg_file).get("figures"):
        return []
    svg_output = output / "assets" / "svg"
    command = [
        sys.executable,
        "-m", "bid_tool.illustration.svg_renderer",
        "--spec",
        str(svg_file),
        "--output",
        str(svg_output),
        "--theme",
        theme,
    ]
    if png:
        command.extend(["--png", "--png-scale", str(png_scale)])
    subprocess.run(command, check=True, cwd=str(_PACKAGE_ROOT))
    return read_json(svg_output / "result.json")


def create_echarts_review_page(chart_package: dict[str, Any], output: Path) -> Path | None:
    if not chart_package.get("charts"):
        return None
    target = output / "review" / "echarts"
    shutil.copytree(WEB_RUNTIME_DIR, target, dirs_exist_ok=True)
    copied_guide = target / "README.md"
    if copied_guide.exists():
        copied_guide.unlink()
    payload = "window.DEMO_CHART_PACKAGE = " + json.dumps(chart_package, ensure_ascii=False, indent=2) + ";\n"
    (target / "demo-specs.js").write_text(payload, encoding="utf-8")
    return target / "index.html"


def export_echarts_images(review_page: Path, charts: list[dict[str, Any]], output: Path, png: bool) -> dict[str, dict[str, str]]:
    try:
        from playwright.sync_api import sync_playwright
    except ImportError as exc:
        raise RuntimeError("自动导出 ECharts 图片需要 playwright；可使用 --no-echarts-export 仅生成审图页面") from exc
    image_dir = output / "assets" / "echarts"
    image_dir.mkdir(parents=True, exist_ok=True)
    exports: dict[str, dict[str, str]] = {}
    browser_errors: list[str] = []
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1600, "height": 1040}, accept_downloads=True)
        page.on("pageerror", lambda error: browser_errors.append(str(error)))
        page.goto(review_page.as_uri(), wait_until="load")
        page.wait_for_selector("#chart-stage svg", timeout=15000)
        for index, chart in enumerate(charts):
            page.locator(".chart-tab").nth(index).click()
            page.wait_for_timeout(100)
            chart_id = chart["id"]
            with page.expect_download(timeout=15000) as svg_download:
                page.locator("#download-svg").click()
            svg_target = image_dir / f"{chart_id}.svg"
            svg_download.value.save_as(svg_target)
            exports[chart_id] = {"svg": svg_target.relative_to(output).as_posix()}
            if png:
                with page.expect_download(timeout=15000) as png_download:
                    page.locator("#download-png").click()
                png_target = image_dir / f"{chart_id}.png"
                png_download.value.save_as(png_target)
                exports[chart_id]["png"] = png_target.relative_to(output).as_posix()
        browser.close()
    if browser_errors:
        raise RuntimeError("ECharts 页面执行错误: " + "; ".join(browser_errors))
    return exports


def make_records(
    job: dict[str, Any],
    svg_results: list[dict[str, Any]],
    chart_exports: dict[str, dict[str, str]],
    review_page: Path | None,
    output: Path,
) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    svg_index = 0
    for item in job["illustrations"]:
        record = {
            "id": item["id"],
            "renderer": item["renderer"],
            "section": item["insertion"]["section"],
            "caption": item["insertion"]["caption"],
            "purpose": item["insertion"].get("purpose", ""),
            "title": item["spec"]["title"],
            "outputs": {},
        }
        if item["renderer"] == "svg":
            result = svg_results[svg_index]
            svg_index += 1
            record["outputs"]["svg"] = (Path("assets") / "svg" / result["svg"]).as_posix()
            if result.get("png"):
                record["outputs"]["png"] = (Path("assets") / "svg" / result["png"]).as_posix()
        else:
            record["outputs"].update(chart_exports.get(item["spec"]["id"], {}))
            if review_page:
                record["outputs"]["reviewHtml"] = review_page.relative_to(output).as_posix()
        records.append(record)
    return records


def write_manifest(job: dict[str, Any], records: list[dict[str, Any]], output: Path, job_file: Path) -> None:
    result = {
        "document": job["document"],
        "sourceJob": str(job_file),
        "illustrations": records,
    }
    (output / "illustration-manifest.json").write_text(
        json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
    )
    lines = [
        "# 标书配图生成清单",
        "",
        f"- 文档：`{job['document']['title']}`",
        f"- 任务来源：`{job_file}`",
        f"- 图件数量：`{len(records)}`",
        "",
        "| 章节位置 | 图题 | 渲染器 | SVG | PNG | 审图页面 |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for record in records:
        files = record["outputs"]
        svg = f"[查看](<{files['svg']}>)" if files.get("svg") else "-"
        png = f"[查看](<{files['png']}>)" if files.get("png") else "-"
        html = f"[打开](<{files['reviewHtml']}>)" if files.get("reviewHtml") else "-"
        lines.append(
            f"| {record['section']} | {record['caption']} | `{record['renderer']}` | {svg} | {png} | {html} |"
        )
    lines.extend(["", "## 自动插图元数据", ""])
    for record in records:
        lines.extend([
            f"### {record['caption']}",
            "",
            f"- 插入章节：`{record['section']}`",
            f"- 图件用途：{record['purpose'] or '-'}",
            f"- 图件标题：{record['title']}",
            "",
        ])
    (output / "生成清单.md").write_text("\n".join(lines), encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser(description="统一生成招投标文档使用的 SVG 框图与 ECharts 数据图")
    parser.add_argument("--job", type=Path, required=True, help="统一配图任务 JSON 文件")
    parser.add_argument("--output", type=Path, default=Path.cwd() / "output" / "illustrations", help="输出目录")
    parser.add_argument("--validate-only", action="store_true", help="仅校验统一任务和各渲染器描述")
    parser.add_argument("--png", action="store_true", help="同步生成 PNG 预览")
    parser.add_argument("--png-scale", type=int, choices=(1, 2, 3), default=2, help="SVG PNG 输出倍率，正式文档推荐 2 或 3")
    parser.add_argument("--no-echarts-export", action="store_true", help="ECharts 只生成本地 HTML 审图页，不自动导出图片")
    parser.add_argument("--open-preview", action="store_true", help="生成完成后打开 ECharts 本地审图页")
    args = parser.parse_args()

    job_file = args.job.resolve()
    job = read_json(job_file)
    errors, svg_package, chart_package = validate_job(job)
    if errors:
        print(f"统一配图任务校验失败: {job_file}")
        for error in errors:
            print(f"  - {error}")
        raise SystemExit(2)
    print(f"统一配图任务校验通过: {job_file} ({len(job['illustrations'])} 张图)")
    if args.validate_only:
        return

    output = args.output.resolve()
    output.mkdir(parents=True, exist_ok=True)
    theme = job.get("style", {}).get("theme", "clarity_blue")
    preferred_format = job.get("style", {}).get("preferredFormat", "svg")
    produce_png = args.png or preferred_format in {"png", "both"}
    svg_file, _ = write_input_packages(output, svg_package, chart_package)
    svg_results = render_svg(svg_file, output, theme, produce_png, args.png_scale)
    review_page = create_echarts_review_page(chart_package, output)
    chart_exports: dict[str, dict[str, str]] = {}
    if review_page and not args.no_echarts_export:
        chart_exports = export_echarts_images(review_page, chart_package["charts"], output, produce_png)
    records = make_records(job, svg_results, chart_exports, review_page, output)
    write_manifest(job, records, output, job_file)
    print(f"完成: {output / '生成清单.md'}")
    if review_page:
        print(f"ECharts 审图页面: {review_page}")
        if args.open_preview:
            import os
            os.startfile(review_page)  # type: ignore[attr-defined]


if __name__ == "__main__":
    main()
