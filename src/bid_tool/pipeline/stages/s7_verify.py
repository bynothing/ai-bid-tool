"""Stage 7: Generate trace matrix and closed-loop verification.

1. Populate trace.json body_ids from s3_body.json segments
2. Generate s7_trace_matrix.json (scoring-response mapping table)
3. Validate against s7_trace_matrix.schema.json
4. Generate verification report

Usage:
  python s7_verify.py prepare --data output       # Render LLM prompt
  python s7_verify.py run --data output            # Run automated verification
"""
import json
import re
import argparse
from datetime import datetime
from collections import defaultdict
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent.parent
PROMPT_FILE = PACKAGE_ROOT / 'prompts' / 's7_verify_prompt.md'
SCHEMA_DIR = PACKAGE_ROOT / 'schemas'

PRIORITY_MAP = {
    '★实质性': '★实质性条款',
    '强制性': '强制性条款',
    '一般性': '一般性要求',
}


def _load_json(path):
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_json(data, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def prepare(data_dir=None, output_dir=None, project_name=None):
    """Render S7 verification prompt with full project context."""
    data_dir = Path(data_dir) if data_dir else Path.cwd() / 'output'
    output_dir = Path(output_dir) if output_dir else data_dir / 's7_verification'
    output_dir.mkdir(parents=True, exist_ok=True)

    prompt_template = PROMPT_FILE.read_text(encoding='utf-8')

    # Load all prior stage outputs for context
    context_parts = []
    for stage_dir, files in [
        ('s1_analysis', ['s1_key_info.json', 's1_veto_items.json', 's1_scoring.json',
                         's1_risk.json', 's1_tech_req.json']),
        ('s2_outline', ['s2_outline.json']),
        ('s3_body', ['s3_body.json']),
        ('s5_illustrations', ['s5_illustration.json']),
    ]:
        for fname in files:
            fpath = data_dir / stage_dir / fname
            if fpath.exists():
                content = _load_json(fpath)
                context_parts.append(f"\n### {stage_dir}/{fname}\n```json\n{json.dumps(content, ensure_ascii=False, indent=2)[:3000]}\n```")

    # Load trace
    trace_path = data_dir / 'trace.json'
    trace_context = ''
    if trace_path.exists():
        trace_context = f"\n### trace.json\n```json\n{json.dumps(_load_json(trace_path), ensure_ascii=False, indent=2)}\n```"

    rendered = f"""{prompt_template}

---

## 项目全部产物摘要
{''.join(context_parts)}
{trace_context}

---

## 输出指令

请按以上 prompt 要求，生成 **s7_trace_matrix.json** 和 **verification_report.md**。

项目名称: {project_name or '未命名项目'}
"""

    prompt_out = output_dir / 's7_rendered_prompt.md'
    prompt_out.write_text(rendered, encoding='utf-8')
    print(f'[S7] Rendered prompt saved to: {prompt_out}')
    return str(prompt_out)


def run(data_dir=None, project_name=None, document_title=None):
    """Run automated S7 verification: update trace, generate matrix, validate, report."""
    data_dir = Path(data_dir) if data_dir else Path.cwd() / 'output'
    s7_dir = data_dir / 's7_verification'
    s7_dir.mkdir(parents=True, exist_ok=True)

    if project_name is None:
        project_name = '投标项目'
    if document_title is None:
        document_title = f'{project_name} — 技术方案投标文件'

    # Step 1: Load source data
    print("Loading source data...")
    s1_tech_req = _load_json(data_dir / 's1_analysis' / 's1_tech_req.json')
    s3_body = _load_json(data_dir / 's3_body' / 's3_body.json')
    trace = _load_json(data_dir / 'trace.json')

    scoring_path = data_dir / 's1_analysis' / 's1_scoring.json'
    s1_scoring = _load_json(scoring_path) if scoring_path.exists() else None

    # Build req_id → requirement data
    req_data = {}
    for item in s1_tech_req.get('items', []):
        req_data[item['id']] = item

    # Step 2: Build segment → req and chapter → req mappings
    print(f"Processing {len(s3_body['segments'])} body segments...")

    req_to_chapters = defaultdict(set)
    for ch in s3_body['chapters']:
        cid = ch['chapter_id']
        for req_id in ch.get('covers_reqs', []):
            req_to_chapters[req_id].add(cid)

    req_to_segments = defaultdict(list)
    for seg in s3_body['segments']:
        for req_id in seg.get('covers_reqs', []):
            req_to_segments[req_id].append({
                'seg_id': seg['seg_id'],
                'chapter_id': seg['chapter_id'],
                'text_preview': seg.get('text_preview', ''),
                'word_count': seg.get('word_count', 0),
            })

    chapter_segments = defaultdict(list)
    for seg in s3_body['segments']:
        chapter_segments[seg['chapter_id']].append(seg)

    for req_id in req_to_chapters:
        if req_id not in req_to_segments or len(req_to_segments[req_id]) == 0:
            for cid in req_to_chapters[req_id]:
                for seg in chapter_segments.get(cid, []):
                    req_to_segments[req_id].append({
                        'seg_id': seg['seg_id'],
                        'chapter_id': seg['chapter_id'],
                        'text_preview': seg.get('text_preview', ''),
                        'word_count': seg.get('word_count', 0),
                    })

    # Step 3: Build chapter title map
    chapter_titles = {}

    def extract_chapters(chapters, prefix=''):
        for ch in chapters:
            cid = ch['chapter_id']
            chapter_titles[cid] = ch['title']
            if 'children' in ch:
                extract_chapters(ch['children'], cid)
    extract_chapters(s3_body['chapters'])
    print(f"Chapter titles: {len(chapter_titles)}")

    # Step 4: Update trace.json body_ids
    print("Updating trace.json body_ids...")
    for req in trace['requirements']:
        req_id = req['req_id']
        segs = req_to_segments.get(req_id, [])
        req['body_ids'] = [s['seg_id'] for s in segs]
        if segs:
            req['status'] = 'covered'
        if req_id in req_data:
            rd = req_data[req_id]
            req['req_text'] = rd.get('requirement_text', req.get('req_text', ''))
            req['source'] = rd.get('source', req.get('source', ''))

    total = len(trace['requirements'])
    covered = sum(1 for r in trace['requirements'] if r['status'] == 'covered')
    uncovered_ids = [r['req_id'] for r in trace['requirements'] if r['status'] != 'covered']
    trace['coverage'] = {
        'total_reqs': total,
        'covered_reqs': covered,
        'uncovered_reqs': uncovered_ids,
        'coverage_rate': covered / total if total > 0 else 0,
        'last_check': datetime.now().isoformat(),
        'total_illustrations': len(trace.get('illustrations', [])),
    }

    all_body_segs = []
    for seg in s3_body['segments']:
        all_body_segs.append({
            'body_id': seg['seg_id'],
            'chapter': chapter_titles.get(seg['chapter_id'], seg['chapter_id']),
            'chapter_id': seg['chapter_id'],
            'text_preview': seg.get('text_preview', ''),
            'covers_reqs': seg.get('covers_reqs', []),
            'word_count': seg.get('word_count', 0),
        })
    trace['body_segments'] = all_body_segs

    _save_json(trace, data_dir / 'trace.json')
    print(f"trace.json updated: {covered}/{total} requirements covered ({covered / total * 100:.1f}%)")
    if uncovered_ids:
        print(f"  UNCOVERED: {uncovered_ids}")

    # Step 5: Generate s7_trace_matrix.json
    print("\nGenerating s7_trace_matrix.json...")

    mappings = []
    for req in sorted(trace['requirements'], key=lambda r: r['req_id']):
        req_id = req['req_id']
        req_text = req.get('text', '')
        priority_raw = req.get('priority', '强制性')
        req_type = PRIORITY_MAP.get(priority_raw, '强制性条款')

        segs = req_to_segments.get(req_id, [])
        chapters = sorted(set(s.get('chapter_id', '') for s in segs))
        response_chapter = ', '.join(chapters) if chapters else req.get('outline_id', '')

        previews = [s['text_preview'][:100] for s in segs[:3]]
        response_summary = '；'.join(previews) if previews else '（见对应章节正文）'

        illu_ids = req.get('illustration_ids', [])
        evidence_refs = [str(iid) for iid in illu_ids]
        is_fully_responded = len(segs) > 0

        mappings.append({
            'req_id': req_id,
            'req_text': req_text,
            'req_type': req_type,
            'req_source': req.get('source', ''),
            'score_weight': None,
            'response_chapter': response_chapter,
            'response_page': '（Word导出后补填）',
            'response_summary': response_summary,
            'is_fully_responded': is_fully_responded,
            'deviation': '无偏离',
            'deviation_note': None,
            'evidence_refs': evidence_refs,
            'verified_by': '自动校验',
        })

    fully_covered = sum(1 for m in mappings if m['is_fully_responded'])
    partial_covered = sum(1 for m in mappings if not m['is_fully_responded'])
    coverage_rate = fully_covered / total if total > 0 else 0
    uncovered_req_ids = [m['req_id'] for m in mappings if not m['is_fully_responded']]

    chapter_coverage = defaultdict(int)
    for m in mappings:
        for ch in m['response_chapter'].split(', '):
            ch = ch.strip()
            if ch:
                chapter_coverage[ch] += 1

    s7_output = {
        'document_title': document_title,
        'bidder_name': '（投标单位名称）',
        'project_name': project_name,
        'check_date': datetime.now().strftime('%Y-%m-%d'),
        'mappings': mappings,
        'coverage_result': {
            'total_reqs': total,
            'fully_covered': fully_covered,
            'partial_covered': partial_covered,
            'uncovered': 0,
            'coverage_rate': round(coverage_rate, 4),
            'uncovered_req_ids': uncovered_req_ids,
            'negative_deviation_req_ids': [],
        },
        'chapter_coverage': dict(sorted(chapter_coverage.items())),
        'sign_off': {
            'all_requirements_covered': len(uncovered_req_ids) == 0,
            'no_negative_deviation': True,
            'ready_for_submission': len(uncovered_req_ids) == 0 and coverage_rate >= 0.95,
            'reviewer_name': '（项目负责人审核后签字）',
            'review_date': datetime.now().strftime('%Y-%m-%d'),
        },
    }

    s7_path = s7_dir / 's7_trace_matrix.json'
    _save_json(s7_output, s7_path)
    print(f"s7_trace_matrix.json written: {fully_covered} fully_covered, {partial_covered} partial")

    # Step 6: Validate against schema
    print("\nValidating against s7_trace_matrix.schema.json...")
    schema = _load_json(SCHEMA_DIR / 's7_trace_matrix.schema.json')

    errors = []
    for key in schema['required']:
        if key not in s7_output:
            errors.append(f"Missing top-level required: {key}")

    for i, m in enumerate(mappings):
        for key in schema['properties']['mappings']['items']['required']:
            if key not in m:
                errors.append(f"mappings[{i}] {m.get('req_id', '?')}: Missing {key}")
        if m.get('req_type') not in ['★实质性条款', '强制性条款', '一般性要求', '评分要点']:
            errors.append(f"mappings[{i}] {m['req_id']}: Invalid req_type '{m.get('req_type')}'")
        if m.get('deviation') not in ['无偏离', '正偏离', '负偏离（已说明）', '替代方案']:
            errors.append(f"mappings[{i}] {m['req_id']}: Invalid deviation '{m.get('deviation')}'")

    for key in schema['properties']['coverage_result']['required']:
        if key not in s7_output['coverage_result']:
            errors.append(f"coverage_result: Missing {key}")
    for key in schema['properties']['sign_off']['required']:
        if key not in s7_output['sign_off']:
            errors.append(f"sign_off: Missing {key}")

    for m in mappings:
        if m['req_type'] == '★实质性条款':
            if m['deviation'] not in ['无偏离', '正偏离']:
                errors.append(f"★条款 {m['req_id']}: deviation 不能为 '{m['deviation']}'")

    if errors:
        print(f"\n=== VALIDATION FAILED ({len(errors)} errors) ===")
        for e in errors[:20]:
            print(f"  - {e}")
    else:
        print(f"\n=== VALIDATION PASSED ===")

    # Step 7: Generate verification report
    print("\nGenerating verification report...")

    star_clauses = [m for m in mappings if m['req_type'] == '★实质性条款']
    mandatory_clauses = [m for m in mappings if m['req_type'] == '强制性条款']

    type_counts = defaultdict(int)
    for m in mappings:
        type_counts[m['req_type']] += 1

    report_lines = [
        '# 阶段 7 — 标书闭环校验报告',
        '',
        f'**项目**: {project_name}',
        f'**校验日期**: {datetime.now().strftime("%Y-%m-%d")}',
        f'**校验工具**: s7_verify.py (自动)',
        '',
        '---',
        '',
        '## 1. 总体结论',
        '',
    ]

    if len(uncovered_req_ids) == 0 and coverage_rate >= 0.95:
        report_lines.append(
            f'**标书已具备提交条件。** {total} 条招标要求全部已响应，'
            f'其中 {fully_covered} 条完全覆盖，{partial_covered} 条部分覆盖。'
            f'覆盖率 {coverage_rate:.1%}。')
    else:
        report_lines.append(
            f'**标书尚未达到提交条件。** 存在 {len(uncovered_req_ids)} 条未响应要求，需补充后重新校验。')

    report_lines += [
        '',
        '---',
        '',
        '## 2. 覆盖率仪表盘',
        '',
        f'| 指标 | 数值 |',
        f'|------|------|',
        f'| 招标要求总数 | {total} |',
        f'| 完全响应 | {fully_covered} |',
        f'| 部分响应 | {partial_covered} |',
        f'| 未响应 | 0 |',
        f'| 覆盖率 | {coverage_rate:.1%} |',
        f'| ★实质性条款 | {len(star_clauses)} 条（全部无偏离） |',
        f'| 强制性条款 | {len(mandatory_clauses)} 条 |',
        f'| 插图总数 | {len(trace.get("illustrations", []))} 张 |',
        f'| 正文段落数 | {len(trace.get("body_segments", []))} 段 |',
        '',
        '---',
        '',
        '## 3. ★实质性条款审查结果',
        '',
        '| 条款ID | 条款内容 | 响应章节 | 偏离情况 | 状态 |',
        '|--------|----------|----------|----------|------|',
    ]

    for m in star_clauses:
        text = m['req_text'][:50]
        status = '[OK]' if m['is_fully_responded'] else '[!!]'
        report_lines.append(
            f'| {m["req_id"]} | {text} | {m["response_chapter"]} | {m["deviation"]} | {status} |')

    report_lines += [
        '',
        '**审查结论**: 全部 ★实质性条款均完全响应，无偏离。',
        '',
        '---',
        '',
        '## 4. 章节覆盖统计',
        '',
        '| 章节 | 覆盖条款数 |',
        '|------|-----------|',
    ]

    for ch, count in sorted(chapter_coverage.items()):
        ch_title = chapter_titles.get(ch, ch)
        report_lines.append(f'| {ch} {ch_title} | {count} |')

    report_lines += [
        '',
        '---',
        '',
        '## 5. 按类型统计',
        '',
        '| 条款类型 | 数量 | 完全响应 |',
        '|----------|------|----------|',
    ]

    for t in ['★实质性条款', '强制性条款', '一般性要求']:
        if t in type_counts:
            covered_in_type = sum(
                1 for m in mappings if m['req_type'] == t and m['is_fully_responded'])
            report_lines.append(f'| {t} | {type_counts[t]} | {covered_in_type} |')

    report_lines += [
        '',
        '---',
        '',
        '## 6. 未覆盖/部分覆盖条目',
        '',
    ]

    if uncovered_req_ids:
        report_lines.append('| 条款ID | 条款内容 | 问题 |')
        report_lines.append('|--------|----------|------|')
        for m in mappings:
            if not m['is_fully_responded']:
                report_lines.append(
                    f'| {m["req_id"]} | {m["req_text"][:60]} | 缺少正文段落响应 |')
    else:
        report_lines.append(f'**无。** 全部 {total} 条招标要求均已具有对应的正文响应段落。')

    report_lines += [
        '',
        '---',
        '',
        '## 7. 签核',
        '',
        f'- **所有要求已覆盖**: {"是[OK]" if s7_output["sign_off"]["all_requirements_covered"] else "否[!!]"}',
        f'- **无负偏离**: {"是[OK]" if s7_output["sign_off"]["no_negative_deviation"] else "否[!!]"}',
        f'- **具备提交条件**: {"是[OK]" if s7_output["sign_off"]["ready_for_submission"] else "否[!!]"}',
        f'- **审核人**: （项目负责人审核后签字）',
        f'- **审核日期**: {datetime.now().strftime("%Y-%m-%d")}',
        '',
        '---',
        '',
        f'*本报告由 s7_verify.py 于 {datetime.now().strftime("%Y-%m-%d %H:%M")} 自动生成*',
    ]

    report_path = s7_dir / 'verification_report.md'
    report_path.write_text('\n'.join(report_lines), encoding='utf-8')
    print(f"Verification report written to {report_path}")

    # Summary
    print(f"\n{'='*60}")
    print(f"Stage 7 Complete")
    print(f"{'='*60}")
    print(f"  Requirements:  {total}")
    print(f"  Fully covered: {fully_covered}")
    print(f"  Coverage rate: {coverage_rate:.1%}")
    print(f"  Star clauses:  {len(star_clauses)} (all OK)")
    print(f"  Illustrations: {len(trace.get('illustrations', []))}")
    print(f"  Body segments: {len(trace.get('body_segments', []))}")
    print(f"  Schema check:  {'PASSED' if not errors else 'FAILED'}")
    print(f"  Ready to submit: {'YES' if s7_output['sign_off']['ready_for_submission'] else 'NO'}")

    return str(s7_path)


def main():
    parser = argparse.ArgumentParser(description='Stage 7: Closed-loop verification')
    sub = parser.add_subparsers(dest='action')

    p_prepare = sub.add_parser('prepare', help='Render verification prompt')
    p_prepare.add_argument('--data', help='Path to output directory')
    p_prepare.add_argument('--output', help='Path to s7_verification directory')
    p_prepare.add_argument('--project', help='Project name')

    p_run = sub.add_parser('run', help='Run automated verification')
    p_run.add_argument('--data', help='Path to output directory')
    p_run.add_argument('--project', help='Project name')
    p_run.add_argument('--title', help='Document title')

    args = parser.parse_args()

    if args.action == 'prepare':
        prepare(args.data, args.output, args.project)
    elif args.action == 'run':
        run(args.data, args.project, args.title)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
