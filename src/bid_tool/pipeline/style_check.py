#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
文风检查引擎
用法:
  python style_check.py --file output/s3_body/chapter_04.md
  python style_check.py --dir output/s3_body/
  python style_check.py --text "正文内容..."
"""
import os, sys, re, argparse, json
from pathlib import Path
from collections import Counter

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# ============================================================
# 禁用词库
# ============================================================
FORBIDDEN_PATTERNS = [
    # AI 排比句式
    (r'不仅是.{1,20}更是', 'AI排比句式', 5),
    (r'全方位.{0,10}多角度', 'AI排比句式', 5),
    (r'多维度.{0,10}立体化', 'AI排比句式', 5),
    (r'从根本上.{0,10}彻底', 'AI排比句式', 5),

    # 互联网/管理咨询黑话
    (r'赋能', '互联网黑话', 3),
    (r'(?<!控制)(?<!管理)(?<!业务)闭环(?!控制)(?!管理)', '互联网黑话', 3),
    (r'抓手', '互联网黑话', 5),
    (r'底座', '互联网黑话', 5),
    (r'颗粒度', '互联网黑话', 3),
    (r'降本增效', '互联网黑话', 5),
    (r'新质生产力', '互联网黑话', 5),

    # 空洞通用套话
    (r'致力于', '空洞套话', 3),
    (r'为您保驾护航', '空洞套话', 5),
    (r'行业领先', '空洞套话', 3),
    (r'一流|国际一流', '空洞套话', 2),

    # AI 高频空洞句式
    (r'通过.{1,30}的方式，实现了', 'AI空洞句式', 4),
    (r'充分考虑了.{1,20}的各种因素', 'AI空洞句式', 5),
    (r'为.{1,20}奠定了坚实的基础', 'AI空洞句式', 5),
    (r'具有重要的现实意义', 'AI空洞句式', 5),
    (r'极大地提升了', 'AI空洞句式', 4),
    (r'显著地改善了', 'AI空洞句式', 4),
]

# "先进的/强大的/完善的/灵活的/高效的" 在没有具体指标时禁用
VAGUE_ADJECTIVES = [
    (r'(?<!采用|使用|具备|提供|实现|通过)先进的(?!的)', '空洞形容词', 2),
    (r'(?<!具有|拥有|提供)强大的(?!的)', '空洞形容词', 2),
    (r'(?<!建立|制定|形成|具备)完善的(?!的)', '空洞形容词', 2),
    (r'(?<!支持|实现|提供)灵活的(?!的)', '空洞形容词', 2),
    (r'(?<!实现|保证|提供)高效的(?!的)', '空洞形容词', 2),
]

# ============================================================
# 必用句式
# ============================================================
REQUIRED_PATTERNS = [
    (r'我方承诺', '承诺句式', 2),
    (r'我方完全响应', '响应句式', 3),
    (r'满足招标文件.*要求', '对标句式', 3),
    (r'本项目采用', '技术方案句式', 2),
    (r'系统基于.*架构', '技术方案句式', 2),
    (r'合同签订.*日内', '交付句式', 2),
    (r'按期交付', '交付句式', 2),
    (r'建立.*机制', '质量保障句式', 1),
    (r'通过.*测试', '质量保障句式', 1),
]

# ============================================================
# 段落检查
# ============================================================
def check_text(text, filename="<inline>"):
    """
    扫描文本，返回 (violations, required_hits, score, details)
    """
    violations = []
    required_hits = Counter()
    details = []

    # 1. 检查禁用词
    for pattern, category, weight in FORBIDDEN_PATTERNS + VAGUE_ADJECTIVES:
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        for m in matches:
            # 获取上下文
            start = max(0, m.start() - 15)
            end = min(len(text), m.end() + 15)
            context = text[start:end].replace('\n', ' ')

            violations.append({
                'word': m.group(),
                'category': category,
                'weight': weight,
                'context': f'...{context}...'
            })

    # 2. 检查必用句式
    for pattern, category, min_count in REQUIRED_PATTERNS:
        matches = list(re.finditer(pattern, text, re.IGNORECASE))
        if len(matches) >= min_count:
            required_hits[category] += len(matches)

    # 3. 计算得分
    violation_penalty = sum(v['weight'] for v in violations)
    total_required = sum(min_count for _, _, min_count in REQUIRED_PATTERNS)
    required_bonus = min(30, sum(required_hits.values()) * 3)

    base_score = 100
    score = max(0, min(100, base_score - violation_penalty + required_bonus))

    # 4. 检查段落长度
    paragraphs = [p.strip() for p in text.split('\n\n') if p.strip() and not p.strip().startswith('#')]
    short_paragraphs = [p for p in paragraphs if 5 < len(p) < 100]
    single_sentence_paragraphs = [p for p in paragraphs if p.count('。') <= 1 and len(p) < 80]

    return {
        'filename': filename,
        'score': score,
        'word_count': len(text),
        'paragraph_count': len(paragraphs),
        'violations': violations,
        'violation_count': len(violations),
        'total_penalty': violation_penalty,
        'required_hits': dict(required_hits),
        'required_coverage': len(required_hits) / len(REQUIRED_PATTERNS) if REQUIRED_PATTERNS else 0,
        'short_paragraphs': len(short_paragraphs),
        'single_sentence_paragraphs': len(single_sentence_paragraphs),
        'gate_pass': score >= 80 and len(violations) <= 5,
    }


def check_file(filepath):
    with open(filepath, 'r', encoding='utf-8') as f:
        text = f.read()
    return check_text(text, os.path.basename(filepath))


def check_directory(dirpath):
    results = []
    for f in Path(dirpath).rglob('*.md'):
        results.append(check_file(str(f)))
    for f in Path(dirpath).rglob('*.json'):
        # 尝试从 JSON 中提取文本字段
        try:
            with open(f, 'r', encoding='utf-8') as fh:
                data = json.load(fh)
            text = _extract_text_from_json(data)
            if text:
                results.append(check_text(text, f.name))
        except:
            pass
    return results


def _extract_text_from_json(data, depth=0):
    """从 JSON 中提取所有文本内容"""
    texts = []
    if isinstance(data, str) and len(data) > 50:
        texts.append(data)
    elif isinstance(data, dict):
        for k, v in data.items():
            if k in ('content', 'text', 'text_preview', 'description', 'requirement_text',
                     'response_summary', 'mitigation', 'bid_strategy'):
                if isinstance(v, str) and len(v) > 10:
                    texts.append(v)
            texts.append(_extract_text_from_json(v, depth + 1))
    elif isinstance(data, list):
        for item in data:
            texts.append(_extract_text_from_json(item, depth + 1))
    return ' '.join(t for t in texts if t)


def print_result(result, verbose=False):
    print(f'\n{"─"*60}')
    status = '[PASS]' if result['gate_pass'] else '[FAIL]'
    print(f'{status} {result["filename"]}')
    print(f'  得分: {result["score"]}/100')
    print(f'  字数: {result["word_count"]} | 段落: {result["paragraph_count"]}')
    print(f'  禁用词命中: {result["violation_count"]} (扣分: {result["total_penalty"]})')
    print(f'  必用句式覆盖: {len(result["required_hits"])}/{len(REQUIRED_PATTERNS)} 类')
    print(f'  短段落: {result["short_paragraphs"]} | 单句段落: {result["single_sentence_paragraphs"]}')

    if result['violations'] and verbose:
        print(f'\n  禁用词详情:')
        for v in sorted(result['violations'], key=lambda x: -x['weight']):
            print(f'    [{v["category"]}] {v["word"]} (扣{v["weight"]}分)')
            print(f'      上下文: {v["context"]}')
    elif result['violations']:
        print(f'  禁用词: {Counter(v["word"] for v in result["violations"]).most_common(5)}')

    if not result['gate_pass']:
        if result['score'] < 80:
            print(f'  阻断原因: 得分 {result["score"]} < 80')
        if result['violation_count'] > 5:
            print(f'  阻断原因: 禁用词命中 {result["violation_count"]} > 5')


def main():
    parser = argparse.ArgumentParser(description='文风检查引擎')
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument('--file', help='检查单个文件')
    group.add_argument('--dir', help='检查目录下所有文件')
    group.add_argument('--text', help='检查文本字符串')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示禁用词详情')
    parser.add_argument('--strict', action='store_true', help='严格模式：任一文件未通过则 exit 1')
    args = parser.parse_args()

    exit_code = 0

    if args.file:
        result = check_file(args.file)
        print_result(result, args.verbose)
        if not result['gate_pass']:
            exit_code = 1

    elif args.dir:
        results = check_directory(args.dir)
        if not results:
            print('[FAIL] 未找到可检查的文件')
            sys.exit(1)

        total_score = 0
        for r in results:
            print_result(r, args.verbose)
            total_score += r['score']
            if not r['gate_pass'] and args.strict:
                exit_code = 1

        avg_score = total_score / len(results)
        print(f'\n{"="*60}')
        print(f'目录整体评估')
        print(f'  文件数: {len(results)}')
        print(f'  平均得分: {avg_score:.1f}/100')
        print(f'  通过率: {sum(1 for r in results if r["gate_pass"])}/{len(results)}')

        if avg_score < 80:
            print(f'  [FAIL] 平均得分 {avg_score:.1f} < 80')
            exit_code = 1
        else:
            print(f'  [PASS] 平均得分达标')

    elif args.text:
        result = check_text(args.text)
        print_result(result, args.verbose)
        if not result['gate_pass']:
            exit_code = 1

    if exit_code == 0:
        print(f'\n[PASS] 文风检查通过')
    else:
        print(f'\n[FAIL] 文风检查未通过')
    sys.exit(exit_code)


if __name__ == '__main__':
    main()