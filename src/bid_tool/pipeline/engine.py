#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标书撰写主控脚本
用法:
  bid-tool init --project "某项目" --workspace ~/bid-workspace
  bid-tool run -d ~/bid-workspace/某项目
  bid-tool status -d ~/bid-workspace/某项目
"""
import json, sys, argparse
from datetime import datetime
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent  # bid_tool/
PROMPTS_DIR = PACKAGE_ROOT / 'prompts'
SCHEMAS_DIR = PACKAGE_ROOT / 'schemas'

# Current project paths (resolved and cached on first use)
_paths = None


def _get_paths(project_dir=None):
    """Resolve and cache ProjectPaths for this session."""
    global _paths
    from bid_tool.workspace import resolve_project_paths
    if project_dir is not None or _paths is None:
        _paths = resolve_project_paths(project_dir)
    return _paths


def _get_output_dir(project_dir=None):
    return _get_paths(project_dir).output


def _get_trace_path(project_dir=None):
    return _get_paths(project_dir).trace


def _get_state_path(project_dir=None):
    return _get_paths(project_dir).state


# ============================================================
# 阶段定义
# ============================================================
STAGES = {
    's1': {
        'name': '招标文件解析', 'output_dir': 's1_analysis', 'prompt': 's1_parse_prompt.md',
        'artifacts': ['s1_key_info.json', 's1_veto_items.json', 's1_scoring.json', 's1_risk.json', 's1_tech_req.json'],
        'gate': {'validator': {'--stage': 's1', '--data': 's1_analysis'}, 'check': '所有5份JSON通过Schema校验'}
    },
    's2': {
        'name': '大纲设计', 'output_dir': 's2_outline', 'prompt': 's2_outline_prompt.md',
        'artifacts': ['s2_outline.json'],
        'gate': {'validator': {'--stage': 's2', '--data': 's2_outline'}, 'check': 'coverage_map覆盖率100%'}
    },
    's3': {
        'name': '正文撰写', 'output_dir': 's3_body', 'prompt': 's3_writing_prompt.md',
        'artifacts': ['s3_body.json'],
        'gate': {'validator': {'--stage': 's3', '--data': 's3_body'}, 'style_check': {'--dir': 's3_body'},
                 'check': '每章.md文件齐全，文风得分>=80'}
    },
    's4': {
        'name': '内容冻结', 'output_dir': 's4_frozen', 'prompt': None,
        'artifacts': ['frozen_approval.json'],
        'gate': {'manual': True, 'check': '人工签字确认正文内容无误'}
    },
    's5_tables': {
        'name': '表格内容规划', 'output_dir': 's5_tables', 'prompt': 's5_table_prompt.md',
        'artifacts': ['table_insertion_plan.json'],
        'gate': {'validator': {'--stage': 's5_tables', '--data': 's5_tables'}}
    },
    's5': {
        'name': '插图描述', 'output_dir': 's5_illustrations', 'prompt': 's5_illustration_prompt.md',
        'artifacts': ['s5_illustration_job.json'],
        'gate': {'validator': {'--stage': 's5', '--data': 's5_illustrations'}}
    },
    's6': {
        'name': '图文合成', 'output_dir': 's6_synthesis', 'prompt': None,
        'artifacts': ['s6_synthesis_report.json', 's6_combined_bid_document.md'],
        'gate': {'manual': True, 'check': '所有插图占位已替换，图文编号一致'}
    },
    's7': {
        'name': '闭环校验', 'output_dir': 's7_verification', 'prompt': 's7_verify_prompt.md',
        'artifacts': ['s7_trace_matrix.json', 'verification_report.md'],
        'gate': {'validator': {'--stage': 's7', '--data': 's7_verification'},
                 'coverage': {'--check-coverage': True, '--trace': 'trace.json'}}
    },
    's8': {
        'name': '最终导出', 'output_dir': 's8_final', 'prompt': None,
        'artifacts': ['投标文件-终稿.docx'],
        'gate': {'manual': True, 'check': 'Word格式正确，页码目录更新'}
    },
    's9': {
        'name': '技术偏离表填写', 'output_dir': 's9_deviation', 'prompt': None,
        'artifacts': ['s9_summaries.json', 's9_bookmark_map.json', 's9_page_numbers.json', 's9_run_report.json'],
        'gate': {'manual': True, 'check': '所有偏离项填写完毕'}
    }
}

STAGE_ORDER = ['s1', 's2', 's3', 's4', 's5_tables', 's5', 's6', 's7', 's8', 's9']


# ============================================================
# 状态管理
# ============================================================
def load_state(project_dir=None):
    state_path = _get_state_path(project_dir)
    if state_path.exists():
        with open(state_path, 'r', encoding='utf-8') as f:
            state = json.load(f)
        state.setdefault('stages', {})
        for stage in STAGE_ORDER:
            state['stages'].setdefault(stage, {'status': 'pending', 'completed_at': None, 'gate_pass': None})
        return state
    return {
        'project': '', 'current_stage': None,
        'stages': {s: {'status': 'pending', 'completed_at': None, 'gate_pass': None} for s in STAGE_ORDER},
        'created_at': datetime.now().isoformat(), 'updated_at': datetime.now().isoformat()
    }


def save_state(state, project_dir=None):
    state['updated_at'] = datetime.now().isoformat()
    out = _get_output_dir(project_dir)
    out.mkdir(parents=True, exist_ok=True)
    with open(_get_state_path(project_dir), 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def mark_stage(state, stage, status, gate_pass=None, project_dir=None):
    state['stages'][stage]['status'] = status
    if status == 'completed':
        state['stages'][stage]['completed_at'] = datetime.now().isoformat()
    if gate_pass is not None:
        state['stages'][stage]['gate_pass'] = gate_pass
    state['current_stage'] = stage
    save_state(state, project_dir)
    try:
        from bid_tool.context_writer import record_stage_complete, update_status_snapshot
        paths = _get_paths(project_dir)
        if status == 'completed':
            gs = "PASS" if gate_pass else ("FAIL" if gate_pass is False else "人工确认")
            record_stage_complete(paths.context, stage, gs)
        update_status_snapshot(paths.context, {s: st['status'] for s, st in state['stages'].items()})
    except Exception:
        pass


# ============================================================
# 门禁执行
# ============================================================
def run_gate(stage, state, verbose=False, project_dir=None):
    gate_config = STAGES[stage]['gate']
    output_dir = _get_output_dir(project_dir)

    print(f'\n{"="*60}')
    print(f'[GATE] 阶段 {stage} — {STAGES[stage]["name"]} 门禁检查')
    print(f'{"="*60}')

    if gate_config.get('manual'):
        print(f'[MANUAL] 此阶段需人工确认: {gate_config["check"]}')
        return None

    all_pass = True

    # S3 collect
    if stage == 's3':
        from .stages.s3_body import collect as s3_collect
        data_dir = output_dir / 's3_body'
        plan_path = data_dir / 's3_plan.json'
        if plan_path.exists() and not (data_dir / 's3_body.json').exists():
            print(f'\n[COLLECT] 收集群组 manifest -> s3_body.json')
            s3_collect(str(data_dir))

    # Schema validation
    if 'validator' in gate_config:
        from .validator import validate_stage
        v_args = gate_config['validator']
        data_dir = output_dir / v_args['--data']
        if not data_dir.exists():
            print(f'[FAIL] 产物目录不存在: {data_dir}')
            return False
        if not validate_stage(v_args['--stage'], str(data_dir)):
            all_pass = False

    # Style check
    if 'style_check' in gate_config:
        from .style_check import check_file, check_text, print_result, _extract_text_from_json
        import json as _json
        data_dir = output_dir / gate_config['style_check']['--dir']
        if data_dir.exists():
            results = []
            for f in sorted(data_dir.glob('ch_*.md')):
                results.append(check_file(str(f)))
            for f in sorted((output_dir / 's3_body').glob('ch_*.md')):
                if str(f) not in [r.get('file', '') for r in results if isinstance(r, dict)]:
                    results.append(check_file(str(f)))
            if not results:
                print(f'[INFO] 暂无正文产物可检查')
            else:
                total_score = sum(r['score'] for r in results)
                avg_score = total_score / len(results) if results else 0
                for r in results:
                    print_result(r, verbose=verbose)
                    if not r['gate_pass']:
                        all_pass = False
                if avg_score < 80:
                    print(f'[FAIL] 平均文风得分 {avg_score:.1f} < 80')
                    all_pass = False

    # Coverage check
    if 'coverage' in gate_config:
        from .validator import check_coverage
        cov_args = gate_config['coverage']
        trace_path = output_dir / cov_args['--trace'] if cov_args.get('--trace') else None
        if trace_path and trace_path.exists():
            if not check_coverage(str(trace_path)):
                all_pass = False
        else:
            print(f'[FAIL] trace.json 不存在: {trace_path}')
            all_pass = False

    if all_pass:
        print(f'\n[GATE PASS] 阶段 {stage} 门禁全部通过')
    else:
        print(f'\n[GATE FAIL] 阶段 {stage} 门禁未通过')
    return all_pass


# ============================================================
# 运行阶段
# ============================================================
def _run_stage_prepare(stage, out_dir, state, project_dir=None):
    output_root = _get_output_dir(project_dir)
    project_name = state.get('project', '')

    if stage == 's1':
        tender_candidates = list(output_root.glob('*.md')) + list(output_root.glob('*.txt'))
        # Also check project tender dir
        paths = _get_paths(project_dir)
        tender_candidates += list(paths.tender.glob('*.md')) + list(paths.tender.glob('*.txt'))
        if tender_candidates:
            from .stages.s1_parse import prepare as s1_prepare
            s1_prepare(str(tender_candidates[0]), str(out_dir), project_name)
        else:
            print('[INFO] 请将招标文件 (.md/.txt) 放入 tender/ 目录')
    elif stage == 's2':
        from .stages.s2_outline import prepare as s2_prepare
        s2_prepare(str(output_root / 's1_analysis'), str(out_dir), project_name)
    elif stage == 's3':
        from .stages.s3_body import prepare as s3_prepare
        s3_prepare(str(output_root / 's1_analysis'), str(output_root / 's2_outline'), str(out_dir), project_name)
    elif stage == 's5_tables':
        from .stages.s5_tables import prepare as s5t_prepare
        s5t_prepare(str(output_root / 's1_analysis'), str(output_root / 's2_outline'),
                    str(output_root / 's3_body'), str(out_dir), project_name)
    elif stage == 's5':
        from .stages.s5_illustrate import prepare as s5_prepare
        s5_prepare(str(output_root / 's3_body'), str(out_dir), project_name, str(output_root / 's5_tables'))
    elif stage == 's7':
        from .stages.s7_verify import prepare as s7_prepare
        s7_prepare(str(output_root), str(out_dir), project_name)


def _run_script_stage(stage, out_dir, state, project_dir=None):
    output_root = _get_output_dir(project_dir)
    if stage == 's6':
        from .stages.s6_synthesize import render_v2_job, synthesize
        s5_dir = output_root / 's5_illustrations'
        images_dir = s5_dir / 'images'
        manifest_path = render_v2_job(s5_dir=s5_dir, images_dir=images_dir, png=True, png_scale=3, export_echarts=False)
        synthesize(s3_chapters_dir=output_root / 's3_body' / 'chapters', s6_dir=out_dir,
                   toolkit_results_dir=images_dir, manifest_path=manifest_path,
                   table_plan_path=output_root / 's5_tables' / 'table_insertion_plan.json')
        return True
    return False


def run_stage(stage, state, skip_gate=False, verbose=False, project_dir=None):
    stage_info = STAGES[stage]
    print(f'\n{"#"*60}')
    print(f'# 阶段 {stage}: {stage_info["name"]}')
    print(f'# 输出: {stage_info["output_dir"]}/')
    print(f'{"#"*60}')

    try:
        from bid_tool.context_writer import record_stage_start
        paths = _get_paths(project_dir)
        record_stage_start(paths.context, stage, stage_info['name'])
    except Exception:
        pass

    output_dir = _get_output_dir(project_dir)
    out_dir = output_dir / stage_info['output_dir']
    out_dir.mkdir(parents=True, exist_ok=True)

    prompt_path = PROMPTS_DIR / stage_info['prompt'] if stage_info['prompt'] else None

    if prompt_path:
        print(f'\n[PROMPT] 准备阶段 {stage} 的 LLM 提示词...')
        print(f'[OUTPUT] 产物路径: {out_dir}/')
        try:
            _run_stage_prepare(stage, out_dir, state, project_dir)
        except Exception as e:
            print(f'[WARN] 阶段 {stage} prepare 执行失败: {e}')
        print(f'\n完成 LLM 调用后运行: bid-tool gate {stage} --continue')
        mark_stage(state, stage, 'in_progress', project_dir=project_dir)
        return False
    else:
        print(f'\n[MANUAL] 此阶段为人工/脚本化操作')
        try:
            if _run_script_stage(stage, out_dir, state, project_dir):
                print(f'[DONE] 阶段 {stage} 脚本执行完成')
                mark_stage(state, stage, 'in_progress', project_dir=project_dir)
                return True
        except Exception as e:
            print(f'[WARN] 阶段 {stage} 脚本执行失败: {e}')
        mark_stage(state, stage, 'in_progress', project_dir=project_dir)
        return False


def continue_stage(stage, state, verbose=False, project_dir=None):
    gate_result = run_gate(stage, state, verbose, project_dir)
    if gate_result is None:
        print(f'\n[ACTION] 请确认阶段 {stage} 完成后运行: bid-tool gate {stage} --confirm')
        return False
    elif gate_result is True:
        mark_stage(state, stage, 'completed', gate_pass=True, project_dir=project_dir)
        return True
    else:
        print(f'\n[BLOCKED] 阶段 {stage} 门禁未通过')
        return False


def confirm_manual_stage(stage, state, project_dir=None):
    if not STAGES[stage]['gate'].get('manual'):
        print(f'[ERROR] 阶段 {stage} 不是人工确认阶段')
        return False
    print(f'\n[CONFIRM] 确认阶段 {stage} 已完成')
    mark_stage(state, stage, 'completed', gate_pass=True, project_dir=project_dir)
    return True


# ============================================================
# 全流程运行
# ============================================================
def run_pipeline(start_from='s1', end_at='s8', skip_gate=False, yes=False, verbose=False, project_dir=None):
    state = load_state(project_dir)
    started = False
    for stage in STAGE_ORDER:
        if not started and stage != start_from:
            continue
        started = True
        if state['stages'][stage]['status'] == 'completed':
            print(f'[SKIP] 阶段 {stage} 已完成，跳过')
            continue
        run_stage(stage, state, skip_gate, verbose, project_dir)
        gate_config = STAGES[stage]['gate']
        if gate_config.get('manual'):
            if yes:
                confirm_manual_stage(stage, state, project_dir)
            else:
                print(f'\n[WAIT] 阶段 {stage} 需要人工确认: bid-tool gate {stage} --confirm')
                return
        else:
            if run_gate(stage, state, verbose, project_dir):
                mark_stage(state, stage, 'completed', gate_pass=True, project_dir=project_dir)
            else:
                print(f'\n[BLOCKED] 流程在阶段 {stage} 阻塞: bid-tool run --from {stage}')
                return
        if stage == end_at:
            break
    print(f'\n{"="*60}')
    print(f'[PIPELINE] 流程执行完毕')
    print_status(state)


def print_status(state):
    print(f'\n项目: {state.get("project", "未设置")}')
    print(f'更新时间: {state.get("updated_at", "未知")}')
    print(f'\n{"阶段":<8} {"状态":<14} {"门禁":<10} {"完成时间"}')
    print(f'{"-"*60}')
    for s in STAGE_ORDER:
        info = state['stages'][s]
        icon = {'pending': '[ ]', 'in_progress': '[>]', 'completed': '[X]', 'failed': '[!]'}.get(info['status'], '[?]')
        gi = {None: '--', True: 'PASS', False: 'FAIL'}.get(info['gate_pass'], '--')
        print(f'{icon} {s:<5} {info["status"]:<14} {gi:<10} {info.get("completed_at", "") or "--"}')


# ============================================================
# CLI 入口
# ============================================================
def _add_project_dir_arg(parser):
    parser.add_argument('--project-dir', '-d', help='项目目录路径')


def cmd_status(args):
    state = load_state(getattr(args, 'project_dir', None))
    paths = _get_paths(getattr(args, 'project_dir', None))
    print(f'\n项目目录: {paths.root}')
    print_status(state)


def cmd_run(args):
    pd = getattr(args, 'project_dir', None)
    start = args.start_from or 's1'
    end = args.end_at or 's8'
    if args.stage:
        start = args.stage; end = args.stage
    run_pipeline(start, end, args.skip_gate, args.yes, args.verbose, pd)


def cmd_gate(args):
    pd = getattr(args, 'project_dir', None)
    state = load_state(pd)
    stage = args.stage
    if stage not in STAGES:
        print(f'[FAIL] 未知阶段: {stage}'); sys.exit(1)
    if args.confirm:
        if confirm_manual_stage(stage, state, pd):
            idx = STAGE_ORDER.index(stage)
            if idx + 1 < len(STAGE_ORDER):
                ns = STAGE_ORDER[idx + 1]
                print(f'\n[NEXT] 下一阶段: {ns} — {STAGES[ns]["name"]}')
                run_stage(ns, state, args.skip_gate, args.verbose, pd)
    elif args.continue_:
        if continue_stage(stage, state, args.verbose, pd):
            idx = STAGE_ORDER.index(stage)
            if idx + 1 < len(STAGE_ORDER):
                ns = STAGE_ORDER[idx + 1]
                print(f'\n[NEXT] 下一阶段: {ns} — {STAGES[ns]["name"]}')
                run_stage(ns, state, args.skip_gate, args.verbose, pd)
    else:
        run_gate(stage, state, args.verbose, pd)


def cmd_init(args):
    pd = getattr(args, 'project_dir', None)
    ws = getattr(args, 'workspace', None)
    pt = getattr(args, 'profile_type', 'software')
    tender = getattr(args, 'tender', None)

    if ws or pd:
        from bid_tool.workspace import init_project
        name = args.project or '未命名项目'
        paths = init_project(workspace=ws or pd, project_name=name, profile_type=pt, tender_path=tender)
        print(f'[OK] 项目已创建: {paths.root}')
        print(f'  产出目录: {paths.output}')
        print(f'  招标文件: {paths.tender}')
        print(f'  上下文:   {paths.context}')
        print(f'[INFO] 下一步: bid-tool run -d {paths.root}')
        return

    # Legacy: cwd/output
    state = load_state()
    state['project'] = args.project or '未命名项目'
    state['created_at'] = datetime.now().isoformat()
    trace_path = _get_trace_path()
    if not trace_path.exists():
        from .trace import TEMPLATE, save
        trace = dict(TEMPLATE)
        trace['project'] = state['project']
        trace['created_at'] = datetime.now().isoformat()
        save(trace)
    save_state(state)
    print(f'[OK] Pipeline 已初始化: {state["project"]}')
    print(f'[WARN] 使用 cwd/output 模式。建议迁移: bid-tool init --project "项目名" --workspace ~/bid-workspace')


def main():
    parser = argparse.ArgumentParser(description='bid-tool — 标书撰写主控脚本')
    sub = parser.add_subparsers(dest='command')

    p_init = sub.add_parser('init', help='初始化新项目')
    p_init.add_argument('--project', help='项目名称')
    p_init.add_argument('--workspace', '-w', help='工作空间目录 (默认 ~/bid-workspace)')
    p_init.add_argument('--profile-type', choices=['software', 'construction'], default='software')
    p_init.add_argument('--tender', help='招标文件路径')
    _add_project_dir_arg(p_init)

    p_status = sub.add_parser('status', help='查看各阶段状态')
    _add_project_dir_arg(p_status)

    p_run = sub.add_parser('run', help='运行流程')
    p_run.add_argument('--from', dest='start_from')
    p_run.add_argument('--end-at'); p_run.add_argument('--stage')
    p_run.add_argument('--skip-gate', action='store_true')
    p_run.add_argument('--yes', '-y', action='store_true')
    p_run.add_argument('--verbose', '-v', action='store_true')
    _add_project_dir_arg(p_run)

    p_gate = sub.add_parser('gate', help='门禁管理')
    p_gate.add_argument('stage')
    p_gate.add_argument('--continue', dest='continue_', action='store_true')
    p_gate.add_argument('--confirm', action='store_true')
    p_gate.add_argument('--skip-gate', action='store_true')
    p_gate.add_argument('--verbose', '-v', action='store_true')
    _add_project_dir_arg(p_gate)

    args = parser.parse_args()
    if args.command == 'init': cmd_init(args)
    elif args.command == 'status': cmd_status(args)
    elif args.command == 'run': cmd_run(args)
    elif args.command == 'gate': cmd_gate(args)
    else: parser.print_help()


if __name__ == '__main__':
    main()
