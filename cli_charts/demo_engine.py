"""Phase 12 self-running demo reel."""

from __future__ import annotations

import contextlib
import io
import itertools
import sys
import time
from collections.abc import Callable, Iterable
from typing import Any

SPEED_BUDGETS = {"fast": 10.0, "normal": 30.0, "slow": 60.0}
OUTRO_TIPS = (
    "Try: glyph-arts gallery",
    "Try: glyph-arts art HELLO --gradient sunset",
    "Try: glyph-arts status",
)


SAMPLES: dict[str, Any] = {
    "art": {"text": "GLYPH ARTS"},
    "banner": {"text": "71 chart types", "font": "big", "color": "cyan"},
    "bar": {"labels": ["Q1", "Q2", "Q3", "Q4"], "values": [12, 18, 15, 24]},
    "pie": {"labels": ["CLI", "API", "Docs"], "values": [45, 35, 20]},
    "line": [{"label": "DAU", "x": [1, 2, 3, 4, 5, 6], "y": [8, 10, 9, 13, 15, 18]}],
    "kline": {
        "dates": ["01/01/2026", "02/01/2026", "03/01/2026", "04/01/2026"],
        "open": [100, 102, 101, 105],
        "high": [104, 105, 108, 110],
        "low": [98, 100, 99, 103],
        "close": [102, 101, 106, 109],
    },
    "heatmap": {"matrix": [[1.0, 0.7, 0.2], [0.7, 1.0, 0.4], [0.2, 0.4, 1.0]], "xlabels": ["A", "B", "C"], "ylabels": ["A", "B", "C"]},
    "spectrum": {"freq": [99.0, 99.15, 99.3, 99.45, 99.6], "power": [-93, -80, -42, -82, -93], "center": 99.3, "bandwidth": 0.2},
    "dashboard": {
        "panels": [
            {"type": "gauge", "title": "CPU", "data": {"label": "CPU", "value": 68, "max": 100}},
            {"type": "sparkline", "title": "Load", "data": {"values": [3, 5, 4, 8, 6, 9]}},
        ]
    },
    "radar": {"labels": ["ATK", "DEF", "SPD", "MGC", "LCK"], "series": [{"label": "Hero", "values": [82, 68, 90, 73, 61]}], "max": 100},
}


DEMO_SCRIPT = (
    ("art", "GLYPH ARTS", 3.0),
    ("banner", "71 chart types", 2.0),
    ("bar", "Sales by quarter", 3.0),
    ("pie", "Market share", 3.0),
    ("line", "Traffic", 3.0),
    ("kline", "OHLC", 3.0),
    ("heatmap", "Correlation", 3.0),
    ("spectrum", "RF Spectrum", 2.0),
    ("dashboard", "Dashboard", 3.0),
    ("line", "Motion preview", 3.0),
    ("radar", "Stat sheet", 2.0),
    ("banner", "pip install glyph-arts", 2.0),
)


def _theme_cycle() -> list[str]:
    try:
        from cli_charts.themes import CUSTOM_THEMES

        themes = sorted(CUSTOM_THEMES)
    except Exception:
        themes = []
    preferred = ["claude", "linear", "tesla", "vercel", "pro", "matrix"]
    ordered = [theme for theme in preferred if theme in themes or theme in {"pro", "matrix"}]
    ordered.extend(theme for theme in themes if theme not in ordered)
    return ordered[:6] or ["pro"]


def render_section(chart_type: str, title: str, theme: str) -> str:
    """Render one demo section by calling chart.py CMDS in-process."""
    from cli_charts.chart import CMDS

    data = SAMPLES[chart_type]
    kwargs: dict[str, Any] = {"no_color": False}
    if chart_type == "art":
        kwargs.update(text=data["text"], font="slant", gradient="sunset")
        data = {}
    if title == "pip install glyph-arts":
        tip = OUTRO_TIPS[int(time.monotonic()) % len(OUTRO_TIPS)]
        data = {"text": f"pip install\nglyph-arts\n{tip}", "font": "small", "color": "green"}
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        try:
            renderer = CMDS["rich_live"] if chart_type == "dashboard" else CMDS[chart_type]
            renderer(data, title, 72, 20, theme, **kwargs)
        except SystemExit as exc:
            if exc.code not in (0, None):
                raise
    return buf.getvalue()


def _run_segments(
    segments: Iterable[tuple[str, str, float]],
    *,
    budget: float,
    clear: bool,
    renderer: Callable[[str, str, str], str] | None = None,
) -> None:
    if renderer is None:
        renderer = render_section
    scale = budget / SPEED_BUDGETS["normal"]
    started = time.monotonic()
    themes = itertools.cycle(_theme_cycle())
    for chart_type, title, normal_seconds in segments:
        section_budget = normal_seconds * scale
        elapsed = time.monotonic() - started
        if elapsed + section_budget > budget:
            print(f"warning: skipping {chart_type} demo section over {budget:.0f}s budget", file=sys.stderr)
            continue
        if clear:
            print("\033[2J\033[H", end="")
            time.sleep(min(0.3 * scale, max(0.0, budget - elapsed)))
        section_started = time.monotonic()
        sys.stdout.write(renderer(chart_type, title, next(themes)))
        sys.stdout.flush()
        remaining = section_budget - (time.monotonic() - section_started)
        if remaining > 0:
            time.sleep(remaining)


def run_demo(speed: str = "normal", clear: bool = True) -> int:
    """Run the terminal demo reel."""
    budget = SPEED_BUDGETS.get(speed, SPEED_BUDGETS["normal"])
    try:
        _run_segments(DEMO_SCRIPT, budget=budget, clear=clear)
    except KeyboardInterrupt:
        print("demo cancelled")
    return 0
