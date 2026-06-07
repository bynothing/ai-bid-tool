# Draw.io Skill Integration

This project integrates selected practices from the public AI Draw.io skill:

https://github.com/Agents365-ai/drawio-skill

The external repository is not required at runtime. Its workflow has been
adapted into the local `drawio` renderer.

## Integrated rules

- Generate editable `.drawio` source before exporting preview assets.
- Use real Draw.io containers and swimlanes for architecture tiers and zones.
- Keep child nodes relative to their container.
- Snap all geometry to the Draw.io 10px grid.
- Use orthogonal edges with explicit entry/exit points.
- Add waypoints when a connector needs a routing corridor.
- Run a deterministic XML lint before export.
- Export SVG/PNG only when the local Draw.io CLI wrapper is available.
- Treat the output artifact, not the Electron process exit code, as the final
  success signal on Windows.

## Renderer responsibilities

`src/bid_tool/illustration_v2/renderers/drawio.py` owns:

- semantic item to Draw.io layout planning;
- architecture layer layouts;
- deployment and topology zone layouts;
- interface relationship layouts;
- flowchart layouts;
- Draw.io XML writing;
- structural linting;
- optional SVG/PNG export.

The pipeline and public API still interact only with the unified drawing tool
abstraction. They do not need to know whether Draw.io, SVG, HTML/CSS, ECharts,
Mermaid, or Graphviz produced the asset.
