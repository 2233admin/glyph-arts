"""Tests for --animate streaming mode (unit-level, no real TTY required)."""
import collections
import subprocess
import sys

import pytest


# ---------------------------------------------------------------------------
# Unit tests — pure logic, no subprocess, no TTY
# ---------------------------------------------------------------------------

def _parse_line(raw: str):
    """Replicate the line-parsing logic from _animate_stdin."""
    raw = raw.strip()
    if not raw:
        return None
    try:
        return float(raw.split()[-1])
    except ValueError:
        return None


def test_parse_line_single_value():
    assert _parse_line("42.5") == 42.5


def test_parse_line_xy_pair():
    assert _parse_line("10 99.1") == 99.1


def test_parse_line_empty():
    assert _parse_line("") is None


def test_parse_line_whitespace_only():
    assert _parse_line("   ") is None


def test_parse_line_non_numeric():
    assert _parse_line("hello") is None


def test_parse_line_label_then_value():
    assert _parse_line("timestamp 1234.5") == 1234.5


def test_window_deque_maxlen():
    buf = collections.deque(maxlen=5)
    for i in range(10):
        buf.append(float(i))
    assert list(buf) == [5.0, 6.0, 7.0, 8.0, 9.0]
    assert len(buf) == 5


def test_window_unlimited():
    buf = collections.deque(maxlen=None)
    for i in range(100):
        buf.append(float(i))
    assert len(buf) == 100
    assert buf[-1] == 99.0


def test_window_zero_means_unlimited():
    window = 0
    buf = collections.deque(maxlen=window if window > 0 else None)
    for i in range(200):
        buf.append(float(i))
    assert len(buf) == 200


def test_animate_types_set():
    # Verify _ANIMATE_TYPES is importable and contains the expected members
    from cli_charts.chart import _ANIMATE_TYPES
    assert 'line' in _ANIMATE_TYPES
    assert 'scatter' in _ANIMATE_TYPES
    assert 'sparkline' in _ANIMATE_TYPES


# ---------------------------------------------------------------------------
# Slow / integration tests — require subprocess + may need a pseudoTTY
# Skip in CI with: pytest -m "not slow"
# ---------------------------------------------------------------------------

@pytest.mark.slow
def test_animate_line_no_crash_eof():
    """Feed 20 values via stdin with --animate line; process must exit 0."""
    data = "\n".join(str(i * 1.5) for i in range(20))
    result = subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", "line", "--animate",
         "--window", "10", "--refresh", "20"],
        input=data,
        capture_output=True,
        text=True,
        timeout=15,
        cwd=str(__file__).split("tests")[0],
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"


@pytest.mark.slow
def test_animate_scatter_no_crash_eof():
    data = "\n".join(str(float(i)) for i in range(15))
    result = subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", "scatter", "--animate",
         "--window", "8"],
        input=data,
        capture_output=True,
        text=True,
        timeout=15,
        cwd=str(__file__).split("tests")[0],
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"


@pytest.mark.slow
def test_animate_sparkline_no_crash():
    data = "\n".join(str(i % 10) for i in range(30))
    result = subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", "sparkline", "--animate"],
        input=data,
        capture_output=True,
        text=True,
        timeout=15,
        cwd=str(__file__).split("tests")[0],
    )
    assert result.returncode == 0, f"stderr: {result.stderr}"


@pytest.mark.slow
def test_animate_unsupported_type_exits_1():
    """bar chart with --animate must reject with exit code 1."""
    result = subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", "bar", "--animate"],
        input="1\n2\n3\n",
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(__file__).split("tests")[0],
    )
    assert result.returncode == 1
    assert "ERROR:schema:" in result.stderr


@pytest.mark.slow
def test_animate_duration_stops():
    """With --duration 1, the process must exit within 5 seconds."""
    import time
    data = "\n".join(str(float(i)) for i in range(1000))
    t0 = time.monotonic()
    result = subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", "line", "--animate",
         "--duration", "1", "--refresh", "10"],
        input=data,
        capture_output=True,
        text=True,
        timeout=10,
        cwd=str(__file__).split("tests")[0],
    )
    elapsed = time.monotonic() - t0
    assert result.returncode == 0, f"stderr: {result.stderr}"
    assert elapsed < 5.0, f"Duration flag did not stop in time: {elapsed:.1f}s"
