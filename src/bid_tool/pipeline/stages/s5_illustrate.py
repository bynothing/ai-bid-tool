"""Stage 5: Generate structured illustration descriptions for diagram toolkit.

Three sub-steps:
  1. prepare  — render LLM prompt with body text and illustration placeholders
  2. assemble — collect individual illustration JSONs into s5_illustration.json
  3. validate — validate against JSON Schema

Usage:
  python s5_illustrate.py prepare --s3-data output/s3_body
  python s5_illustrate.py assemble --data output/s5_illustrations
  python s5_illustrate.py validate --data output/s5_illustrations
"""
import json
import argparse
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
PROMPT_FILE = PACKAGE_ROOT / 'prompts' / 's5_illustration_prompt.md'
SCHEMA_DIR = PACKAGE_ROOT / 'schemas'

OUTPUT_FILES = ['s5_illustration.json']

STYLE_GUIDE = {
    "font_family": "微软雅黑, Consolas",
    "font_size_range": "9pt-28pt",
    "icon_style": "线性图标, Material Design Icons 风格, 单色#1a3a5c",
    "connector_style": "实线箭头",
    "shadow_style": "box-shadow: 0 2px 8px rgba(0,0,0,0.08), 圆角矩形 border-radius: 6px",
    "border_style": "节点边框 1px solid #d0d5dd"
}


def _load_json(path):
    with open(path, 'r', encoding='utf-8-sig') as f:
        return json.load(f)


def prepare(s3_data_dir=None, output_dir=None, project_name=None, tables_data_dir=None):
    """Render S5 illustration prompt with body text context."""
    s3_data_dir = Path(s3_data_dir) if s3_data_dir else Path.cwd() / 'output' / 's3_body'
    output_dir = Path(output_dir) if output_dir else Path.cwd() / 'output' / 's5_illustrations'
    tables_data_dir = Path(tables_data_dir) if tables_data_dir else Path.cwd() / 'output' / 's5_tables'
    output_dir.mkdir(parents=True, exist_ok=True)

    prompt_template = PROMPT_FILE.read_text(encoding='utf-8')

    # Load body text for context (find all illustration placeholders)
    s3_body_path = s3_data_dir / 's3_body.json'
    body_context = ''
    if s3_body_path.exists():
        body = _load_json(s3_body_path)
        body_context = f"\n### s3_body.json (摘要)\n```json\n{json.dumps(body, ensure_ascii=False, indent=2)[:5000]}\n```"

    table_context = ''
    table_plan_path = tables_data_dir / 'table_insertion_plan.json'
    if table_plan_path.exists():
        table_plan = _load_json(table_plan_path)
        table_context = f"\n### 已规划表格（请避免生成重复插图）\n```json\n{json.dumps(table_plan, ensure_ascii=False, indent=2)[:12000]}\n```"

    rendered = f"""{prompt_template}

---

## 正文内容（插图占位检测）
{body_context}

## 表格化内容计划
{table_context or '未发现 table_insertion_plan.json；请仍优先避免把清单、对照、资源配置类内容画成图。'}

## 设计规范

{json.dumps(STYLE_GUIDE, ensure_ascii=False, indent=2)}

---

## 输出指令

请按以上 prompt 要求，输出一份完整 Illustration Job v2 JSON（60张图左右）。
将最终 JSON 保存为：
  {output_dir / 's5_illustration_job.json'}

项目名称: {project_name or '未命名项目'}
"""

    prompt_out = output_dir / 's5_rendered_prompt.md'
    prompt_out.write_text(rendered, encoding='utf-8')
    print(f'[S5] Rendered prompt saved to: {prompt_out}')
    print(f'[S5] Save LLM output to: {output_dir / "s5_illustration_job.json"}')
    print(f'[S5] After LLM completes, run: bid-illustrate --job {output_dir / "s5_illustration_job.json"} --validate-only')

    return str(prompt_out)


def assemble(data_dir=None):
    """Collect individual illustration JSONs into s5_illustration.json."""
    data_dir = Path(data_dir) if data_dir else Path.cwd() / 'output' / 's5_illustrations'

    illustrations = []
    errors = []

    for fpath in sorted(data_dir.glob('*.json')):
        if fpath.name == 's5_illustration.json':
            continue
        try:
            illustrations.append(_load_json(fpath))
        except (json.JSONDecodeError, Exception) as e:
            errors.append((fpath.name, str(e)))

    print(f'Loaded {len(illustrations)} illustrations, {len(errors)} errors')
    for name, err in errors:
        print(f'  ERROR: {name}: {err}')

    output = {
        "illustrations": illustrations,
        "style_guide": STYLE_GUIDE
    }

    outpath = data_dir / 's5_illustration.json'
    outpath.write_text(json.dumps(output, ensure_ascii=False, indent=2), encoding='utf-8')

    print(f'Written {len(illustrations)} illustrations to {outpath}')
    ids = sorted(i.get('illu_id', '?') for i in illustrations)
    print(f'IDs: {ids}')

    return str(outpath)


def validate(data_dir=None):
    """Validate S5 outputs against schemas."""
    from ..validator import validate_stage
    data_dir = data_dir or str(Path.cwd() / 'output' / 's5_illustrations')
    return validate_stage('s5', data_dir)


def main():
    parser = argparse.ArgumentParser(description='Stage 5: Generate illustration descriptions')
    sub = parser.add_subparsers(dest='action')

    p_prepare = sub.add_parser('prepare', help='Render illustration prompt')
    p_prepare.add_argument('--s3-data', help='Path to s3_body directory')
    p_prepare.add_argument('--output', help='Output directory')
    p_prepare.add_argument('--project', help='Project name')
    p_prepare.add_argument('--tables-data', help='Path to s5_tables directory')

    p_assemble = sub.add_parser('assemble', help='Assemble individual JSONs into unified file')
    p_assemble.add_argument('--data', help='Path to s5_illustrations directory')

    p_validate = sub.add_parser('validate', help='Validate S5 outputs')
    p_validate.add_argument('--data', help='Path to s5_illustrations directory')

    args = parser.parse_args()

    if args.action == 'prepare':
        prepare(args.s3_data, args.output, args.project, args.tables_data)
    elif args.action == 'assemble':
        assemble(args.data)
    elif args.action == 'validate':
        ok = validate(args.data)
        raise SystemExit(0 if ok else 1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
