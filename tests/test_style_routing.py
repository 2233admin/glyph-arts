"""Tests for Phase 1: style routing infrastructure."""
import os
import subprocess
import sys

import pytest

from cli_charts.registry import (
    STYLES, STYLE_ROUTES, STYLE_ENGINES, DEFAULT_STYLE,
    styles_for, resolve_engine,
)


def _run(args, env=None):
    full_env = {**os.environ, **(env or {}), "NO_COLOR": "1"}
    result = subprocess.run(
        [sys.executable, "-m", "cli_charts"] + args,
        capture_output=True, text=True, env=full_env,
    )
    return result.returncode, result.stdout, result.stderr


class TestRegistry:
    def test_styles_tuple_has_expected_entries(self):
        assert "fast" in STYLES
        assert "smooth" in STYLES
        assert "science" in STYLES
        assert len(STYLES) == 8

    def test_style_routes_maps_line_to_multiple_engines(self):
        assert "line" in STYLE_ROUTES
        assert "fast" in STYLE_ROUTES["line"]
        assert "smooth" in STYLE_ROUTES["line"]
        assert "science" in STYLE_ROUTES["line"]

    def test_styles_for_returns_available_styles(self):
        line_styles = styles_for("line")
        assert "fast" in line_styles
        assert "smooth" in line_styles

    def test_styles_for_unknown_type_returns_default(self):
        assert styles_for("nonexistent") == [DEFAULT_STYLE]

    def test_resolve_engine_returns_none_for_default(self):
        assert resolve_engine("line", "fast") is None
        assert resolve_engine("line", None) is None

    def test_resolve_engine_returns_engine_for_style(self):
        assert resolve_engine("line", "smooth") == "tplot"
        assert resolve_engine("line", "science") == "uniplot"
        assert resolve_engine("bar", "clean") == "textcharts"


class TestCLIStyleParam:
    def test_list_styles_exits_zero(self):
        rc, out, err = _run(["--list-styles"])
        assert rc == 0
        assert "line" in out
        assert "smooth" in out

    def test_style_science_renders_uniplot(self):
        rc, out, err = _run([
            "line", "--style", "science", "--json",
            '[{"label":"A","x":[1,2,3],"y":[4,5,6]}]',
        ])
        assert rc == 0
        assert len(out.strip()) > 0

    def test_style_smooth_renders_tplot(self):
        rc, out, err = _run([
            "line", "--style", "smooth", "--json",
            '[{"label":"A","x":[1,2,3],"y":[4,5,6]}]',
        ])
        assert rc == 0
        assert len(out.strip()) > 0

    def test_style_clean_renders_textcharts_bar(self):
        rc, out, err = _run([
            "bar", "--style", "clean", "--json",
            '{"categories":["X","Y","Z"],"values":[10,20,30]}',
        ])
        assert rc == 0
        assert "X" in out or "Y" in out or "Z" in out

    def test_style_retro_renders_sparkline(self):
        rc, out, err = _run([
            "sparkline", "--style", "retro", "--json",
            '{"values":[1,3,5,2,8]}',
        ])
        assert rc == 0
        assert len(out.strip()) > 0

    def test_env_var_overrides_default(self):
        rc, out, err = _run(
            ["line", "--json", '[{"label":"A","x":[1,2,3],"y":[4,5,6]}]'],
            env={"GLYPH_ARTS_STYLE": "science"},
        )
        assert rc == 0

    def test_gauge_style_still_works(self):
        rc, out, err = _run([
            "gauge", "--gauge-style", "half-circle", "--json",
            '[{"label":"CPU","value":72,"max":100}]',
        ])
        assert rc == 0
