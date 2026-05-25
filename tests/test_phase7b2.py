"""Phase 7b-2 Rich borrowed primitives."""

from __future__ import annotations

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
        errors="replace",
        timeout=10,
        cwd=ROOT,
    )


def test_animate_spinner_dots_arg_parses() -> None:
    result = _run(
        [
            "animate",
            "line",
            "--duration",
            "0.01",
            "--frames",
            "1",
            "--spinner",
            "dots",
            "--json",
            '[{"label":"x","x":[1],"y":[10]}]',
        ]
    )

    assert result.returncode == 0


def test_spinner_invalid_name_returns_1() -> None:
    result = _run(
        [
            "animate",
            "line",
            "--duration",
            "0.01",
            "--frames",
            "1",
            "--spinner",
            "not-a-spinner",
            "--json",
            '[{"label":"x","x":[1],"y":[10]}]',
        ]
    )

    assert result.returncode == 1
    assert "spinner" in result.stderr.lower()


def test_gauge_rich_progress_flag_dispatches() -> None:
    result = _run(
        [
            "gauge",
            "--rich-progress",
            "--json",
            '[{"label":"CPU","value":72,"max":100},{"label":"RAM","value":14,"max":32}]',
        ]
    )

    assert result.returncode == 0
    assert "CPU" in result.stdout
    assert "RAM" in result.stdout


def test_code_engine_syntax_highlight_python() -> None:
    source = ROOT / "cli_charts" / "chart.py"

    result = _run(["code", "--file", str(source), "--lang", "python"])

    assert result.returncode == 0
    assert "main" in result.stdout
    assert "\x1b[" in result.stdout


def test_code_engine_unsupported_lang_returns_1() -> None:
    source = ROOT / "cli_charts" / "chart.py"

    result = _run(["code", "--file", str(source), "--lang", "notalang"])

    assert result.returncode == 1
    assert "unsupported" in result.stderr.lower()


def test_status_engine_ok_kind() -> None:
    result = _run(["status", "--kind", "ok", "--message", "All tests green"])

    assert result.returncode == 0
    assert "All tests green" in result.stdout


def test_status_engine_invalid_kind_returns_1() -> None:
    result = _run(["status", "--kind", "bad", "--message", "nope"])

    assert result.returncode == 1
    assert "kind" in result.stderr.lower()


def test_chart_help_includes_code_and_status() -> None:
    result = _run(["--help"])

    assert result.returncode == 0
    assert "code" in result.stdout
    assert "status" in result.stdout
