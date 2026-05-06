"""Phase 4 tests for cursor-home terminal animation."""

import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
        cwd=ROOT,
    )


def test_animate_signature() -> None:
    from cli_charts.render.animate_engine import ANIMATE_SUPPORTED, render_animate

    assert ANIMATE_SUPPORTED == {"line", "bar", "scatter", "sparkline"}
    assert callable(render_animate)
    params = list(inspect.signature(render_animate).parameters)
    assert params[:4] == ["chart_type", "data", "duration", "frames"]


def test_animate_unsupported_type_returns_1() -> None:
    from cli_charts.render.animate_engine import render_animate

    assert render_animate("kline", [], 1, 1) == 1


def test_animate_invalid_duration_returns_1() -> None:
    from cli_charts.render.animate_engine import render_animate

    assert render_animate("line", [], 0, 1) == 1


def test_animate_help_no_crash() -> None:
    result = _run(["animate", "--help"])

    assert result.returncode == 0
    assert "animate" in result.stdout


def test_animate_in_engine_choices() -> None:
    from cli_charts.chart import CMDS

    result = _run(["--help"])

    assert "animate" in CMDS
    assert result.returncode == 0
    assert "animate" in result.stdout


def test_interpolate_data_progressive() -> None:
    from cli_charts.render.animate_engine import _interpolate_data

    data = [
        {
            "label": "DAU",
            "x": list(range(1, 11)),
            "y": list(range(101, 111)),
        }
    ]

    frames = _interpolate_data(data, 30)

    assert len(frames) == 30
    assert frames[0][0]["x"] == [1]
    assert frames[0][0]["y"] == [101]
    assert frames[14][0]["x"] == [1, 2, 3, 4, 5]
    assert frames[14][0]["y"] == [101, 102, 103, 104, 105]
    assert frames[29][0]["x"] == list(range(1, 11))
    assert frames[29][0]["y"] == list(range(101, 111))
