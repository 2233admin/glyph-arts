import subprocess
import sys


def run_cli(*args):
    return subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", *args],
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=10,
    )


def test_bar_style_braille_emits_braille():
    result = run_cli("bar", "--json", '{"labels":["A"],"values":[3]}', "--style", "braille", "--no-color", "--no-splash")
    assert result.returncode == 0, result.stderr
    assert "⣿" in result.stdout


def test_bar_style_shade_emits_shade_or_block():
    result = run_cli("bar", "--json", '{"labels":["A"],"values":[3]}', "--style", "shade", "--no-color", "--no-splash")
    assert result.returncode == 0, result.stderr
    assert "█" in result.stdout or "░" in result.stdout


def test_gauge_half_circle_alias_still_works():
    result = run_cli("gauge", "--json", '[{"label":"CPU","value":50,"max":100}]', "--style", "half-circle", "--no-color", "--no-splash")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip()


def test_bar_symbols_override_style():
    result = run_cli("bar", "--json", '{"labels":["A"],"values":[3]}', "--style", "braille", "--symbols", "arrows", "--no-color", "--no-splash")
    assert result.returncode == 0, result.stderr
    assert "^" in result.stdout or "↑" in result.stdout
    assert "⣿" not in result.stdout
