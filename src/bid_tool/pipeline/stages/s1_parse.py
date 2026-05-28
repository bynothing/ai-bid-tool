"""Stage 1: Parse tender documents — extract key info, veto items, scoring, risks, tech reqs.

Usage:
  python s1_parse.py prepare --tender <doc.md>          # Render prompt with tender doc
  python s1_parse.py validate --data output/s1_analysis  # Validate outputs against schemas
"""
import json
import argparse
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent  # bid_tool/
PROMPT_FILE = PACKAGE_ROOT / 'prompts' / 's1_parse_prompt.md'
SCHEMA_DIR = PACKAGE_ROOT / 'schemas'

OUTPUT_FILES = [
    's1_key_info.json',
    's1_veto_items.json',
    's1_scoring.json',
    's1_risk.json',
    's1_tech_req.json',
]


def prepare(tender_path, output_dir=None, project_name=None):
    """Render S1 prompt with tender document content."""
    tender_path = Path(tender_path)
    if not tender_path.exists():
        raise FileNotFoundError(f"Tender file not found: {tender_path}")

    output_dir = Path(output_dir) if output_dir else Path.cwd() / 'output' / 's1_analysis'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Read prompt template
    prompt_template = PROMPT_FILE.read_text(encoding='utf-8')

    # Read tender document
    tender_content = tender_path.read_text(encoding='utf-8')
    # Truncate if too large (prompt templates expect manageable input)
    if len(tender_content) > 80000:
        tender_content = tender_content[:80000] + '\n\n[... 招标文件过长，已截断至前80000字符 ...]'

    # Read schemas for reference in prompt
    schema_refs = []
    for sf in sorted(SCHEMA_DIR.glob('s1_*.schema.json')):
        schema = json.loads(sf.read_text(encoding='utf-8'))
        schema_refs.append(f"\n### {sf.name}\n```json\n{json.dumps(schema, ensure_ascii=False, indent=2)}\n```")

    # Render final prompt
    rendered = f"""{prompt_template}

---

## 当前招标文件内容

```
{tender_content}
```

---

## 参考 JSON Schema

以下为各输出文件必须遵守的 JSON Schema，请严格按 Schema 输出：
{''.join(schema_refs)}

---

## 输出指令

请按以上 prompt 要求，分别输出以下 5 个 JSON 文件，每个文件的内容需通过对应 Schema 校验：

1. **s1_key_info.json** — 项目关键信息表
2. **s1_veto_items.json** — 一票否决项清单
3. **s1_scoring.json** — 评分标准拆解
4. **s1_risk.json** — 风险分析表
5. **s1_tech_req.json** — 技术需求逐条提炼

项目名称: {project_name or '未命名项目'}
"""

    # Save rendered prompt for LLM consumption
    prompt_out = output_dir / 's1_rendered_prompt.md'
    prompt_out.write_text(rendered, encoding='utf-8')
    print(f'[S1] Rendered prompt saved to: {prompt_out}')
    print(f'[S1] Send this prompt to LLM, then save each output JSON to: {output_dir}/')
    print(f'[S1] Expected outputs: {", ".join(OUTPUT_FILES)}')
    print(f'[S1] After LLM completes, run: python s1_parse.py validate --data {output_dir}')

    return str(prompt_out)


def validate(data_dir=None):
    """Validate S1 outputs against schemas."""
    from ..validator import validate_stage
    data_dir = data_dir or str(Path.cwd() / 'output' / 's1_analysis')
    return validate_stage('s1', data_dir)


def main():
    parser = argparse.ArgumentParser(description='Stage 1: Parse tender documents')
    sub = parser.add_subparsers(dest='action')

    p_prepare = sub.add_parser('prepare', help='Render prompt with tender document')
    p_prepare.add_argument('--tender', required=True, help='Path to tender document (.md/.docx)')
    p_prepare.add_argument('--output', help='Output directory')
    p_prepare.add_argument('--project', help='Project name')

    p_validate = sub.add_parser('validate', help='Validate S1 outputs')
    p_validate.add_argument('--data', help='Path to s1_analysis directory')

    args = parser.parse_args()

    if args.action == 'prepare':
        prepare(args.tender, args.output, args.project)
    elif args.action == 'validate':
        ok = validate(args.data)
        raise SystemExit(0 if ok else 1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
