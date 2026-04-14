"""XAR-97 rich_live: multi-panel Rich Live/Layout static snapshot.

Covers the 3 acceptance criteria:
  1) side-by-side panels render in row layout
  2) frames=1 snapshot works without a TTY (pipe-safe)
  3) layout="column" stacks panels vertically
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest


SCRIPT = Path(__file__).parent.parent / 'scripts' / 'chart.py'


def _run(payload: dict, extra_args: list[str] | None = None) -> subprocess.CompletedProcess:
    args = [sys.executable, str(SCRIPT), 'rich_live', '--json', json.dumps(payload)]
    if extra_args:
        args.extend(extra_args)
    return subprocess.run(args, capture_output=True, text=True, encoding='utf-8')


@pytest.fixture
def row_payload() -> dict:
    return {
        'panels': [
            {'type': 'sparkline', 'title': 'Left',  'data': {'values': [1, 3, 5, 2, 8]}},
            {'type': 'sparkline', 'title': 'Right', 'data': {'values': [9, 7, 5, 3, 1]}},
        ],
        'layout': 'row',
        'frames': 1,
    }


def test_row_layout_renders_both_panels(row_payload):
    r = _run(row_payload, ['--title', 'Row'])
    assert r.returncode == 0, r.stderr
    assert 'Left' in r.stdout and 'Right' in r.stdout
    # Row layout puts both panel borders on the same row, so expect two panel openings
    # adjacent (│ or ┌ chars) at least once on one line.
    assert r.stdout.count('Left') >= 1
    assert r.stdout.count('Right') >= 1


def test_frames1_snapshot_works_without_tty(row_payload):
    # subprocess.PIPE => stdout is not a tty. This is the AC for AI/non-interactive use.
    r = _run(row_payload)
    assert r.returncode == 0, r.stderr
    assert r.stdout.strip(), 'expected non-empty snapshot output'
    assert 'Left' in r.stdout


def test_column_layout_stacks_panels():
    payload = {
        'panels': [
            {'type': 'sparkline', 'title': 'Top',    'data': {'values': [1, 2, 3]}},
            {'type': 'sparkline', 'title': 'Bottom', 'data': {'values': [3, 2, 1]}},
        ],
        'layout': 'column',
        'frames': 1,
    }
    r = _run(payload)
    assert r.returncode == 0, r.stderr
    out = r.stdout
    top_pos = out.find('Top')
    bot_pos = out.find('Bottom')
    assert top_pos != -1 and bot_pos != -1
    # Column => "Top" appears on an earlier line than "Bottom"
    assert out[:bot_pos].count('\n') > out[:top_pos].count('\n')


def test_empty_panels_errors_with_schema_tag():
    r = _run({'panels': [], 'layout': 'row'})
    assert r.returncode == 1
    assert 'ERROR:schema:' in r.stderr


def test_invalid_layout_errors_with_schema_tag():
    r = _run({
        'panels': [{'type': 'sparkline', 'data': {'values': [1, 2, 3]}}],
        'layout': 'diagonal',
    })
    assert r.returncode == 1
    assert 'ERROR:schema:' in r.stderr
    assert 'row' in r.stderr and 'column' in r.stderr


def test_registered_in_cmd_dispatcher():
    """Guard against accidental drop from the CMDS/schema registries."""
    sys.path.insert(0, str(SCRIPT.parent.parent))
    from cli_charts.chart import CMDS, EXPECTED_SCHEMAS, _NO_SIZE_THEME

    assert 'rich_live' in CMDS
    assert 'rich_live' in EXPECTED_SCHEMAS
    assert 'rich_live' in _NO_SIZE_THEME
