#!/usr/bin/env python3
"""Standalone launcher for the bid illustration platform."""
from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent
SRC = ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from bid_tool.illustration.toolkit import main

if __name__ == "__main__":
    main()
