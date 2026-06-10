"""Stage 3: Write chapter body text.

Flow:
  1. Read S2 outline, display summary + coupling analysis
  2. Ask user interactively:
     a. Outline OK? (Y/n/edit)
     b. Expected total word count? (Enter = auto)
     c. Any technical approach / strategy? (Enter = auto-decide)
  3. Split chapters into independent groups by coupling
  4. Render one focused prompt per group (for parallel subagent writing)
  5. After all groups written: gate collects them into s3_body.json

Usage:
  python s3_body.py prepare --s1-data output/s1_analysis --s2-data output/s2_outline
  python s3_body.py collect --data output/s3_body
  python s3_body.py validate --data output/s3_body
"""
import json
import sys
import argparse
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
PROMPT_FILE = PACKAGE_ROOT / 'prompts' / 's3_writing_prompt.md'
SCHEMA_DIR = PACKAGE_ROOT / 'schemas'


def _load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _is_interactive():
    """Check if we can prompt the user interactively."""
    return sys.stdin.isatty() and sys.stdout.isatty()


def _ask_user(outline_summary, total_estimated_words):
    """Interactively ask user for outline confirmation, word budget, and technical approach.

    Returns dict with keys: outline_confirmed, word_budget, user_approach
    """
    result = {
        "outline_confirmed": True,
        "outline_changes": "",
        "word_budget": None,
        "user_approach": "",
    }

    if not _is_interactive():
        print("[INFO] 非交互模式，使用默认设置（字数按大纲比例自动评估）")
        return result

    print(f"\n{'─'*60}")
    print(f"  请确认以下内容后继续（直接回车 = 使用默认值）")
    print(f"{'─'*60}")

    # Q1: Outline confirmation
    print(f"\n  [1/3] 大纲结构是否正确？")
    print(f"        预估总字数: {total_estimated_words}")
    print(f"        章节数: {outline_summary.get('total_chapters', '?')}")
    resp = input(f"        (Y=确认 / N=需要修改 / 直接回车=确认): ").strip().lower()
    if resp == 'n':
        result["outline_confirmed"] = False
        result["outline_changes"] = input(f"        请说明需要如何修改大纲: ").strip()
        print(f"  [!] 已记录修改需求，请在 S2 输出中调整后重新运行。")
        return result

    # Q2: Word budget
    suggested = max(35000, min(total_estimated_words * 2, 65000))
    resp = input(f"\n  [2/3] 期望全文总字数？(直接回车 = 自动 {suggested} 字): ").strip()
    if resp.isdigit():
        result["word_budget"] = int(resp)
    else:
        result["word_budget"] = suggested
        print(f"        自动评估: {suggested} 字")

    # Q3: Technical approach
    print(f"\n  [3/3] 是否有技术方案的总体思路需要融入正文？")
    print(f"        例如：'采用装配式隔墙方案'、'重点突出BIM应用'、'强调绿色施工'等")
    resp = input(f"        (直接输入思路 / 直接回车 = 自行决策): ").strip()
    if resp:
        result["user_approach"] = resp
        print(f"        已记录: {resp[:80]}...")
    else:
        print(f"        将根据招标要求和项目类型自行决策技术路线。")

    print(f"\n{'─'*60}")
    print(f"  确认完成，开始生成群组提示词...")
    print(f"{'─'*60}")
    return result


def prepare(s1_data_dir=None, s2_data_dir=None, output_dir=None, project_name=None,
            word_budget=None, style_guide_path=None, user_approach=None, interactive=True):
    """Plan S3: show outline, ask user, analyze coupling, render per-group prompts.

    Parameters:
        interactive: If True, ask user for confirmation & preferences.
        word_budget: Pre-set word budget (overrides interactive prompt).
        user_approach: Pre-set technical approach (overrides interactive prompt).
    """
    s1_data_dir = Path(s1_data_dir) if s1_data_dir else Path.cwd() / 'output' / 's1_analysis'
    s2_data_dir = Path(s2_data_dir) if s2_data_dir else Path.cwd() / 'output' / 's2_outline'
    output_dir = Path(output_dir) if output_dir else Path.cwd() / 'output' / 's3_body'
    output_dir.mkdir(parents=True, exist_ok=True)

    # Load S2 outline
    outline_path = s2_data_dir / 's2_outline.json'
    if not outline_path.exists():
        print(f'[FAIL] S2 outline not found: {outline_path}')
        return None

    outline = _load_json(outline_path)
    chapters = outline.get('chapters', [])
    coverage_summary = outline.get('coverage_summary', {})

    # Calculate total from outline
    total_estimated_words = sum(ch.get('estimated_words', 0) for ch in chapters)
    total_pages = sum(ch.get('estimated_pages', 0) for ch in chapters)
    total_chapters = len(chapters)

    # Print outline summary (always shown)
    print(f'\n{"="*60}')
    print(f'  S2 大纲摘要 — {project_name or "未命名项目"}')
    print(f'{"="*60}')
    print(f'  章节: {total_chapters} | 预估字数: {total_estimated_words} | 预估页数: {total_pages}')
    print(f'  需求覆盖率: {coverage_summary.get("coverage_rate", 0)*100:.0f}%')
    print(f'\n  章节列表:')
    for ch in chapters:
        n_children = len(ch.get('children', []))
        n_illus = len(ch.get('illustration_placeholders', []))
        n_reqs = len(ch.get('covers_reqs', []))
        print(f'    {ch["chapter_id"]} {ch["title"]}  (~{ch.get("estimated_words", 0)}字, {n_children}子节, {n_reqs}需求, {n_illus}图)')

    # Interactive Q&A
    user_input = {"outline_confirmed": True, "word_budget": word_budget, "user_approach": user_approach or ""}

    if interactive and _is_interactive() and word_budget is None and user_approach is None:
        outline_summary = {
            "total_chapters": total_chapters,
            "total_estimated_words": total_estimated_words,
        }
        user_input = _ask_user(outline_summary, total_estimated_words)

        if not user_input["outline_confirmed"]:
            print(f'\n[BLOCKED] 大纲需修改: {user_input["outline_changes"]}')
            print(f'  请修改 S2 输出后重新运行: bid-tool run --stage s3')
            return None
    elif not interactive:
        print("\n[INFO] 非交互模式，自动评估参数")
        if user_input["word_budget"] is None:
            user_input["word_budget"] = max(35000, min(total_estimated_words * 2, 65000))
        if not user_input["user_approach"]:
            user_input["user_approach"] = ""

    final_word_budget = user_input["word_budget"] or max(35000, min(total_estimated_words * 2, 65000))
    final_approach = user_input.get("user_approach", "")

    # Run chapter planner
    from ..chapter_planner import plan_and_render

    plan = plan_and_render(
        str(outline_path), str(s1_data_dir), str(s2_data_dir),
        str(output_dir), project_name, final_word_budget,
        user_approach=final_approach
    )

    # Print group assignment
    groups = plan['group_prompts']
    print(f'\n{"="*60}')
    print(f'  章节耦合分析 — {plan["total_groups"]} 个独立群组（可并行撰写）')
    print(f'{"="*60}')
    print(f'  总字数: {final_word_budget} 字')
    if final_approach:
        print(f'  技术思路: {final_approach[:100]}')
    print()
    for g in groups:
        chs = ', '.join(g['chapters'])
        print(f'  [{g["group_id"]}] {g["label"]}')
        print(f'      章节: {chs}')
        print(f'      字数: {g["word_budget"]} 字')
        print(f'      提示词: {g["prompt_file"]}')
        print()

    print(f'  并行撰写完成后运行: bid-tool gate s3 --continue')

    # Store user input in plan for later reference
    plan['user_input'] = {
        "outline_confirmed": user_input["outline_confirmed"],
        "word_budget": final_word_budget,
        "user_approach": final_approach,
    }

    plan_path = output_dir / 's3_plan.json'
    with open(plan_path, 'w', encoding='utf-8') as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    return plan


def collect(data_dir=None):
    """Collect all group manifests into unified s3_body.json.

    Scans s3_body/ for *_manifest.json files, merges chapters,
    segments, and illustration_manifest entries into one manifest.
    """
    data_dir = Path(data_dir) if data_dir else Path.cwd() / 'output' / 's3_body'

    plan_path = data_dir / 's3_plan.json'
    if not plan_path.exists():
        print(f'[FAIL] s3_plan.json not found in {data_dir}')
        return None

    plan = _load_json(plan_path)

    all_chapters = []
    all_segments = []
    all_illustrations = []
    all_chapter_files = []
    total_words = 0
    all_covered_reqs = set()

    manifest_files = sorted(data_dir.glob('*_manifest.json'))
    if not manifest_files:
        print(f'[FAIL] No *_manifest.json files found in {data_dir}')
        return None

    for mf in manifest_files:
        manifest = _load_json(mf)
        chapters = manifest.get('chapters', [])
        segments = manifest.get('segments', [])
        illustrations = manifest.get('illustration_manifest', {}).get('items', [])

        for ch in chapters:
            total_words += ch.get('word_count', 0)
            for req in ch.get('covers_reqs', []):
                all_covered_reqs.add(req)

            all_chapter_files.append({
                "chapter_id": ch.get('chapter_id', ''),
                "filename": ch.get('content_file', ''),
                "title": ch.get('title', ''),
                "word_count": ch.get('word_count', 0),
                "covers_reqs": ch.get('covers_reqs', []),
                "illustration_refs": ch.get('illustration_refs', []),
            })

        all_chapters.extend(chapters)
        all_segments.extend(segments)
        all_illustrations.extend(illustrations)

        print(f'  Collected: {mf.name} → {len(chapters)} ch, {len(segments)} seg, {len(illustrations)} illu')

    # Build req list
    all_reqs = []
    s1_dir = data_dir.parent / 's1_analysis'
    tech_path = s1_dir / 's1_tech_req.json'
    if tech_path.exists():
        tech = _load_json(tech_path)
        all_reqs = [item['id'] for item in tech.get('items', [])]

    uncovered = [r for r in all_reqs if r not in all_covered_reqs]

    s3_body = {
        "document_title": f"{plan.get('project_name', '项目')}技术方案",
        "total_words": total_words,
        "chapter_files": all_chapter_files,
        "chapters": all_chapters,
        "segments": all_segments,
        "illustration_manifest": {
            "total_count": len(all_illustrations),
            "items": all_illustrations,
        },
        "coverage": {
            "total_reqs": len(all_reqs),
            "covered_reqs": len(all_covered_reqs),
            "uncovered_reqs": uncovered,
            "coverage_rate": round(len(all_covered_reqs) / len(all_reqs), 4) if all_reqs else 0,
        }
    }

    out_path = data_dir / 's3_body.json'
    with open(out_path, 'w', encoding='utf-8') as f:
        json.dump(s3_body, f, ensure_ascii=False, indent=2)

    print(f'\n  Unified manifest: {out_path}')
    print(f'  {total_words} 字, {len(all_chapters)} 章, {len(all_segments)} 段')
    if all_reqs:
        print(f'  Coverage: {len(all_covered_reqs)}/{len(all_reqs)} ({100*len(all_covered_reqs)/len(all_reqs):.0f}%)')

    return s3_body


def validate(data_dir=None):
    """Validate S3 outputs against schemas."""
    from ..validator import validate_stage
    data_dir = data_dir or str(Path.cwd() / 'output' / 's3_body')
    return validate_stage('s3', data_dir)


def main():
    parser = argparse.ArgumentParser(description='Stage 3: Write chapter body text (parallel groups)')
    sub = parser.add_subparsers(dest='action')

    p_prepare = sub.add_parser('prepare', help='Plan S3: display outline, ask user, render group prompts')
    p_prepare.add_argument('--s1-data', help='s1_analysis directory')
    p_prepare.add_argument('--s2-data', help='s2_outline directory')
    p_prepare.add_argument('--output', help='Output directory')
    p_prepare.add_argument('--project', help='Project name')
    p_prepare.add_argument('--word-budget', type=int, help='Word budget (skips interactive prompt)')
    p_prepare.add_argument('--approach', help='Technical approach (skips interactive prompt)')
    p_prepare.add_argument('--no-interactive', action='store_true', help='Skip interactive prompts')
    p_prepare.add_argument('--style-guide', help='Path to style_guide.md')

    p_collect = sub.add_parser('collect', help='Collect group manifests into s3_body.json')
    p_collect.add_argument('--data', help='s3_body directory')

    p_validate = sub.add_parser('validate', help='Validate s3_body.json')
    p_validate.add_argument('--data', help='s3_body directory')

    args = parser.parse_args()

    if args.action == 'prepare':
        prepare(
            args.s1_data, args.s2_data, args.output, args.project,
            word_budget=args.word_budget,
            user_approach=args.approach,
            interactive=not args.no_interactive,
        )
    elif args.action == 'collect':
        collect(args.data)
    elif args.action == 'validate':
        ok = validate(args.data)
        raise SystemExit(0 if ok else 1)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
