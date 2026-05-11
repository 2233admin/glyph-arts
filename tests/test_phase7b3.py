"""Phase 7b3 chart marker integration."""

from __future__ import annotations

import contextlib
import io
import subprocess
import sys
from pathlib import Path

import pytest

from cli_charts import chart
from cli_charts.symbols import BLOCK, get_symbol

ROOT = Path(__file__).resolve().parents[1]
SCATTER_DATA = '[{"x":[1,2,3],"y":[10,20,15]}]'
BAR_DATA = '{"labels":["A","B"],"values":[10,20]}'
GAUGE_DATA = '[{"label":"CPU","value":73,"max":100}]'
CANDLE_DATA = (
    '{"dates":["2026-05-01","2026-05-02"],'
    '"open":[10,20],"high":[24,25],"low":[8,15],"close":[22,16]}'
)


def _run(args: list[str]) -> tuple[int, str, str]:
    out = io.StringIO()
    err = io.StringIO()
    code = 0
    old_argv = sys.argv
    sys.argv = ["glyph-arts", *args]
    with contextlib.redirect_stdout(out), contextlib.redirect_stderr(err):
        try:
            chart.main()
        except SystemExit as exc:
            code = int(exc.code or 0)
        finally:
            sys.argv = old_argv
    return code, out.getvalue(), err.getvalue()


def test_scatter_marker_triangle_renders_symbol_from_symbol_sets() -> None:
    code, out, err = _run(
        ["scatter", "--marker", "triangle", "--no-color", "--width", "40", "--height", "12", "--json", SCATTER_DATA]
    )

    assert code == 0, err
    assert get_symbol("triangle_up") in out


def test_scatter_marker_circle_renders_circle_symbol() -> None:
    code, out, err = _run(
        ["scatter", "--marker", "circle", "--no-color", "--width", "40", "--height", "12", "--json", SCATTER_DATA]
    )

    assert code == 0, err
    assert get_symbol("circle") in out


def test_bar_symbols_progress_renders_progress_symbols() -> None:
    code, out, err = _run(["bar", "--symbols", "progress", "--no-color", "--width", "40", "--height", "12", "--json", BAR_DATA])

    assert code == 0, err
    assert BLOCK["progress_full"] in out


def test_bar_symbols_arrows_renders_arrow_symbols() -> None:
    code, out, err = _run(["bar", "--symbols", "arrows", "--no-color", "--width", "40", "--height", "12", "--json", BAR_DATA])

    assert code == 0, err
    assert get_symbol("arrow_up") in out


def test_gauge_style_half_circle_renders_half_circle_style() -> None:
    code, out, err = _run(["gauge", "--gauge-style", "half-circle", "--no-color", "--json", GAUGE_DATA])

    assert code == 0, err
    assert get_symbol("half_circle_left") in out
    assert get_symbol("half_circle_right") in out


def test_gauge_style_full_circle_renders_full_circle_style() -> None:
    code, out, err = _run(["gauge", "--gauge-style", "full-circle", "--no-color", "--json", GAUGE_DATA])

    assert code == 0, err
    assert get_symbol("circle") in out


def test_ascii_tier_fallback_for_marker_symbols_candle_and_gauge(monkeypatch: pytest.MonkeyPatch) -> None:
    monkeypatch.setattr(chart, "detect_font_tier", lambda: "ascii")

    cases = [
        (["scatter", "--marker", "triangle", "--no-color", "--width", "40", "--height", "12", "--json", SCATTER_DATA], get_symbol("triangle_up", "ascii")),
        (["bar", "--symbols", "arrows", "--no-color", "--width", "40", "--height", "12", "--json", BAR_DATA], get_symbol("arrow_up", "ascii")),
        (["kline", "--candle-style", "geom", "--no-color", "--width", "40", "--height", "12", "--json", CANDLE_DATA], get_symbol("triangle_up", "ascii")),
        (["gauge", "--gauge-style", "half-circle", "--no-color", "--json", GAUGE_DATA], get_symbol("half_circle_left", "ascii")),
    ]
    for args, expected in cases:
        code, out, err = _run(args)
        assert code == 0, err
        assert expected in out


def test_default_no_flag_scatter_output_matches_p7b2_baseline() -> None:
    base_args = ["scatter", "--no-color", "--width", "40", "--height", "12", "--json", SCATTER_DATA]
    code, out, err = _run(base_args)

    assert code == 0, err
    assert out == (
        "    ┌──────────────────────────────────┐\n"
        "20.0┤                 •                │\n"
        "18.3┤                                  │\n"
        "    │                                  │\n"
        "16.7┤                                  │\n"
        "15.0┤                                 •│\n"
        "13.3┤                                  │\n"
        "    │                                  │\n"
        "11.7┤                                  │\n"
        "10.0┤•                                 │\n"
        "    └┬───────┬────────┬───────┬───────┬┘\n"
        "   1.00    1.50     2.00    2.50   3.00 \n\n"
    )


def test_invalid_symbol_set_key_returns_argparse_error() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli_charts.chart",
            "scatter",
            "--marker",
            "not-a-set",
            "--json",
            SCATTER_DATA,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
        cwd=ROOT,
    )

    assert result.returncode == 2
    assert "invalid choice" in result.stderr


def test_scatter_marker_triangle_json_output_matches_expected_snapshot() -> None:
    code, out, err = _run(
        ["scatter", "--marker", "triangle", "--no-color", "--width", "40", "--height", "12", "--json", SCATTER_DATA]
    )

    assert code == 0, err
    assert out == (
        "    ┌──────────────────────────────────┐\n"
        f"20.0┤                 {get_symbol('triangle_up')}                │\n"
        "18.3┤                                  │\n"
        "    │                                  │\n"
        "16.7┤                                  │\n"
        f"15.0┤                                 {get_symbol('triangle_up')}│\n"
        "13.3┤                                  │\n"
        "    │                                  │\n"
        "11.7┤                                  │\n"
        f"10.0┤{get_symbol('triangle_up')}                                 │\n"
        "    └┬───────┬────────┬───────┬───────┬┘\n"
        "   1.00    1.50     2.00    2.50   3.00 \n\n"
    )
