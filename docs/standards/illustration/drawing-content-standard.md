# Drawing Content Standard

This document defines the content and visual rules for `illustration_v2`
drawings, especially Draw.io diagrams generated from structured jobs.

## Goals

- Diagrams must explain system structure, not decorate text.
- Colors must support hierarchy and status; they must not become a rainbow.
- Arrows must show a small number of important relations.
- Text must be short, non-redundant, and readable after export to PNG.
- Generated `.drawio` files must stay editable.

## Content Rules

### Node Text

- Node title: 2 to 10 Chinese characters, or one compact English noun phrase.
- Node subtitle: optional. Use only for role, protocol, or key constraint.
- Do not repeat the parent container name inside child node subtitles.
- Do not put full sentences in nodes.
- Use nouns for nodes: `API 网关`, `数据湖仓`, `监控中心`.

### Edge Labels

- Edge labels are optional. Use them only when they add information.
- Keep labels at 2 to 6 Chinese characters where possible.
- Prefer protocol, data type, or business meaning: `HTTPS`, `事件`, `审计日志`.
- Avoid generic verbs that repeat across the graph: `请求`, `调用`, `读取`, `写入`,
  `同步`, `通知`, `反馈`, `流转`.
- If a graph has many edges, label only important edges.
- Do not put the same label on several adjacent edges unless it is a formal
  protocol name.

### Diagram Complexity

- One diagram should normally contain no more than 18 nodes and 22 edges.
- If a diagram exceeds 24 nodes or 30 edges, split it into a main overview and
  one or more detail diagrams.
- For layered architecture, keep cross-layer arrows mostly vertical or adjacent.
- For topology diagrams, prefer zone-to-zone flows over every device-to-device
  connection.
- For flowcharts, keep one main path and at most two feedback loops.

## Visual Rules

### Palette

- Use one dominant engineering blue system.
- Use low-saturation fills and restrained strokes.
- Reserve warm colors for gateways, risk, exceptions, or decisions.
- Reserve green for start/end, healthy status, or completion.
- Avoid saturated purple, red, orange, and green appearing in equal weight.

### Containers

- Containers express ownership, network zones, layers, or process lanes.
- Container headers must be quiet and readable.
- Child nodes must remain visually lighter than the container header.

### Arrows

- Use orthogonal connectors.
- Use one arrow style for normal flow.
- Use dashed lines only for async, backup, optional, or reference relations.
- Route long cross-zone arrows through a corridor when possible.
- Avoid labels at dense crossing points.

### Typography

- Titles use strong weight, but diagram body text must stay compact.
- Keep node subtitles visually secondary.
- Do not repeat the diagram title in section captions inside the graph.

## Renderer Enforcement

The Draw.io renderer should enforce these minimum rules:

- Normalize node titles and subtitles before rendering.
- Remove subtitles that duplicate the parent container title.
- Normalize edge labels by trimming generic repeated labels and limiting length.
- Use container-aware absolute coordinates when calculating connector direction.
- Use the restrained engineering-blue palette by default.
- Add warnings only for structural issues; visual normalization should be quiet.
