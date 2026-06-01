#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
质量门禁校验引擎
用法:
  python validator.py --stage s1 --data output/s1_analysis/
  python validator.py --stage s2 --data output/s2_outline/
  python validator.py --check-coverage --trace output/trace.json
"""
import json, os, sys, argparse, glob
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent  # bid_tool/
TEMPLATES_DIR = ROOT / 'schemas'

# 各阶段对应的 schema 文件
STAGE_SCHEMAS = {
    's1': [
        's1_key_info.schema.json',
        's1_veto_items.schema.json',
        's1_scoring.schema.json',
        's1_risk.schema.json',
        's1_tech_req.schema.json',
    ],
    's2': ['s2_outline.schema.json'],
    's3': ['s3_body.schema.json'],
    's5_tables': ['s5_table_plan.schema.json'],
    's5': ['illustration_job_v2.schema.json'],
    's7': ['s7_trace_matrix.schema.json'],
}

# 阶段间覆盖率门禁要求
COVERAGE_GATES = {
    's1_to_s2': {'required_rate': 1.0, 'check': 'all_reqs_have_ids'},
    's2_to_s3': {'required_rate': 1.0, 'check': 'outline_covers_all_reqs'},
    's3_to_s4': {'required_rate': 1.0, 'check': 'body_covers_all_outline'},
    's5_to_s6': {'required_rate': 1.0, 'check': 'illustrations_cover_placeholders'},
    's7_final': {'required_rate': 1.0, 'check': 'trace_matrix_closed'},
}


def load_json(filepath):
    """加载 JSON 文件，支持 YAML front matter 的 .md 文件"""
    with open(filepath, 'r', encoding='utf-8-sig') as f:
        content = f.read()

    # 尝试提取 YAML/JSON front matter
    if content.startswith('---'):
        parts = content.split('---', 2)
        if len(parts) >= 3:
            front = parts[1].strip()
            try:
                return json.loads(front)
            except json.JSONDecodeError:
                pass

    # 纯 JSON
    try:
        return json.loads(content)
    except json.JSONDecodeError:
        return None


def check_schema_required(data, schema):
    """检查数据是否满足 schema 中的 required 字段"""
    issues = []
    if not isinstance(data, dict):
        return [f"数据不是有效的 JSON 对象: {type(data)}"]

    for field in schema.get('required', []):
        if field not in data or data[field] is None:
            issues.append(f"缺少必填字段: {field}")
        elif isinstance(data[field], (list, str)) and len(data[field]) == 0:
            issues.append(f"必填字段为空: {field}")

    # 检查数组元素是否满足子 schema（如有）
    for field, prop in schema.get('properties', {}).items():
        if field in data and prop.get('type') == 'array' and 'items' in prop:
            item_schema = prop['items']
            if isinstance(item_schema, dict) and 'required' in item_schema:
                for i, item in enumerate(data[field]):
                    for rf in item_schema['required']:
                        if rf not in item or item[rf] is None:
                            issues.append(f"{field}[{i}].{rf} 为空")
                        elif isinstance(item.get(rf), str) and len(item[rf]) == 0:
                            issues.append(f"{field}[{i}].{rf} 为空字符串")

    return issues


def check_jsonschema(data, schema):
    try:
        import jsonschema
    except ImportError:
        return check_schema_required(data, schema)

    validator = jsonschema.Draft202012Validator(schema)
    issues = []
    for issue in sorted(validator.iter_errors(data), key=lambda error: list(error.path)):
        location = ".".join(str(item) for item in issue.path) or "<root>"
        issues.append(f"{location}: {issue.message}")
    return issues


def check_table_plan_semantics(data):
    issues = []
    seen_ids = set()
    for index, table in enumerate(data.get('tables', [])):
        table_id = table.get('id', f'<table-{index}>')
        if table_id in seen_ids:
            issues.append(f"tables[{index}].id: 重复表格ID {table_id}")
        seen_ids.add(table_id)

        columns = table.get('columns', [])
        expected = len(columns)
        for row_index, row in enumerate(table.get('rows', [])):
            if len(row) != expected:
                issues.append(
                    f"tables[{index}].rows[{row_index}]: 单元格数量 {len(row)} 与列数 {expected} 不一致"
                )
    return issues


def validate_stage(stage, data_dir):
    """对指定阶段的输出进行全量校验"""
    if stage not in STAGE_SCHEMAS:
        print(f'[FAIL] 未知阶段: {stage}')
        return False

    schema_files = STAGE_SCHEMAS[stage]
    all_issues = {}

    # 特殊映射：schema 文件名 -> 数据文件名前缀
    DATA_PREFIX_MAP = {
        's5_table_plan.schema.json': 'table_insertion_plan',
        'illustration_job_v2.schema.json': 's5_illustration_job',
        's5_illustration.schema.json': 's5_illustration',
    }

    for sf in schema_files:
        schema_path = str(TEMPLATES_DIR / sf)
        if not Path(schema_path).exists():
            all_issues[sf] = [f'Schema 文件不存在: {schema_path}']
            continue

        schema = load_json(schema_path)
        if schema is None:
            all_issues[sf] = [f'无法解析 Schema: {schema_path}']
            continue

        # 查找对应的数据文件
        data_prefix = DATA_PREFIX_MAP.get(sf, sf.replace('.schema.json', ''))
        data_files = glob.glob(os.path.join(data_dir, f'{data_prefix}.json'))
        if not data_files:
            data_files = glob.glob(os.path.join(data_dir, f'{data_prefix}_job.json'))

        if not data_files:
            all_issues[sf] = [f'在 {data_dir} 中未找到 {data_prefix} 的数据文件']
            continue

        issues = []
        for df in data_files:
            data = load_json(df)
            if data is None:
                issues.append(f'无法解析数据文件: {df}')
                continue
            if sf in ('illustration_job_v2.schema.json', 's5_table_plan.schema.json'):
                issues.extend(check_jsonschema(data, schema))
                if sf == 's5_table_plan.schema.json':
                    issues.extend(check_table_plan_semantics(data))
            else:
                issues.extend(check_schema_required(data, schema))

        all_issues[sf] = issues

    # 输出结果
    total_issues = sum(len(v) for v in all_issues.values())
    print(f'\n{"="*60}')
    print(f'阶段 {stage} 校验结果')
    print(f'{"="*60}')

    for sf, issues in all_issues.items():
        status = '[PASS]' if len(issues) == 0 else '[FAIL]'
        print(f'{status} {sf}: {len(issues)} 个问题')
        for issue in issues:
            print(f'  - {issue}')

    if total_issues == 0:
        print(f'\n[PASS] 阶段 {stage} 全部校验通过')
        return True
    else:
        print(f'\n[FAIL] 阶段 {stage} 共 {total_issues} 个问题，阻塞门禁')
        return False


def check_coverage(trace_path):
    """检查 trace.json 的覆盖率"""
    trace = load_json(trace_path)
    if trace is None:
        print(f'[FAIL] 无法加载 trace.json: {trace_path}')
        return False

    cov = trace.get('coverage', {})
    if not cov:
        # 从 requirements 数组计算
        reqs = trace.get('requirements', [])
        total = len(reqs)
        covered = sum(1 for r in reqs if r.get('status') == 'covered')
        uncovered = [r['req_id'] for r in reqs if r.get('status') != 'covered']
        rate = covered / total if total > 0 else 0
    else:
        total = cov.get('total_reqs', 0)
        covered = cov.get('covered_reqs', 0)
        uncovered = cov.get('uncovered_reqs', [])
        rate = cov.get('coverage_rate', 0)

    print(f'\n{"="*60}')
    print(f'追溯覆盖率检查')
    print(f'{"="*60}')
    print(f'  总需求数: {total}')
    print(f'  已覆盖:   {covered}')
    print(f'  未覆盖:   {len(uncovered)}')
    print(f'  覆盖率:   {rate:.1%}')

    if uncovered:
        print(f'\n  未覆盖需求:')
        for rid in uncovered:
            # 查找需求详情
            for r in trace.get('requirements', []):
                if r['req_id'] == rid:
                    print(f'    {rid}: {r.get("text", "")[:80]}')
                    break

    required = COVERAGE_GATES.get('s7_final', {}).get('required_rate', 1.0)
    if rate >= required:
        print(f'\n[PASS] 覆盖率 {rate:.1%} >= {required:.1%}')
        return True
    else:
        print(f'\n[FAIL] 覆盖率 {rate:.1%} < {required:.1%}，门禁未通过')
        return False


def check_duplicates(data_dir):
    """检查同目录下是否有内容高度重复的文件（>90% 相似度标记）"""
    import hashlib

    files = glob.glob(os.path.join(data_dir, '*.md'))
    files += glob.glob(os.path.join(data_dir, '*.json'))

    if len(files) < 2:
        print('[PASS] 文件数不足，跳过重复检测')
        return True

    hashes = {}
    issues = []

    for f in files:
        with open(f, 'r', encoding='utf-8', errors='ignore') as fh:
            content = fh.read()
        # 规范化后取 hash
        normalized = ' '.join(content.lower().split())
        h = hashlib.md5(normalized.encode()).hexdigest()
        fname = os.path.basename(f)

        if h in hashes:
            issues.append(f'文件 {fname} 与 {hashes[h]} 内容高度相似（MD5 相同）')
        else:
            hashes[h] = fname

    if issues:
        print(f'\n[WARN] 发现 {len(issues)} 对疑似重复文件:')
        for i in issues:
            print(f'  - {i}')
    else:
        print('[PASS] 未发现重复文件')
    return True  # 重复文件仅警告，不阻断


def main():
    parser = argparse.ArgumentParser(description='标书质量门禁校验引擎')
    parser.add_argument('--stage', choices=list(STAGE_SCHEMAS.keys()), help='校验指定阶段')
    parser.add_argument('--data', help='阶段产物目录')
    parser.add_argument('--check-coverage', action='store_true', help='检查 trace.json 覆盖率')
    parser.add_argument('--check-duplicates', action='store_true', help='检查文件重复')
    parser.add_argument('--trace', default=None, help='trace.json 路径')
    args = parser.parse_args()

    exit_code = 0

    if args.stage:
        data_dir = args.data or str(Path.cwd() / 'output' / f'{args.stage}_analysis')
        if not validate_stage(args.stage, data_dir):
            exit_code = 1

    if args.check_coverage:
        trace_path = args.trace or str(Path.cwd() / 'output' / 'trace.json')
        if not Path(trace_path).exists():
            print(f'[FAIL] trace.json 不存在: {trace_path}')
            exit_code = 1
        elif not check_coverage(trace_path):
            exit_code = 1

    if args.check_duplicates:
        data_dir = args.data or str(Path.cwd() / 'output')
        check_duplicates(data_dir)

    if exit_code == 0:
        print(f'\n[GATE] PASS - 所有门禁已通过')
    else:
        print(f'\n[GATE] FAIL - 存在未通过的门禁')

    sys.exit(exit_code)


if __name__ == '__main__':
    main()
