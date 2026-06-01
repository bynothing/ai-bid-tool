# Material Library

This directory is the entry point for source material used to design and refine
illustration v2 templates.

## Directory Contract

- `incoming/`: raw target documents, screenshots, hand-drawn references, or user-provided files.
- `references/`: curated reference images and visual examples that are allowed to influence template design.
- `normalized/`: cleaned and renamed source material, ready for analysis.
- `analysis/`: extracted design observations, layout summaries, and template candidates.

Rules:

- Keep raw files immutable once placed in `incoming/`.
- Put all interpretation in `analysis/`; do not overwrite source material.
- A template can only move into `templates/` after it has a written analysis summary and a contract.

