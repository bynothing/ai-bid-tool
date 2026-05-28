"""Test trace module."""
import tempfile
import json
from pathlib import Path
import pytest


@pytest.fixture
def temp_trace_dir():
    """Create a temporary directory with a trace.json."""
    tmpdir = Path(tempfile.mkdtemp())
    trace_path = tmpdir / 'output' / 'trace.json'
    trace_path.parent.mkdir(parents=True, exist_ok=True)
    return trace_path


def test_trace_template():
    """TEMPLATE should have expected structure."""
    from bid_tool.pipeline.trace import TEMPLATE
    assert 'project' in TEMPLATE
    assert 'requirements' in TEMPLATE
    assert 'body_segments' in TEMPLATE
    assert 'illustrations' in TEMPLATE
    assert 'coverage' in TEMPLATE


def test_trace_init_and_load(temp_trace_dir):
    """init should create trace.json, load should read it."""
    from bid_tool.pipeline.trace import load, save, TEMPLATE

    trace = dict(TEMPLATE)
    trace['project'] = 'Test Project'
    save(trace, trace_path=temp_trace_dir)
    assert temp_trace_dir.exists()

    loaded = load(trace_path=temp_trace_dir)
    assert loaded is not None
    assert loaded['project'] == 'Test Project'
    assert 'requirements' in loaded


def test_trace_recalc_coverage():
    """_recalc_coverage should update coverage stats."""
    from bid_tool.pipeline.trace import _recalc_coverage

    trace = {
        'requirements': [
            {'req_id': 'RQ-001', 'status': 'covered'},
            {'req_id': 'RQ-002', 'status': 'uncovered'},
            {'req_id': 'RQ-003', 'status': 'covered'},
        ]
    }
    _recalc_coverage(trace)
    assert trace['coverage']['total_reqs'] == 3
    assert trace['coverage']['covered_reqs'] == 2
    assert trace['coverage']['coverage_rate'] == pytest.approx(2 / 3)
    assert 'RQ-002' in trace['coverage']['uncovered_reqs']


def test_trace_load_nonexistent():
    """load should return None for nonexistent trace file."""
    from bid_tool.pipeline.trace import load
    result = load(trace_path=Path('/nonexistent/path/trace.json'))
    assert result is None


def test_trace_default_path():
    """Default trace path should be in cwd/output/."""
    from bid_tool.pipeline.trace import _default_trace_path
    path = _default_trace_path()
    assert path.name == 'trace.json'
    assert 'output' in str(path)
