"""Phase 12 interactive and static gallery command."""

from __future__ import annotations

import contextlib
import html
import io
import re
import sys
from pathlib import Path

from rich.console import Console
from rich.live import Live
from rich.panel import Panel
from rich.prompt import Prompt

MAX_HTML_BYTES = 2 * 1024 * 1024
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[ -/]*[@-~]")

GALLERY_CHARTS = [
    "kline", "line", "scatter", "step", "bar", "pie", "multibar", "stackedbar",
    "hist", "heatmap", "spectrum", "waterfall", "box", "indicator", "event", "confusion", "sparkline",
    "table", "tree", "panel", "gauge", "dashboard", "graph", "curve", "uniplot",
    "banner", "radar",
]

SAMPLES = {
    "kline": {"dates": ["01/01/2026", "02/01/2026", "03/01/2026"], "open": [10, 12, 11], "high": [13, 14, 15], "low": [9, 10, 10], "close": [12, 11, 14]},
    "line": [{"label": "A", "x": [1, 2, 3, 4], "y": [2, 5, 3, 7]}],
    "scatter": [{"label": "A", "x": [1, 2, 3, 4], "y": [4, 2, 6, 5]}],
    "step": [{"label": "A", "x": [1, 2, 3, 4], "y": [1, 3, 2, 5]}],
    "bar": {"labels": ["A", "B", "C"], "values": [4, 7, 5]},
    "pie": {"labels": ["A", "B", "C"], "values": [40, 35, 25]},
    "multibar": {"labels": ["Q1", "Q2"], "series": [{"label": "Rev", "values": [10, 14]}, {"label": "Cost", "values": [6, 8]}]},
    "stackedbar": {"labels": ["Q1", "Q2"], "series": [{"label": "Core", "values": [6, 9]}, {"label": "Plus", "values": [3, 4]}]},
    "hist": {"values": [1, 2, 2, 3, 3, 3, 4, 5], "bins": 5},
    "heatmap": {"matrix": [[1, 2], [3, 4]], "xlabels": ["A", "B"], "ylabels": ["X", "Y"]},
    "spectrum": {"freq": [99.0, 99.15, 99.3, 99.45, 99.6], "power": [-93, -80, -42, -82, -93], "center": 99.3, "bandwidth": 0.2},
    "waterfall": {"matrix": [[-94, -80, -52, -45, -60, -90], [-94, -72, -45, -42, -55, -88], [-94, -82, -58, -44, -50, -86]], "xlabels": ["99.0", "99.6"], "ylabels": ["t-2", "t-1", "now"], "min": -94, "max": -42},
    "box": {"data": [[1, 2, 3, 4], [2, 3, 5, 6]], "labels": ["A", "B"]},
    "indicator": {"value": 72, "label": "Health"},
    "event": {"data": [1, 3, 5, 8, 13]},
    "confusion": {"actual": [0, 1, 1, 0], "predicted": [0, 1, 0, 0], "labels": ["No", "Yes"]},
    "sparkline": {"values": [1, 3, 2, 5, 4, 7]},
    "table": {"columns": ["Metric", "Value"], "rows": [["DAU", "12k"], ["Conv", "8%"]]},
    "tree": {"label": "root", "children": [{"label": "charts"}, {"label": "themes"}]},
    "panel": {"content": "Terminal-native charts", "title": "glyph-arts", "box": "ROUNDED"},
    "gauge": [{"label": "CPU", "value": 72, "max": 100}, {"label": "RAM", "value": 12, "max": 32}],
    "dashboard": {"panels": [{"type": "gauge", "title": "CPU", "data": {"label": "CPU", "value": 72, "max": 100}}, {"type": "sparkline", "title": "Load", "data": {"values": [1, 3, 5, 2, 8]}}]},
    "graph": {"edges": [["A", "B"], ["B", "C"], ["A", "C"]]},
    "curve": {"points": [[0, 0], [1, 1], [2, 0], [3, 2]]},
    "uniplot": [{"label": "A", "x": [1, 2, 3, 4], "y": [2, 4, 3, 6]}],
    "banner": {"text": "GLYPH", "font": "big", "color": "cyan"},
    "radar": {"labels": ["ATK", "DEF", "SPD", "MGC", "LCK"], "series": [{"label": "Hero", "values": [80, 60, 90, 70, 50]}], "max": 100},
}


def available_themes() -> list[str]:
    try:
        from cli_charts.themes import CUSTOM_THEMES

        custom = sorted(CUSTOM_THEMES)
    except Exception:
        custom = []
    themes = ["pro", "clear", "matrix", *custom]
    seen: set[str] = set()
    result = []
    for theme in themes:
        if theme not in seen:
            seen.add(theme)
            result.append(theme)
    return result


def render_preview(chart_type: str, theme: str, width: int = 60, height: int = 20) -> str:
    from cli_charts.chart import CMDS

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf), contextlib.redirect_stderr(buf):
        try:
            renderer = CMDS["rich_live"] if chart_type == "dashboard" else CMDS[chart_type]
            renderer(SAMPLES[chart_type], chart_type, width, height, theme, no_color=True)
        except ImportError as exc:
            print(f"{chart_type}: optional renderer unavailable ({exc.name})")
        except SystemExit as exc:
            if exc.code not in (0, None):
                raise
    return buf.getvalue()


def _plain(text: str) -> str:
    return ANSI_RE.sub("", text)


def _html_document(charts: list[str], themes: list[str]) -> str:
    cells = []
    for chart_type in charts:
        for theme in themes:
            rendered = html.escape(_plain(render_preview(chart_type, theme, 54, 14)))
            cells.append(f'<section class="cell"><h3>{chart_type} / {theme}</h3><pre>{rendered}</pre></section>')
    return """<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<title>glyph-arts gallery</title>
<style>
body{margin:24px;background:#111;color:#eee;font:14px/1.4 system-ui,sans-serif}
a{color:#74c7ec}.grid{display:grid;grid-template-columns:repeat(auto-fit,minmax(320px,1fr));gap:12px}
.cell{border:1px solid #333;border-radius:8px;padding:12px;background:#181818;overflow:auto}
h1{margin:0 0 4px}h3{margin:0 0 8px;color:#a6e3a1;font-size:13px}
pre{margin:0;font:11px/1.05 Consolas,Menlo,monospace;white-space:pre;color:#ddd}
</style>
</head>
<body>
<h1>glyph-arts gallery</h1>
<p>Static preview of terminal-native charts. <a href="https://pypi.org/project/glyph-arts/">PyPI</a> / <a href="https://github.com/">GitHub</a></p>
<main class="grid">
""" + "\n".join(cells) + """
</main>
</body>
</html>
"""


def write_html(output: str, chart: str | None = None, theme: str | None = None) -> Path:
    charts = [chart] if chart else list(GALLERY_CHARTS)
    themes = [theme] if theme else available_themes()[:6]
    for theme_count in (len(themes), min(3, len(themes)), 1):
        selected = themes[:theme_count]
        doc = _html_document(charts, selected)
        if len(doc.encode("utf-8")) < MAX_HTML_BYTES or theme_count == 1:
            path = Path(output)
            path.write_text(doc, encoding="utf-8")
            size_kb = path.stat().st_size / 1024
            print(f"Wrote {path} ({len(charts)} charts x {len(selected)} themes, {size_kb:.1f} KB)")
            return path
    raise RuntimeError("unreachable")


def run_tui(chart: str | None = None, theme: str | None = None) -> int:
    console = Console()
    charts = list(GALLERY_CHARTS)
    themes = available_themes()
    chart_idx = charts.index(chart) if chart in charts else 0
    theme_idx = themes.index(theme) if theme in themes else 0
    try:
        while True:
            left = "\n".join(("> " if i == chart_idx else "  ") + name for i, name in enumerate(charts))
            preview = render_preview(charts[chart_idx], themes[theme_idx])
            body = f"{left}\n\n<up/down> chart  <left/right> theme  <q> quit  <enter> render full"
            with Live(Panel.fit(body), console=console, transient=True, refresh_per_second=4):
                pass
            console.print(Panel(preview, title=f"{charts[chart_idx]} / {themes[theme_idx]}"))
            command = Prompt.ask("gallery", default="")
            if command in {"q", "quit"}:
                return 0
            if command in {"down", "j"}:
                chart_idx = (chart_idx + 1) % len(charts)
            elif command in {"up", "k"}:
                chart_idx = (chart_idx - 1) % len(charts)
            elif command in {"right", "l"}:
                theme_idx = (theme_idx + 1) % len(themes)
            elif command in {"left", "h"}:
                theme_idx = (theme_idx - 1) % len(themes)
            elif command == "":
                print("\033[2J\033[H", end="")
                sys.stdout.write(render_preview(charts[chart_idx], themes[theme_idx], 90, 28))
                Prompt.ask("press enter to return", default="")
    except KeyboardInterrupt:
        return 0


def run_gallery(output: str | None = None, chart: str | None = None, theme: str | None = None) -> int:
    if chart and chart not in GALLERY_CHARTS:
        raise SystemExit(f"unknown gallery chart: {chart}")
    if output:
        write_html(output, chart=chart, theme=theme)
        return 0
    return run_tui(chart=chart, theme=theme)
