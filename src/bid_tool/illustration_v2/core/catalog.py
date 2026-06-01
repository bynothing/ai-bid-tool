"""Capability catalog for the isolated v2 decision layer."""
from __future__ import annotations

from .models import CapabilityCatalog, RendererCapability, Template, TemplateContract, TextLimit


ICON_WHITELIST = (
    "server",
    "cloud",
    "shield",
    "user",
    "users",
    "monitor",
    "settings",
    "code",
    "database",
    "file",
    "chart",
    "calendar",
    "check",
    "dashboard",
    "link",
    "cpu",
    "activity",
    "target",
)


def build_capability_catalog() -> CapabilityCatalog:
    """Build the static v2 capability catalog.

    Phase 1 deliberately starts with one high-control SVG template.  Additional
    templates should be added here without touching the legacy illustration
    package.
    """

    arch_template = Template(
        id="arch.layered.v2",
        diagram_type="architecture.layered",
        variant_of="architecture.layered",
        renderer="template_svg",
        svg_template="templates/architecture/layered/arch.layered.v2/template.svg",
        summary="Frozen three-layer architecture SVG template for formal bid diagrams.",
        contract=TemplateContract(
            schema_kind="layered",
            paradigm=(
                "A three-layer architecture diagram. Layers are stacked vertically "
                "from user/application concerns down to platform/data/support "
                "concerns. Each layer contains one to four compact capability cards."
            ),
            min_layers=2,
            max_layers=3,
            min_items_per_layer=1,
            max_items_per_layer=4,
            text_limits=(
                TextLimit("title", 16),
                TextLimit("desc", 42),
                TextLimit("label", 18),
                TextLimit("subtitle", 36),
            ),
            icon_whitelist=ICON_WHITELIST,
        ),
        theme_vars={
            "primary": "#123f6d",
            "primary_alt": "#1f78a8",
            "line": "#c9d8e8",
            "wash": "#f4f8fc",
            "text": "#10253f",
            "muted": "#55708c",
        },
    )
    platform_interface = Template(
        id="platform.interface.v2",
        diagram_type="relationship.platform_interface",
        variant_of="relationship.platform_interface",
        renderer="template_svg",
        svg_template="",
        summary="Two-platform interface relationship template with center data exchange lanes.",
        contract=TemplateContract(
            schema_kind="platform_interface",
            paradigm=(
                "Two large platform containers are placed on the left and right. "
                "Data exchange flows run through the middle with protocol labels, "
                "and bottom requirement chips summarize security, audit, and interface rules."
            ),
            min_layers=2,
            max_layers=4,
            min_items_per_layer=1,
            max_items_per_layer=5,
            text_limits=(
                TextLimit("title", 40),
                TextLimit("subtitle", 42),
                TextLimit("label", 20),
                TextLimit("desc", 52),
            ),
            icon_whitelist=ICON_WHITELIST,
            required_data_fields=("left", "right", "flows"),
        ),
        theme_vars={
            "primary": "#0f4f8a",
            "primary_alt": "#2379b7",
            "line": "#c9d8e8",
            "wash": "#f6fbff",
            "text": "#10253f",
            "muted": "#55708c",
        },
    )
    resilience_flow = Template(
        id="process.resilience.v2",
        diagram_type="process.resilience_flow",
        variant_of="process.resilience_flow",
        renderer="template_svg",
        svg_template="",
        summary="Exception handling and retry/compensation flow template.",
        contract=TemplateContract(
            schema_kind="resilience_flow",
            paradigm=(
                "A normal reporting flow is shown at the top. Exception scenarios "
                "feed into a central handling and compensation mechanism, with right-side "
                "deduplication and audit closure panels."
            ),
            min_layers=0,
            max_layers=0,
            min_items_per_layer=0,
            max_items_per_layer=0,
            text_limits=(
                TextLimit("title", 26),
                TextLimit("subtitle", 54),
                TextLimit("label", 20),
                TextLimit("desc", 64),
            ),
            icon_whitelist=ICON_WHITELIST,
            required_data_fields=("steps", "exceptions", "mechanisms"),
        ),
        theme_vars={
            "primary": "#104f94",
            "primary_alt": "#2b7fc8",
            "line": "#cbd9ea",
            "wash": "#f6fbff",
            "text": "#10253f",
            "muted": "#55708c",
        },
    )
    inspection_cards = Template(
        id="inspection.cards.v2",
        diagram_type="taxonomy.inspection_cards",
        variant_of="taxonomy.inspection_cards",
        renderer="template_svg",
        svg_template="",
        summary="Three-column inspection classification card template.",
        contract=TemplateContract(
            schema_kind="inspection_cards",
            paradigm=(
                "Two to four vertical classification cards compare inspection types. "
                "Each card contains trigger mode, inspection content, check points, and output."
            ),
            min_layers=0,
            max_layers=0,
            min_items_per_layer=0,
            max_items_per_layer=0,
            text_limits=(
                TextLimit("title", 18),
                TextLimit("subtitle", 28),
                TextLimit("label", 18),
                TextLimit("desc", 58),
            ),
            icon_whitelist=ICON_WHITELIST,
            required_data_fields=("categories",),
        ),
        theme_vars={
            "primary": "#0f4f8a",
            "primary_alt": "#1f7ac6",
            "line": "#cbd9ea",
            "wash": "#f7fbff",
            "text": "#10253f",
            "muted": "#55708c",
        },
    )
    severity_closure = Template(
        id="severity.closure.v2",
        diagram_type="process.severity_closure",
        variant_of="process.severity_closure",
        renderer="template_svg",
        svg_template="",
        summary="Fault severity matrix plus issue closure process template.",
        contract=TemplateContract(
            schema_kind="severity_closure",
            paradigm=(
                "A severity response matrix occupies the top half. A linear issue "
                "closure workflow and key guarantees occupy the bottom half."
            ),
            min_layers=0,
            max_layers=0,
            min_items_per_layer=0,
            max_items_per_layer=0,
            text_limits=(
                TextLimit("title", 24),
                TextLimit("subtitle", 42),
                TextLimit("label", 18),
                TextLimit("desc", 70),
            ),
            icon_whitelist=ICON_WHITELIST,
            required_data_fields=("levels", "steps"),
        ),
        theme_vars={
            "primary": "#0b4c94",
            "primary_alt": "#2b72c4",
            "line": "#cbd9ea",
            "wash": "#f7fbff",
            "text": "#10253f",
            "muted": "#55708c",
        },
    )
    security_loop = Template(
        id="security.loop.v2",
        diagram_type="security.closed_loop",
        variant_of="security.closed_loop",
        renderer="template_svg",
        svg_template="",
        summary="Radial data security closed-loop guarantee template.",
        contract=TemplateContract(
            schema_kind="security_loop",
            paradigm=(
                "A central assurance core is surrounded by five coordinated controls. "
                "A bottom governance loop expresses continuous management and improvement."
            ),
            min_layers=0,
            max_layers=0,
            min_items_per_layer=0,
            max_items_per_layer=0,
            text_limits=(
                TextLimit("title", 20),
                TextLimit("subtitle", 38),
                TextLimit("label", 18),
                TextLimit("desc", 56),
            ),
            icon_whitelist=ICON_WHITELIST,
            required_data_fields=("center", "controls"),
        ),
        theme_vars={
            "primary": "#0758bd",
            "primary_alt": "#0097a7",
            "line": "#cbd9ea",
            "wash": "#f7fbff",
            "text": "#10253f",
            "muted": "#55708c",
        },
    )

    return CapabilityCatalog(
        templates=[
            arch_template,
            platform_interface,
            resilience_flow,
            inspection_cards,
            severity_closure,
            security_loop,
        ],
        renderers=[
            RendererCapability(
                id="template_svg",
                tier=1,
                strengths=("frozen geometry", "contract validation", "stable formal bid output"),
                weaknesses=("only registered templates", "strict capacity limits"),
            ),
            RendererCapability(
                id="structured_svg_fallback",
                tier=2,
                strengths=("always local", "safe simple layout", "works without browser tools"),
                weaknesses=("less polished than frozen templates", "limited automatic layout"),
            ),
            RendererCapability(
                id="free_svg_floor",
                tier=3,
                strengths=("prevents blank output", "records human review requirement"),
                weaknesses=("lowest visual control", "manual review required"),
            ),
        ],
    )
