"""HTML-based renderer for UI prototypes, compatibility matrices, and Gantt charts.

Generates self-contained HTML files from S5 illustration JSONs, then screenshots
them via Playwright to produce PNG images for the bid document.

Usage:
    python render_html_illustrations.py
    python render_html_illustrations.py --illu KU-001
    python render_html_illustrations.py --illu KU-016 --no-screenshot
"""
import json
import os
import sys
import argparse
from pathlib import Path

BASE = r'D:\AI_native_change\甘肃放射源项目\工程项目投标'
S5_DIR = os.path.join(BASE, 'output', 's5_illustrations')
OUT_DIR = os.path.join(BASE, 'output', 's6_synthesis', 'assets')

HTML_ILLU_IDS = [
    'KU-001',   # Main interface layout
    'KU-008',   # Database management
    'KU-009',   # Data import
    'KU-010',   # Fitting analysis
    'KU-013',   # Material design params
    'KU-012',   # Compatibility matrix
    'LC-003',   # Gantt chart
    'KU-016',   # Post-processing visualization workbench
    'KU-017',   # MODBUS real-time monitoring dashboard
    'KU-018',   # System environment check report
    'KU-019',   # Phase diagram visualization
    'KU-020',   # Performance test dashboard
    'KU-021',   # Permission management config
]

# ═══════════════════════════════════════════════════════════════
# CSS Design System
# ═══════════════════════════════════════════════════════════════

DESIGN_SYSTEM_CSS = r'''
:root {
    /* ── Brand ── */
    --primary: #1a3a5c;
    --primary-dark: #0f2340;
    --accent: #007bb5;
    --accent-warm: #e8833e;

    /* ── Semantic ── */
    --success: #10b981;
    --success-bg: #e8f5e9;
    --success-text: #15803d;
    --warning: #f59e0b;
    --warning-bg: #fff8e1;
    --warning-text: #92400e;
    --error: #ef4444;
    --error-bg: #ffebee;
    --error-text: #b91c1c;
    --info: #3b82f6;
    --info-bg: #e3f2fd;

    /* ── Surfaces ── */
    --bg-page: #f0f2f5;
    --bg-panel: #ffffff;
    --bg-card: #fafbfc;
    --bg-hover: #f0f4f8;
    --bg-dark: #0f2340;
    --bg-dark-alt: #132a4a;

    /* ── Text ── */
    --text-primary: #1a1a2e;
    --text-secondary: #555555;
    --text-muted: #888888;
    --text-inverse: #ffffff;

    /* ── Borders ── */
    --border-light: #eef0f2;
    --border-medium: #dde0e4;
    --border-strong: #c0c4cc;

    /* ── Typography scale ── */
    --fs-l0: 42px;
    --fs-l1: 24px;
    --fs-l2: 18px;
    --fs-l3: 15px;
    --fs-l4: 13px;
    --fs-l5: 12px;

    /* ── Spacing ── */
    --space-xs: 4px;
    --space-sm: 8px;
    --space-md: 12px;
    --space-lg: 16px;
    --space-xl: 20px;
    --space-2xl: 24px;

    /* ── Radii ── */
    --radius-sm: 4px;
    --radius-md: 6px;
    --radius-lg: 8px;
    --radius-xl: 10px;

    /* ── Shadows ── */
    --shadow-sm: 0 1px 2px rgba(0,0,0,0.05);
    --shadow-md: 0 2px 8px rgba(0,0,0,0.08);
    --shadow-lg: 0 4px 16px rgba(0,0,0,0.12);
}

* { margin:0; padding:0; box-sizing:border-box; }

body {
    font-family: "Microsoft YaHei","Noto Sans SC",Arial,sans-serif;
    background: var(--bg-page);
    color: var(--text-primary);
    font-size: var(--fs-l3);
    width: 1600px;
    min-height: 1000px;
    line-height: 1.6;
}

/* ═══════════════════════════════════════════════
   Application Shell
   ═══════════════════════════════════════════════ */

.app-titlebar {
    background: var(--primary);
    color: var(--text-inverse);
    height: 36px;
    display: flex;
    align-items: center;
    padding: 0 var(--space-lg);
    font-size: var(--fs-l4);
    font-weight: 600;
    user-select: none;
}
.app-titlebar .app-icon { width: 18px; height: 18px; margin-right: 10px; }
.app-titlebar .app-name { flex: 1; }
.app-titlebar .win-ctrl { display: flex; gap: var(--space-sm); font-size: 14px; color: #c0d0e0; }

.app-menubar {
    background: #f0f1f4;
    border-bottom: 1px solid var(--border-medium);
    height: 30px;
    display: flex;
    align-items: center;
    padding: 0 var(--space-sm);
    font-size: var(--fs-l4);
}
.app-menubar span {
    padding: var(--space-xs) 10px;
    border-radius: var(--radius-sm);
    cursor: default;
}
.app-menubar span:hover { background: #e0e3e8; }

.app-toolbar {
    background: var(--bg-panel);
    border-bottom: 1px solid #e5e7eb;
    height: 44px;
    display: flex;
    align-items: center;
    padding: 0 var(--space-md);
    gap: 6px;
}
.app-toolbar.dark {
    background: var(--primary);
    border-bottom-color: rgba(255,255,255,0.08);
}

.app-statusbar {
    background: var(--bg-dark);
    color: #c0d5e8;
    height: 28px;
    display: flex;
    align-items: center;
    padding: 0 var(--space-lg);
    font-size: var(--fs-l5);
}
.app-statusbar .sb-item { margin-right: 28px; }

.app-console {
    background: var(--bg-dark);
    color: #c0d5e8;
    padding: var(--space-md) var(--space-lg);
    font-family: Consolas, "Courier New", monospace;
    font-size: var(--fs-l5);
    line-height: 1.6;
}
.app-console .log-success { color: var(--success); }
.app-console .log-info { color: var(--accent); }
.app-console .log-muted { color: #666; }

.app-footer-bar {
    background: #f0f1f4;
    height: 44px;
    display: flex;
    align-items: center;
    padding: 0 var(--space-lg);
    gap: var(--space-sm);
    border-top: 1px solid #e5e7eb;
}

.app-workspace-bar {
    background: var(--primary);
    color: var(--text-inverse);
    height: 42px;
    display: flex;
    align-items: center;
    padding: 0 var(--space-lg);
    font-size: var(--fs-l4);
    gap: var(--space-md);
}

/* ═══════════════════════════════════════════════
   Layouts
   ═══════════════════════════════════════════════ */

.layout-app { display: flex; flex-direction: column; min-height: 1000px; }
.layout-hsplit { display: flex; flex: 1; min-height: 0; }
.layout-sidebar-content { display: flex; flex: 1; min-height: 500px; }
.layout-quad {
    display: grid;
    grid-template-columns: 1fr 1fr;
    grid-template-rows: 1fr 1fr;
    gap: var(--space-md);
    flex: 1;
    min-height: 500px;
}
.layout-2col { display: grid; grid-template-columns: 1fr 1fr; gap: var(--space-lg); }
.layout-3col { display: flex; flex: 1; min-height: 480px; }
.layout-3col > .col-side { width: 280px; flex-shrink: 0; }
.layout-3col > .col-main { flex: 1; min-width: 0; }
.layout-3col > .col-detail { width: 260px; flex-shrink: 0; }

.content-scroll { flex: 1; overflow-y: auto; padding: var(--space-lg); }

/* ═══════════════════════════════════════════════
   Navigation
   ═══════════════════════════════════════════════ */

.nav-sidebar {
    width: 200px;
    background: var(--bg-dark);
    color: #c0d5e8;
    font-size: var(--fs-l4);
    overflow-y: auto;
    flex-shrink: 0;
}
.nav-sidebar .nav-title {
    padding: var(--space-md) var(--space-xl);
    font-weight: 700;
    font-size: 14px;
    color: var(--text-inverse);
    border-bottom: 1px solid rgba(255,255,255,0.08);
}
.nav-sidebar .nav-item {
    padding: var(--space-sm) var(--space-xl);
    cursor: default;
    transition: background 0.15s;
}
.nav-sidebar .nav-item:hover { background: rgba(255,255,255,0.06); }
.nav-sidebar .nav-item.active {
    background: rgba(255,255,255,0.08);
    border-left: 3px solid var(--accent);
    color: var(--text-inverse);
}
.nav-sidebar .nav-section {
    padding: var(--space-sm) var(--space-xl);
    color: var(--accent);
    cursor: default;
    margin-top: var(--space-sm);
    font-weight: 600;
}

.nav-tabs {
    display: flex;
    border-bottom: 2px solid #e5e7eb;
    gap: 0;
    margin-bottom: var(--space-lg);
}
.nav-tabs .tab-item {
    padding: 10px var(--space-xl);
    font-size: 14px;
    cursor: default;
    border-bottom: 3px solid transparent;
    color: var(--text-secondary);
    transition: all 0.15s;
}
.nav-tabs .tab-item:hover { color: var(--primary); background: var(--bg-hover); }
.nav-tabs .tab-item.active {
    border-bottom-color: var(--accent-warm);
    color: var(--primary);
    font-weight: 600;
}

/* ═══════════════════════════════════════════════
   Panels
   ═══════════════════════════════════════════════ */

.panel {
    background: var(--bg-panel);
    border-radius: var(--radius-lg);
    border: 1px solid var(--border-medium);
    overflow: hidden;
}
.panel-header {
    padding: var(--space-md) var(--space-lg);
    font-size: var(--fs-l3);
    font-weight: 700;
    color: var(--primary);
    border-bottom: 1px solid var(--border-light);
    display: flex;
    align-items: center;
    gap: var(--space-sm);
}
.panel-body { padding: var(--space-lg); }
.panel-body.compact { padding: var(--space-md); }

/* ═══════════════════════════════════════════════
   Data Table
   ═══════════════════════════════════════════════ */

.data-table {
    width: 100%;
    border-collapse: collapse;
    font-size: var(--fs-l4);
}
.data-table thead tr {
    background: var(--primary);
    color: var(--text-inverse);
}
.data-table th {
    padding: 10px var(--space-md);
    text-align: left;
    font-weight: 600;
    white-space: nowrap;
}
.data-table th.right { text-align: right; }
.data-table th.center { text-align: center; }
.data-table td {
    padding: var(--space-sm) var(--space-md);
    border-bottom: 1px solid var(--border-light);
}
.data-table td.right { text-align: right; font-family: Consolas, monospace; }
.data-table td.center { text-align: center; }
.data-table tbody tr:nth-child(even) { background: #f9fafb; }
.data-table tbody tr:hover { background: var(--bg-hover); }
.data-table tbody tr.row-selected {
    background: #e3f2fd;
    border-left: 3px solid var(--accent-warm);
}

.data-table.compact th,
.data-table.compact td {
    padding: 6px var(--space-sm);
}

/* ═══════════════════════════════════════════════
   Badges
   ═══════════════════════════════════════════════ */

.badge {
    display: inline-block;
    padding: 2px 10px;
    border-radius: 10px;
    font-size: var(--fs-l5);
    font-weight: 500;
}
.badge--primary { background: var(--info); color: var(--text-inverse); }
.badge--success { background: var(--success); color: var(--text-inverse); }
.badge--warning { background: var(--warning); color: var(--text-inverse); }
.badge--error { background: var(--error); color: var(--text-inverse); }
.badge--muted { background: #9ca3af; color: var(--text-inverse); }
.badge--accent { background: var(--accent-warm); color: var(--text-inverse); }

/* ═══════════════════════════════════════════════
   Status Dots
   ═══════════════════════════════════════════════ */

.status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
    margin-right: 6px;
    vertical-align: middle;
}
.status-dot--ok { background: var(--success); }
.status-dot--warn { background: var(--warning); }
.status-dot--err { background: var(--error); }

/* ═══════════════════════════════════════════════
   Buttons
   ═══════════════════════════════════════════════ */

.btn {
    height: 32px;
    padding: 0 14px;
    border: 1px solid #d1d5db;
    border-radius: var(--radius-sm);
    background: var(--bg-panel);
    font-size: var(--fs-l4);
    cursor: default;
    display: inline-flex;
    align-items: center;
    gap: 6px;
    color: var(--primary);
    white-space: nowrap;
    transition: all 0.15s;
}
.btn:hover { background: var(--bg-hover); border-color: var(--border-strong); }
.btn--primary { background: var(--accent); color: #fff; border-color: var(--accent); }
.btn--primary:hover { background: #006a9e; }
.btn--accent { background: var(--accent-warm); color: #fff; border-color: var(--accent-warm); }
.btn--danger { color: var(--error); border-color: var(--error); }
.btn--ghost {
    background: transparent;
    color: var(--text-inverse);
    border: 1px solid rgba(255,255,255,0.25);
}
.btn--ghost:hover { background: rgba(255,255,255,0.1); }
.btn--sm { height: 26px; padding: 0 10px; font-size: var(--fs-l5); }
.btn--lg { height: 40px; padding: 0 var(--space-xl); font-size: var(--fs-l3); font-weight: 600; }
.btn--block { width: 100%; justify-content: center; }
.btn-sep {
    width: 1px;
    height: 24px;
    background: #e5e7eb;
    margin: 0 6px;
}

/* ═══════════════════════════════════════════════
   Form elements
   ═══════════════════════════════════════════════ */

.form-group { margin-bottom: var(--space-md); }
.form-label {
    display: block;
    font-size: var(--fs-l4);
    font-weight: 600;
    color: var(--text-primary);
    margin-bottom: var(--space-xs);
}
.form-label.light { color: var(--text-inverse); }
.form-input, .form-select {
    height: 30px;
    padding: 0 var(--space-sm);
    border: 1px solid #d1d5db;
    border-radius: var(--radius-sm);
    font-size: var(--fs-l4);
    background: var(--bg-panel);
    color: var(--text-primary);
}
.form-input:focus, .form-select:focus { outline: none; border-color: var(--accent); box-shadow: 0 0 0 2px rgba(0,123,181,0.15); }
.form-input.wide { width: 100%; }
.form-input.narrow { width: 80px; text-align: right; }
.form-select { cursor: default; }

.form-row {
    display: flex;
    gap: var(--space-sm);
    align-items: center;
    margin-bottom: var(--space-xs);
}

/* ═══════════════════════════════════════════════
   Metric cards
   ═══════════════════════════════════════════════ */

.metric-card {
    background: var(--bg-panel);
    border: 1px solid var(--border-medium);
    border-radius: var(--radius-lg);
    padding: var(--space-lg);
    display: flex;
    flex-direction: column;
    gap: var(--space-xs);
}
.metric-card__label {
    font-size: var(--fs-l5);
    color: var(--text-muted);
    text-transform: uppercase;
    letter-spacing: 0.5px;
}
.metric-card__value {
    font-size: 32px;
    font-weight: 700;
    line-height: 1.1;
}
.metric-card__value.success { color: var(--success); }
.metric-card__value.warning { color: var(--warning); }
.metric-card__value.error { color: var(--error); }
.metric-card__value.primary { color: var(--primary); }
.metric-card__sub { font-size: var(--fs-l5); color: var(--text-muted); }

.metrics-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(160px, 1fr));
    gap: var(--space-md);
}

/* ═══════════════════════════════════════════════
   Progress bar
   ═══════════════════════════════════════════════ */

.progress-bar {
    background: #e5e7eb;
    border-radius: var(--radius-md);
    height: 18px;
    overflow: hidden;
}
.progress-bar__fill {
    background: var(--primary);
    height: 100%;
    border-radius: var(--radius-md);
    transition: width 0.3s;
}
.progress-bar__fill.accent { background: var(--accent); }
.progress-bar__fill.success { background: var(--success); }
.progress-bar__fill.warning { background: var(--warning); }

/* ═══════════════════════════════════════════════
   Check items
   ═══════════════════════════════════════════════ */

.check-item {
    padding: var(--space-sm) var(--space-md);
    border-radius: var(--radius-sm);
    font-size: var(--fs-l4);
    margin-bottom: var(--space-sm);
    display: flex;
    align-items: center;
    gap: var(--space-sm);
}
.check-item--pass { background: var(--success-bg); color: var(--success-text); }
.check-item--warn { background: var(--warning-bg); color: var(--warning-text); }
.check-item--fail { background: var(--error-bg); color: var(--error-text); }
.check-item__icon { font-weight: 700; font-size: 14px; width: 20px; }

/* ═══════════════════════════════════════════════
   Alerts
   ═══════════════════════════════════════════════ */

.alert {
    padding: var(--space-md) var(--space-lg);
    border-radius: var(--radius-md);
    font-size: var(--fs-l4);
    line-height: 1.6;
}
.alert--info { background: var(--info-bg); color: #1e40af; border-left: 3px solid var(--info); }
.alert--warn { background: var(--warning-bg); color: var(--warning-text); border-left: 3px solid var(--warning); }
.alert--success { background: var(--success-bg); color: var(--success-text); border-left: 3px solid var(--success); }

/* ═══════════════════════════════════════════════
   Template cards
   ═══════════════════════════════════════════════ */

.template-card {
    padding: var(--space-sm) var(--space-md);
    border: 1px solid var(--border-medium);
    border-radius: var(--radius-sm);
    margin-bottom: 6px;
    cursor: default;
    transition: all 0.15s;
}
.template-card:hover { border-color: var(--accent); background: var(--bg-hover); }
.template-card__title { font-weight: 600; font-size: var(--fs-l4); }
.template-card__meta { font-size: var(--fs-l5); color: var(--text-muted); margin-top: 2px; }

/* ═══════════════════════════════════════════════
   Drop zone
   ═══════════════════════════════════════════════ */

.drop-zone {
    border: 2px dashed var(--primary);
    border-radius: var(--radius-xl);
    background: #eef0f5;
    padding: 30px;
    text-align: center;
}
.drop-zone__icon { font-size: 40px; color: var(--primary); }
.drop-zone__text {
    font-size: var(--fs-l3);
    color: var(--primary);
    margin-top: var(--space-sm);
}
.drop-zone__link {
    color: var(--accent);
    text-decoration: underline;
    cursor: default;
}
.drop-zone__file {
    margin-top: var(--space-md);
    background: var(--bg-panel);
    border-radius: var(--radius-md);
    padding: 10px var(--space-lg);
    display: inline-block;
    font-size: var(--fs-l4);
    text-align: left;
}

/* ═══════════════════════════════════════════════
   Utility
   ═══════════════════════════════════════════════ */

.flex-1 { flex: 1; }
.flex-col { display: flex; flex-direction: column; }
.gap-sm { gap: var(--space-sm); }
.gap-md { gap: var(--space-md); }
.gap-lg { gap: var(--space-lg); }
.p-lg { padding: var(--space-lg); }
.p-xl { padding: var(--space-xl); }
.mb-md { margin-bottom: var(--space-md); }
.mb-lg { margin-bottom: var(--space-lg); }
.text-right { text-align: right; }
.text-center { text-align: center; }
.text-muted { color: var(--text-muted); }
.text-success { color: var(--success); }
.text-warning { color: var(--warning); }
.text-error { color: var(--error); }
.font-mono { font-family: Consolas, "Courier New", monospace; }
.divider { border-top: 1px solid var(--border-medium); margin: var(--space-md) 0; }
.truncate { overflow: hidden; text-overflow: ellipsis; white-space: nowrap; }
'''

# ═══════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════


def load_illu(illu_id):
    path = os.path.join(S5_DIR, f'{illu_id}.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def wrap_html(title, body_html, extra_css='', scale_factor=1.0):
    """Build complete HTML document.

    Args:
        title: Page title (shown in titlebar and <title>)
        body_html: Inner HTML (below titlebar)
        extra_css: Additional component-specific CSS
        scale_factor: Font scale override. 1.0 for Gantt/timeline, 1.15 for UI mockups.
    """
    scale_css = ''
    if scale_factor != 1.0:
        scale_css = f'''
        body {{
            --fs-l0: {42 * scale_factor:.0f}px;
            --fs-l1: {24 * scale_factor:.0f}px;
            --fs-l2: {18 * scale_factor:.0f}px;
            --fs-l3: {15 * scale_factor:.0f}px;
            --fs-l4: {13 * scale_factor:.0f}px;
            --fs-l5: {12 * scale_factor:.0f}px;
        }}'''

    return f'''<!DOCTYPE html>
<html lang="zh-CN">
<head><meta charset="utf-8"><title>{title}</title><style>
{DESIGN_SYSTEM_CSS}
{extra_css}
{scale_css}
</style></head>
<body>
<div class="layout-app">
<div class="app-titlebar">
    <span class="app-icon">&#9632;</span>
    <span class="app-name">{title}</span>
    <span class="win-ctrl">&minus; &Square; &times;</span>
</div>
{body_html}
</div>
</body></html>'''


# ═══════════════════════════════════════════════
# KU-001: Main interface layout
# ═══════════════════════════════════════════════

def render_ku001(illu):
    layers = illu['text_content']['layers']
    content_layer = layers[2]  # 主内容区
    status_layer = layers[3]   # 状态栏

    # Tab content
    tabs_html = ''.join(
        f'<div class="tab-item{" active" if i == 0 else ""}">{node["name"]}</div>'
        for i, node in enumerate(content_layer['nodes'])
    )

    # Status bar
    status_items = ''.join(
        f'<span class="sb-item">{node["name"]}: {node["subtitle"][:60]}</span>'
        for node in status_layer['nodes']
    )

    body = f'''
<div class="app-menubar">
    <span>文件</span><span>数据</span><span>模块</span><span>工具</span><span>帮助</span>
</div>
<div class="app-toolbar">
    <button class="btn">新建项目</button>
    <span class="btn-sep"></span>
    <button class="btn">导入数据</button>
    <button class="btn">导出图表</button>
    <span class="btn-sep"></span>
    <button class="btn">拟合分析</button>
    <button class="btn">生成报告</button>
    <input class="form-input" style="margin-left:auto;width:220px;" placeholder="搜索 Ctrl+F">
</div>
<div class="layout-sidebar-content">
    <div class="nav-sidebar">
        <div class="nav-title">导航菜单</div>
        <div class="nav-item active">数据库管理</div>
        <div class="nav-item">材料设计</div>
        <div class="nav-item">热环境确定</div>
        <div class="nav-item">热环境响应评估</div>
    </div>
    <div class="content-scroll">
        <div class="nav-tabs">{tabs_html}</div>
        <div class="panel" style="min-height:380px;">
            <div style="padding:40px;text-align:center;color:var(--text-muted);font-size:var(--fs-l3);">
                功能模块内容区域 — 各模块面板嵌入此处
            </div>
        </div>
    </div>
</div>
<div class="app-statusbar">
    <span class="sb-item"><span class="status-dot status-dot--ok"></span>就绪</span>
    {status_items}
</div>'''
    return wrap_html(illu['text_content']['main_title'], body, scale_factor=1.15)


# ═══════════════════════════════════════════════
# KU-008: Database management interface
# ═══════════════════════════════════════════════

def render_ku008(illu):
    layers = illu['text_content']['layers']
    toolbar_layer = layers[0]
    nav_layer = layers[1]

    # Toolbar
    tb_parts = []
    for node in toolbar_layer['nodes']:
        if '搜索' in node['name']:
            tb_parts.append('<input class="form-input" style="width:260px;" placeholder="输入材料名称或分子式检索...">')
        elif '筛选' in node['name']:
            label = node['name'].replace('筛选下拉: ', '')
            tb_parts.append(f'<select class="form-select"><option>{label}</option></select>')
        elif node.get('is_highlighted'):
            tb_parts.append(f'<button class="btn btn--primary">{node["name"]}</button>')
    toolbar_html = ''.join(tb_parts)

    # Navigation tree
    nav_parts = []
    for node in nav_layer['nodes']:
        if node['name'].startswith('[+'):
            nav_parts.append(f'<div class="nav-section">{node["name"]}</div>')
        else:
            nav_parts.append(f'<div class="nav-item">▶ {node["name"]}</div>')
    nav_html = ''.join(nav_parts)

    # Data table
    data_rows = [
        ('铝合金6061', 'Al-Mg-Si', '2.70', '167', '896', '实验数据, 已验证'),
        ('钛合金TC4', 'Ti-6Al-4V', '4.43', '7.2', '526', '实验数据, 高温'),
        ('碳化硅SiC', 'SiC', '3.21', '120', '670', '计算数据, 已验证'),
        ('氧化铝Al₂O₃', 'Al₂O₃', '3.95', '30', '880', '实验数据, 2024批次'),
        ('钨W', 'W', '19.25', '173', '134', '实验数据, 高温'),
        ('铜Cu', 'Cu', '8.96', '401', '385', '文献数据, 已验证'),
        ('石英玻璃SiO₂', 'SiO₂', '2.20', '1.38', '703', '实验数据'),
        ('聚酰亚胺PI', '(C₂₂H₁₀N₂O₅)n', '1.42', '0.22', '1090', '计算数据'),
    ]
    row_html = ''
    for i, row in enumerate(data_rows):
        cls = 'row-selected' if i == 0 else ''
        cells = ''.join(
            f'<td class="{"right" if j >= 2 else ""}">{cell}</td>'
            for j, cell in enumerate(row)
        )
        row_html += f'<tr class="{cls}">{cells}</tr>'

    body = f'''
<div class="app-toolbar dark" style="flex-wrap:wrap;gap:8px;height:auto;min-height:44px;">{toolbar_html}</div>
<div class="layout-sidebar-content">
    <div class="nav-sidebar" style="width:210px;">
        <div class="nav-title">数据分类</div>
        {nav_html}
    </div>
    <div class="content-scroll" style="padding:8px;">
        <table class="data-table">
            <thead><tr>
                <th>材料名称</th>
                <th>分子式</th>
                <th class="right">密度 (g/cm³)</th>
                <th class="right">热导率 (W/m·K)</th>
                <th class="right">比热容 (J/kg·K)</th>
                <th>标签</th>
            </tr></thead>
            <tbody>{row_html}</tbody>
        </table>
    </div>
    <div style="width:250px;background:#fafbfc;border-left:1px solid var(--border-medium);padding:16px;overflow-y:auto;">
        <h4 style="font-size:var(--fs-l3);color:var(--primary);margin-bottom:12px;">属性详情</h4>
        <div style="font-size:var(--fs-l4);line-height:2.2;">
            <div><span class="text-muted">材料名称</span> <b>铝合金6061</b></div>
            <div><span class="text-muted">分子式</span> <b>Al-Mg-Si</b></div>
            <div><span class="text-muted">密度</span> <b>2.70 g/cm³</b></div>
            <div><span class="text-muted">热导率</span> <b>167 W/m·K</b></div>
            <div><span class="text-muted">比热容</span> <b>896 J/kg·K</b></div>
        </div>
        <div class="divider">
            <span class="badge badge--primary">实验数据</span>
            <span class="badge badge--success">已验证</span>
        </div>
        <div class="flex-col gap-sm" style="margin-top:12px;">
            <button class="btn btn--block">编辑</button>
            <button class="btn btn--danger btn--block">删除</button>
            <button class="btn btn--block">导出</button>
        </div>
    </div>
</div>
<div class="app-statusbar">
    <span class="sb-item">共 1,247 条记录</span>
    <span class="sb-item">分类: 热物理数据 | 符合条件: 86 条</span>
    <span class="sb-item" style="margin-left:auto;">SQLite: ./db/material.db</span>
</div>'''
    return wrap_html(illu['text_content']['main_title'], body, scale_factor=1.15)


# ═══════════════════════════════════════════════
# KU-009: Data import interface
# ═══════════════════════════════════════════════

def render_ku009(illu):
    body = '''
<div class="flex-col gap-lg p-xl" style="flex:1;">
    <!-- Drop zone -->
    <div class="drop-zone">
        <div class="drop-zone__icon">&#8682;</div>
        <div class="drop-zone__text">将 xls / xlsx / txt / csv 文件拖拽到此处，或 <span class="drop-zone__link">点击选择文件</span></div>
        <div class="drop-zone__file">
            热物理参数实验数据_2024.xlsx | 2.3 MB | 1,247 行 | 8 列 <span style="color:var(--error);margin-left:8px;cursor:default;">&times; 移除</span>
        </div>
    </div>
    <!-- Preview + Mapping -->
    <div class="layout-hsplit gap-lg">
        <div style="flex:6;" class="panel">
            <div class="panel-header">数据预览（前10行）</div>
            <div class="panel-body compact">
                <table class="data-table compact">
                    <thead><tr>
                        <th>材料名称 ▼</th>
                        <th class="right">密度 ▼</th>
                        <th class="right">热导率 ▼</th>
                        <th style="color:#999;border:1px dashed #ccc;">未映射 ▼</th>
                    </tr></thead>
                    <tbody>'''
    for row in [('铝合金6061','2.70','167','-'),('钛合金TC4','4.43','7.2','-'),
                ('碳化硅SiC','3.21','120','-'),('氧化铝Al₂O₃','3.95','30','-'),
                ('钨W','19.25','173','-'),('铜Cu','8.96','401','-')]:
        body += f'<tr><td>{row[0]}</td><td class="right">{row[1]}</td><td class="right">{row[2]}</td><td class="text-muted">{row[3]}</td></tr>'
    body += '''</tbody></table>
            </div>
        </div>
        <div style="flex:4;" class="panel">
            <div class="panel-header">列映射配置</div>
            <div class="panel-body" style="font-size:var(--fs-l4);line-height:2.4;">
                <div>材料名称 → 材料名称 <span class="text-success">✓</span></div>
                <div>密度(kg/m³) → 密度(g/cm³) <span class="text-success">✓</span></div>
                <div>导热系数 → 热导率(W/m·K) <span class="text-success">✓</span></div>
                <div>备注 → <span class="text-warning">(不导入)</span></div>
            </div>
        </div>
    </div>
    <!-- Tags + Buttons -->
    <div class="layout-hsplit gap-lg">
        <div style="flex:1;display:flex;align-items:center;gap:8px;flex-wrap:wrap;">
            <span class="badge badge--primary">实验数据 &times;</span>
            <span class="badge badge--warning">高温 &times;</span>
            <span class="badge badge--muted">2024批次 &times;</span>
            <button class="btn btn--sm">+ 添加标签</button>
        </div>
        <div style="display:flex;gap:8px;">
            <button class="btn btn--primary btn--lg">开始导入</button>
            <button class="btn">取消</button>
            <button class="btn">保存映射模板</button>
        </div>
    </div>
    <!-- Progress -->
    <div class="panel">
        <div class="panel-body compact">
            <div class="progress-bar">
                <div class="progress-bar__fill" style="width:62%;"></div>
            </div>
            <div style="font-size:var(--fs-l4);color:var(--text-secondary);margin-top:8px;">
                已导入 773 / 1,247 条 | 异常 3 行 <span style="color:var(--accent);cursor:default;">[查看详情 ▼]</span>
            </div>
        </div>
    </div>
</div>'''
    return wrap_html(illu['text_content']['main_title'], body, scale_factor=1.15)


# ═══════════════════════════════════════════════
# KU-010: Fitting analysis interface
# ═══════════════════════════════════════════════

def render_ku010(illu):
    body = f'''
<div style="background:var(--primary);color:var(--text-inverse);padding:0 16px;height:48px;display:flex;align-items:center;font-family:Consolas,monospace;font-size:var(--fs-l3);">
    y = a·x² + b·x + c &nbsp;&nbsp; <span style="color:#c0d5e8;">a=1.234×10⁻³</span> &nbsp;&nbsp; <span style="color:var(--text-inverse);font-weight:700;">b=5.678</span> &nbsp;&nbsp; <span style="color:#c0d5e8;">c=0.012</span>
</div>
<div class="layout-3col">
    <div class="col-side" style="background:var(--bg-dark);color:#c0d5e8;padding:16px;font-size:var(--fs-l4);">
        <div class="form-group">
            <label class="form-label light">X轴数据</label>
            <select class="form-select wide"><option>热导率 (W/m·K)</option></select>
        </div>
        <div class="form-group">
            <label class="form-label light">Y轴数据</label>
            <select class="form-select wide"><option>比热容 (J/kg·K)</option></select>
        </div>
        <div class="divider" style="border-color:rgba(255,255,255,0.1);">
            <div style="color:var(--text-inverse);font-size:var(--fs-l4);margin-bottom:6px;">拟合算法</div>
            <div style="line-height:2.4;">○ 线性 y=ax+b</div>
            <div>○ 多项式</div>
            <div style="color:var(--accent);">● 指数 y=a·e^(bx)</div>
            <div>○ 对数</div>
            <div>○ 自定义公式</div>
        </div>
        <button class="btn btn--primary btn--block btn--lg" style="margin-top:16px;">执行拟合</button>
    </div>
    <div class="col-main content-scroll" style="position:relative;">
        <div style="border:1px solid var(--border-medium);border-radius:var(--radius-lg);height:320px;position:relative;overflow:hidden;background:linear-gradient(white 0%, #fafbfc 100%);">
            <svg width="100%" height="100%" viewBox="0 0 700 320">
                <text x="350" y="16" text-anchor="middle" font-size="13" fill="#666" font-family="Microsoft YaHei">热导率 (W/m·K) — 比热容 (J/kg·K) 拟合关系</text>
                <line x1="50" y1="40" x2="50" y2="280" stroke="#e5e7eb" stroke-width="0.5"/>
                <line x1="50" y1="280" x2="650" y2="280" stroke="#e5e7eb" stroke-width="0.5"/>
                <circle cx="120" cy="200" r="5" fill="#3b82f6" opacity="0.7"/><circle cx="180" cy="170" r="5" fill="#3b82f6" opacity="0.7"/>
                <circle cx="240" cy="140" r="5" fill="#3b82f6" opacity="0.7"/><circle cx="300" cy="120" r="5" fill="#3b82f6" opacity="0.7"/>
                <circle cx="360" cy="100" r="5" fill="#3b82f6" opacity="0.7"/><circle cx="420" cy="85" r="5" fill="#3b82f6" opacity="0.7"/>
                <circle cx="480" cy="70" r="5" fill="#3b82f6" opacity="0.7"/><circle cx="540" cy="60" r="5" fill="#3b82f6" opacity="0.7"/>
                <path d="M100 240 Q350 160 620 55" stroke="#ef4444" stroke-width="2.5" fill="none"/>
                <rect x="480" y="40" width="155" height="48" rx="6" fill="white" fill-opacity="0.9" stroke="#d0d0d0"/>
                <circle cx="500" cy="58" r="5" fill="#3b82f6" opacity="0.7"/><text x="512" y="62" font-size="11" fill="#666">原始数据 (n=86)</text>
                <line x1="500" y1="78" x2="530" y2="78" stroke="#ef4444" stroke-width="2"/><text x="536" y="82" font-size="11" fill="#666">R²=0.9823</text>
            </svg>
        </div>
    </div>
    <div class="col-detail" style="padding:16px;font-size:var(--fs-l4);">
        <div class="mb-lg">
            <div class="metric-card__label">拟合优度 R²</div>
            <div class="metric-card__value success">0.9823</div>
            <div class="metric-card__sub">RMSE = 12.47</div>
        </div>
        <div class="divider">
            <div style="line-height:2.2;font-family:Consolas,monospace;">
                a = 1.234×10⁻³ ± 0.00012<br>
                b = 5.678 ± 0.234<br>
                c = 0.012 ± 0.001
            </div>
        </div>
        <div style="font-size:var(--fs-l5);color:var(--text-muted);padding:8px 0;">
            σ_residual = 12.47<br>Max +residual = +28.3<br>Max -residual = -31.2
        </div>
    </div>
</div>
<div class="app-footer-bar">
    <button class="btn">导出 PNG 300dpi</button>
    <button class="btn">导出 TIFF 300dpi</button>
    <button class="btn">导出 JPG 300dpi</button>
    <span style="margin-left:auto;display:flex;align-items:center;gap:8px;">
        <span class="text-muted" style="font-size:var(--fs-l5);">缩放:</span>
        <input type="range" value="100" style="width:120px;">
        <button class="btn">重置视图</button>
        <button class="btn btn--primary">导出拟合报告</button>
    </span>
</div>'''
    return wrap_html(illu['text_content']['main_title'], body, scale_factor=1.15)


# ═══════════════════════════════════════════════
# KU-013: Material design parameter config
# ═══════════════════════════════════════════════

def render_ku013(illu):
    body = f'''
<div class="app-workspace-bar">
    <span>工作空间: D:\\Projects\\MaterialDesign\\WS_20240115_001</span>
    <button class="btn btn--ghost btn--sm">浏览...</button>
    <span>|</span>
    <button class="btn btn--ghost btn--sm">新建工作空间</button>
    <button class="btn btn--ghost btn--sm">打开工作空间</button>
    <span style="margin-left:auto;">MaterialDesign_20240115_001.project</span>
    <button class="btn btn--ghost btn--sm">保存</button>
</div>
<div class="layout-3col">
    <!-- Left: Parameter form -->
    <div class="col-side content-scroll" style="border-right:1px solid var(--border-medium);">
        <h4 style="font-size:var(--fs-l3);color:var(--primary);margin-bottom:12px;">参数输入</h4>
        <div class="panel-body compact" style="background:#f8fafc;border:1px solid var(--border-medium);border-radius:var(--radius-md);margin-bottom:12px;">
            <div style="font-size:var(--fs-l4);font-weight:600;margin-bottom:8px;">材料组分</div>
            <div class="form-row"><span style="width:70px;font-size:var(--fs-l5);">SiO₂</span><input class="form-input narrow" value="45" style="border-color:var(--success);"> <span>%</span><span class="text-success">✓</span></div>
            <div class="form-row"><span style="width:70px;font-size:var(--fs-l5);">Al₂O₃</span><input class="form-input narrow" value="30" style="border-color:var(--success);"> <span>%</span><span class="text-success">✓</span></div>
            <div class="form-row"><span style="width:70px;font-size:var(--fs-l5);">CaO</span><input class="form-input narrow" value="25"> <span>%</span></div>
            <div style="margin-top:4px;font-size:var(--fs-l5);" class="text-success">总和 = 100% ✓</div>
        </div>
        <div class="form-group">
            <div class="form-label">温度范围</div>
            <div class="form-row">
                <input class="form-input narrow" value="300" style="width:70px;"> <span>K ~</span>
                <input class="form-input narrow" value="2000" style="width:70px;"> <span>K</span>
                <span class="text-success">✓</span>
            </div>
            <div style="font-size:var(--fs-l5);color:var(--text-muted);margin-top:4px;">步长: <input class="form-input" style="width:50px;height:22px;font-size:11px;" value="50"> K</div>
        </div>
        <div class="form-group">
            <div class="form-label">压力</div>
            <div class="form-row">
                <input class="form-input" style="width:100px;" value="0.1"> <span style="font-size:var(--fs-l5);">MPa</span>
                <span class="text-success">✓</span>
            </div>
        </div>
        <div class="form-group">
            <div class="form-label">计算模式</div>
            <div style="line-height:2.4;font-size:var(--fs-l4);">
                ○ 热物理计算 &nbsp; ● 热化学计算<br>○ 相图计算 &nbsp; ○ 全计算
            </div>
        </div>
    </div>
    <!-- Center: Validation -->
    <div class="col-main content-scroll" style="border-right:1px solid var(--border-medium);">
        <h4 style="font-size:var(--fs-l3);color:var(--primary);margin-bottom:12px;">合规校验结果</h4>
        <div class="check-item check-item--pass"><span class="check-item__icon">✓</span> 总和=100%校验 — 通过</div>
        <div class="check-item check-item--pass"><span class="check-item__icon">✓</span> 参数范围校验 — 通过</div>
        <div class="check-item check-item--pass"><span class="check-item__icon">✓</span> 必填项校验 — 通过</div>
        <div class="check-item check-item--warn"><span class="check-item__icon">⚠</span> 格式校验 — 温度步长建议为50K倍数</div>
        <div class="alert alert--success" style="margin-top:16px;">
            <b>校验汇总：</b>4项校验 — 3项通过，1项警告
        </div>
        <button class="btn btn--primary btn--lg btn--block" style="margin-top:12px;">开始DLL计算（预计耗时约 12s）</button>
    </div>
    <!-- Right: Templates -->
    <div class="col-detail content-scroll">
        <h4 style="font-size:var(--fs-l3);color:var(--primary);margin-bottom:8px;">参数模板</h4>
        <input class="form-input wide" placeholder="搜索模板..." style="margin-bottom:8px;">
        <div class="template-card">
            <div class="template-card__title">SiO₂-Al₂O₃-CaO三元系</div>
            <div class="template-card__meta">45/30/25% 2024-01-10</div>
            <button class="btn btn--primary btn--sm" style="float:right;margin-top:-28px;">加载</button>
        </div>
        <div class="template-card">
            <div class="template-card__title">高铝配方Al₂O₃-60%</div>
            <div class="template-card__meta">15/60/25% 2024-01-08</div>
            <button class="btn btn--primary btn--sm" style="float:right;margin-top:-28px;">加载</button>
        </div>
        <div class="template-card">
            <div class="template-card__title">低SiO₂变体</div>
            <div class="template-card__meta">30/35/35% 2024-01-05</div>
            <button class="btn btn--primary btn--sm" style="float:right;margin-top:-28px;">加载</button>
        </div>
        <button class="btn btn--block" style="margin-top:8px;">保存当前为模板</button>
    </div>
</div>
<div class="app-console">
    <div style="margin-bottom:8px;display:flex;gap:6px;">
        <span class="badge badge--success" style="width:100px;text-align:center;">校验 100%</span>
        <span class="badge badge--accent" style="width:250px;text-align:center;">热化学计算 进行中...</span>
        <span class="badge badge--muted" style="width:250px;text-align:center;">相图计算 等待</span>
        <span class="badge badge--muted" style="width:150px;text-align:center;">后处理 等待</span>
    </div>
    <div class="log-success">
        [14:30:01] 开始参数合规性校验...<br>
        [14:30:01] 组分总和校验通过（100.00%）<br>
        [14:30:01] 参数范围校验通过<br>
        [14:30:02] 加载mat_design.dll... DLL加载成功<br>
        [14:30:02] 开始热化学计算（温度范围300~2000K, 步长50K, 共35个温度点）
    </div>
</div>'''
    return wrap_html(illu['text_content']['main_title'], body, scale_factor=1.15)


# ═══════════════════════════════════════════════
# KU-012: Compatibility matrix
# ═══════════════════════════════════════════════

def render_ku012(illu):
    layers = illu['text_content']['layers'][0]
    nodes = layers['nodes']

    def parse_status(detail):
        if 'Win7:✓' in detail or detail.startswith('Win7:✓'):
            return ['pass', 'pass', 'pass'] if 'Win10:✓' in detail and 'Win11:✓' in detail else ['warn', 'pass', 'pass']
        if 'Win7:⚠' in detail:
            return ['warn', 'pass', 'pass']
        if 'Win7:✗' in detail:
            return ['fail', 'pass', 'pass']
        return ['pass', 'pass', 'pass']

    def status_cell(status):
        colors = {
            'pass': ('success-bg', 'success', '✓ 通过'),
            'warn': ('warning-bg', 'warning', '⚠ 需处理'),
            'fail': ('error-bg', 'error', '✗ 不兼容')
        }
        bg, color, text = colors[status]
        return f'<td style="background:var(--{bg});color:var(--{color});padding:8px 12px;text-align:center;font-weight:600;font-size:var(--fs-l5);">{text}</td>'

    rows = ''
    for i, node in enumerate(nodes):
        statuses = parse_status(node.get('detail', ''))
        rows += f'<tr><td style="padding:8px 12px;font-weight:600;font-size:var(--fs-l4);">{node["label"]}</td>'
        for s in statuses:
            rows += status_cell(s)
        rows += '</tr>'

    body = f'''
<div class="content-scroll">
    <div class="panel">
        <table class="data-table">
            <thead>
                <tr>
                    <th style="width:260px;">软件/库组件</th>
                    <th class="center">Windows 7 SP1 x64</th>
                    <th class="center">Windows 10 22H2 x64</th>
                    <th class="center">Windows 11 23H2 x64</th>
                </tr>
            </thead>
            <tbody>{rows}</tbody>
        </table>
    </div>
    <div style="margin-top:16px;display:flex;gap:12px;font-size:var(--fs-l5);color:var(--text-secondary);">
        <span><span class="badge badge--success">✓ 通过</span> = 兼容</span>
        <span><span class="badge badge--warning">⚠ 需处理</span> = 需替代方案</span>
        <span><span class="badge badge--error">✗ 不兼容</span> = 需降级</span>
    </div>
    <div class="alert alert--info" style="margin-top:16px;">
        <b>已知问题与解决方案：</b>
        <div style="margin-top:4px;line-height:2;">
            <div>• <b>Python 3.10 + Win7</b>：需预装KB3063858(Universal C Runtime)，部署脚本自动检测安装</div>
            <div>• <b>pandas 2.x + Win7</b>：Win7使用pandas 1.5.3替代，API完全兼容</div>
            <div>• <b>h5py + Win7</b>：光盘预置经Win7测试的wheel包，使用--no-index安装</div>
            <div>• <b>PyQt5 + 高DPI</b>：启动脚本设置QT_SCALE_FACTOR + 调用AA_EnableHighDpiScaling</div>
        </div>
    </div>
</div>'''
    return wrap_html(illu['text_content']['main_title'], body, scale_factor=1.15)


# ═══════════════════════════════════════════════
# LC-003: Gantt chart
# ═══════════════════════════════════════════════

def render_lc003(illu):
    layers = illu['text_content']['layers'][0]
    nodes = layers['nodes']

    MONTHS = 18
    COL_WIDTH = 68
    LEFT_WIDTH = 260
    ROW_HEIGHT = 72

    phase_colors = ['#4caf50', '#2196f3', '#ff9800', '#9c27b0', '#ef4444']
    phase_names = ['阶段一', '阶段二', '阶段三', '阶段四', '阶段五']
    phase_spans = [
        (0, 0.5, '方案设计 M1'),
        (0.5, 2.0, '数据库模块 M1-M2'),
        (2.0, 3.0, '核心集成 V1.0 M2-M3'),
        (3.0, 12.0, '全功能迭代 V2.0 M3-M12'),
        (12.0, 18.0, '终版交付 V3.0 M13-M18'),
    ]
    milestones = [(0.5, '方案审核'), (2.0, 'DB检测'), (3.0, 'V1.0交付'), (12.0, 'V2.0+测评'), (18.0, '终验')]

    month_header = ''.join(
        f'<div style="width:{COL_WIDTH}px;text-align:center;font-size:12px;font-weight:600;color:var(--primary);flex-shrink:0;">M{m}</div>'
        for m in range(1, MONTHS + 1)
    )

    body = f'''
<div class="content-scroll" style="overflow-x:auto;">
    <div style="position:relative;min-width:{LEFT_WIDTH + MONTHS * COL_WIDTH + 40}px;">
        <div style="display:flex;margin-left:{LEFT_WIDTH}px;border-bottom:1px solid #d0d0d0;padding-bottom:8px;">{month_header}</div>
        <div style="position:relative;height:380px;margin-top:8px;">
            <div style="position:absolute;left:0;top:0;width:{LEFT_WIDTH}px;">'''
    for i, node in enumerate(nodes[:5]):
        body += f'<div style="height:{ROW_HEIGHT}px;display:flex;align-items:center;font-size:12px;font-weight:600;padding-right:12px;color:var(--primary);">{node["label"][:30]}...</div>'
    body += f'''</div>
            <div style="position:absolute;left:{LEFT_WIDTH}px;top:0;right:0;height:380px;">'''
    for m in range(MONTHS + 1):
        body += f'<div style="position:absolute;left:{m * COL_WIDTH}px;top:0;height:100%;border-left:1px solid #f0f0f0;"></div>'
    for i, (start, end, label) in enumerate(phase_spans):
        left = start * COL_WIDTH
        width = (end - start) * COL_WIDTH
        body += f'<div style="position:absolute;left:{left:.0f}px;top:{10 + i * ROW_HEIGHT}px;width:{width:.0f}px;height:28px;background:{phase_colors[i]};border-radius:4px;display:flex;align-items:center;padding:0 10px;font-size:11px;color:#fff;font-weight:600;">{phase_names[i]}：{label}</div>'
    for m_pos, m_label in milestones:
        mx = m_pos * COL_WIDTH
        body += f'<div style="position:absolute;left:{mx-8:.0f}px;top:32px;font-size:20px;color:var(--accent-warm);">◆</div><div style="position:absolute;left:{mx-24:.0f}px;top:60px;font-size:9px;color:var(--accent-warm);width:48px;text-align:center;">{m_label}</div>'
    body += '''
            </div>
        </div>
        <div style="margin-left:{}px;margin-top:8px;display:flex;gap:16px;font-size:11px;">'''.format(LEFT_WIDTH)
    for phase_name, color in zip(phase_names, phase_colors):
        body += f'<span><span style="display:inline-block;width:14px;height:14px;background:{color};border-radius:3px;vertical-align:middle;margin-right:4px;"></span>{phase_name}</span>'
    body += f'<span style="margin-left:12px;">◆ 里程碑节点</span></div>'
    body += f'''
        <div style="margin-left:{LEFT_WIDTH}px;margin-top:12px;font-size:var(--fs-l5);color:var(--text-secondary);background:#f8fafc;padding:8px 12px;border-radius:4px;">
            <b>版本演进：</b>V1.0（最小可用·60%功能）→ V2.0（全功能+第三方测评）→ V3.0（生产就绪·完整文档+终验交付）
        </div>
    </div>
</div>'''
    return wrap_html(illu['text_content']['main_title'], body, scale_factor=1.0)


# ═══════════════════════════════════════════════
# KU-016: Post-processing visualization workbench (CH-07.4)
# ═══════════════════════════════════════════════

def render_ku016(illu):
    extra = '''
.quad-cell { background:var(--bg-panel); border:1px solid var(--border-medium); border-radius:8px; overflow:hidden; display:flex; flex-direction:column; }
.quad-cell__header { padding:8px 12px; font-size:var(--fs-l4); font-weight:700; color:var(--primary); border-bottom:1px solid var(--border-light); background:#fafbfc; display:flex; align-items:center; gap:6px; }
.quad-cell__body { flex:1; display:flex; align-items:center; justify-content:center; position:relative; min-height:150px; }
.viz-placeholder { color:var(--text-muted); font-size:var(--fs-l5); }
.tool-palette { display:flex; gap:4px; padding:6px 10px; border-bottom:1px solid var(--border-light); background:#fafbfc; flex-wrap:wrap; }
.tool-chip { padding:2px 10px; border:1px solid var(--border-medium); border-radius:12px; font-size:var(--fs-l5); cursor:default; white-space:nowrap; }
.tool-chip.active { background:var(--primary); color:var(--text-inverse); border-color:var(--primary); }'''

    body = '''
<div class="app-toolbar">
    <button class="btn">导入数据</button>
    <button class="btn">导出结果</button>
    <span class="btn-sep"></span>
    <button class="btn btn--primary">计算</button>
    <button class="btn">重置视图</button>
    <span class="btn-sep"></span>
    <select class="form-select"><option>温度场</option><option>热应力</option><option>相变分数</option></select>
    <input class="form-input" style="width:120px;margin-left:auto;" placeholder="时间步: 50/200">
</div>
<div class="tool-palette">
    <span style="font-size:var(--fs-l5);color:var(--text-muted);margin-right:8px;">工具:</span>
    <span class="tool-chip active">平移</span>
    <span class="tool-chip">缩放</span>
    <span class="tool-chip">探针</span>
    <span class="tool-chip">剖切</span>
    <span class="tool-chip">等值线</span>
    <span class="tool-chip">动画</span>
    <span class="tool-chip">标注</span>
</div>
<div class="layout-quad p-lg gap-md" style="background:var(--bg-page);">
    <div class="quad-cell">
        <div class="quad-cell__header">&#9726; 温度云图 (K)</div>
        <div class="quad-cell__body">
            <svg width="100%" height="100%" viewBox="0 0 320 180">
                <defs>
                    <radialGradient id="heat1"><stop offset="0%" stop-color="#ef4444"/><stop offset="50%" stop-color="#f59e0b"/><stop offset="100%" stop-color="#3b82f6"/></radialGradient>
                </defs>
                <rect x="20" y="15" width="280" height="150" rx="6" fill="url(#heat1)" opacity="0.7"/>
                <rect x="60" y="50" width="60" height="40" rx="4" fill="white" opacity="0.25"/>
                <rect x="180" y="80" width="50" height="30" rx="4" fill="white" opacity="0.25"/>
                <rect x="130" y="110" width="40" height="20" rx="3" fill="white" opacity="0.3"/>
                <text x="160" y="170" text-anchor="middle" font-size="10" fill="#888">T_max=1892K | T_min=312K | ΔT=1580K</text>
            </svg>
        </div>
    </div>
    <div class="quad-cell">
        <div class="quad-cell__header">&#8599; 速度矢量场 (m/s)</div>
        <div class="quad-cell__body">
            <svg width="100%" height="100%" viewBox="0 0 320 180">
                <rect x="20" y="15" width="280" height="150" rx="6" fill="#f0f4f8"/>
                <line x1="60" y1="100" x2="110" y2="60" stroke="#007bb5" stroke-width="1.5" marker-end="url(#arrow1)"/>
                <line x1="140" y1="120" x2="190" y2="80" stroke="#007bb5" stroke-width="1.5"/>
                <line x1="200" y1="90" x2="250" y2="50" stroke="#007bb5" stroke-width="1.5"/>
                <line x1="80" y1="130" x2="130" y2="100" stroke="#007bb5" stroke-width="1"/>
                <line x1="160" y1="110" x2="200" y2="75" stroke="#007bb5" stroke-width="1.2"/>
                <line x1="220" y1="70" x2="260" y2="40" stroke="#007bb5" stroke-width="1.3"/>
                <text x="160" y="170" text-anchor="middle" font-size="10" fill="#888">v_max=3.42m/s | Re=1.28×10⁴</text>
            </svg>
        </div>
    </div>
    <div class="quad-cell">
        <div class="quad-cell__header">&#8768; 热流线分布 (W/m²)</div>
        <div class="quad-cell__body">
            <svg width="100%" height="100%" viewBox="0 0 320 180">
                <rect x="20" y="15" width="280" height="150" rx="6" fill="#fafbfc"/>
                <path d="M40 80 Q100 40 160 80 Q220 120 280 80" stroke="#e8833e" stroke-width="1.5" fill="none"/>
                <path d="M40 100 Q100 60 160 100 Q220 140 280 100" stroke="#e8833e" stroke-width="1.2" fill="none" opacity="0.7"/>
                <path d="M40 120 Q100 80 160 120 Q220 160 280 120" stroke="#e8833e" stroke-width="1.0" fill="none" opacity="0.5"/>
                <path d="M40 60 Q100 20 160 60 Q220 100 280 60" stroke="#e8833e" stroke-width="1.0" fill="none" opacity="0.5"/>
                <text x="160" y="170" text-anchor="middle" font-size="10" fill="#888">q_max=1.24×10⁵W/m²</text>
            </svg>
        </div>
    </div>
    <div class="quad-cell">
        <div class="quad-cell__header">&#9678; 等值线图 — 温度(K)</div>
        <div class="quad-cell__body">
            <svg width="100%" height="100%" viewBox="0 0 320 180">
                <rect x="20" y="15" width="280" height="150" rx="6" fill="#fafbfc"/>
                <ellipse cx="160" cy="90" rx="100" ry="55" fill="none" stroke="#3b82f6" stroke-width="1" opacity="0.5"/>
                <ellipse cx="160" cy="90" rx="75" ry="40" fill="none" stroke="#f59e0b" stroke-width="1.2" opacity="0.6"/>
                <ellipse cx="160" cy="90" rx="50" ry="25" fill="none" stroke="#ef4444" stroke-width="1.4" opacity="0.7"/>
                <ellipse cx="160" cy="90" rx="25" ry="12" fill="none" stroke="#ef4444" stroke-width="1.8"/>
                <text x="160" y="170" text-anchor="middle" font-size="10" fill="#888">等值线间距 ΔT=200K | 共8条</text>
            </svg>
        </div>
    </div>
</div>
<div class="app-statusbar">
    <span class="sb-item"><span class="status-dot status-dot--ok"></span>就绪</span>
    <span class="sb-item">网格: 128×64×32</span>
    <span class="sb-item">时间步: 50/200 | Δt=0.01s</span>
    <span class="sb-item">残差: 1.2×10⁻⁶</span>
    <span class="sb-item" style="margin-left:auto;">内存: 1.8 GB | 计算耗时: 42.3s</span>
</div>'''
    return wrap_html(illu['text_content']['main_title'], body, extra, scale_factor=1.15)


# ═══════════════════════════════════════════════
# KU-017: MODBUS real-time monitoring dashboard (CH-08.3)
# ═══════════════════════════════════════════════

def render_ku017(illu):
    body = '''
<div class="app-toolbar">
    <button class="btn btn--primary">开始采集</button>
    <button class="btn">暂停</button>
    <button class="btn">导出CSV</button>
    <span class="btn-sep"></span>
    <span style="font-size:var(--fs-l4);">刷新间隔:</span>
    <select class="form-select"><option>1 s</option><option selected>5 s</option><option>30 s</option></select>
    <span style="margin-left:auto;display:flex;align-items:center;gap:8px;">
        <span class="status-dot status-dot--ok"></span>
        <span style="font-size:var(--fs-l4);color:var(--success);font-weight:600;">连接正常</span>
    </span>
</div>
<div class="p-lg flex-col gap-md" style="flex:1;">
    <!-- Top metrics -->
    <div class="metrics-grid" style="grid-template-columns:repeat(5,1fr);">
        <div class="metric-card">
            <div class="metric-card__label">炉膛温度</div>
            <div class="metric-card__value warning">1,247.3</div>
            <div class="metric-card__sub">°C | 上限 1350°C</div>
        </div>
        <div class="metric-card">
            <div class="metric-card__label">真空度</div>
            <div class="metric-card__value success">2.4×10⁻³</div>
            <div class="metric-card__sub">Pa | 警戒 5×10⁻³</div>
        </div>
        <div class="metric-card">
            <div class="metric-card__label">冷却水流量</div>
            <div class="metric-card__value primary">12.8</div>
            <div class="metric-card__sub">L/min | 正常范围</div>
        </div>
        <div class="metric-card">
            <div class="metric-card__label">加热功率</div>
            <div class="metric-card__value warning">84.2</div>
            <div class="metric-card__sub">kW | 额定 100kW</div>
        </div>
        <div class="metric-card">
            <div class="metric-card__label">设备在线数</div>
            <div class="metric-card__value success">12</div>
            <div class="metric-card__sub">/ 12 台 | 全部在线</div>
        </div>
    </div>
    <!-- Device table -->
    <div class="panel">
        <div class="panel-header">MODBUS 设备实时数据</div>
        <div class="panel-body compact" style="max-height:280px;overflow-y:auto;">
            <table class="data-table compact">
                <thead><tr>
                    <th>从站地址</th><th>设备名称</th><th class="right">寄存器 40001</th><th class="right">寄存器 40002</th><th class="right">寄存器 40003</th><th class="center">状态</th><th class="right">更新时间</th>
                </tr></thead>
                <tbody>'''
    devices = [
        ('01', '高温炉主控', '1247.3°C', '84.2kW', '12.8L/min', 'ok', '14:32:05'),
        ('02', '真空泵组', '2.4Pa', '98.5%', '1450rpm', 'ok', '14:32:04'),
        ('03', '冷却循环泵', '0.45MPa', '28.3°C', '12.8L/min', 'warn', '14:32:03'),
        ('04', '温度巡检仪-1', '312.4°C', '456.7°C', '892.1°C', 'ok', '14:32:05'),
        ('05', '温度巡检仪-2', '315.1°C', '461.2°C', '888.7°C', 'ok', '14:32:04'),
        ('06', '压力变送器-A', '0.12MPa', '4.2mA', '21.3%', 'ok', '14:32:05'),
        ('07', '流量计-主管路', '12.8', '0.0', '142.6', 'ok', '14:32:04'),
    ]
    for addr, name, r1, r2, r3, status, ts in devices:
        dot = 'ok' if status == 'ok' else 'warn'
        body += f'<tr><td>{addr}</td><td><b>{name}</b></td><td class="right">{r1}</td><td class="right">{r2}</td><td class="right">{r3}</td><td class="center"><span class="status-dot status-dot--{dot}"></span>{"正常" if status == "ok" else "预警"}</td><td class="right">{ts}</td></tr>'
    body += '''</tbody></table>
        </div>
    </div>
</div>
<div class="app-statusbar">
    <span class="sb-item">COM3 | 9600-8-N-1</span>
    <span class="sb-item">轮询周期: 5s</span>
    <span class="sb-item">今日采集: 17,280 条</span>
    <span class="sb-item" style="margin-left:auto;">最后刷新: 2024-12-15 14:32:05</span>
</div>'''
    return wrap_html(illu['text_content']['main_title'], body, scale_factor=1.15)


# ═══════════════════════════════════════════════
# KU-018: System environment check report (CH-09.2)
# ═══════════════════════════════════════════════

def render_ku018(illu):
    extra = '''
.checklist-title { font-size:var(--fs-l2); font-weight:700; color:var(--primary); margin-bottom:var(--space-md); display:flex; align-items:center; gap:8px; }
.check-category { margin-bottom:var(--space-xl); }
.check-category__name { font-size:var(--fs-l3); font-weight:600; color:var(--primary); margin-bottom:var(--space-sm); padding-bottom:6px; border-bottom:1px solid var(--border-light); }
.summary-bar { display:flex; gap:var(--space-xl); padding:var(--space-lg); background:var(--bg-panel); border-radius:var(--radius-lg); border:1px solid var(--border-medium); margin-bottom:var(--space-lg); }'''

    body = '''
<div class="app-menubar">
    <span>检测</span><span>报告</span><span>工具</span><span>帮助</span>
</div>
<div class="content-scroll">
    <div style="font-size:var(--fs-l1);font-weight:700;color:var(--primary);margin-bottom:4px;">系统环境检测报告</div>
    <div class="text-muted" style="margin-bottom:20px;">检测时间: 2024-12-15 14:30 | 目标环境: Windows 7/10/11 x64 | 检测版本: EnvCheck v2.1.0</div>
    <!-- Summary -->
    <div class="summary-bar">
        <div style="text-align:center;"><div class="metric-card__value success">11</div><div class="metric-card__sub">通过</div></div>
        <div style="text-align:center;"><div class="metric-card__value warning">2</div><div class="metric-card__sub">警告</div></div>
        <div style="text-align:center;"><div class="metric-card__value error">1</div><div class="metric-card__sub">未通过</div></div>
        <div style="text-align:center;"><div style="font-size:32px;font-weight:700;color:var(--text-muted);">—</div><div class="metric-card__sub">总计 14 项</div></div>
    </div>
    <!-- Category 1 -->
    <div class="check-category">
        <div class="check-category__name">一、操作系统与运行库</div>'''
    for label, status in [
        ('操作系统版本检测 (Windows 10 22H2 x64)', 'pass'),
        ('.NET Framework 4.8 运行时', 'pass'),
        ('Visual C++ 2015-2022 Redistributable (x64)', 'pass'),
        ('Universal C Runtime (KB3063858)', 'warn'),
        ('Windows Installer 5.0+', 'pass'),
    ]:
        body += f'<div class="check-item check-item--{status}"><span class="check-item__icon">{"✓" if status == "pass" else "⚠" if status == "warn" else "✗"}</span> {label}</div>'
    body += '</div>'
    # Category 2
    body += '<div class="check-category"><div class="check-category__name">二、Python 环境与依赖包</div>'
    for label, status in [
        ('Python 3.10.11 (x64)', 'pass'),
        ('numpy 1.26.4 + scipy 1.12.0', 'pass'),
        ('pandas 2.1.4 (Win10+) / 1.5.3 (Win7 fallback)', 'pass'),
        ('PyQt5 5.15.10 + PyQtGraph 0.13.7', 'pass'),
        ('h5py 3.10.0 (HDF5 1.14.3)', 'warn'),
    ]:
        body += f'<div class="check-item check-item--{status}"><span class="check-item__icon">{"✓" if status == "pass" else "⚠" if status == "warn" else "✗"}</span> {label}</div>'
    body += '</div>'
    # Category 3
    body += '<div class="check-category"><div class="check-category__name">三、硬件与驱动检测</div>'
    for label, status in [
        ('CPU: Intel Core i7-12700 (12核20线程)', 'pass'),
        ('内存: 32 GB DDR5 (可用 28.4 GB)', 'pass'),
        ('磁盘空间: 系统盘 120 GB / 数据盘 800 GB', 'pass'),
        ('OpenGL 3.3+ 图形驱动 (NVIDIA RTX 3060)', 'fail'),
    ]:
        body += f'<div class="check-item check-item--{status}"><span class="check-item__icon">{"✓" if status == "pass" else "⚠" if status == "warn" else "✗"}</span> {label}</div>'
    body += '</div>'
    # Action buttons
    body += '''
    <div style="display:flex;gap:12px;margin-top:16px;">
        <button class="btn btn--primary btn--lg">导出检测报告 (PDF)</button>
        <button class="btn btn--lg">重新检测</button>
        <button class="btn btn--lg">导出 JSON</button>
    </div>
</div>'''
    return wrap_html(illu['text_content']['main_title'], body, extra, scale_factor=1.15)


# ═══════════════════════════════════════════════
# KU-019: Phase diagram visualization (CH-06.3)
# ═══════════════════════════════════════════════

def render_ku019(illu):
    extra = '''
.phase-legend { display:flex; gap:16px; flex-wrap:wrap; padding:8px 0; font-size:var(--fs-l5); }
.phase-legend span { display:flex; align-items:center; gap:4px; }
.phase-swatch { width:12px; height:12px; border-radius:2px; }'''

    body = f'''
<div class="app-toolbar">
    <button class="btn btn--primary">相图计算</button>
    <button class="btn">导出 SVG</button>
    <button class="btn">导出数据</button>
    <span class="btn-sep"></span>
    <span style="font-size:var(--fs-l4);">体系:</span>
    <select class="form-select"><option>SiO₂-Al₂O₃-CaO</option><option>MgO-Al₂O₃-SiO₂</option></select>
    <span style="font-size:var(--fs-l4);">T=</span>
    <input class="form-input" style="width:70px;" value="1600">
    <span style="font-size:var(--fs-l4);">°C</span>
</div>
<div class="layout-hsplit" style="flex:1;min-height:500px;">
    <!-- Ternary phase diagram -->
    <div style="flex:1;padding:16px;background:var(--bg-panel);display:flex;flex-direction:column;">
        <div style="font-size:var(--fs-l3);font-weight:700;color:var(--primary);margin-bottom:8px;">SiO₂-Al₂O₃-CaO 三元相图 (T=1600°C)</div>
        <div style="flex:1;display:flex;align-items:center;justify-content:center;">
            <svg width="440" height="400" viewBox="0 0 440 400">
                <!-- Triangle -->
                <polygon points="220,20 30,370 410,370" fill="#fafbfc" stroke="#1a3a5c" stroke-width="2"/>
                <!-- Labels -->
                <text x="220" y="12" text-anchor="middle" font-size="14" font-weight="700" fill="#1a3a5c">SiO₂</text>
                <text x="12" y="390" text-anchor="end" font-size="14" font-weight="700" fill="#1a3a5c">Al₂O₃</text>
                <text x="428" y="390" text-anchor="start" font-size="14" font-weight="700" fill="#1a3a5c">CaO</text>
                <!-- Phase regions (approximate) -->
                <path d="M220 100 L150 220 L180 280 L250 200 Z" fill="#e3f2fd" stroke="#3b82f6" stroke-width="1" opacity="0.6"/>
                <text x="200" y="180" font-size="11" fill="#3b82f6">Liquid</text>
                <path d="M60 340 L150 220 L220 100 L100 300 Z" fill="#fff3e0" stroke="#e8833e" stroke-width="1" opacity="0.6"/>
                <text x="120" y="260" font-size="10" fill="#e8833e">Mullite+L</text>
                <path d="M150 220 L250 200 L350 320 L180 280 Z" fill="#e8f5e9" stroke="#10b981" stroke-width="1" opacity="0.6"/>
                <text x="250" y="260" font-size="10" fill="#10b981">Anorthite+L</text>
                <path d="M100 300 L180 280 L60 340 Z" fill="#fce4ec" stroke="#ef4444" stroke-width="1" opacity="0.5"/>
                <text x="90" y="310" font-size="9" fill="#ef4444">Corundum</text>
                <!-- Data point -->
                <circle cx="175" cy="220" r="6" fill="#ef4444" stroke="white" stroke-width="2"/>
                <text x="190" y="218" font-size="11" fill="#ef4444" font-weight="600">目标配方</text>
                <!-- Grid lines -->
                <line x1="125" y1="195" x2="315" y2="195" stroke="#ccc" stroke-width="0.3"/>
                <line x1="80" y1="283" x2="360" y2="283" stroke="#ccc" stroke-width="0.3"/>
            </svg>
        </div>
    </div>
    <!-- Phase identification table -->
    <div style="width:380px;padding:16px;background:#fafbfc;border-left:1px solid var(--border-medium);overflow-y:auto;">
        <div style="font-size:var(--fs-l3);font-weight:700;color:var(--primary);margin-bottom:12px;">相识别结果</div>
        <table class="data-table compact">
            <thead><tr><th>相名称</th><th class="center">含量 (wt%)</th><th class="center">状态</th></tr></thead>
            <tbody>
                <tr><td>液相 (Liquid)</td><td class="right">62.4</td><td class="center"><span class="badge badge--primary">稳定</span></td></tr>
                <tr><td>莫来石 (Mullite)</td><td class="right">22.1</td><td class="center"><span class="badge badge--success">主要相</span></td></tr>
                <tr><td>钙长石 (Anorthite)</td><td class="right">12.8</td><td class="center"><span class="badge badge--success">次生相</span></td></tr>
                <tr><td>刚玉 (Corundum)</td><td class="right">2.7</td><td class="center"><span class="badge badge--warning">微量</span></td></tr>
            </tbody>
        </table>
        <div class="divider"></div>
        <div style="font-size:var(--fs-l4);line-height:2;">
            <div><span class="text-muted">液相线温度:</span> <b>1,847°C</b></div>
            <div><span class="text-muted">固相线温度:</span> <b>1,312°C</b></div>
            <div><span class="text-muted">初晶相:</span> <b>莫来石 (Mullite)</b></div>
            <div><span class="text-muted">共晶点:</span> <b>T=1,265°C</b></div>
            <div><span class="text-muted">计算数据库:</span> <b>FACT Oxide (FToxid)</b></div>
        </div>
        <button class="btn btn--primary btn--block btn--lg" style="margin-top:16px;">重新计算</button>
    </div>
</div>
<div class="app-statusbar">
    <span class="sb-item"><span class="status-dot status-dot--ok"></span>计算完成</span>
    <span class="sb-item">Gibbs自由能最小化 | 迭代 47 步</span>
    <span class="sb-item" style="margin-left:auto;">耗时: 2.8s | FactSage 8.2</span>
</div>'''
    return wrap_html(illu['text_content']['main_title'], body, extra, scale_factor=1.15)


# ═══════════════════════════════════════════════
# KU-020: Performance test dashboard (CH-12.2)
# ═══════════════════════════════════════════════

def render_ku020(illu):
    extra = '''
.perf-chart { background:var(--bg-panel); border:1px solid var(--border-medium); border-radius:var(--radius-lg); padding:16px; }
.perf-chart__title { font-size:var(--fs-l4); font-weight:700; color:var(--primary); margin-bottom:4px; }
.perf-threshold { display:flex; align-items:center; gap:8px; padding:8px 12px; background:var(--bg-card); border-radius:var(--radius-sm); margin-bottom:8px; font-size:var(--fs-l5); }
.perf-threshold__bar { flex:1; height:6px; background:#e5e7eb; border-radius:3px; position:relative; }
.perf-threshold__fill { height:100%; border-radius:3px; position:absolute; left:0; top:0; }'''

    body = '''
<div class="app-toolbar">
    <button class="btn btn--primary">运行测试</button>
    <button class="btn">停止</button>
    <span class="btn-sep"></span>
    <select class="form-select"><option>全部用例</option><option>计算性能</option><option>IO吞吐</option><option>内存压力</option></select>
    <span style="margin-left:auto;font-size:var(--fs-l4);">并发:</span>
    <select class="form-select"><option>1线程</option><option selected>4线程</option><option>8线程</option><option>16线程</option></select>
</div>
<div class="p-lg flex-col gap-md" style="flex:1;">
    <!-- Top metrics -->
    <div class="metrics-grid" style="grid-template-columns:repeat(4,1fr);">
        <div class="metric-card">
            <div class="metric-card__label">总用例数</div>
            <div class="metric-card__value primary">42</div>
            <div class="metric-card__sub">通过 40 / 失败 2</div>
        </div>
        <div class="metric-card">
            <div class="metric-card__label">通过率</div>
            <div class="metric-card__value warning">95.2</div>
            <div class="metric-card__sub">% | 目标 ≥ 95%</div>
        </div>
        <div class="metric-card">
            <div class="metric-card__label">平均响应时间</div>
            <div class="metric-card__value success">47.3</div>
            <div class="metric-card__sub">ms | 目标 < 200ms</div>
        </div>
        <div class="metric-card">
            <div class="metric-card__label">CPU 占用峰值</div>
            <div class="metric-card__value primary">62.8</div>
            <div class="metric-card__sub">% | 目标 < 80%</div>
        </div>
    </div>
    <!-- Performance charts grid -->
    <div class="layout-2col">
        <div class="perf-chart">
            <div class="perf-chart__title">DLL 计算耗时 (ms) — 热化学计算</div>
            <div style="height:120px;position:relative;margin:8px 0;">
                <svg width="100%" height="100%" viewBox="0 0 340 120">
                    <line x1="40" y1="100" x2="320" y2="100" stroke="#e5e7eb" stroke-width="1"/>
                    <rect x="50" y="70" width="18" height="30" fill="#3b82f6" rx="1"/><text x="59" y="115" text-anchor="middle" font-size="8" fill="#888">1</text>
                    <rect x="80" y="55" width="18" height="45" fill="#3b82f6" rx="1"/><text x="89" y="115" text-anchor="middle" font-size="8" fill="#888">4</text>
                    <rect x="110" y="45" width="18" height="55" fill="#3b82f6" rx="1"/><text x="119" y="115" text-anchor="middle" font-size="8" fill="#888">8</text>
                    <rect x="140" y="45" width="18" height="55" fill="#3b82f6" rx="1"/><text x="149" y="115" text-anchor="middle" font-size="8" fill="#888">16</text>
                    <line x1="50" y1="82" x2="320" y2="82" stroke="#10b981" stroke-width="1.5" stroke-dasharray="4,3"/>
                    <text x="325" y="86" font-size="9" fill="#10b981">阈值200ms</text>
                </svg>
            </div>
            <div class="perf-threshold"><span style="width:100px;">1线程</span><div class="perf-threshold__bar"><div class="perf-threshold__fill" style="width:42%;background:var(--success);"></div></div><span>84ms</span></div>
            <div class="perf-threshold"><span style="width:100px;">4线程</span><div class="perf-threshold__bar"><div class="perf-threshold__fill" style="width:31%;background:var(--success);"></div></div><span>62ms</span></div>
            <div class="perf-threshold"><span style="width:100px;">8线程</span><div class="perf-threshold__bar"><div class="perf-threshold__fill" style="width:24%;background:var(--success);"></div></div><span>48ms</span></div>
            <div class="perf-threshold"><span style="width:100px;">16线程</span><div class="perf-threshold__bar"><div class="perf-threshold__fill" style="width:22%;background:var(--success);"></div></div><span>44ms</span></div>
        </div>
        <div class="perf-chart">
            <div class="perf-chart__title">IO 吞吐量 (MB/s) — HDF5 读写</div>
            <div class="metrics-grid" style="grid-template-columns:1fr 1fr;margin-top:8px;">
                <div class="metric-card"><div class="metric-card__label">顺序读</div><div class="metric-card__value success" style="font-size:24px;">384.2</div><div class="metric-card__sub">MB/s</div></div>
                <div class="metric-card"><div class="metric-card__label">顺序写</div><div class="metric-card__value primary" style="font-size:24px;">217.6</div><div class="metric-card__sub">MB/s</div></div>
            </div>
            <div class="perf-threshold"><span style="width:100px;">1 MB 块</span><div class="perf-threshold__bar"><div class="perf-threshold__fill" style="width:82%;background:var(--success);"></div></div><span>386 MB/s</span></div>
            <div class="perf-threshold"><span style="width:100px;">128 KB 块</span><div class="perf-threshold__bar"><div class="perf-threshold__fill" style="width:71%;background:var(--info);"></div></div><span>312 MB/s</span></div>
            <div class="perf-threshold"><span style="width:100px;">4 KB 块</span><div class="perf-threshold__bar"><div class="perf-threshold__fill" style="width:38%;background:var(--warning);"></div></div><span>84 MB/s</span></div>
        </div>
    </div>
    <!-- Failed test cases -->
    <div class="panel">
        <div class="panel-header">失败用例详情</div>
        <div class="panel-body compact">
            <table class="data-table compact">
                <thead><tr><th>用例ID</th><th>用例名称</th><th class="center">状态</th><th class="right">耗时(ms)</th><th>错误信息</th></tr></thead>
                <tbody>
                    <tr><td>TC-017</td><td>h5py_parallel_write_8thread</td><td class="center"><span class="badge badge--error">失败</span></td><td class="right">1,247</td><td>HDF5 parallel write timeout (30s)</td></tr>
                    <tr><td>TC-029</td><td>memory_pressure_16GB_limit</td><td class="center"><span class="badge badge--warning">跳过</span></td><td class="right">—</td><td>测试环境内存不足 (req 32GB, avail 16GB)</td></tr>
                </tbody>
            </table>
        </div>
    </div>
</div>
<div class="app-statusbar">
    <span class="sb-item">测试套件: PerformanceTestSuite v3.1</span>
    <span class="sb-item">总耗时: 127.4s</span>
    <span class="sb-item" style="margin-left:auto;">平台: Win10 x64 | Python 3.10.11 | 32GB RAM</span>
</div>'''
    return wrap_html(illu['text_content']['main_title'], body, extra, scale_factor=1.15)


# ═══════════════════════════════════════════════
# KU-021: Permission management config (CH-05.2)
# ═══════════════════════════════════════════════

def render_ku021(illu):
    extra = '''
.perm-matrix { display:grid; grid-template-columns:140px repeat(5,1fr); gap:1px; background:var(--border-medium); border:1px solid var(--border-medium); border-radius:var(--radius-sm); overflow:hidden; }
.perm-matrix > div { background:var(--bg-panel); padding:8px 10px; font-size:var(--fs-l5); display:flex; align-items:center; }
.perm-matrix .perm-header { background:var(--primary); color:var(--text-inverse); font-weight:600; font-size:var(--fs-l5); justify-content:center; }
.perm-matrix .perm-label { font-weight:600; color:var(--primary); }
.perm-matrix .perm-check { justify-content:center; }'''

    body = '''
<div class="app-menubar">
    <span>系统</span><span>用户管理</span><span>角色管理</span><span>权限配置</span><span>审计日志</span>
</div>
<div class="app-toolbar">
    <button class="btn btn--primary">新增用户</button>
    <button class="btn">批量导入</button>
    <button class="btn">导出列表</button>
    <span class="btn-sep"></span>
    <input class="form-input" style="width:200px;margin-left:auto;" placeholder="搜索用户...">
</div>
<div class="layout-hsplit" style="flex:1;min-height:500px;">
    <!-- User list -->
    <div style="width:420px;border-right:1px solid var(--border-medium);display:flex;flex-direction:column;">
        <div class="panel-body compact" style="flex:1;overflow-y:auto;">
            <table class="data-table compact">
                <thead><tr><th>用户名</th><th>角色</th><th class="center">状态</th><th>最后登录</th></tr></thead>
                <tbody>
                    <tr class="row-selected"><td><b>admin</b></td><td>系统管理员</td><td class="center"><span class="status-dot status-dot--ok"></span>活跃</td><td>2024-12-15 14:20</td></tr>
                    <tr><td>zhangsan</td><td>数据管理员</td><td class="center"><span class="status-dot status-dot--ok"></span>活跃</td><td>2024-12-15 11:45</td></tr>
                    <tr><td>lisi</td><td>工程师</td><td class="center"><span class="status-dot status-dot--ok"></span>活跃</td><td>2024-12-15 09:30</td></tr>
                    <tr><td>wangwu</td><td>工程师</td><td class="center"><span class="status-dot status-dot--warn"></span>锁定</td><td>2024-12-10 16:22</td></tr>
                    <tr><td>zhaoliu</td><td>只读用户</td><td class="center"><span class="status-dot status-dot--ok"></span>活跃</td><td>2024-12-14 08:15</td></tr>
                    <tr><td>guest</td><td>访客</td><td class="center"><span class="status-dot status-dot--err"></span>禁用</td><td>—</td></tr>
                </tbody>
            </table>
        </div>
    </div>
    <!-- Right: Role + Permission config -->
    <div class="flex-col flex-1">
        <div class="p-lg" style="border-bottom:1px solid var(--border-medium);">
            <div class="form-label">选中用户: <b>admin</b> (系统管理员)</div>
            <div class="form-row" style="margin-top:8px;">
                <div class="form-group" style="flex:1;">
                    <div class="form-label">角色分配</div>
                    <select class="form-select wide"><option selected>系统管理员</option><option>数据管理员</option><option>工程师</option><option>只读用户</option><option>访客</option></select>
                </div>
                <button class="btn btn--primary" style="align-self:flex-end;">应用</button>
            </div>
        </div>
        <div class="p-lg flex-1" style="overflow-y:auto;">
            <div class="form-label mb-md">权限矩阵 — 角色: 系统管理员</div>
            <div class="perm-matrix">
                <div class="perm-header">模块</div><div class="perm-header">查看</div><div class="perm-header">编辑</div><div class="perm-header">删除</div><div class="perm-header">导出</div><div class="perm-header">管理</div>'''
    perms = [
        ('数据库管理', '✓','✓','✓','✓','✓'),
        ('材料设计', '✓','✓','✓','✓','—'),
        ('热环境确定', '✓','✓','✓','✓','—'),
        ('热环境响应', '✓','✓','✓','✓','—'),
        ('用户管理', '✓','✓','✓','—','✓'),
        ('系统配置', '✓','—','—','—','✓'),
        ('审计日志', '✓','—','—','✓','—'),
    ]
    for label, v, e, d, x, m in perms:
        check = lambda c: f'<span style="color:var(--success);font-weight:700;">{c}</span>' if c == '✓' else f'<span style="color:var(--text-muted);">{c}</span>'
        body += f'<div class="perm-label">{label}</div><div class="perm-check">{check(v)}</div><div class="perm-check">{check(e)}</div><div class="perm-check">{check(d)}</div><div class="perm-check">{check(x)}</div><div class="perm-check">{check(m)}</div>'
    body += '''</div>
            <div style="margin-top:16px;display:flex;gap:8px;">
                <button class="btn btn--primary">保存权限</button>
                <button class="btn">重置</button>
                <button class="btn">导出权限报告</button>
            </div>
        </div>
    </div>
</div>
<div class="app-statusbar">
    <span class="sb-item">用户总数: 6 | 活跃: 4</span>
    <span class="sb-item">角色: 5个预定义角色</span>
    <span class="sb-item" style="margin-left:auto;">权限配置文件: ./config/permissions_v2.1.json</span>
</div>'''
    return wrap_html(illu['text_content']['main_title'], body, extra, scale_factor=1.15)


# ═══════════════════════════════════════════════
# Renderer dispatch
# ═══════════════════════════════════════════════

RENDERERS = {
    'KU-001': render_ku001,
    'KU-008': render_ku008,
    'KU-009': render_ku009,
    'KU-010': render_ku010,
    'KU-013': render_ku013,
    'KU-012': render_ku012,
    'LC-003': render_lc003,
    'KU-016': render_ku016,
    'KU-017': render_ku017,
    'KU-018': render_ku018,
    'KU-019': render_ku019,
    'KU-020': render_ku020,
    'KU-021': render_ku021,
}


def render_and_screenshot(illu_id, png_output_dir):
    """Generate HTML, save it, and screenshot to PNG."""
    illu = load_illu(illu_id)
    renderer = RENDERERS.get(illu_id)
    if not renderer:
        print(f"  No renderer for {illu_id}")
        return None

    html = renderer(illu)

    os.makedirs(png_output_dir, exist_ok=True)
    html_path = os.path.join(png_output_dir, f'{illu_id}.html')
    with open(html_path, 'w', encoding='utf-8') as f:
        f.write(html)
    print(f"  HTML saved: {html_path}")

    png_path = os.path.join(png_output_dir, f'{illu_id}.png')
    try:
        from playwright.sync_api import sync_playwright
        with sync_playwright() as pw:
            browser = pw.chromium.launch(headless=True)
            page = browser.new_page(
                viewport={"width": 1600, "height": 1000},
                device_scale_factor=2,
            )
            page.goto(f'file:///{html_path.replace(chr(92), "/")}', wait_until="networkidle")
            page.screenshot(path=png_path, full_page=True)
            browser.close()
        print(f"  PNG saved: {png_path} ({os.path.getsize(png_path)} bytes)")
    except Exception as e:
        print(f"  Screenshot failed: {e}")
        return None

    return png_path


def main():
    parser = argparse.ArgumentParser(description='Render HTML illustrations for bid document')
    parser.add_argument('--illu', help='Render specific illustration ID only')
    parser.add_argument('--no-screenshot', action='store_true', help='Generate HTML only, no screenshot')
    args = parser.parse_args()

    png_dir = OUT_DIR
    os.makedirs(png_dir, exist_ok=True)

    ids = [args.illu] if args.illu else HTML_ILLU_IDS

    print(f"Rendering {len(ids)} HTML illustration(s)...")
    for illu_id in ids:
        print(f"\n[{illu_id}]")
        if args.no_screenshot:
            illu = load_illu(illu_id)
            renderer = RENDERERS.get(illu_id)
            if renderer:
                html = renderer(illu)
                html_path = os.path.join(png_dir, f'{illu_id}.html')
                with open(html_path, 'w', encoding='utf-8') as f:
                    f.write(html)
                print(f"  HTML saved: {html_path}")
            else:
                print(f"  No renderer for {illu_id}")
        else:
            render_and_screenshot(illu_id, png_dir)

    print(f"\nDone. Output directory: {png_dir}")


if __name__ == '__main__':
    main()
