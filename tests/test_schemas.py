"""Test all JSON Schemas are valid and loadable."""
import json
import pytest
from pathlib import Path

SCHEMA_DIR = Path(__file__).resolve().parent.parent / 'src' / 'bid_tool' / 'schemas'

# All expected schema files
EXPECTED_SCHEMAS = [
    's1_key_info.schema.json',
    's1_veto_items.schema.json',
    's1_scoring.schema.json',
    's1_risk.schema.json',
    's1_tech_req.schema.json',
    's2_outline.schema.json',
    's3_body.schema.json',
    's5_illustration.schema.json',
    's7_trace_matrix.schema.json',
    'proposal_illustration_job.schema.json',
    'svg_diagram.schema.json',
    'echarts_diagram.schema.json',
]


def _load_schema(name):
    path = SCHEMA_DIR / name
    assert path.exists(), f"Schema file missing: {name}"
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


@pytest.mark.parametrize('schema_name', EXPECTED_SCHEMAS)
def test_schema_is_valid_json(schema_name):
    """Every schema file should be valid JSON."""
    schema = _load_schema(schema_name)
    assert isinstance(schema, dict), f"{schema_name} is not a JSON object"
    assert '$schema' in schema or 'type' in schema, f"{schema_name} missing $schema or type"


@pytest.mark.parametrize('schema_name', EXPECTED_SCHEMAS)
def test_schema_is_valid_jsonschema(schema_name):
    """Every schema should be usable by jsonschema.Draft202012Validator."""
    jsonschema = pytest.importorskip('jsonschema')
    schema = _load_schema(schema_name)
    try:
        jsonschema.Draft202012Validator(schema)
    except Exception as e:
        pytest.fail(f"{schema_name}: {e}")


def test_all_schemas_present():
    """Check no schema files are missing."""
    actual = sorted(p.name for p in SCHEMA_DIR.glob('*.schema.json'))
    expected = sorted(EXPECTED_SCHEMAS)
    assert actual == expected, f"Schema mismatch: {set(expected) ^ set(actual)}"


def test_schemas_from_package():
    """Schemas should be importable from the package."""
    from bid_tool.pipeline.validator import STAGE_SCHEMAS
    from bid_tool.illustration.toolkit import SCHEMA_DIR as ILLU_SCHEMA_DIR
    assert 's1' in STAGE_SCHEMAS
    assert 's7' in STAGE_SCHEMAS
    assert ILLU_SCHEMA_DIR.exists()


def test_pipeline_stage_schemas_match_files():
    """Validator STAGE_SCHEMAS should reference existing files."""
    from bid_tool.pipeline.validator import STAGE_SCHEMAS
    for stage, schemas in STAGE_SCHEMAS.items():
        for sf in schemas:
            path = SCHEMA_DIR / sf
            assert path.exists(), f"Schema referenced by validator but missing: {sf}"


def test_illustration_schemas_match_files():
    """Illustration toolkit schemas should reference existing files."""
    from bid_tool.illustration.toolkit import SCHEMA_DIR as ILLU_SCHEMA_DIR
    for name in ['proposal_illustration_job.schema.json',
                 'svg_diagram.schema.json',
                 'echarts_diagram.schema.json']:
        assert (ILLU_SCHEMA_DIR / name).exists(), f"Missing illustration schema: {name}"
