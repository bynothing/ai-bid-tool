"""Stage 6: Synthesize diagrams into chapter markdown files.

Two-phase process:
  Phase A (convert): Read S5 illustration JSONs → unified job JSON for illustration toolkit
  Phase B (synthesize): Read illustration-manifest.json → insert images into chapter markdown

Usage:
  python s6_synthesize.py convert                          # Phase A only
  python s6_synthesize.py synthesize                       # Phase B only
  python s6_synthesize.py all                              # Both phases
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
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _save_json(data, path):
    Path(path).parent.mkdir(parents=True, exist_ok=True)
    with open(path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


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
    match = re.match(r'(\d+)\s+.+?(?:\(第(\d+)节\))?$', section_str)
    if match:
        ch_num = match.group(1)
        sub_sec = match.group(2)
        ch_key = CHAPTER_NUM_MAP.get(ch_num, f'CH-{int(ch_num):02d}')
        return ch_key, sub_sec
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

        print(f"  WARNING: Section header '{target_header}' not found in chapter {ch_key}")
        return None
    else:
        for i, line in enumerate(lines):
            if line.startswith('## ') and not line.startswith('###'):
                return i
        return len(lines)


def _build_image_markdown(illu, assets_rel_dir, figure_number):
    illu_id_orig = illu.get('_s5_illu_id', illu['id'].upper().replace('_', '-'))
    title = illu.get('title', '')
    caption_text = title if title else illu.get('caption', '')
    png_file = os.path.basename(illu['outputs']['png'])
    png_path = f"{assets_rel_dir}/{png_file}"
    figure_label = f"**{figure_number}  {illu_id_orig}** {caption_text}"

    return [
        '',
        f'![{caption_text}]({png_path})',
        '',
        f'*{figure_label}*',
        '',
    ]


def synthesize(s3_chapters_dir=None, s6_dir=None, toolkit_results_dir=None,
               chapter_files=None, manifest_path=None):
    """Insert illustrations into chapter markdown files and generate combined document.

    Args:
        s3_chapters_dir: Path to s3_body/chapters directory
        s6_dir: Path to s6_synthesis output directory
        toolkit_results_dir: Path to illustration toolkit results directory
        chapter_files: Dict mapping chapter IDs to filenames
        manifest_path: Path to illustration-manifest.json (overrides default)
    """
    output_dir = Path.cwd() / 'output'
    s3_chapters_dir = Path(s3_chapters_dir) if s3_chapters_dir else output_dir / 's3_body' / 'chapters'
    s6_dir = Path(s6_dir) if s6_dir else output_dir / 's6_synthesis'

    if chapter_files is None:
        chapter_files = {
            'CH-01': 'CH-01_项目理解与总体技术方案.md',
            'CH-02': 'CH-02_资质保密与合规保障.md',
            'CH-03': 'CH-03_总体集成通用技术方案.md',
            'CH-04': 'CH-04_人机交互界面设计.md',
            'CH-05': 'CH-05_数据库模块技术方案.md',
            'CH-06': 'CH-06_材料设计模块技术方案.md',
            'CH-07': 'CH-07_热环境确定模块技术方案.md',
            'CH-08': 'CH-08_热环境响应评估模块技术方案.md',
            'CH-09': 'CH-09_运行环境兼容性与离线部署方案.md',
            'CH-10': 'CH-10_集成对接与数据贯通方案.md',
            'CH-11': 'CH-11_项目实施与交付方案.md',
            'CH-12': 'CH-12_测试验收与质量保障.md',
            'CH-13': 'CH-13_售后服务与质保承诺.md',
        }

    # Resolve manifest path
    if manifest_path:
        manifest_path = Path(manifest_path)
    else:
        manifest_path = s6_dir / 'illustration-manifest.json'
        if not manifest_path.exists() and toolkit_results_dir:
            manifest_path = Path(toolkit_results_dir) / 'illustration-manifest.json'
    manifest = _load_json(manifest_path)

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

    # Create assets directory and copy files
    assets_dir = s6_dir / 'assets'
    assets_dir.mkdir(parents=True, exist_ok=True)

    copied_count = 0
    if toolkit_results_dir:
        svg_assets_dir = Path(toolkit_results_dir) / 'assets' / 'svg'
        if svg_assets_dir.exists():
            for fname in os.listdir(svg_assets_dir):
                if fname.endswith(('.svg', '.png')):
                    src = svg_assets_dir / fname
                    dst = assets_dir / fname
                    shutil.copy2(src, dst)
                    copied_count += 1
            print(f"Refreshed {copied_count} asset files in {assets_dir}")

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

    syn_chapters_dir = s6_dir / 'chapters'
    syn_chapters_dir.mkdir(parents=True, exist_ok=True)

    insertion_log = []
    total_inserted = 0

    for ch_key, ch_fname in chapter_files.items():
        ch_path = s3_chapters_dir / ch_fname
        if not ch_path.exists():
            print(f"  ERROR: Chapter file not found: {ch_path}")
            continue

        with open(ch_path, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')
        illus_list = chapter_illus.get(ch_key, [])

        if not illus_list:
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

        ch_num = int(ch_key.split('-')[1])

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
            img_lines = _build_image_markdown(ill, 'assets', figure_number)
            insertions.append((insert_at, img_lines, s5_id))
            insertion_log.append({
                'chapter': ch_key,
                'illu_id': s5_id,
                'figure_number': figure_number,
                'inserted_at_line': insert_at,
                'section_ref': ill.get('section', ''),
            })

        for insert_at, img_lines, s5_id in insertions:
            for j, img_line in enumerate(img_lines):
                lines.insert(insert_at + j, img_line)

        syn_content = '\n'.join(lines)
        syn_path = syn_chapters_dir / ch_fname
        with open(syn_path, 'w', encoding='utf-8') as f:
            f.write(syn_content)

        print(f"  {ch_key}: inserted {len(insertions)} illustrations → {syn_path}")

    report = {
        'stage': 's6_synthesis',
        'total_illustrations': len(manifest['illustrations']),
        'total_inserted': total_inserted,
        'chapters_processed': len(chapter_files),
        'assets_copied': copied_count,
        'insertion_log': insertion_log,
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
    print(f"  Inserted:      {total_inserted}")
    print(f"  Assets copied: {copied_count}")
    print(f"  Chapters:      {len(chapter_files)}")
    print(f"  Combined doc:  {combined_path}")
    print(f"  Report:        {report_path}")


# ─── CLI ───

if __name__ == '__main__':
    import argparse
    parser = argparse.ArgumentParser(description='Stage 6: Synthesize illustrations into chapters')
    parser.add_argument('action', nargs='?', default='all',
                        choices=['convert', 'synthesize', 'all'],
                        help='Which phase to run')
    parser.add_argument('--s5-dir', type=Path, help='S5 illustrations directory')
    parser.add_argument('--s5-validated-dir', type=Path, help='S5 validated directory')
    parser.add_argument('--s3-chapters-dir', type=Path, help='S3 chapters directory')
    parser.add_argument('--s6-dir', type=Path, help='S6 output directory')
    parser.add_argument('--toolkit-results', type=Path, help='Toolkit results directory')
    parser.add_argument('--project', help='Project name')
    args = parser.parse_args()

    output_dir = Path.cwd() / 'output'
    s5_dir = args.s5_dir or output_dir / 's5_illustrations'
    s6_dir = args.s6_dir or output_dir / 's6_synthesis'

    if args.action in ('convert', 'all'):
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
            toolkit_results_dir=args.toolkit_results,
        )
