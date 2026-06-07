#!/usr/bin/env python3
"""bid-tool — 标书自动生成工具统一入口

Usage:
  bid-tool init --project "项目名" --type software    初始化新项目
  bid-tool run                                         运行全流程
  bid-tool run --from s2 --to s7                       部分运行
  bid-tool status                                      查看状态
  bid-tool gate s3                                     门禁检查
  bid-tool illustrate --job <作业JSON>                  仅运行配图工具
  bid-tool export --format docx                         仅导出
"""
import argparse
import sys
from pathlib import Path


def cmd_init(args):
    from .pipeline.engine import cmd_init as engine_init
    engine_init(args)


def cmd_run(args):
    from .pipeline.engine import cmd_run as engine_run
    engine_run(args)


def cmd_status(args):
    from .pipeline.engine import cmd_status as engine_status
    engine_status(args)


def cmd_gate(args):
    from .pipeline.engine import cmd_gate as engine_gate
    engine_gate(args)


def cmd_illustrate(args):
    from .illustration_v2.toolkit import main as illustrate_main
    # Patch sys.argv for the illustration toolkit's argparse
    original_argv = sys.argv
    try:
        sys.argv = [
            'bid-tool-illustrate',
            '--job', str(args.job),
            '--output', str(args.output or Path.cwd() / 'output' / 'illustrations'),
        ]
        if args.png:
            sys.argv.append('--png')
        if getattr(args, 'png_scale', None):
            sys.argv.extend(['--png-scale', str(args.png_scale)])
        if args.validate_only:
            sys.argv.append('--validate-only')
        if getattr(args, 'no_echarts_export', False):
            sys.argv.append('--no-echarts-export')
        illustrate_main()
    except SystemExit as e:
        if e.code != 0:
            raise
    finally:
        sys.argv = original_argv


def cmd_illustration_bundle(args):
    from .illustration_v2.standalone import build_bundle

    output = build_bundle(
        args.output,
        include_examples=not args.no_examples,
        make_zip=args.zip,
    )
    print(f"Standalone illustration bundle created: {output}")
    print(f"Launcher: {output / 'run_illustration.py'}")
    if args.zip:
        print(f"Zip: {output.with_suffix('.zip')}")


def cmd_export(args):
    from .pipeline.stages.s8_export import export_to_docx
    from .profiles import load_profile

    chapter_name_map = {}
    if args.profile:
        try:
            profile = load_profile(args.profile)
            chapter_name_map = profile.get('chapter_templates', {})
        except FileNotFoundError:
            print(f'[WARN] Profile not found: {args.profile}, using empty chapter map')

    export_to_docx(
        combined_md=args.input,
        s6_dir=args.s6_dir,
        s8_dir=args.output,
        trace_path=args.trace,
        chapter_name_map=chapter_name_map,
        project_name=args.project,
    )


def main():
    parser = argparse.ArgumentParser(
        description='bid-tool — 标书自动生成工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog='''
常用命令:
  bid-tool init --project "某项目" --type software    初始化新项目
  bid-tool status                                     查看各阶段状态
  bid-tool run                                        运行全流程
  bid-tool run --from s2 --to s7                      部分运行
  bid-tool gate s3                                    门禁检查
  bid-tool illustrate --job examples/示例.json         生成配图
  bid-tool export --profile software                  导出 DOCX
        '''
    )
    sub = parser.add_subparsers(dest='command')

    # init
    p_init = sub.add_parser('init', help='初始化新项目')
    p_init.add_argument('--project', help='项目名称')
    p_init.add_argument('--type', dest='profile_type', choices=['software', 'construction'],
                        default='software', help='项目类型')

    # status
    sub.add_parser('status', help='查看各阶段状态')

    # run
    p_run = sub.add_parser('run', help='运行流程')
    p_run.add_argument('--from', dest='start_from', help='从指定阶段开始（如 s2）')
    p_run.add_argument('--to', dest='end_at', help='到指定阶段结束（如 s7）')
    p_run.add_argument('--stage', help='仅运行指定阶段')
    p_run.add_argument('--skip-gate', action='store_true', help='跳过门禁检查')
    p_run.add_argument('--yes', '-y', action='store_true', help='自动确认人工阶段')
    p_run.add_argument('--verbose', '-v', action='store_true', help='详细输出')

    # gate
    p_gate = sub.add_parser('gate', help='门禁管理')
    p_gate.add_argument('stage', help='阶段编号（如 s3）')
    p_gate.add_argument('--continue', dest='continue_', action='store_true',
                        help='门禁通过后继续下一阶段')
    p_gate.add_argument('--confirm', action='store_true', help='确认人工阶段完成')
    p_gate.add_argument('--skip-gate', action='store_true')
    p_gate.add_argument('--verbose', '-v', action='store_true')

    # illustrate
    p_illu = sub.add_parser('illustrate', help='运行配图工具')
    p_illu.add_argument('--job', type=Path, required=True, help='统一配图任务 JSON 文件')
    p_illu.add_argument('--output', type=Path, help='输出目录')
    p_illu.add_argument('--png', action='store_true', help='同步生成 PNG 预览')
    p_illu.add_argument('--png-scale', type=int, choices=(1, 2, 3), default=2, help='PNG 输出倍率')
    p_illu.add_argument('--validate-only', action='store_true', help='仅校验任务文件')
    p_illu.add_argument('--no-echarts-export', action='store_true',
                        help='ECharts 只生成本地 HTML 审图页，不自动导出图片')

    # illustration bundle
    p_bundle = sub.add_parser('illustration-bundle', help='生成可独立解压运行的绘图工具包')
    p_bundle.add_argument('--output', type=Path, default=Path.cwd() / 'dist' / 'bid-illustration-standalone',
                          help='独立绘图工具包输出目录')
    p_bundle.add_argument('--no-examples', action='store_true', help='不复制 examples 目录')
    p_bundle.add_argument('--zip', action='store_true', help='同时生成 zip 压缩包')

    # export
    p_export = sub.add_parser('export', help='导出 DOCX')
    p_export.add_argument('--profile', choices=['software', 'construction'],
                          default='software', help='项目类型配置')
    p_export.add_argument('--input', type=Path, help='s6_combined_bid_document.md 路径')
    p_export.add_argument('--s6-dir', type=Path, help='s6_synthesis 目录（用于解析图片路径）')
    p_export.add_argument('--output', type=Path, help='s8_final 输出目录')
    p_export.add_argument('--trace', type=Path, help='trace.json 路径')
    p_export.add_argument('--project', help='项目名称（用于输出文件名）')

    args = parser.parse_args()

    if args.command == 'init':
        cmd_init(args)
    elif args.command == 'status':
        cmd_status(args)
    elif args.command == 'run':
        cmd_run(args)
    elif args.command == 'gate':
        cmd_gate(args)
    elif args.command == 'illustrate':
        cmd_illustrate(args)
    elif args.command == 'illustration-bundle':
        cmd_illustration_bundle(args)
    elif args.command == 'export':
        cmd_export(args)
    else:
        parser.print_help()


if __name__ == '__main__':
    main()
