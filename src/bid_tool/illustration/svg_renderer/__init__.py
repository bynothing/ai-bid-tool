"""SVG diagram renderer package.

All public names re-exported for backward compatibility.
"""
from ._engine import *  # noqa: F401,F403

# Wildcard imports skip underscore-prefixed names. Explicitly re-export them:
from ._engine import (
    _theme_with_palette,
    apply_font_scale,
    slug,
    esc,
    defs,
    icon_symbols,
    note_bar,
    item_card,
    edge_visual,
    append_semantic_edge,
    append_edge_tip,
    style_color,
    formal_bid_css,
    svg_text_block,
    bullet_list,
    formal_panel,
    section_box,
    load_spec,
    validate_spec,
    quality_warnings,
    render_png,
    write_manifest,
)
