from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def test_effect_gallery_renders_multiple_presets() -> None:
    result = _run(["effect", "--width", "72"])
    assert result.returncode == 0, result.stderr
    assert "Effect Gallery" in result.stdout
    assert "Pipeline Effect" in result.stdout
    assert "Signal Panel" in result.stdout
    assert "Density Matrix" in result.stdout
    assert "Swimlane" in result.stdout
    assert "Kanban" in result.stdout


def test_chat_effects_alias_is_visible() -> None:
    result = _run(["chat", "effects", "--width", "72"])
    assert result.returncode == 0, result.stderr
    assert "Effect Gallery" in result.stdout
    assert "\x1b[" not in result.stdout


def test_effect_pipeline_uses_supplied_steps() -> None:
    payload = json.dumps({"steps": ["Input", "Route", "Render", "Verify", "Reply"]})
    result = _run(["effect", "pipeline", "--json", payload, "--width", "64"])
    assert result.returncode == 0, result.stderr
    for label in ("Input", "Route", "Render", "Verify", "Reply"):
        assert label in result.stdout
    assert "▼" in result.stdout


def test_effect_signal_panel_has_spectrum_and_waterfall() -> None:
    result = _run(["effect", "signal-panel", "--width", "80"])
    assert result.returncode == 0, result.stderr
    assert "spectrum" in result.stdout
    assert "waterfall" in result.stdout
    assert any(ch in result.stdout for ch in "░▒▓█")
    assert "range" in result.stdout


def test_effect_system_status_uses_halftone_status_bars() -> None:
    result = _run(["effect", "system-status", "--width", "80"])
    assert result.returncode == 0, result.stderr
    assert "System Status" in result.stdout
    assert "⠶⠶⠶⠶⣤⣤⣤⣶⣶⣿⣿⣿⣿⣿⣿" in result.stdout
    assert "╔" in result.stdout
    assert "║" in result.stdout


def test_effect_matrix_uses_unicode_shade_ramp() -> None:
    result = _run(["effect", "matrix", "--width", "80"])
    assert result.returncode == 0, result.stderr
    assert "legend" in result.stdout
    assert "░▒▓█" in result.stdout


def test_effect_additional_presets_render() -> None:
    for preset, marker in [
        ("swimlane", "User"),
        ("kanban", "TODO"),
        ("quadrant", "impact"),
        ("mindmap", "Chat Drawing"),
    ]:
        result = _run(["effect", preset, "--width", "80"])
        assert result.returncode == 0, result.stderr
        assert marker in result.stdout
