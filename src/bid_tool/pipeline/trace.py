#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
追溯链管理工具
用法:
  python trace.py init          # 初始化 trace.json
  python trace.py add-req ...   # 添加需求条目
  python trace.py link ...      # 建立追溯关联
  python trace.py check         # 覆盖率检查
  python trace.py lookup RQ-001 # 查询某条款的完整追溯路径
  python trace.py report        # 生成追溯报告
"""
import json, os, sys, argparse
from datetime import datetime
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent  # bid_tool/

TEMPLATE = {
    "project": "",
    "created_at": "",
    "updated_at": "",
    "requirements": [],
    "body_segments": [],
    "illustrations": [],
    "coverage": {
        "total_reqs": 0,
        "covered_reqs": 0,
        "uncovered_reqs": [],
        "coverage_rate": 0.0,
        "last_check": ""
    }
}


def _default_trace_path():
    return Path.cwd() / 'output' / 'trace.json'


def load(trace_path=None):
    path = trace_path or _default_trace_path()
    if not path.exists():
        return None
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def save(data, trace_path=None):
    path = trace_path or _default_trace_path()
    data['updated_at'] = datetime.now().isoformat()
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def cmd_init(args):
    trace_path = _default_trace_path()
    if trace_path.exists():
        print(f'[WARN] trace.json 已存在，将被覆盖')
    trace = dict(TEMPLATE)
    trace['project'] = args.project or '未命名项目'
    trace['created_at'] = datetime.now().isoformat()
    save(trace)
    print(f'[OK] trace.json 已初始化: {trace_path}')


def cmd_add_req(args):
    trace = load()
    if trace is None:
        print('[FAIL] trace.json 不存在，请先 init')
        return

    req = {
        "req_id": args.id,
        "source": args.source or "",
        "text": args.text or "",
        "type": args.type or "技术要求",
        "priority": args.priority or "mandatory",
        "analysis_id": "",
        "outline_id": "",
        "body_ids": [],
        "illustration_ids": [],
        "status": "uncovered"
    }

    # 检查是否重复
    existing = [r for r in trace['requirements'] if r['req_id'] == args.id]
    if existing:
        print(f'[WARN] {args.id} 已存在，将更新')
        trace['requirements'] = [r for r in trace['requirements'] if r['req_id'] != args.id]

    trace['requirements'].append(req)
    _recalc_coverage(trace)
    save(trace)
    print(f'[OK] 添加需求: {args.id}')


def cmd_link(args):
    """建立追溯关联: python trace.py link --req RQ-001 --body TX-3.1.1"""
    trace = load()
    if trace is None:
        print('[FAIL] trace.json 不存在')
        return

    req = next((r for r in trace['requirements'] if r['req_id'] == args.req), None)
    if req is None:
        print(f'[FAIL] 需求 {args.req} 不存在')
        return

    if args.body:
        if args.body not in req['body_ids']:
            req['body_ids'].append(args.body)
        # 同步更新 body_segments
        seg = next((s for s in trace['body_segments'] if s['body_id'] == args.body), None)
        if seg and args.req not in seg.get('covers_reqs', []):
            seg['covers_reqs'].append(args.req)

    if args.illu:
        if args.illu not in req['illustration_ids']:
            req['illustration_ids'].append(args.illu)
        illu = next((i for i in trace['illustrations'] if i['illu_id'] == args.illu), None)
        if illu and args.req not in illu.get('covers_reqs', []):
            illu['covers_reqs'].append(args.req)

    if args.outline:
        req['outline_id'] = args.outline

    if args.analysis:
        req['analysis_id'] = args.analysis

    req['status'] = 'covered' if req['body_ids'] else req['status']
    _recalc_coverage(trace)
    save(trace)
    print(f'[OK] {args.req} ← {args.body or args.illu or args.outline}')


def cmd_check(args):
    trace = load()
    if trace is None:
        print('[FAIL] trace.json 不存在')
        return

    cov = trace.get('coverage', {})
    total = len(trace['requirements'])
    uncovered = [r for r in trace['requirements'] if r['status'] != 'covered']

    print(f'\n{"="*60}')
    print(f'追溯覆盖率报告')
    print(f'{"="*60}')
    print(f'  需求总数:   {total}')
    print(f'  已覆盖:     {total - len(uncovered)}')
    print(f'  未覆盖:     {len(uncovered)}')
    print(f'  覆盖率:     {(total - len(uncovered)) / total * 100:.1f}%' if total > 0 else '  N/A')

    if uncovered:
        print(f'\n  未覆盖需求明细:')
        for r in uncovered:
            print(f'    [{r["req_id"]}] {r["text"][:70]}')
            print(f'      类型: {r["type"]} | 优先级: {r["priority"]}')
            print(f'      来源: {r["source"]}')

    # 按类型统计
    by_type = {}
    for r in trace['requirements']:
        t = r.get('type', '其他')
        by_type[t] = by_type.get(t, {'total': 0, 'covered': 0})
        by_type[t]['total'] += 1
        if r['status'] == 'covered':
            by_type[t]['covered'] += 1

    print(f'\n  按类型统计:')
    for t, stats in sorted(by_type.items()):
        print(f'    {t}: {stats["covered"]}/{stats["total"]}')

    # 按优先级统计
    by_priority = {}
    for r in trace['requirements']:
        p = r.get('priority', '未标注')
        by_priority[p] = by_priority.get(p, {'total': 0, 'covered': 0})
        by_priority[p]['total'] += 1
        if r['status'] == 'covered':
            by_priority[p]['covered'] += 1

    print(f'\n  按优先级统计:')
    for p, stats in sorted(by_priority.items()):
        status = '[PASS]' if stats['covered'] == stats['total'] else '[FAIL]'
        print(f'    {status} {p}: {stats["covered"]}/{stats["total"]}')

    if uncovered and args.strict:
        print(f'\n[FAIL] 存在未覆盖需求，严格模式阻断')
        sys.exit(1)
    elif uncovered:
        print(f'\n[WARN] 存在未覆盖需求')
    else:
        print(f'\n[PASS] 全部需求已覆盖')


def cmd_lookup(args):
    trace = load()
    if trace is None:
        print('[FAIL] trace.json 不存在')
        return

    req = next((r for r in trace['requirements'] if r['req_id'] == args.id), None)
    if req is None:
        # 尝试反向查找：从 body_id 查
        seg = next((s for s in trace['body_segments'] if s['body_id'] == args.id), None)
        if seg:
            print(f'\n  正文段落: {seg["body_id"]}')
            print(f'  章节: {seg["chapter"]}')
            print(f'  覆盖的需求:')
            for rid in seg.get('covers_reqs', []):
                r = next((x for x in trace['requirements'] if x['req_id'] == rid), None)
                if r:
                    print(f'    [{rid}] {r["text"][:60]}')
            return

        illu = next((i for i in trace['illustrations'] if i['illu_id'] == args.id), None)
        if illu:
            print(f'\n  插图: {illu["illu_id"]} - {illu["title"]}')
            print(f'  类型: {illu["type"]}')
            print(f'  覆盖的需求:')
            for rid in illu.get('covers_reqs', []):
                r = next((x for x in trace['requirements'] if x['req_id'] == rid), None)
                if r:
                    print(f'    [{rid}] {r["text"][:60]}')
            return

        print(f'[FAIL] 未找到: {args.id}')
        return

    print(f'\n{"="*60}')
    print(f'追溯路径: {args.id}')
    print(f'{"="*60}')
    print(f''
          f'  需求: {req["text"]}')
    print(f'  类型: {req["type"]} | 优先级: {req["priority"]}')
    print(f'  来源: {req["source"]}')
    print(f'  状态: {req["status"]}')
    print(f''
          f'  追溯链:')
    print(f'    分析条目: {req.get("analysis_id") or "未分配"}')
    print(f'    大纲条目: {req.get("outline_id") or "未分配"}')
    print(f'    正文段落: {req.get("body_ids") or "未关联"}')
    print(f'    插图编号: {req.get("illustration_ids") or "无"}')

    # 显示正文详情
    for bid in req.get('body_ids', []):
        seg = next((s for s in trace['body_segments'] if s['body_id'] == bid), None)
        if seg:
            print(f''
                  f'    [{bid}] {seg["chapter"]}: {seg["text_preview"][:80]}')


def cmd_report(args):
    trace = load()
    if trace is None:
        print('[FAIL] trace.json 不存在')
        return

    total = len(trace['requirements'])
    covered = sum(1 for r in trace['requirements'] if r['status'] == 'covered')

    # 生成 Markdown 报告
    lines = [
        f'# 追溯覆盖率报告',
        f'',
        f'**项目**: {trace["project"]}',
        f'**检查时间**: {datetime.now().strftime("%Y-%m-%d %H:%M")}',
        f'',
        f'## 总体情况',
        f'',
        f'| 指标 | 数值 |',
        f'|------|------|',
        f'| 需求总数 | {total} |',
        f'| 已覆盖 | {covered} |',
        f'| 未覆盖 | {total - covered} |',
        f'| 覆盖率 | {covered / total * 100:.1f}%' if total > 0 else '| 覆盖率 | N/A |',
        f'',
        f'## 未覆盖需求',
        f'',
    ]

    uncovered = [r for r in trace['requirements'] if r['status'] != 'covered']
    if uncovered:
        lines.append('| ID | 类型 | 优先级 | 需求内容 |')
        lines.append('|----|------|--------|----------|')
        for r in uncovered:
            lines.append(f'| {r["req_id"]} | {r["type"]} | {r["priority"]} | {r["text"][:50]} |')
    else:
        lines.append('无未覆盖需求。')

    lines += [
        f'',
        f'## 详细追溯表',
        f'',
        f'| 需求ID | 正文段落 | 插图 | 状态 |',
        f'|--------|----------|------|------|',
    ]
    for r in sorted(trace['requirements'], key=lambda x: x['req_id']):
        body_str = ', '.join(r.get('body_ids', [])) or '-'
        illu_str = ', '.join(r.get('illustration_ids', [])) or '-'
        status = '[OK]' if r['status'] == 'covered' else '[!!]'
        lines.append(f'| {r["req_id"]} | {body_str} | {illu_str} | {status} |')

    report = '\n'.join(lines)
    report_path = Path.cwd() / 'output' / 'coverage_report.md'
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)
    print(f'[OK] 报告已生成: {report_path}')


def _recalc_coverage(trace):
    total = len(trace['requirements'])
    uncovered = [r['req_id'] for r in trace['requirements'] if r['status'] != 'covered']
    covered = total - len(uncovered)
    trace['coverage'] = {
        'total_reqs': total,
        'covered_reqs': covered,
        'uncovered_reqs': uncovered,
        'coverage_rate': covered / total if total > 0 else 0,
        'last_check': datetime.now().isoformat()
    }


def main():
    parser = argparse.ArgumentParser(description='追溯链管理工具')
    sub = parser.add_subparsers(dest='command')

    p_init = sub.add_parser('init')
    p_init.add_argument('--project', help='项目名称')

    p_add = sub.add_parser('add-req')
    p_add.add_argument('--id', required=True)
    p_add.add_argument('--text')
    p_add.add_argument('--source')
    p_add.add_argument('--type', default='技术要求')
    p_add.add_argument('--priority', default='mandatory')

    p_link = sub.add_parser('link')
    p_link.add_argument('--req', required=True)
    p_link.add_argument('--body')
    p_link.add_argument('--illu')
    p_link.add_argument('--outline')
    p_link.add_argument('--analysis')

    p_check = sub.add_parser('check')
    p_check.add_argument('--strict', action='store_true', help='严格模式：发现未覆盖则 exit 1')

    p_lookup = sub.add_parser('lookup')
    p_lookup.add_argument('id')

    sub.add_parser('report')

    args = parser.parse_args()

    if args.command == 'init':
        cmd_init(args)
    elif args.command == 'add-req':
        cmd_add_req(args)
    elif args.command == 'link':
        cmd_link(args)
    elif args.command == 'check':
        cmd_check(args)
    elif args.command == 'lookup':
        cmd_lookup(args)
    elif args.command == 'report':
        cmd_report(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()