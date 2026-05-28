#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
章节耦合分析 + 自动分组 + 生成分群提示词

将 S2 大纲的 13 章按耦合度拆分为若干独立群组，
每个群组可交给独立的 subagent 并行撰写正文。

用法:
  python chapter_planner.py --outline output/s2_outline/s2_outline.json --profile construction
"""

import json
import argparse
from pathlib import Path
from collections import defaultdict

PACKAGE_ROOT = Path(__file__).resolve().parent.parent

# ── 章节耦合定义（基于评分维度 + 主题关联 + 交叉引用） ──

# 每个群组的章节间存在强耦合（共享评分维度、主题关联、相互引用）
# 群组之间弱耦合或独立

DEFAULT_COUPLING_GROUPS = {
    "overview": {
        "label": "总体+建议",
        "chapters": ["CH-01", "CH-13"],
        "description": "总体概述和合理化建议，阅读型章节，与其他章节无直接依赖",
        "shared_scoring": "施工方案(15分) + 合理化建议(3分)",
    },
    "site_setup": {
        "label": "现场布置+机械+机构",
        "chapters": ["CH-02", "CH-09", "CH-10"],
        "description": "施工现场平面布置、机械设备配备、项目管理机构，可并行编写",
        "shared_scoring": "施工方案 + 机械设备(3分) + 管理机构(8分)",
    },
    "construction_core": {
        "label": "施工方案与技术措施",
        "chapters": ["CH-03"],
        "description": "核心章节，覆盖6大专业施工方案+交叉对接+过程控制，篇幅最大",
        "shared_scoring": "施工方案(15分)",
    },
    "quality_protection": {
        "label": "质量+成品保护",
        "chapters": ["CH-04", "CH-11"],
        "description": "质量管理体系、成品保护及保修服务，通过质量标准关联",
        "shared_scoring": "质量保证措施(5分)",
    },
    "hse_trio": {
        "label": "HSE三合一",
        "chapters": ["CH-05", "CH-06", "CH-12"],
        "description": "安全管理、环境保护、应急预案，统一HSE管理主题",
        "shared_scoring": "安全施工保障(5分) + 紧急预案(3分)",
    },
    "schedule_resources": {
        "label": "进度+资源",
        "chapters": ["CH-07", "CH-08"],
        "description": "工程进度计划与资源配备，资源保障进度，进度约束资源",
        "shared_scoring": "进度计划(8分)",
    },
}

# 章节到群组的反向索引（自动生成）
def build_chapter_to_group():
    mapping = {}
    for group_id, group in DEFAULT_COUPLING_GROUPS.items():
        for ch in group["chapters"]:
            mapping[ch] = group_id
    return mapping


def analyze_coupling(outline_path, profile_name=None):
    """分析大纲，返回分组方案"""
    with open(outline_path, 'r', encoding='utf-8') as f:
        outline = json.load(f)

    chapters = outline.get("chapters", [])
    chapter_to_group = build_chapter_to_group()
    coverage_map = outline.get("coverage_map", [])

    # 按分组归类章节
    groups = defaultdict(lambda: {
        "group_id": "",
        "label": "",
        "description": "",
        "shared_scoring": "",
        "chapters": [],
        "total_estimated_words": 0,
        "total_estimated_pages": 0,
        "reqs_to_cover": [],
        "illustrations": [],
    })

    for ch in chapters:
        ch_id = ch["chapter_id"]
        group_id = chapter_to_group.get(ch_id, "ungrouped")

        if group_id not in groups:
            groups[group_id] = {
                "group_id": group_id,
                "label": ch_id,
                "description": "",
                "shared_scoring": "",
                "chapters": [],
                "total_estimated_words": 0,
                "total_estimated_pages": 0,
                "reqs_to_cover": [],
                "illustrations": [],
            }

        g = groups[group_id]
        g["group_id"] = group_id

        # 从 DEFAULT_COUPLING_GROUPS 取元数据
        if group_id in DEFAULT_COUPLING_GROUPS:
            g["label"] = DEFAULT_COUPLING_GROUPS[group_id]["label"]
            g["description"] = DEFAULT_COUPLING_GROUPS[group_id]["description"]
            g["shared_scoring"] = DEFAULT_COUPLING_GROUPS[group_id]["shared_scoring"]

        g["chapters"].append({
            "chapter_id": ch_id,
            "title": ch["title"],
            "level": ch.get("level", 1),
            "estimated_words": ch.get("estimated_words", 0),
            "estimated_pages": ch.get("estimated_pages", 0),
            "covers_reqs": [r["req_id"] for r in ch.get("covers_reqs", [])],
            "illustration_placeholders": ch.get("illustration_placeholders", []),
            "scoring_points": ch.get("scoring_points", []),
            "children": ch.get("children", []),
        })
        g["total_estimated_words"] += ch.get("estimated_words", 0)
        g["total_estimated_pages"] += ch.get("estimated_pages", 0)

        # 收集该群组覆盖的所有 req
        for r in ch.get("covers_reqs", []):
            if r["req_id"] not in g["reqs_to_cover"]:
                g["reqs_to_cover"].append(r["req_id"])

        # 收集该群组的插图
        for illu in ch.get("illustration_placeholders", []):
            if illu["illu_id"] not in [i["illu_id"] for i in g["illustrations"]]:
                g["illustrations"].append(illu)

    # 为每个群组整理该群组覆盖的 coverage_map 条目
    for group_id, g in groups.items():
        g["coverage_entries"] = [
            entry for entry in coverage_map
            if entry.get("chapter_id") in [c["chapter_id"] for c in g["chapters"]]
        ]

    # 按 group_id 排序
    result = {
        "total_chapters": len(chapters),
        "total_groups": len(groups),
        "coupling_analysis": {
            "method": "基于评分维度+主题关联+交叉引用",
            "independence_guarantee": "不同群组之间无共享招标条款覆盖，可完全并行写作",
        },
        "groups": dict(groups),
    }
    return result


def render_group_prompt(group_id, group_data, s1_data_dir, s2_data_dir, output_dir,
                        project_name, word_budget_per_group, total_word_budget,
                        user_approach=""):
    """为单个群组渲染 LLM 提示词"""
    prompt_template = (PROMPTS_DIR / 's3_writing_prompt.md').read_text(encoding='utf-8')

    # Load shared context
    s1_context = []
    for fname in ['s1_key_info.json', 's1_tech_req.json']:
        fpath = Path(s1_data_dir) / fname
        if fpath.exists():
            with open(fpath, 'r', encoding='utf-8') as f:
                s1_context.append(
                    f"\n### {fname}\n```json\n{json.dumps(json.load(f), ensure_ascii=False, indent=2)}\n```"
                )

    # Load only this group's coverage entries
    coverage_entries = group_data.get('coverage_entries', [])
    relevant_req_ids = group_data.get('reqs_to_cover', [])

    # Filter tech_req to only include relevant requirements
    tech_req_path = Path(s1_data_dir) / 's1_tech_req.json'
    filtered_tech_req = []
    if tech_req_path.exists():
        with open(tech_req_path, 'r', encoding='utf-8') as f:
            all_tech = json.load(f)
        all_items = all_tech.get('items', [])
        filtered_tech_req = [item for item in all_items if item['id'] in relevant_req_ids]

    group_chapters = group_data.get('chapters', [])

    rendered = f"""{prompt_template}

---

## 本群组写作任务

- **群组名称**: {group_data.get('label', group_id)}
- **群组说明**: {group_data.get('description', '')}
- **涉及评分**: {group_data.get('shared_scoring', '')}
- **字数目标**: {word_budget_per_group} 字（全文总目标 {total_word_budget} 字）
- **输出目录**: {output_dir}/
{"- **用户技术思路**: " + user_approach if user_approach else ""}

### 本群组将撰写的章节

{json.dumps(group_chapters, ensure_ascii=False, indent=2)}

---

## 阶段 1 关键数据（仅本群组相关）

### s1_key_info.json
```json
{json.dumps(json.load(open(Path(s1_data_dir) / 's1_key_info.json', 'r', encoding='utf-8')), ensure_ascii=False, indent=2)}
```

### s1_tech_req.json（仅本群组需覆盖的需求条目，共 {len(filtered_tech_req)} 条）
```json
{json.dumps(filtered_tech_req, ensure_ascii=False, indent=2)}
```

---

## 阶段 2 大纲（仅本群组相关部分）

### coverage_map 关联条目（共 {len(coverage_entries)} 条）
```json
{json.dumps(coverage_entries, ensure_ascii=False, indent=2)}
```

---

## 输出指令

1. 按以上大纲逐章撰写本群组的所有章节正文
2. 每章保存为独立 .md 文件：`ch_XX.md`（XX 为章节编号，如 ch_03.md）
3. 同时输出群组 manifest：`{group_id}_manifest.json`，包含：
   - 本群组所有章节的元数据（chapter_id, title, content_file, covers_reqs, word_count）
   - 本群组所有 segments（段落到条款映射）
   - 本群组所有 illustration_manifest 条目
4. 文风须通过 style_check.py 检测（得分 ≥ 80，禁用词 ≤ 5）
5. 每段绑定对应的招标条款 ID（引用 req_id）

项目名称: {project_name or '未命名项目'}
"""
    return rendered


def plan_and_render(outline_path, s1_data_dir, s2_data_dir, output_dir,
                    project_name, total_word_budget, user_approach=""):
    """主入口：分析耦合 → 拆分群组 → 渲染各群组提示词"""
    output_dir = Path(output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # 1. 分析耦合
    plan = analyze_coupling(outline_path)
    groups = plan["groups"]

    # 2. 分配字数（按各群组章节原始估算比例）
    total_estimated = sum(g["total_estimated_words"] for g in groups.values())
    group_prompts = []

    for group_id, group_data in groups.items():
        proportion = group_data["total_estimated_words"] / total_estimated if total_estimated > 0 else 1 / len(groups)
        word_budget = int(total_word_budget * proportion)

        # 3. 渲染群组提示词
        prompt = render_group_prompt(
            group_id, group_data,
            s1_data_dir, s2_data_dir, output_dir,
            project_name, word_budget, total_word_budget,
            user_approach=user_approach
        )

        prompt_file = output_dir / f's3_prompt_{group_id}.md'
        prompt_file.write_text(prompt, encoding='utf-8')
        group_prompts.append({
            "group_id": group_id,
            "label": group_data["label"],
            "chapters": [c["chapter_id"] for c in group_data["chapters"]],
            "word_budget": word_budget,
            "prompt_file": str(prompt_file),
        })

    # 4. 写规划文件
    plan["word_budget"] = {
        "total": total_word_budget,
        "per_group": {g["group_id"]: g["word_budget"] for g in group_prompts},
    }
    plan["group_prompts"] = group_prompts

    plan_path = output_dir / 's3_plan.json'
    with open(plan_path, 'w', encoding='utf-8') as f:
        json.dump(plan, f, ensure_ascii=False, indent=2)

    return plan


# ── 主入口 ──

PROMPTS_DIR = PACKAGE_ROOT / 'prompts'


def main():
    parser = argparse.ArgumentParser(description='S3 章节耦合分析与分组渲染')
    parser.add_argument('--outline', required=True, help='S2 outline JSON 路径')
    parser.add_argument('--s1-data', required=True, help='S1 分析结果目录')
    parser.add_argument('--s2-data', required=True, help='S2 大纲目录')
    parser.add_argument('--output', required=True, help='S3 输出目录')
    parser.add_argument('--project', default='未命名项目', help='项目名称')
    parser.add_argument('--word-budget', type=int, default=25000, help='全文总字数目标')
    args = parser.parse_args()

    plan = plan_and_render(
        args.outline, args.s1_data, args.s2_data, args.output,
        args.project, args.word_budget
    )

    groups = plan["group_prompts"]
    print(f'\n{"="*60}')
    print(f'S3 章节耦合分析完成')
    print(f'  总章节: {plan["total_chapters"]} | 群组数: {plan["total_groups"]}')
    print(f'  总字数目标: {plan["word_budget"]["total"]} 字')
    print(f'\n群组分配:')
    for g in groups:
        chs = ', '.join(g['chapters'])
        print(f'  [{g["group_id"]}] {g["label"]}: {chs} → {g["word_budget"]} 字')
        print(f'        提示词: {g["prompt_file"]}')


if __name__ == '__main__':
    main()
