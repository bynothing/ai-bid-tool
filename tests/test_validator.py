"""Test validator module."""
import json
import tempfile
from pathlib import Path
import pytest


def _make_temp_dir_with_files(files):
    """Create a temporary directory with JSON files for testing."""
    tmpdir = Path(tempfile.mkdtemp())
    for fname, content in files.items():
        path = tmpdir / fname
        path.write_text(json.dumps(content, ensure_ascii=False), encoding='utf-8')
    return tmpdir


def test_check_schema_required_valid():
    """Required fields present should pass."""
    from bid_tool.pipeline.validator import check_schema_required
    schema = {'required': ['name', 'value']}
    data = {'name': 'test', 'value': 42}
    issues = check_schema_required(data, schema)
    assert issues == []


def test_check_schema_required_missing():
    """Missing required field should be reported."""
    from bid_tool.pipeline.validator import check_schema_required
    schema = {'required': ['name', 'value']}
    data = {'name': 'test'}
    issues = check_schema_required(data, schema)
    assert any('value' in i for i in issues)


def test_check_schema_required_null():
    """Null required field should be reported."""
    from bid_tool.pipeline.validator import check_schema_required
    schema = {'required': ['name']}
    data = {'name': None}
    issues = check_schema_required(data, schema)
    assert any('name' in i for i in issues)


def test_check_schema_required_empty_string():
    """Empty string in required field should be reported."""
    from bid_tool.pipeline.validator import check_schema_required
    schema = {'required': ['name']}
    data = {'name': ''}
    issues = check_schema_required(data, schema)
    assert any('name' in i for i in issues)


def test_check_schema_nested_array_items():
    """Nested array items with required fields should be validated."""
    from bid_tool.pipeline.validator import check_schema_required
    schema = {
        'properties': {
            'items': {
                'type': 'array',
                'items': {'required': ['id', 'text']}
            }
        }
    }
    data = {
        'items': [
            {'id': '1', 'text': 'hello'},
            {'id': '2'},  # Missing 'text'
        ]
    }
    issues = check_schema_required(data, schema)
    assert any('items[1].text' in i for i in issues)


def test_check_schema_non_dict_data():
    """Non-dict data should return an error."""
    from bid_tool.pipeline.validator import check_schema_required
    issues = check_schema_required([1, 2, 3], {'required': ['x']})
    assert len(issues) == 1
    assert '不是有效的 JSON 对象' in issues[0]


def test_load_json_with_front_matter():
    """load_json should handle YAML front matter."""
    from bid_tool.pipeline.validator import load_json
    import tempfile
    import os
    fd, fname = tempfile.mkstemp(suffix='.md', text=True)
    os.close(fd)
    try:
        Path(fname).write_text('---\n{"key": "value"}\n---\n# Markdown content', encoding='utf-8')
        result = load_json(fname)
        assert result == {'key': 'value'}
    finally:
        Path(fname).unlink(missing_ok=True)


def test_load_json_pure_json():
    """load_json should handle pure JSON files."""
    from bid_tool.pipeline.validator import load_json
    import tempfile
    import os
    fd, fname = tempfile.mkstemp(suffix='.json', text=True)
    os.close(fd)
    try:
        Path(fname).write_text('{"key": "value"}', encoding='utf-8')
        result = load_json(fname)
        assert result == {'key': 'value'}
    finally:
        Path(fname).unlink(missing_ok=True)


def test_coverage_gates_defined():
    """COVERAGE_GATES should have expected entries."""
    from bid_tool.pipeline.validator import COVERAGE_GATES
    assert 's1_to_s2' in COVERAGE_GATES
    assert 's7_final' in COVERAGE_GATES
    for gate_name, gate in COVERAGE_GATES.items():
        assert 'required_rate' in gate
        assert 'check' in gate
        assert 0 <= gate['required_rate'] <= 1.0


def test_validate_stage_unknown_stage():
    """validate_stage should return False for unknown stage."""
    from bid_tool.pipeline.validator import validate_stage
    result = validate_stage('unknown_stage', '/tmp')
    assert result is False
