"""Stage 2: Design chapter outline aligned with scoring criteria.

Usage:
  python s2_outline.py prepare --s1-data output/s1_analysis   # Render prompt with S1 data
  python s2_outline.py validate --data output/s2_outline       # Validate against schema
"""
import json
import argparse
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
PROMPT_FILE = PACKAGE_ROOT / 'prompts' / 's2_outline_prompt.md'
SCHEMA_DIR = PACKAGE_ROOT / 'schemas'

OUTPUT_FILES = ['s2_outline.json']


def _load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def prepare(s1_data_dir=None, output_dir=None, project_name=None, chapter_templates=None):
    """Render S2 prompt with S1 stage outputs as context."""
    s1_data_dir = Path(s1_data_dir) if s1_data_dir else Path.cwd() / 'output' / 's1_analysis'
    output_dir = Path(output_dir) if output_dir else Path.cwd() / 'output' / 's2_outline'
    output_dir.mkdir(parents=True, exist_ok=True)

    prompt_template = PROMPT_FILE.read_text(encoding='utf-8')

    # Load S1 outputs for context
    s1_context = []
    for fname in ['s1_key_info.json', 's1_tech_req.json', 's1_scoring.json',
                   's1_veto_items.json', 's1_risk.json']:
        fpath = s1_data_dir / fname
        if fpath.exists():
            content = _load_json(fpath)
            s1_context.append(f"\n### {fname}\n```json\n{json.dumps(content, ensure_ascii=False, indent=2)}\n```")
        else:
            s1_context.append(f"\n### {fname}\n[文件不存在: {fpath}]")

    # Chapter template hint
    chapter_hint = ''
    if chapter_templates:
        chapter_hint = '\n## 参考章节模板\n\n以下为建议的章节结构，请根据实际评分标准调整：\n\n'
        for ch_id, ch_name in chapter_templates.items():
            chapter_hint += f'- **{ch_id}**: {ch_name}\n'

    # Load schema
    schema_path = SCHEMA_DIR / 's2_outline.schema.json'
    schema = json.loads(schema_path.read_text(encoding='utf-8'))

    rendered = f"""{prompt_template}

---

## 阶段 1 分析结果

以下是从招标文件中提取的结构化分析数据，请基于这些数据设计大纲：
{''.join(s1_context)}

---

## 参考 JSON Schema

```json
{json.dumps(schema, ensure_ascii=False, indent=2)}
```
{chapter_hint}
---

## 输出指令

请按以上 prompt 要求，输出 **s2_outline.json**，内容包括：
1. 章节大纲 (chapters 数组)
2. 覆盖率映射 (coverage_map)，确保每个评分项都有对应章节
3. 未覆盖需求列表 (uncovered_reqs)，如果全部覆盖则为空数组

项目名称: {project_name or '未命名项目'}
"""

    prompt_out = output_dir / 's2_rendered_prompt.md'
    prompt_out.write_text(rendered, encoding='utf-8')
    print(f'[S2] Rendered prompt saved to: {prompt_out}')
    print(f'[S2] Expected output: {", ".join(OUTPUT_FILES)} → {output_dir}/')
    print(f'[S2] After LLM completes, run: python s2_outline.py validate --data {output_dir}')

    return str(prompt_out)


def validate(data_dir=None):
    """Validate S2 outputs against schemas."""
    from ..validator import validate_stage
    data_dir = data_dir or str(Path.cwd() / 'output' / 's2_outline')
    return validate_stage('s2', data_dir)


def main():
    parser = argparse.ArgumentParser(description='Stage 2: Design chapter outline')
    sub = parser.add_subparsers(dest='action')

    p_prepare = sub.add_parser('prepare', help='Render prompt with S1 data')
    p_prepare.add_argument('--s1-data', help='Path to s1_analysis directory')
    p_prepare.add_argument('--output', help='Output directory')
    p_prepare.add_argument('--project', help='Project name')

    p_validate = sub.add_parser('validate', help='Validate S2 outputs')
    p_validate.add_argument('--data', help='Path to s2_outline directory')

    args = parser.parse_args()

    if args.action == 'prepare':
        prepare(args.s1_data, args.output, args.project)
    elif args.action == 'validate':
        ok = validate(args.data)
        raise SystemExit(0 if ok else 1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
