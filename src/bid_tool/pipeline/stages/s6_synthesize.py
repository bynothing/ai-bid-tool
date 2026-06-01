"""Stage 6: Render and synthesize illustration assets into chapter markdown.

Default v2 process:
  Phase A (render): Read s5_illustration_job.json -> illustration platform assets
  Phase B (synthesize): Read illustration-manifest.json -> insert images into chapter markdown

Legacy compatibility:
  legacy-convert: Read old per-illustration S5 JSONs -> v1 unified job

Usage:
  python s6_synthesize.py render                           # Render v2 job only
  python s6_synthesize.py synthesize                       # Phase B only
  python s6_synthesize.py all                              # Render v2 + synthesize
  python s6_synthesize.py legacy-convert                   # Historical v1 conversion
"""
import json
import os
import re
import shutil
from collections import defaultdict
from pathlib import Path


# ─── Phase A: Convert S5 illustrations to unified job format ───

# S5 illustration type → (renderer, diagram_type)
TYPE_MAP = {
    '架构图': ('svg', 'layered_architecture'),
    '部署图': ('svg', 'layered_architecture'),
    '框图': ('svg', 'capability_map'),
    '示意图': ('svg', 'capability_map'),
    '界面原型': ('svg', 'capability_map'),
    '流程图': ('svg', 'flowchart'),
    '甘特图': ('svg', 'flowchart'),
    '数据表': ('svg', 'relationship_map'),
}

# Chapter number to section label mapping (fallback; prefer profile)
DEFAULT_CHAPTER_SECTION_MAP = {
    'CH-01': '1 项目理解与总体技术方案',
    'CH-02': '2 资质、保密与合规保障',
    'CH-03': '3 总体集成通用技术方案',
    'CH-04': '4 人机交互界面设计',
    'CH-05': '5 数据库模块技术方案',
    'CH-06': '6 材料设计模块技术方案',
    'CH-07': '7 热环境确定模块技术方案',
    'CH-08': '8 热环境响应评估模块技术方案',
    'CH-09': '9 运行环境兼容性与离线部署方案',
    'CH-10': '10 集成对接与数据贯通方案',
    'CH-11': '11 项目实施与交付方案',
    'CH-12': '12 测试、验收与质量保障',
    'CH-13': '13 售后服务与质保承诺',
}

# Chapter number → Chinese chapter number mapping
CHAPTER_NUM_MAP = {
    '1': 'CH-01', '2': 'CH-02', '3': 'CH-03', '4': 'CH-04',
    '5': 'CH-05', '6': 'CH-06', '7': 'CH-07', '8': 'CH-08',
    '9': 'CH-09', '10': 'CH-10', '11': 'CH-11', '12': 'CH-12', '13': 'CH-13',
}


def _load_json(path):
    with open(path, 'r', encoding='utf-8-sig') as f:
        return json.load(f)


def _save_json(data, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def render_v2_job(s5_dir=None, images_dir=None, png=True, png_scale=2, export_echarts=True):
    """Render the S5 Illustration Job v2 through the standalone illustration API.

    This is the main bid-tool integration path. It treats the illustration
    platform as an external tool: S5 owns the v2 JSON, the platform owns
    rendering, and S6/S8 consume only the returned manifest.
    """

    from bid_tool.illustration import api

    s5_dir = Path(s5_dir) if s5_dir else Path.cwd() / 'output' / 's5_illustrations'
    job_path = s5_dir / 's5_illustration_job.json'
    if not job_path.exists():
        raise FileNotFoundError(
            f"未找到 Illustration Job v2: {job_path}\n"
            "请先完成 S5，并将 AI 输出保存为 s5_illustration_job.json。"
        )

    images_dir = Path(images_dir) if images_dir else s5_dir / 'images'
    job = api.load(job_path)
    errors, warnings = api.validate(job)
    if errors:
        raise ValueError("S5 配图任务校验失败:\n" + "\n".join(f"- {item}" for item in errors))

    if warnings:
        print("[S6] 配图任务质量提示:")
        for warning in warnings:
            print(f"  - {warning}")

    print(f"[S6] Rendering illustrations via independent platform API")
    print(f"  Job:    {job_path}")
    print(f"  Output: {images_dir}")
    decisions = api.plan(job)
    for decision in decisions:
        print(f"  - {decision['id']}: {decision['type']} -> {decision['renderer']}")

    records = api.render(
        job,
        images_dir,
        png=png,
        png_scale=png_scale,
        export_echarts=export_echarts,
    )
    manifest_path = images_dir / 'illustration-manifest.json'
    print(f"[S6] Illustration render complete: {manifest_path} ({len(records)} figures)")
    return str(manifest_path)


def _truncate(text, max_len):
    if not text:
        return ''
    text = text.strip()
    if len(text) <= max_len:
        return text
    for sep in ['；', ';', '，', ',', '。', '.', '、', ' ']:
        pos = text.rfind(sep, 0, max_len)
        if pos > max_len // 2:
            return text[:pos + 1]
    return text[:max_len - 1] + '…'


def _summarize_node_name(name, max_len=20):
    if not name:
        return ''
    name = name.strip()
    name = name.replace('.project项目文件', '工程项目文件')
    name = name.replace('.project工程文件', '工程项目文件')
    name = name.replace('.project文件', '工程文件')
    if '：' in name and len(name) > 25:
        name = name.split('：')[0]
    return _truncate(name, max_len)


def _summarize_node_desc(desc, max_len=40):
    if not desc:
        return ''
    desc = desc.strip()
    for sep in ['；', ';', '。', '：']:
        if sep in desc:
            parts = desc.split(sep)
            for part in parts:
                if len(part.strip()) > 8:
                    return _truncate(part.strip(), max_len)
    return _truncate(desc, max_len)


def _make_id(illu_id):
    return illu_id.replace('-', '_').lower()


def _get_chapter_section(chapter_ref, chapter_section_map=None):
    if chapter_section_map is None:
        chapter_section_map = DEFAULT_CHAPTER_SECTION_MAP
    match = re.match(r'(CH-\d+)', chapter_ref)
    if match:
        ch_prefix = match.group(1)
        return chapter_section_map.get(ch_prefix, chapter_ref)
    return chapter_ref


def _convert_layered_architecture(illu):
    tc = illu.get('text_content', {})
    spec = {
        'type': 'layered_architecture',
        'title': tc.get('main_title', illu.get('title', '')),
        'subtitle': illu.get('subtitle', ''),
        'placement': illu.get('chapter_ref', ''),
    }
    layers = []
    for s5_layer in tc.get('layers', []):
        items = []
        for node in s5_layer.get('nodes', []):
            raw_name = node.get('name', node.get('label', ''))
            raw_desc = node.get('subtitle', node.get('detail', node.get('description', '')))
            item = {
                'title': _summarize_node_name(raw_name, 22),
                'desc': _summarize_node_desc(raw_desc, 50),
            }
            if node.get('is_highlighted'):
                item['style'] = 'accent'
            items.append(item)

        layer = {
            'label': s5_layer.get('name', ''),
            'en': s5_layer.get('en_name', ''),
            'items': items,
        }
        if s5_layer.get('is_dark'):
            layer['style'] = 'dark'
        n = len(items)
        if n <= 3:
            layer['columns'] = n
        elif n <= 6:
            layer['columns'] = min(n, 3)
        else:
            layer['columns'] = 4
        layers.append(layer)

    spec['layers'] = layers
    footnote = tc.get('footnote', '')
    if footnote:
        spec['note'] = footnote[:300]
    return spec


def _convert_flowchart(illu):
    MAX_COLS_PER_ROW = 5
    tc = illu.get('text_content', {})
    spec = {
        'type': 'flowchart',
        'title': tc.get('main_title', illu.get('title', '')),
        'subtitle': illu.get('subtitle', ''),
        'placement': illu.get('chapter_ref', ''),
    }
    nodes = []
    edges = []
    prev_node_id = None
    node_idx = 0
    display_row = 0

    source_layers = tc.get('layers', [])
    total_nodes = sum(len(layer.get('nodes', [])) for layer in source_layers)
    title_limit = 12 if total_nodes > 12 else 16

    for layer_idx, s5_layer in enumerate(source_layers):
        layer_nodes = s5_layer.get('nodes', [])
        col_in_row = 0

        for node_idx_in_layer, node in enumerate(layer_nodes):
            if node_idx_in_layer > 0 and node_idx_in_layer % MAX_COLS_PER_ROW == 0:
                display_row += 1
                col_in_row = 0

            nid = node.get('id', f"n{node_idx:02d}")
            raw_label = node.get('label', node.get('name', ''))
            raw_detail = node.get('detail', node.get('subtitle', ''))
            label = _summarize_node_name(raw_label, title_limit)
            detail = _summarize_node_desc(raw_detail, 60)

            kind = 'process'
            if any(kw in label for kw in ['决策', '判断', '检查', '校验']):
                kind = 'decision'
            elif any(kw in label for kw in ['结束', '输出', '导出']):
                kind = 'success'

            short_desc = detail[:10] if total_nodes <= 10 and len(detail) <= 10 else ''
            nodes.append({
                'id': nid, 'row': display_row, 'col': col_in_row,
                'title': label, 'desc': short_desc, 'kind': kind,
            })

            if node_idx_in_layer == 0 and layer_idx > 0:
                edges.append({'from': prev_node_id, 'to': nid, 'label': '', 'relation': 'flow'})
            elif node_idx > 0:
                edges.append({'from': nodes[node_idx - 1]['id'], 'to': nid, 'label': '', 'relation': 'flow'})

            prev_node_id = nid
            node_idx += 1
            col_in_row += 1

        display_row += 1

    spec['nodes'] = nodes
    spec['edges'] = edges if edges else [{'from': nodes[0]['id'], 'to': nodes[-1]['id'], 'relation': 'flow'}]

    footnote = tc.get('footnote', '')
    if footnote:
        spec['note'] = footnote[:300]
    return spec


def _convert_capability_map(illu):
    tc = illu.get('text_content', {})
    spec = {
        'type': 'capability_map',
        'title': tc.get('main_title', illu.get('title', '')),
        'subtitle': illu.get('subtitle', ''),
        'placement': illu.get('chapter_ref', ''),
    }
    groups = []
    for s5_layer in tc.get('layers', []):
        items = []
        for node in s5_layer.get('nodes', []):
            raw_name = node.get('name', node.get('label', ''))
            raw_desc = node.get('subtitle', node.get('detail', ''))
            item = {
                'title': _summarize_node_name(raw_name, 20),
                'desc': _summarize_node_desc(raw_desc, 35),
            }
            if node.get('is_highlighted'):
                item['style'] = 'accent'
            items.append(item)
        groups.append({'label': s5_layer.get('name', ''), 'icon': '', 'items': items})

    spec['groups'] = groups
    spec['columns'] = 2 if len(groups) > 3 else min(len(groups), 3)

    footnote = tc.get('footnote', '')
    if footnote:
        spec['note'] = footnote[:300]
    return spec


def _convert_relationship_map(illu):
    tc = illu.get('text_content', {})
    spec = {
        'type': 'relationship_map',
        'title': tc.get('main_title', illu.get('title', '')),
        'subtitle': illu.get('subtitle', ''),
        'placement': illu.get('chapter_ref', ''),
    }
    containers = []
    edges = []
    all_node_ids = []
    node_idx = 0

    for layer_idx, s5_layer in enumerate(tc.get('layers', [])):
        container_nodes = []
        for node in s5_layer.get('nodes', []):
            nid = f"Rn{node_idx:02d}"
            raw_name = node.get('name', node.get('label', ''))
            raw_sub = node.get('subtitle', node.get('detail', ''))
            container_nodes.append({
                'id': nid,
                'title': _summarize_node_name(raw_name, 22),
                'subtitle': _summarize_node_desc(raw_sub, 45),
            })
            all_node_ids.append(nid)
            node_idx += 1

        containers.append({
            'id': f"C{layer_idx:02d}",
            'title': s5_layer.get('name', ''),
            'subtitle': s5_layer.get('description', '')[:120],
            'row': layer_idx, 'col': 0,
            'columns': 1 if len(container_nodes) <= 3 else 2,
            'nodes': container_nodes,
        })

    for i in range(len(containers) - 1):
        src_nodes = containers[i]['nodes']
        dst_nodes = containers[i + 1]['nodes']
        if src_nodes and dst_nodes:
            edges.append({'from': src_nodes[-1]['id'], 'to': dst_nodes[0]['id'], 'label': '', 'relation': 'data'})

    if not edges and len(all_node_ids) >= 2:
        edges.append({'from': all_node_ids[0], 'to': all_node_ids[-1], 'label': '关联', 'relation': 'data'})

    spec['containers'] = containers
    spec['edges'] = edges
    spec['columns'] = min(len(containers), 3)

    footnote = tc.get('footnote', '')
    if footnote:
        spec['note'] = footnote[:300]
    return spec


CONVERTERS = {
    'layered_architecture': _convert_layered_architecture,
    'flowchart': _convert_flowchart,
    'capability_map': _convert_capability_map,
    'relationship_map': _convert_relationship_map,
}


def convert_s5_to_job(s5_dir, s5_validated_dir=None, s6_dir=None, chapter_section_map=None,
                      html_illu_ids=None, document_title=None, project_name=None):
    """Convert S5 illustration JSONs to unified job format for illustration toolkit.

    Args:
        s5_dir: Path to s5_illustrations directory
        s5_validated_dir: Path to s5_5_validated directory (LLM-validated versions, optional)
        s6_dir: Path to s6_synthesis output directory
        chapter_section_map: Dict mapping chapter IDs to section labels
        html_illu_ids: Set of illustration IDs that are pre-generated as HTML
        document_title: Document title for the job
        project_name: Project name for the job

    Returns:
        Path to the generated job JSON file
    """
    s5_dir = Path(s5_dir)
    s6_dir = Path(s6_dir) if s6_dir else Path.cwd() / 'output' / 's6_synthesis'
    if chapter_section_map is None:
        chapter_section_map = DEFAULT_CHAPTER_SECTION_MAP
    if html_illu_ids is None:
        html_illu_ids = set()
    if document_title is None:
        document_title = '投标文件 — 技术方案'
    if project_name is None:
        project_name = '投标项目'

    illustrations = []
    errors = []
    _using_validated = False

    illu_files = sorted([
        f for f in os.listdir(s5_dir)
        if f.endswith('.json') and f != 's5_illustrations.json'
    ])

    print(f"Found {len(illu_files)} illustration files")

    for fname in illu_files:
        illu_id_base = fname.replace('.json', '')
        illu_path = s5_dir / fname

        # Prefer validated version if available
        if s5_validated_dir:
            validated_path = Path(s5_validated_dir) / fname
            if validated_path.exists():
                illu_path = validated_path
                _using_validated = True

        try:
            illu = _load_json(illu_path)
        except Exception as e:
            errors.append(f"Failed to load {fname}: {e}")
            continue

        illu_id = illu.get('illu_id', '')
        s5_type = illu.get('type', '')

        if s5_type in TYPE_MAP:
            renderer, diag_type = TYPE_MAP[s5_type]
        else:
            print(f"  WARNING: Unknown type '{s5_type}' for {illu_id}, defaulting to capability_map")
            renderer, diag_type = 'svg', 'capability_map'

        if illu_id in html_illu_ids:
            print(f"  SKIP (HTML): {illu_id} — pre-rendered via HTML generator")
            continue

        converter = CONVERTERS.get(diag_type, _convert_capability_map)
        try:
            spec = converter(illu)
        except Exception as e:
            errors.append(f"Failed to convert {fname}: {e}")
            continue

        chapter_ref = illu.get('chapter_ref', '')
        section = _get_chapter_section(chapter_ref, chapter_section_map)
        if '.' in chapter_ref:
            section = f"{section} (第{chapter_ref.split('.')[1]}节)"

        illu_title = illu.get('title', '')
        caption = f"{illu_id} {illu_title}"

        tc = illu.get('text_content', {})
        layers = tc.get('layers', [])
        after_text = ''
        if layers:
            after_text = layers[0].get('description', '')[:100]

        illustrations.append({
            'id': _make_id(illu_id),
            'renderer': renderer,
            'insertion': {
                'section': section,
                'afterText': after_text,
                'caption': caption,
                'purpose': illu.get('subtitle', illu_title)[:100],
            },
            'spec': spec,
            '_s5_illu_id': illu_id,
            '_s5_chapter_ref': chapter_ref,
        })

    job = {
        'version': '1.0',
        'document': {
            'title': document_title,
            'projectName': project_name,
            'bidSection': '技术方案',
        },
        'style': {
            'theme': 'clarity_blue',
            'preferredFormat': 'both',
        },
        'illustrations': illustrations,
    }

    s6_dir = Path(s6_dir)
    s6_dir.mkdir(parents=True, exist_ok=True)
    job_path = s6_dir / 's6_unified_job.json'
    _save_json(job, job_path)

    # Generate HTML illustration manifest entries
    html_manifest_entries = []
    for fname in illu_files:
        fpath = s5_dir / fname
        try:
            illu = _load_json(fpath)
        except Exception:
            continue
        illu_id = illu.get('illu_id', '')
        if illu_id not in html_illu_ids:
            continue

        chapter_ref = illu.get('chapter_ref', '')
        section = _get_chapter_section(chapter_ref, chapter_section_map)
        if '.' in chapter_ref:
            section = f"{section} (第{chapter_ref.split('.')[1]}节)"

        tc = illu.get('text_content', {})
        html_manifest_entries.append({
            'id': _make_id(illu_id),
            'renderer': 'html',
            'section': section,
            'caption': f"{illu_id} {illu.get('title', '')}",
            'purpose': illu.get('title', '')[:100],
            'title': tc.get('main_title', illu.get('title', '')),
            '_s5_illu_id': illu_id,
            '_s5_chapter_ref': chapter_ref,
            'outputs': {'png': f'assets/{illu_id}.png'},
        })

    html_manifest_path = s6_dir / 'html_manifest_entries.json'
    _save_json({'illustrations': html_manifest_entries}, html_manifest_path)

    print(f"\nSVG illustrations: {len(illustrations)}")
    print(f"HTML illustrations: {len(html_manifest_entries)}")
    if _using_validated:
        print(f"Source: LLM-validated S5 files — code truncation minimal")
    else:
        print(f"Source: Original S5 files — code-based truncation active")
    print(f"Errors: {len(errors)}")
    for e in errors:
        print(f"  - {e}")
    print(f"\nJob saved to: {job_path}")
    print(f"HTML entries saved to: {html_manifest_path}")

    type_counts = {}
    for ill in illustrations:
        t = ill['spec']['type']
        type_counts[t] = type_counts.get(t, 0) + 1
    print("\nDiagram type distribution:")
    for t, c in sorted(type_counts.items()):
        print(f"  {t}: {c}")

    return str(job_path)


# ─── Phase B: Synthesize illustrations into chapter markdown ───

def _parse_section(section_str):
    if not section_str:
        return None, None
    section_str = section_str.strip()
    # Pattern: "CH-01" or "CH-01.2"
    direct = re.match(r'^(CH-\d+)(?:[.\-](\d+))?$', section_str, re.IGNORECASE)
    if direct:
        return direct.group(1).upper(), direct.group(2)
    # Pattern: "1.2 标题" or "1 标题" (dotted or spaced chapter number)
    match = re.match(r'(\d+)(?:\.(\d+))?\s+', section_str)
    if match:
        ch_num = match.group(1)
        sub_sec = match.group(2)
        ch_key = CHAPTER_NUM_MAP.get(ch_num, f'CH-{int(ch_num):02d}')
        return ch_key, sub_sec
    return None, None


def _select_manifest_image(illu):
    outputs = illu.get('outputs', {})
    for key in ('png', 'svg', 'html', 'reviewHtml'):
        value = outputs.get(key)
        if value:
            return key, value
    return None, None


def _find_insertion_point(lines, ch_key, sub_sec):
    ch_num = int(ch_key.split('-')[1])

    if sub_sec:
        target_header = f'## {ch_num}.{sub_sec} '
        for i, line in enumerate(lines):
            if line.startswith(target_header):
                for j in range(i + 1, len(lines)):
                    if lines[j].startswith('## ') and not lines[j].startswith('###'):
                        return j
                return len(lines)

        target_header_no_space = f'## {ch_num}.{sub_sec}'
        for i, line in enumerate(lines):
            if line.startswith(target_header_no_space) and (
                    len(line) == len(target_header_no_space) or
                    not line[len(target_header_no_space)].isdigit()):
                for j in range(i + 1, len(lines)):
                    if lines[j].startswith('## ') and not lines[j].startswith('###'):
                        return j
                return len(lines)

        # Exact match failed. Try finding a nearby subsection.
        # Try the next higher subsection (e.g., 1.5 not found → try 1.4, 1.3...)
        sub_num = int(sub_sec)
        for fallback_sub in range(sub_num - 1, 0, -1):
            fb_header = f'## {ch_num}.{fallback_sub} '
            for i, line in enumerate(lines):
                if line.startswith(fb_header):
                    for j in range(i + 1, len(lines)):
                        if lines[j].startswith('## ') and not lines[j].startswith('###'):
                            return j
                    return len(lines)

        # Fallback: insert before the last ## heading in the chapter
        last_h2 = None
        for i, line in enumerate(lines):
            if line.startswith(f'## {ch_num}.') and not line.startswith('###'):
                last_h2 = i
        if last_h2 is not None:
            for j in range(last_h2 + 1, len(lines)):
                if lines[j].startswith('## ') and not lines[j].startswith('###'):
                    return j
            return len(lines)

        # Ultimate fallback: end of chapter
        print(f"  WARNING: Section '{ch_num}.{sub_sec}' not found in {ch_key}, inserting at chapter end")
        return len(lines)
    else:
        for i, line in enumerate(lines):
            if line.startswith('## ') and not line.startswith('###'):
                return i
        return len(lines)


def _build_image_markdown(illu, assets_rel_dir, figure_number):
    illu_id_orig = illu.get('_s5_illu_id', illu['id'].upper().replace('_', '-'))
    title = illu.get('title', '')
    caption_text = title if title else illu.get('caption', '')
    asset_name = illu.get('outputs', {}).get('_s6_asset')
    asset_kind = illu.get('outputs', {}).get('_s6_asset_kind')
    if asset_name:
        image_path = asset_name
    else:
        asset_kind, asset_name = _select_manifest_image(illu)
        if not asset_name:
            raise ValueError(f"{illu.get('id')}: manifest outputs 中缺少 png/svg/html")
        image_path = f"{assets_rel_dir}/{os.path.basename(asset_name)}"
    figure_label = f"{figure_number}  {illu_id_orig} {caption_text}"

    if asset_kind == 'html' or str(image_path).lower().endswith(('.html', '.htm')):
        return [
            '',
            f'[查看交互式图件：{caption_text}]({image_path})',
            '',
            f'*{figure_label}*',
            '',
        ]

    return [
        '',
        f'![{caption_text}]({image_path})',
        '',
        f'*{figure_label}*',
        '',
    ]


def _copy_manifest_assets(manifest, manifest_path, assets_dir):
    manifest_dir = Path(manifest_path).parent
    # The manifest output paths may be relative to the project output directory
    # rather than the manifest directory. Try multiple base paths.
    output_root = manifest_dir
    while output_root.name != 'output' and output_root.parent != output_root:
        output_root = output_root.parent
    base_candidates = [
        manifest_dir,
        output_root,  # e.g., output/
        output_root.parent if output_root.name == 'output' else None,  # project root
    ]
    base_candidates = [p for p in base_candidates if p is not None]

    assets_dir.mkdir(parents=True, exist_ok=True)
    copied_count = 0

    for illu in manifest.get('illustrations', []):
        kind, rel_path = _select_manifest_image(illu)
        if not rel_path:
            print(f"  WARNING: {illu.get('id')} has no png/svg/html output, skipped")
            continue

        # Try each base path
        src = None
        for base in base_candidates:
            candidate = base / rel_path
            if candidate.exists():
                src = candidate
                break

        if src is None:
            print(f"  WARNING: asset missing for {illu.get('id')}: tried {[str(b / rel_path) for b in base_candidates]}")
            continue
        safe_id = re.sub(r'[^A-Za-z0-9_-]+', '_', illu.get('id', 'figure')).strip('_') or 'figure'
        suffix = src.suffix or {'svg': '.svg', 'html': '.html'}.get(kind, '.png')
        dst_name = f"{safe_id}_{src.stem}{suffix}"
        dst = assets_dir / dst_name
        shutil.copy2(src, dst)
        outputs = illu.setdefault('outputs', {})
        outputs['_s6_asset'] = f"assets/{dst_name}"
        outputs['_s6_asset_kind'] = kind
        copied_count += 1

    return copied_count


def _load_table_plan(table_plan_path=None):
    if table_plan_path:
        path = Path(table_plan_path)
    else:
        path = Path.cwd() / 'output' / 's5_tables' / 'table_insertion_plan.json'
    if not path.exists():
        return {"tables": []}
    return _load_json(path)


def _build_table_markdown(table, table_number):
    columns = [str(col).strip() for col in table.get('columns', [])]
    rows = table.get('rows', [])
    title = table.get('title') or table.get('id', table_number)
    title = re.sub(r'^表\s*\d+\s*[-－]\s*\d+\s*', '', str(title)).strip() or str(title)
    purpose = table.get('purpose', '')
    notes = table.get('notes', [])

    lines = ['', f'*{table_number}  {title}*', '']
    if purpose:
        lines.extend([f'> {purpose}', ''])
    lines.append('| ' + ' | '.join(columns) + ' |')
    lines.append('| ' + ' | '.join(['---'] * len(columns)) + ' |')
    for row in rows:
        values = [str(value).replace('\n', '<br>') for value in row]
        if len(values) < len(columns):
            values.extend([''] * (len(columns) - len(values)))
        if len(values) > len(columns):
            values = values[:len(columns)]
        lines.append('| ' + ' | '.join(values) + ' |')
    if notes:
        lines.append('')
        lines.extend(f'> 注：{note}' for note in notes)
    lines.append('')
    return lines


def _auto_discover_chapter_files(s3_chapters_dir):
    """Auto-discover CH-XX_*.md files from the chapters directory.

    Falls back to the parent directory if no CH-* files found in the given dir.
    Returns a dict {CH-XX: filename} and the actual directory used.
    """
    chapters_dir = Path(s3_chapters_dir)
    actual_dir = chapters_dir

    def _scan(directory):
        result = {}
        for f in sorted(directory.glob('CH-*.md')):
            m = re.match(r'(CH-\d+)', f.name, re.IGNORECASE)
            if m:
                result[m.group(1).upper()] = f.name
        # Also scan lowercase ch_XX.md patterns
        if not result:
            for f in sorted(directory.glob('ch_*.md')):
                m = re.match(r'(ch-\d+)', f.name, re.IGNORECASE)
                if m:
                    result[m.group(1).upper()] = f.name
        return result

    chapter_files = _scan(chapters_dir)
    if not chapter_files:
        # Fall back: try parent directory (s3_body directly, not s3_body/chapters)
        parent = chapters_dir.parent
        chapter_files = _scan(parent)
        if chapter_files:
            actual_dir = parent

    if not chapter_files:
        # Last resort: try parent's parent (e.g., s3_body without chapters subdir
        # but chapters_dir was pointing to something else)
        for ancestor in [chapters_dir.parent, chapters_dir.parent.parent]:
            chapter_files = _scan(ancestor)
            if chapter_files:
                actual_dir = ancestor
                break

    return chapter_files, actual_dir


def _resolve_manifest_path(s6_dir, toolkit_results_dir, s5_dir):
    """Search for illustration-manifest.json in multiple locations."""
    candidates = [
        s6_dir / 'illustration-manifest.json',
    ]
    if toolkit_results_dir:
        candidates.append(Path(toolkit_results_dir) / 'illustration-manifest.json')
    if s5_dir:
        candidates.append(Path(s5_dir) / 'images' / 'illustration-manifest.json')
    # Also search output/s5_illustrations/images/
    candidates.append(s6_dir.parent / 's5_illustrations' / 'images' / 'illustration-manifest.json')
    for candidate in candidates:
        if candidate.exists():
            return candidate
    return candidates[0]  # Return primary path even if missing (will error with clear message)


def _enrich_manifest_from_job(manifest, s5_job_path):
    """If manifest entries lack section/caption, enrich from the S5 illustration job."""
    if not s5_job_path or not Path(s5_job_path).exists():
        return manifest

    s5_job = _load_json(s5_job_path)
    # Build a lookup from illu_id → {section, title, chapter_ref}
    illu_lookup = {}
    for ill in s5_job.get('illustrations', []):
        illu_id = ill.get('id', '')
        chapter_ref = ill.get('insertion', {}).get('section', '')
        caption = ill.get('insertion', {}).get('caption', '')
        if not chapter_ref:
            chapter_ref = ill.get('_s5_chapter_ref', '')
        if not caption:
            caption = ill.get('_s5_illu_id', illu_id) + ' ' + ill.get('spec', {}).get('title', '')
        illu_lookup[illu_id] = {
            'section': chapter_ref,
            'caption': caption,
        }

    for entry in manifest.get('illustrations', []):
        eid = entry.get('id', '')
        # Normalize: try TU-001, tu_001, TU_001 variations
        info = illu_lookup.get(eid) or illu_lookup.get(eid.replace('-', '_').upper()) or illu_lookup.get(eid.replace('_', '-'))
        if info:
            if not entry.get('section'):
                entry['section'] = info['section']
            if not entry.get('caption'):
                entry['caption'] = info['caption']
            if not entry.get('purpose'):
                entry['purpose'] = entry.get('intent', '')

    return manifest


def synthesize(s3_chapters_dir=None, s6_dir=None, toolkit_results_dir=None,
               chapter_files=None, manifest_path=None, table_plan_path=None,
               s5_dir=None):
    """Insert illustrations into chapter markdown files and generate combined document.

    Args:
        s3_chapters_dir: Path to s3_body/chapters directory (auto-discovered if None)
        s6_dir: Path to s6_synthesis output directory
        toolkit_results_dir: Path to illustration toolkit results directory
        chapter_files: Dict mapping chapter IDs to filenames (auto-discovered if None)
        manifest_path: Path to illustration-manifest.json (auto-discovered if None)
        table_plan_path: Path to table_insertion_plan.json
        s5_dir: Path to s5_illustrations directory (for job file enrichment)
    """
    output_dir = Path.cwd() / 'output'
    s3_chapters_dir = Path(s3_chapters_dir) if s3_chapters_dir else output_dir / 's3_body' / 'chapters'
    s6_dir = Path(s6_dir) if s6_dir else output_dir / 's6_synthesis'

    if chapter_files is None:
        chapter_files, s3_chapters_dir = _auto_discover_chapter_files(s3_chapters_dir)
        if not chapter_files:
            print("  WARNING: No CH-*.md chapter files found. Using empty mapping.")
            chapter_files = {}
        else:
            print(f"  Auto-discovered {len(chapter_files)} chapter files in {s3_chapters_dir}")
            for ch in sorted(chapter_files):
                print(f"    {ch}: {chapter_files[ch]}")

    # Resolve manifest path
    if manifest_path:
        manifest_path = Path(manifest_path)
    else:
        s5_dir_resolved = Path(s5_dir) if s5_dir else output_dir / 's5_illustrations'
        manifest_path = _resolve_manifest_path(s6_dir, toolkit_results_dir, s5_dir_resolved)
    print(f"  Manifest: {manifest_path}")
    manifest = _load_json(manifest_path)

    # Enrich manifest entries with section/caption from S5 job file if missing
    s5_job_path = s6_dir.parent / 's5_illustrations' / 's5_illustration_job.json'
    manifest = _enrich_manifest_from_job(manifest, s5_job_path)

    # Load id → s5_id mapping
    id_to_s5 = {}
    job_path = s6_dir / 's6_unified_job.json'
    html_entries_path = s6_dir / 'html_manifest_entries.json'

    if job_path.exists():
        job = _load_json(job_path)
        for ill in job['illustrations']:
            id_to_s5[ill['id']] = ill.get('_s5_illu_id', ill['id'].upper())

    if html_entries_path.exists():
        html_entries = _load_json(html_entries_path)
        for ill in html_entries['illustrations']:
            id_to_s5[ill['id']] = ill.get('_s5_illu_id', ill['id'].upper())

    # Create assets directory and copy manifest-referenced files. S6 consumes
    # only the public manifest contract; renderer-private folders stay hidden.
    assets_dir = s6_dir / 'assets'
    copied_count = _copy_manifest_assets(manifest, manifest_path, assets_dir)
    print(f"Refreshed {copied_count} manifest asset files in {assets_dir}")

    # Group illustrations by chapter
    chapter_illus = defaultdict(list)
    for ill in manifest['illustrations']:
        s5_id = id_to_s5.get(ill['id'], ill['id'])
        ill['_s5_illu_id'] = s5_id

        section_str = ill.get('section', '')
        ch_key, sub_sec = _parse_section(section_str)

        if ch_key:
            chapter_illus[ch_key].append({'ill': ill, 'sub_sec': sub_sec})
        else:
            print(f"  WARNING: Could not parse section '{section_str}' for {ill['id']}")

    print(f"\nIllustrations by chapter:")
    for ch_key in sorted(chapter_illus.keys()):
        print(f"  {ch_key}: {len(chapter_illus[ch_key])} illustrations")

    table_plan = _load_table_plan(table_plan_path)
    chapter_tables = defaultdict(list)
    for table in table_plan.get('tables', []):
        ch_key, sub_sec = _parse_section(table.get('section', ''))
        if ch_key:
            chapter_tables[ch_key].append({'table': table, 'sub_sec': sub_sec})
        else:
            print(f"  WARNING: Could not parse table section '{table.get('section', '')}' for {table.get('id')}")

    if chapter_tables:
        print(f"\nTables by chapter:")
        for ch_key in sorted(chapter_tables.keys()):
            print(f"  {ch_key}: {len(chapter_tables[ch_key])} tables")

    syn_chapters_dir = s6_dir / 'chapters'
    syn_chapters_dir.mkdir(parents=True, exist_ok=True)

    insertion_log = []
    table_insertion_log = []
    total_inserted = 0
    total_tables_inserted = 0

    for ch_key, ch_fname in chapter_files.items():
        ch_path = s3_chapters_dir / ch_fname
        if not ch_path.exists():
            print(f"  ERROR: Chapter file not found: {ch_path}")
            continue

        with open(ch_path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')
        illus_list = chapter_illus.get(ch_key, [])
        tables_list = chapter_tables.get(ch_key, [])

        if not illus_list and not tables_list:
            syn_path = syn_chapters_dir / ch_fname
            with open(syn_path, 'w', encoding='utf-8') as f:
                f.write(content)
            continue

        def _sort_key(item):
            sub_sec = item['sub_sec']
            if sub_sec is None:
                return (0, 0)
            try:
                return (1, int(sub_sec))
            except (ValueError, TypeError):
                return (1, 999)
        sorted_illus = sorted(illus_list, key=_sort_key)
        sorted_tables = sorted(tables_list, key=_sort_key)

        ch_num = int(ch_key.split('-')[1])

        table_insertions = []
        table_counter = 1
        for item in sorted_tables:
            table = item['table']
            sub_sec = item['sub_sec']
            insert_at = _find_insertion_point(lines, ch_key, sub_sec)
            if insert_at is not None:
                table_number = f'表 {ch_num}-{table_counter}'
                table_lines = _build_table_markdown(table, table_number)
                table_insertions.append((insert_at, table_lines, table.get('id', ''), table_number))
                table_insertion_log.append({
                    'chapter': ch_key,
                    'table_id': table.get('id', ''),
                    'table_number': table_number,
                    'inserted_at_line': insert_at,
                    'section_ref': table.get('section', ''),
                })
                total_tables_inserted += 1
                table_counter += 1
            else:
                print(f"  WARNING: Could not insert table {table.get('id')} in {ch_key}")

        raw_insertions = []
        for item in sorted_illus:
            ill = item['ill']
            sub_sec = item['sub_sec']
            s5_id = ill.get('_s5_illu_id', '')

            insert_at = _find_insertion_point(lines, ch_key, sub_sec)
            if insert_at is not None:
                raw_insertions.append((insert_at, s5_id, ill))
                total_inserted += 1
            else:
                print(f"  WARNING: Could not insert {s5_id} in {ch_key}")

        raw_insertions.sort(key=lambda x: x[0], reverse=True)
        grouped = defaultdict(list)
        for item in raw_insertions:
            grouped[item[0]].append(item)
        raw_insertions = []
        for insert_at in sorted(grouped.keys(), reverse=True):
            raw_insertions.extend(reversed(grouped[insert_at]))

        fig_num_map = {}
        fig_counter = 1
        for item in sorted_illus:
            s5_id = item['ill'].get('_s5_illu_id', '')
            if s5_id in {x[1] for x in raw_insertions}:
                fig_num_map[s5_id] = f'图 {ch_num}-{fig_counter}'
                fig_counter += 1

        insertions = []
        for insert_at, s5_id, ill in raw_insertions:
            figure_number = fig_num_map[s5_id]
            try:
                img_lines = _build_image_markdown(ill, 'assets', figure_number)
                insertions.append((insert_at, img_lines, s5_id))
            except ValueError as exc:
                print(f"  WARNING: Skipping {s5_id} — {exc}")
                continue
            insertion_log.append({
                'chapter': ch_key,
                'illu_id': s5_id,
                'figure_number': figure_number,
                'inserted_at_line': insert_at,
                'section_ref': ill.get('section', ''),
            })

        combined_insertions = []
        combined_insertions.extend((insert_at, 0, table_lines) for insert_at, table_lines, _, _ in table_insertions)
        combined_insertions.extend((insert_at, 1, img_lines) for insert_at, img_lines, _ in insertions)
        combined_insertions.sort(key=lambda x: (x[0], x[1]), reverse=True)
        for insert_at, _, block_lines in combined_insertions:
            for j, block_line in enumerate(block_lines):
                lines.insert(insert_at + j, block_line)

        syn_content = '\n'.join(lines)
        syn_path = syn_chapters_dir / ch_fname
        with open(syn_path, 'w', encoding='utf-8') as f:
            f.write(syn_content)

        print(f"  {ch_key}: inserted {len(table_insertions)} tables, {len(insertions)} illustrations → {syn_path}")

    report = {
        'stage': 's6_synthesis',
        'total_illustrations': len(manifest['illustrations']),
        'total_tables': len(table_plan.get('tables', [])),
        'total_tables_inserted': total_tables_inserted,
        'total_inserted': total_inserted,
        'chapters_processed': len(chapter_files),
        'assets_copied': copied_count,
        'insertion_log': insertion_log,
        'table_insertion_log': table_insertion_log,
        'chapter_files': {ch: str(syn_chapters_dir / fname) for ch, fname in chapter_files.items()},
    }

    report_path = s6_dir / 's6_synthesis_report.json'
    _save_json(report, report_path)

    combined_path = s6_dir / 's6_combined_bid_document.md'
    with open(combined_path, 'w', encoding='utf-8') as out:
        for ch_key in sorted(chapter_files.keys(), key=lambda k: int(k.split('-')[1])):
            ch_fname = chapter_files[ch_key]
            syn_ch_path = syn_chapters_dir / ch_fname
            if syn_ch_path.exists():
                with open(syn_ch_path, 'r', encoding='utf-8') as f:
                    out.write(f.read())
                out.write('\n\n')

    print(f"\n{'='*60}")
    print(f"Stage 6 Synthesis Complete")
    print(f"{'='*60}")
    print(f"  Illustrations: {len(manifest['illustrations'])}")
    print(f"  Tables:        {total_tables_inserted}/{len(table_plan.get('tables', []))}")
    print(f"  Inserted:      {total_inserted}")
    print(f"  Assets copied: {copied_count}")
    print(f"  Chapters:      {len(chapter_files)}")
    print(f"  Combined doc:  {combined_path}")
    print(f"  Report:        {report_path}")


# ─── CLI ───

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Stage 6: Render and synthesize illustrations into chapters')
    parser.add_argument('action', nargs='?', default='all',
                        choices=['render', 'synthesize', 'all', 'legacy-convert', 'convert'],
                        help='Which phase to run')
    parser.add_argument('--s5-dir', type=Path, help='S5 illustrations directory')
    parser.add_argument('--s5-validated-dir', type=Path, help='S5 validated directory')
    parser.add_argument('--s3-chapters-dir', type=Path, help='S3 chapters directory')
    parser.add_argument('--s6-dir', type=Path, help='S6 output directory')
    parser.add_argument('--toolkit-results', type=Path, help='Toolkit results directory')
    parser.add_argument('--table-plan', type=Path, help='Table insertion plan JSON')
    parser.add_argument('--project', help='Project name')
    parser.add_argument('--no-png', action='store_true', help='Do not export PNG previews during render')
    parser.add_argument('--png-scale', type=int, choices=(1, 2, 3), default=2, help='PNG export scale')
    parser.add_argument('--no-echarts-export', action='store_true',
                        help='ECharts only generates local review pages')
    args = parser.parse_args()

    output_dir = Path.cwd() / 'output'
    s5_dir = args.s5_dir or output_dir / 's5_illustrations'
    s6_dir = args.s6_dir or output_dir / 's6_synthesis'

    manifest_path = None

    if args.action in ('render', 'all'):
        manifest_path = render_v2_job(
            s5_dir=s5_dir,
            images_dir=args.toolkit_results or (s5_dir / 'images'),
            png=not args.no_png,
            png_scale=args.png_scale,
            export_echarts=not args.no_echarts_export,
        )

    if args.action in ('legacy-convert', 'convert'):
        if args.action == 'convert':
            print("[WARN] action 'convert' is legacy. Prefer 'render' or 'all' for Illustration Job v2.")
        convert_s5_to_job(
            s5_dir=s5_dir,
            s5_validated_dir=args.s5_validated_dir,
            s6_dir=s6_dir,
            project_name=args.project,
        )

    if args.action in ('synthesize', 'all'):
        synthesize(
            s3_chapters_dir=args.s3_chapters_dir,
            s6_dir=s6_dir,
            toolkit_results_dir=args.toolkit_results or (s5_dir / 'images'),
            manifest_path=manifest_path,
            table_plan_path=args.table_plan,
        )
