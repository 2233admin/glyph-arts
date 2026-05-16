from __future__ import annotations

import builtins
import subprocess
import sys

from cli_charts.render.interactive_engine import INTERACTIVE_SUPPORTED, render_interactive

LINE_DATA = [{"label": "DAU", "x": [1, 2, 3], "y": [100, 115, 108]}]


def run_chart(*args: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
    )


def test_render_interactive_signature() -> None:
    assert INTERACTIVE_SUPPORTED == frozenset({"line"})
    assert callable(render_interactive)


def test_unsupported_type_returns_1(capsys) -> None:
    rc = render_interactive("bar", {"labels": ["A"], "values": [1]}, 80, 20)

    captured = capsys.readouterr()
    assert rc == 1
    assert "only supports line" in captured.err


def test_invalid_data_returns_1() -> None:
    result = run_chart("line", "--engine", "interactive", "--json", "{}")

    assert result.returncode == 1
    assert "ERROR:schema:" in result.stderr


def test_textual_dep_missing_returns_2(monkeypatch, capsys) -> None:
    real_import = builtins.__import__

    def fake_import(name, *args, **kwargs):
        if name == "textual.app" or name.startswith("textual."):
            raise ImportError("textual blocked")
        return real_import(name, *args, **kwargs)

    monkeypatch.setattr(builtins, "__import__", fake_import)

    rc = render_interactive("line", LINE_DATA, 80, 20)

    captured = capsys.readouterr()
    assert rc == 2
    assert "ERROR:dep:" in captured.err


def test_engine_choices_includes_interactive() -> None:
    result = run_chart("--help")

    assert result.returncode == 0
    assert "{ascii,pixel,interactive}" in result.stdout


def test_subprocess_help_no_crash() -> None:
    result = run_chart("line", "--engine", "interactive", "--help")

    assert result.returncode == 0
