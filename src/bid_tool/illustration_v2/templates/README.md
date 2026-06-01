# Template Library

The template library stores frozen SVG geometry and its self-describing
contract. Runtime rendering may inject text, theme variables, and visibility
flags, but must not alter geometry.

## Layout

```text
templates/
  <domain>/
    <diagram-family>/
      <template-id>/
        README.md
        analysis.md
        contract.json
        template.svg
        snapshots/
```

## Required Files

- `analysis.md`: why this template exists, what visual pattern it freezes, and when it should be selected.
- `contract.json`: machine-readable content limits for LLM generation and deterministic validation.
- `template.svg`: frozen geometry with explicit `{{SLOT}}` placeholders when the template is fully static.
- Renderer-backed templates may keep frozen geometry in `renderers/template_svg.py` while the contract stabilizes; the template directory still owns the public contract and regression snapshots.
- `snapshots/`: golden visual outputs for regression checks.

## Registered V2 Templates

| Template id | Diagram type | Reference |
| --- | --- | --- |
| `arch.layered.v2` | `architecture.layered` | Initial architecture pilot |
| `platform.interface.v2` | `relationship.platform_interface` | legacy `图片3.png` |
| `process.resilience.v2` | `process.resilience_flow` | legacy `图片4.png` |
| `inspection.cards.v2` | `taxonomy.inspection_cards` | legacy `图片5.png` |
| `severity.closure.v2` | `process.severity_closure` | legacy `图片6.png` |
| `security.loop.v2` | `security.closed_loop` | legacy `图片7.png` |
