"""Stage 5T: Plan structured table insertions before illustration planning.

Usage:
  python -m bid_tool.pipeline.stages.s5_tables prepare --s3-data output/s3_body
  python -m bid_tool.pipeline.stages.s5_tables validate --data output/s5_tables
"""
import argparse
import json
from pathlib import Path


PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
PROMPT_FILE = PACKAGE_ROOT / "prompts" / "s5_table_prompt.md"


def _load_json(path):
    with open(path, "r", encoding="utf-8-sig") as f:
        return json.load(f)


def _read_context_file(path, max_chars=12000):
    if not path.exists():
        return ""
    text = path.read_text(encoding="utf-8")
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n\n...[内容已截断，保留前部供表格规划使用]..."


def prepare(s1_data_dir=None, s2_data_dir=None, s3_data_dir=None, output_dir=None, project_name=None):
    """Render the table-planning prompt with frozen body context."""

    output_root = Path.cwd() / "output"
    s1_data_dir = Path(s1_data_dir) if s1_data_dir else output_root / "s1_analysis"
    s2_data_dir = Path(s2_data_dir) if s2_data_dir else output_root / "s2_outline"
    s3_data_dir = Path(s3_data_dir) if s3_data_dir else output_root / "s3_body"
    output_dir = Path(output_dir) if output_dir else output_root / "s5_tables"
    output_dir.mkdir(parents=True, exist_ok=True)

    prompt_template = PROMPT_FILE.read_text(encoding="utf-8")

    context = {
        "s1_key_info": _load_json(s1_data_dir / "s1_key_info.json") if (s1_data_dir / "s1_key_info.json").exists() else {},
        "s1_scoring": _load_json(s1_data_dir / "s1_scoring.json") if (s1_data_dir / "s1_scoring.json").exists() else {},
        "s1_tech_req": _load_json(s1_data_dir / "s1_tech_req.json") if (s1_data_dir / "s1_tech_req.json").exists() else {},
        "s2_outline": _load_json(s2_data_dir / "s2_outline.json") if (s2_data_dir / "s2_outline.json").exists() else {},
        "s3_body": _load_json(s3_data_dir / "s3_body.json") if (s3_data_dir / "s3_body.json").exists() else {},
    }

    chapters = []
    chapters_dir = s3_data_dir / "chapters"
    if chapters_dir.exists():
        for path in sorted(chapters_dir.glob("*.md")):
            chapters.append({"file": path.name, "content": _read_context_file(path, max_chars=8000)})
    else:
        for path in sorted(s3_data_dir.glob("ch_*.md")):
            chapters.append({"file": path.name, "content": _read_context_file(path, max_chars=8000)})

    rendered = f"""{prompt_template}

---

## 项目信息

项目名称: {project_name or '未命名项目'}

## 上游结构化上下文

```json
{json.dumps(context, ensure_ascii=False, indent=2)[:30000]}
```

## 章节正文上下文

```json
{json.dumps(chapters, ensure_ascii=False, indent=2)[:50000]}
```

---

## 输出指令

请基于以上材料输出一份完整 `table_insertion_plan.json`。
将最终 JSON 保存为：
  {output_dir / 'table_insertion_plan.json'}
"""

    prompt_out = output_dir / "s5_table_rendered_prompt.md"
    prompt_out.write_text(rendered, encoding="utf-8")
    print(f"[S5T] Rendered table-planning prompt saved to: {prompt_out}")
    print(f"[S5T] Save LLM output to: {output_dir / 'table_insertion_plan.json'}")
    print(f"[S5T] After LLM completes, run: python -m bid_tool.pipeline.stages.s5_tables validate --data {output_dir}")
    return str(prompt_out)


def validate(data_dir=None):
    from ..validator import validate_stage

    data_dir = data_dir or str(Path.cwd() / "output" / "s5_tables")
    return validate_stage("s5_tables", data_dir)


def main():
    parser = argparse.ArgumentParser(description="Stage 5T: Plan table insertions")
    sub = parser.add_subparsers(dest="action")

    p_prepare = sub.add_parser("prepare", help="Render table planning prompt")
    p_prepare.add_argument("--s1-data", help="Path to s1_analysis directory")
    p_prepare.add_argument("--s2-data", help="Path to s2_outline directory")
    p_prepare.add_argument("--s3-data", help="Path to s3_body directory")
    p_prepare.add_argument("--output", help="Output directory")
    p_prepare.add_argument("--project", help="Project name")

    p_validate = sub.add_parser("validate", help="Validate table plan")
    p_validate.add_argument("--data", help="Path to s5_tables directory")

    args = parser.parse_args()

    if args.action == "prepare":
        prepare(args.s1_data, args.s2_data, args.s3_data, args.output, args.project)
    elif args.action == "validate":
        ok = validate(args.data)
        raise SystemExit(0 if ok else 1)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
