"""Isolated illustration v2 package.

This package is intentionally separate from ``bid_tool.illustration``.  It is a
fresh implementation of the template-first illustration architecture described
in ``src/bid_tool/devlop-plan/illustration_refactor_plan.md``.
"""

from .api import list_capabilities, load_job, plan, render, validate

__all__ = ["list_capabilities", "load_job", "plan", "render", "validate"]

