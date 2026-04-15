"""#6 Regression: ZeroDivisionError on balanced 2x2 confusion matrix.

plotext color-scale bug: when all matrix cells are equal (M==m),
`(M - m)` is zero and the internal `to_255` lambda crashes.
Guard added in chart.py must absorb this and render cleanly (exit 0).
"""
import json
import subprocess
import sys
from pathlib import Path

import pytest

SCRIPT = Path(__file__).parent.parent / 'scripts' / 'chart.py'


def _run(payload: dict) -> subprocess.CompletedProcess:
    return subprocess.run(
        [sys.executable, str(SCRIPT), 'confusion', '--json', json.dumps(payload)],
        capture_output=True, text=True, encoding='utf-8',
    )


# --- normal cases (must keep working) ---

def test_normal_2x2_renders():
    """Clear winner: one class always correct, other always wrong."""
    r = _run({'actual': [0, 0, 1, 1], 'predicted': [0, 0, 0, 0]})
    assert r.returncode == 0, r.stderr


def test_perfect_classifier_renders():
    r = _run({'actual': [0, 1, 0, 1], 'predicted': [0, 1, 0, 1]})
    assert r.returncode == 0, r.stderr


# --- regression: balanced / uniform matrix must not crash ---

def test_balanced_2x2_no_crash():
    """Regression #6: actual=[0,0,1,1] predicted=[0,1,0,1] -> uniform 2x2 matrix."""
    r = _run({'actual': [0, 0, 1, 1], 'predicted': [0, 1, 0, 1]})
    assert r.returncode == 0, f'expected exit 0, got {r.returncode}. stderr: {r.stderr}'
    assert r.stdout.strip(), 'expected non-empty output'


def test_uniform_single_class_no_crash():
    """All samples from one class -> 1x1 uniform matrix."""
    r = _run({'actual': [0, 0, 0, 0], 'predicted': [0, 0, 0, 0]})
    assert r.returncode == 0, f'expected exit 0, got {r.returncode}. stderr: {r.stderr}'
    assert r.stdout.strip(), 'expected non-empty output'


def test_balanced_with_labels():
    """Balanced matrix with explicit labels."""
    r = _run({
        'actual':     ['cat', 'cat', 'dog', 'dog'],
        'predicted':  ['cat', 'dog', 'cat', 'dog'],
        'labels':     ['cat', 'dog'],
    })
    assert r.returncode == 0, f'expected exit 0. stderr: {r.stderr}'
    assert r.stdout.strip()
