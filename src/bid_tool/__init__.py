"""bid-tool — Automated bid document generation toolkit.

Combines a 9-stage bid writing pipeline with an integrated illustration
generation system (SVG architecture diagrams + ECharts data charts).

Stages:
    S1  Parse tender document  →  S2  Design outline  →  S3  Write body
    S4  Freeze content         →  S5  Generate illustrations
    S6  Synthesize             →  S7  Verify & trace    →  S8  Export DOCX
    S9  Fill deviation table

Usage:
    bid-tool init --project "Project Name" --type construction
    bid-tool run
    bid-tool illustrate --job examples/demo.json
"""

__version__ = "1.0.0"
