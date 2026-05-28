#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
标书撰写主控脚本
用法:
  python pipeline.py run              # 运行全流程
  python pipeline.py run --from s2    # 从阶段2开始
  python pipeline.py run --stage s3   # 仅运行阶段3
  python pipeline.py status           # 查看各阶段状态
  python pipeline.py gate s3          # 手动执行阶段3的门禁检查
"""
import json, sys, argparse
from datetime import datetime
from pathlib import Path

PACKAGE_ROOT = Path(__file__).resolve().parent.parent  # bid_tool/
PROMPTS_DIR = PACKAGE_ROOT / 'prompts'
SCHEMAS_DIR = PACKAGE_ROOT / 'schemas'


def _get_output_dir():
    return Path.cwd() / 'output'


def _get_trace_path():
    return _get_output_dir() / 'trace.json'


def _get_state_path():
    return _get_output_dir() / 'pipeline_state.json'

# ============================================================
# 阶段定义
# ============================================================
STAGES = {
    's1': {
        'name': '招标文件解析',
        'description': '从招标文件提取关键信息、一票否决项、评分标准、风险、技术需求',
        'input': '原始招标文件（.doc/.docx/.md）',
        'output_dir': 's1_analysis',
        'prompt': 's1_parse_prompt.md',
        'artifacts': [
            's1_key_info.json', 's1_veto_items.json', 's1_scoring.json',
            's1_risk.json', 's1_tech_req.json'
        ],
        'gate': {
            'validator': {'--stage': 's1', '--data': 'output/s1_analysis'},
            'check': '所有5份JSON通过Schema校验，必填字段非空'
        }
    },
    's2': {
        'name': '大纲设计',
        'description': '设计对标评分标准的技术方案章节大纲',
        'input': '阶段1全部输出',
        'output_dir': 's2_outline',
        'prompt': 's2_outline_prompt.md',
        'artifacts': ['s2_outline.json'],
        'gate': {
            'validator': {'--stage': 's2', '--data': 'output/s2_outline'},
            'check': 'outline通过Schema校验，coverage_map覆盖率100%，uncovered_reqs为空'
        }
    },
    's3': {
        'name': '正文撰写',
        'description': '按大纲逐章撰写去AI化正文，每章独立 .md 文件',
        'input': '阶段1+阶段2全部输出',
        'output_dir': 's3_body',
        'prompt': 's3_writing_prompt.md',
        'artifacts': ['s3_body.json', 'ch_01.md', 'ch_02.md', 'ch_03.md', 'ch_04.md',
                      'ch_05.md', 'ch_06.md', 'ch_07.md', 'ch_08.md', 'ch_09.md',
                      'ch_10.md', 'ch_11.md', 'ch_12.md', 'ch_13.md'],
        'gate': {
            'validator': {'--stage': 's3', '--data': 'output/s3_body'},
            'style_check': {'--dir': 'output/s3_body'},
            'check': '每章 .md 文件齐全，manifest.json 通过 Schema 校验，文风得分>=80，禁用词<=5'
        }
    },
    's4': {
        'name': '内容冻结',
        'description': '人工审核确认正文，冻结后不可修改',
        'input': '阶段3输出',
        'output_dir': 's4_frozen',
        'prompt': None,
        'artifacts': ['frozen_approval.json'],
        'gate': {
            'manual': True,
            'check': '人工签字确认：正文内容无误，文风达标，可进入图示化阶段'
        }
    },
    's5': {
        'name': '插图描述',
        'description': '为所有插图占位生成结构化描述',
        'input': '阶段3正文+illustration_manifest',
        'output_dir': 's5_illustrations',
        'prompt': 's5_illustration_prompt.md',
        'artifacts': ['s5_illustration.json'],
        'gate': {
            'validator': {'--stage': 's5', '--data': 'output/s5_illustrations'},
            'check': '插图文案通过Schema校验，illu_id覆盖所有manifest中的ID'
        }
    },
    's6': {
        'name': '图文合成',
        'description': '将插图嵌入正文，生成完整标书草稿',
        'input': '阶段4冻结稿+阶段5插图',
        'output_dir': 's6_synthesis',
        'prompt': None,
        'artifacts': ['synthesis_report.json', 'draft_full.md'],
        'gate': {
            'manual': True,
            'check': '所有插图占位已替换，图文编号一致，页码连续'
        }
    },
    's7': {
        'name': '闭环校验',
        'description': '生成评分标准-投标响应一一对应对照表',
        'input': '全部前序产物',
        'output_dir': 's7_verification',
        'prompt': 's7_verify_prompt.md',
        'artifacts': ['s7_trace_matrix.json', 'verification_report.md'],
        'gate': {
            'validator': {'--stage': 's7', '--data': 'output/s7_verification'},
            'coverage': {'--check-coverage': True, '--trace': 'output/trace.json'},
            'check': 'trace_matrix通过Schema校验，coverage>=95%，★条款100%响应'
        }
    },
    's8': {
        'name': '最终导出',
        'description': '生成Word/PDF格式的最终投标文件',
        'input': '阶段6合成稿+阶段7校验通过',
        'output_dir': 's8_final',
        'prompt': None,
        'artifacts': ['投标文件-终稿.docx'],
        'gate': {
            'manual': True,
            'check': 'Word格式正确，页码目录更新，签字盖章位置正确'
        }
    },
    's9': {
        'name': '技术偏离表填写',
        'description': '自动提取响应摘要，填写报价文件偏离表，插入交叉引用',
        'input': '阶段3正文 + 报价文件模板DOCX',
        'output_dir': 's9_deviation',
        'prompt': None,  # 脚本驱动，无需 LLM
        'artifacts': [
            's9_summaries.json',
            's9_bookmark_map.json',
            's9_page_numbers.json',
            's9_run_report.json'
        ],
        'gate': {
            'manual': True,
            'script': 'python scripts/s9_fill_deviation.py --formal-doc <报价文件.docx> --dry-run',
            'check': '所有偏离项填写完毕，响应摘要全员非空，偏离情况全部正确'
        }
    }
}

STAGE_ORDER = ['s1', 's2', 's3', 's4', 's5', 's6', 's7', 's8', 's9']


# ============================================================
# 状态管理
# ============================================================
def load_state():
    state_path = _get_state_path()
    if state_path.exists():
        with open(state_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {
        'project': '',
        'current_stage': None,
        'stages': {s: {'status': 'pending', 'completed_at': None, 'gate_pass': None}
                   for s in STAGE_ORDER},
        'created_at': datetime.now().isoformat(),
        'updated_at': datetime.now().isoformat()
    }


def save_state(state):
    state['updated_at'] = datetime.now().isoformat()
    output_dir = _get_output_dir()
    output_dir.mkdir(parents=True, exist_ok=True)
    with open(_get_state_path(), 'w', encoding='utf-8') as f:
        json.dump(state, f, ensure_ascii=False, indent=2)


def mark_stage(state, stage, status, gate_pass=None):
    state['stages'][stage]['status'] = status
    if status == 'completed':
        state['stages'][stage]['completed_at'] = datetime.now().isoformat()
    if gate_pass is not None:
        state['stages'][stage]['gate_pass'] = gate_pass
    state['current_stage'] = stage
    save_state(state)


# ============================================================
# 门禁执行
# ============================================================
def run_gate(stage, state, verbose=False):
    """执行指定阶段的门禁检查"""
    gate_config = STAGES[stage]['gate']

    print(f'\n{"="*60}')
    print(f'[GATE] 阶段 {stage} — {STAGES[stage]["name"]} 门禁检查')
    print(f'{"="*60}')

    if gate_config.get('manual'):
        print(f'[MANUAL] 此阶段需人工确认: {gate_config["check"]}')
        return None  # 返回 None 表示需要人工判断

    all_pass = True

    # 0. S3 special: collect group manifests into unified s3_body.json
    if stage == 's3':
        from .stages.s3_body import collect as s3_collect
        data_dir = Path.cwd() / 'output' / 's3_body'
        plan_path = data_dir / 's3_plan.json'
        if plan_path.exists() and not (data_dir / 's3_body.json').exists():
            print(f'\n[COLLECT] 收集群组 manifest → s3_body.json')
            s3_collect(str(data_dir))
        elif plan_path.exists():
            print(f'[INFO] s3_body.json 已存在，跳过 collect。如需重新收集请先删除 s3_body.json')

    # 1. Schema 校验
    if 'validator' in gate_config:
        from .validator import validate_stage
        v_args = gate_config['validator']
        data_dir = Path.cwd() / v_args['--data']
        if not data_dir.exists():
            print(f'[FAIL] 产物目录不存在: {data_dir}')
            return False

        if not validate_stage(v_args['--stage'], str(data_dir)):
            all_pass = False

    # 2. 文风检查（仅检查正文产物，排除提示词文件）
    if 'style_check' in gate_config:
        from .style_check import check_file, check_text, print_result, _extract_text_from_json
        import json as _json
        data_dir = Path.cwd() / gate_config['style_check']['--dir']
        if data_dir.exists():
            results = []
            # Only check chapter .md files and the unified manifest
            for f in sorted(data_dir.glob('ch_*.md')):
                results.append(check_file(str(f)))
            manifest_path = data_dir / 's3_body.json'
            if manifest_path.exists():
                with open(manifest_path, 'r', encoding='utf-8') as fh:
                    data = _json.load(fh)
                text = _extract_text_from_json(data)
                if text:
                    results.append(check_text(text, 's3_body.json'))
            # If no chapter files yet, check manifests
            if not results:
                for f in sorted(data_dir.glob('*_manifest.json')):
                    results.append(check_file(str(f)))
            if not results:
                print(f'[INFO] 暂无正文产物可检查（ch_*.md 或 *_manifest.json）')
            else:
                total_score = 0
                for r in results:
                    print_result(r, verbose=verbose)
                    total_score += r['score']
                    if not r['gate_pass']:
                        all_pass = False
                avg_score = total_score / len(results)
                if avg_score < 80:
                    print(f'[FAIL] 平均文风得分 {avg_score:.1f} < 80')
                    all_pass = False

    # 3. 覆盖率检查
    if 'coverage' in gate_config:
        from .validator import check_coverage
        cov_args = gate_config['coverage']
        trace_path = Path.cwd() / cov_args['--trace'] if cov_args.get('--trace') else None
        if trace_path and trace_path.exists():
            if not check_coverage(str(trace_path)):
                all_pass = False
        else:
            print(f'[FAIL] trace.json 不存在: {trace_path}')
            all_pass = False

    # 4. Gate summary
    if all_pass:
        print(f'\n[GATE PASS] 阶段 {stage} 门禁全部通过')
        print(f'  检查内容: {gate_config["check"]}')
    else:
        print(f'\n[GATE FAIL] 阶段 {stage} 门禁未通过')
        print(f'  检查内容: {gate_config["check"]}')

    return all_pass


# ============================================================
# 运行阶段
# ============================================================

def _run_stage_prepare(stage, out_dir, state):
    """Call stage-specific prepare function to render LLM prompt with context."""
    output_root = _get_output_dir()
    project_name = state.get('project', '')

    if stage == 's1':
        # S1 requires a tender document path (check output dir for tender doc)
        tender_candidates = list(output_root.glob('*.md')) + list(output_root.glob('*.txt'))
        if tender_candidates:
            from .stages.s1_parse import prepare as s1_prepare
            s1_prepare(str(tender_candidates[0]), str(out_dir), project_name)
        else:
            print('[INFO] 请将招标文件 (.md/.txt) 放入 output/ 目录，然后运行:')
            print(f'  python -m bid_tool.pipeline.stages.s1_parse prepare --tender <招标文件> --output {out_dir}')

    elif stage == 's2':
        s1_dir = output_root / 's1_analysis'
        from .stages.s2_outline import prepare as s2_prepare
        s2_prepare(str(s1_dir), str(out_dir), project_name)

    elif stage == 's3':
        s1_dir = output_root / 's1_analysis'
        s2_dir = output_root / 's2_outline'
        from .stages.s3_body import prepare as s3_prepare
        s3_prepare(str(s1_dir), str(s2_dir), str(out_dir), project_name)

    elif stage == 's5':
        s3_dir = output_root / 's3_body'
        from .stages.s5_illustrate import prepare as s5_prepare
        s5_prepare(str(s3_dir), str(out_dir), project_name)

    elif stage == 's7':
        from .stages.s7_verify import prepare as s7_prepare
        s7_prepare(str(output_root), str(out_dir), project_name)


def run_stage(stage, state, skip_gate=False, verbose=False):
    """运行单个阶段"""
    stage_info = STAGES[stage]
    print(f'\n{"#"*60}')
    print(f'# 阶段 {stage}: {stage_info["name"]}')
    print(f'# 输入: {stage_info["input"]}')
    print(f'# 输出: {stage_info["output_dir"]}/')
    print(f'{"#"*60}')

    # 检查输出目录
    output_dir = _get_output_dir()
    out_dir = output_dir / stage_info['output_dir']
    out_dir.mkdir(parents=True, exist_ok=True)

    # 检查是否有 prompt 模板
    if stage_info['prompt']:
        prompt_path = PROMPTS_DIR / stage_info['prompt']
        if not prompt_path.exists():
            print(f'[WARN] Prompt 模板不存在: {prompt_path}')
    else:
        prompt_path = None

    # 此阶段需要 LLM 执行
    if prompt_path:
        print(f'\n[PROMPT] 准备阶段 {stage} 的 LLM 提示词...')
        print(f'  模板: {prompt_path}')
        print(f'[OUTPUT] 产物路径: {out_dir}/')
        print(f'[OUTPUT] 预期文件: {stage_info["artifacts"]}')

        # Call stage-specific prepare function
        try:
            _run_stage_prepare(stage, out_dir, state)
        except Exception as e:
            print(f'[WARN] 阶段 {stage} prepare 执行失败: {e}')
            print(f'[INFO] 请手动使用提示词模板: {prompt_path}')

        print(f'\n完成 LLM 调用后，将产物保存到上述路径。')
        print(f'然后运行: bid-tool gate {stage} --continue')
        mark_stage(state, stage, 'in_progress')
        return False  # 返回 False 表示等待 LLM 完成
    else:
        print(f'\n[MANUAL] 此阶段为人工/脚本化操作，不需要 LLM 参与')
        print(f'[INFO] 完成后运行: python pipeline.py gate {stage} --continue')
        mark_stage(state, stage, 'in_progress')
        return False


def continue_stage(stage, state, verbose=False):
    """门禁通过后继续到下一阶段"""
    gate_result = run_gate(stage, state, verbose)

    if gate_result is None:
        # 人工确认阶段
        print(f'\n[ACTION] 请确认阶段 {stage} 完成后，运行:')
        print(f'  python pipeline.py gate {stage} --confirm')
        return False
    elif gate_result is True:
        mark_stage(state, stage, 'completed', gate_pass=True)
        print(f'\n[DONE] 阶段 {stage} 完成')
        return True
    else:
        print(f'\n[BLOCKED] 阶段 {stage} 门禁未通过，请修复后重新运行 gate')
        return False


def confirm_manual_stage(stage, state):
    """确认人工阶段"""
    gate_config = STAGES[stage]['gate']
    if not gate_config.get('manual'):
        print(f'[ERROR] 阶段 {stage} 不是人工确认阶段')
        return False

    print(f'\n[CONFIRM] 确认阶段 {stage} 已完成？')
    print(f'  检查项: {gate_config["check"]}')
    # 此处接受命令行 --yes 参数自动确认
    mark_stage(state, stage, 'completed', gate_pass=True)
    print(f'[DONE] 阶段 {stage} 人工确认完成')
    return True


# ============================================================
# 全流程运行
# ============================================================
def run_pipeline(start_from='s1', end_at='s8', skip_gate=False, yes=False, verbose=False):
    """运行全部或部分流程"""
    state = load_state()
    started = False

    for stage in STAGE_ORDER:
        if not started and stage != start_from:
            continue
        started = True

        stage_info = STAGES[stage]
        current_status = state['stages'][stage]['status']

        if current_status == 'completed':
            print(f'[SKIP] 阶段 {stage} 已完成，跳过')
            continue

        # 运行阶段
        run_stage(stage, state, skip_gate, verbose)

        # 执行门禁（自动阶段）
        gate_config = stage_info['gate']
        if gate_config.get('manual'):
            if yes:
                confirm_manual_stage(stage, state)
            else:
                print(f'\n[WAIT] 阶段 {stage} 需要人工确认，请检查产物后运行:')
                print(f'  python pipeline.py gate {stage} --confirm')
                return
        else:
            gate_result = run_gate(stage, state, verbose)
            if gate_result:
                mark_stage(state, stage, 'completed', gate_pass=True)
            else:
                print(f'\n[BLOCKED] 流程在阶段 {stage} 阻塞，请修复后继续')
                print(f'  修复后运行: python pipeline.py run --from {stage}')
                return

        if stage == end_at:
            break

    print(f'\n{"="*60}')
    print(f'[PIPELINE] 流程执行完毕')
    print_status(state)


# ============================================================
# 状态展示
# ============================================================
def print_status(state):
    print(f'\n项目: {state.get("project", "未设置")}')
    print(f'更新时间: {state.get("updated_at", "未知")}')
    print(f'\n{"阶段":<8} {"状态":<14} {"门禁":<10} {"完成时间"}')
    print(f'{"-"*60}')
    for s in STAGE_ORDER:
        info = state['stages'][s]
        status_icon = {
            'pending': '[ ]',
            'in_progress': '[>]',
            'completed': '[X]',
            'failed': '[!]'
        }.get(info['status'], '[?]')

        gate_icon = {
            None: '--',
            True: 'PASS',
            False: 'FAIL'
        }.get(info['gate_pass'], '--')

        completed = info.get('completed_at', '') or '--'
        print(f'{status_icon} {s:<5} {info["status"]:<14} {gate_icon:<10} {completed}')


def cmd_status(args):
    state = load_state()
    print_status(state)


def cmd_run(args):
    start = args.start_from or 's1'
    end = args.end_at or 's8'
    if args.stage:
        start = args.stage
        end = args.stage
    run_pipeline(start, end, args.skip_gate, args.yes, args.verbose)


def cmd_gate(args):
    state = load_state()
    stage = args.stage

    if stage not in STAGES:
        print(f'[FAIL] 未知阶段: {stage}')
        sys.exit(1)

    if args.confirm:
        if confirm_manual_stage(stage, state):
            # 自动推进到下一阶段
            idx = STAGE_ORDER.index(stage)
            if idx + 1 < len(STAGE_ORDER):
                next_stage = STAGE_ORDER[idx + 1]
                print(f'\n[NEXT] 下一阶段: {next_stage} — {STAGES[next_stage]["name"]}')
                run_stage(next_stage, state, args.skip_gate, args.verbose)
    elif args.continue_:
        if continue_stage(stage, state, args.verbose):
            # 自动推进到下一阶段
            idx = STAGE_ORDER.index(stage)
            if idx + 1 < len(STAGE_ORDER):
                next_stage = STAGE_ORDER[idx + 1]
                print(f'\n[NEXT] 下一阶段: {next_stage} — {STAGES[next_stage]["name"]}')
                run_stage(next_stage, state, args.skip_gate, args.verbose)
    else:
        run_gate(stage, state, args.verbose)


def cmd_init(args):
    """初始化新项目的 pipeline"""
    state = load_state()
    state['project'] = args.project or '未命名项目'
    state['created_at'] = datetime.now().isoformat()

    # 初始化 trace.json
    trace_path = _get_trace_path()
    if not trace_path.exists():
        from .trace import TEMPLATE, save
        trace = dict(TEMPLATE)
        trace['project'] = state['project']
        trace['created_at'] = datetime.now().isoformat()
        save(trace)
        print(f'[OK] trace.json 已初始化')

    save_state(state)
    print(f'[OK] Pipeline 已初始化: {state["project"]}')
    print(f'[INFO] 下一步: bid-tool run')


# ============================================================
# CLI 入口
# ============================================================
def main():
    parser = argparse.ArgumentParser(
        description='标书撰写主控脚本 — 8阶段调度 + 质量门禁',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
常用命令:
  bid-tool init --project "某项目"      初始化新项目
  bid-tool status                      查看各阶段状态
  bid-tool run                         运行全流程（门禁自动检查）
  bid-tool run --from s2               从阶段2继续
  bid-tool run --stage s3              仅运行阶段3
  bid-tool run --yes                   全自动（人工阶段也自动确认）
  bid-tool gate s3                     手动执行阶段3门禁
  bid-tool gate s3 --continue          门禁通过后继续下一阶段
  bid-tool gate s4 --confirm           人工确认阶段4
        '''
    )
    sub = parser.add_subparsers(dest='command')

    p_init = sub.add_parser('init', help='初始化新项目')
    p_init.add_argument('--project', help='项目名称')

    p_status = sub.add_parser('status', help='查看各阶段状态')

    p_run = sub.add_parser('run', help='运行流程')
    p_run.add_argument('--from', dest='start_from', help='从指定阶段开始（如 s2）')
    p_run.add_argument('--end-at', help='到指定阶段结束（如 s7）')
    p_run.add_argument('--stage', help='仅运行指定阶段')
    p_run.add_argument('--skip-gate', action='store_true', help='跳过门禁检查（不推荐）')
    p_run.add_argument('--yes', '-y', action='store_true', help='自动确认所有人工阶段')
    p_run.add_argument('--verbose', '-v', action='store_true', help='详细输出')

    p_gate = sub.add_parser('gate', help='门禁管理')
    p_gate.add_argument('stage', help='阶段编号（如 s3）')
    p_gate.add_argument('--continue', dest='continue_', action='store_true',
                        help='门禁通过后继续下一阶段')
    p_gate.add_argument('--confirm', action='store_true', help='确认人工阶段完成')
    p_gate.add_argument('--skip-gate', action='store_true')
    p_gate.add_argument('--verbose', '-v', action='store_true')

    args = parser.parse_args()

    if args.command == 'init':
        cmd_init(args)
    elif args.command == 'status':
        cmd_status(args)
    elif args.command == 'run':
        cmd_run(args)
    elif args.command == 'gate':
        cmd_gate(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
