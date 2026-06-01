# Legacy Example Style Summary

Source:
`materials/references/legacy_illustration/example`

## Shared Visual Language

- White canvas with a deep blue headline and restrained subtitle.
- Thin blue/green/orange/purple strokes, light pastel fills, and compact rounded panels.
- Numbered circles or icon badges identify flow order, category order, and control points.
- Bid-document density is high, but geometry remains strictly aligned to grids.
- Bottom strips capture guarantees, evidence, auditability, or closed-loop principles.

## Template Families Extracted

| Reference | Template id | Diagram type | Pattern |
| --- | --- | --- | --- |
| 图片3.png | `platform.interface.v2` | `relationship.platform_interface` | Left/right platform containers with center data exchange lanes. |
| 图片4.png | `process.resilience.v2` | `process.resilience_flow` | Normal flow, exception scenarios, retry/compensation, audit closure. |
| 图片5.png | `inspection.cards.v2` | `taxonomy.inspection_cards` | Multi-column classification cards with trigger/content/check/output. |
| 图片6.png | `severity.closure.v2` | `process.severity_closure` | Severity response matrix plus issue closure process. |
| 图片7.png | `security.loop.v2` | `security.closed_loop` | Central assurance core with five surrounding controls and management loop. |

## Implementation Rule

The files above are visual references only. `illustration_v2` keeps its own
models, validators, renderers, templates, examples, and manifests. Runtime jobs
inject structured content into deterministic SVG geometry; they do not import
legacy implementation code.
