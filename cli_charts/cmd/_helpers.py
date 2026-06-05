#!/usr/bin/env python3
"""glyph-arts: terminal-visible chart toolkit for Claude Code.

Usage: python chart.py <type> [options]
See CHART_TYPES_BY_ENGINE for the authoritative chart type list.

Animation (--animate):
  Stream values from stdin line-by-line; chart re-renders after each point.
  Supported types: line, scatter, sparkline
  Flags: --refresh FPS (default 10), --window N (default 50), --duration SEC
"""
import argparse
import contextlib
import datetime
import importlib
import io
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile

from cli_charts.cmd.media_args import add_media_arguments
from cli_charts.cmd.media_dispatch import dispatch_media
from cli_charts.font_tier import detect_font_tier
from cli_charts.osc8 import link as _osc8_link
from cli_charts.registry import DEFAULT_STYLE, STYLE_ROUTES, resolve_engine
from cli_charts.registry import STYLES as _STYLES
from cli_charts.symbols import BLOCK, BRAILLE_ALL, get_symbol
from cli_charts.themes import get_palette as _get_palette

_VERSION: str | None = None


def _load_version() -> str:
    global _VERSION
    if _VERSION is not None:
        return _VERSION
    try:
        from pathlib import Path as _Path

        _VERSION = (_Path(__file__).parent.parent / "VERSION").read_text(encoding="utf-8").strip()
    except Exception:
        try:
            from importlib.metadata import version as _pkg_version

            _VERSION = _pkg_version("glyph-arts")
        except Exception:
            _VERSION = "unknown"
    return _VERSION


class _LazyVersionAction(argparse.Action):
    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, **kwargs):
        super().__init__(option_strings=option_strings, dest=dest, nargs=0, default=default, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        parser.exit(message=f"glyph-arts {_load_version()}\n")


# -- helpers -----------------------------------------------------------------

_MARKER_SYMBOLS = {
    'circle': 'circle',
    'triangle': 'triangle_up',
    'diamond': 'diamond',
    'star': 'star',
    'square': 'square',
}


def _symbol_tier(kw):
    tier = kw.get('font_tier') or detect_font_tier()
    return 'unicode' if tier == 'unicode-extended' else tier


def _bar_symbols(name, tier):
    if name == 'ascii':
        return '#', ' '
    if name == 'unicode':
        return BLOCK['eighth_low_8'], ' '
    if name == 'progress':
        return BLOCK['progress_full'], BLOCK['progress_empty']
    if name == 'braille':
        return BRAILLE_ALL[255], BRAILLE_ALL[0]
    if name == 'arrows':
        return get_symbol('arrow_up', tier=tier), get_symbol('arrow_down', tier=tier)
    if name == 'block':
        return BLOCK['eighth_low_8'], ' '
    if name == 'shade':
        return BLOCK['eighth_low_8'], BLOCK['shade_light']
    raise ValueError(f"unknown symbol set: {name!r}")


def _style_to_bar_symbols(style):
    return {
        'auto': None,
        'unicode': 'unicode',
        'ascii': 'ascii',
        'braille': 'braille',
        'block': 'block',
        'shade': 'shade',
    }.get(style)


def _style_to_gauge(style):
    return {
        'auto': 'bar',
        'unicode': 'bar',
        'ascii': 'ascii',
        'braille': 'braille',
        'block': 'block',
        'shade': 'shade',
        'bar': 'bar',
        'half-circle': 'half-circle',
        'full-circle': 'full-circle',
    }.get(style, style)


def _capture_stdout(func):
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        func()
    return buf.getvalue()

def _canvas_line(canvas, x0, y0, x1, y1):
    """Bresenham's line algorithm -- drawille Canvas has no built-in line()."""
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        canvas.set(x0, y0)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy


# -- media renderer metadata --------------------------------------------------

_MEDIA_TYPES = {'image', 'video'}
_IMAGE_EXTENSIONS = {
    '.avif', '.bmp', '.gif', '.jpeg', '.jpg', '.png', '.tif', '.tiff', '.webp',
}
_CHAT_GROUP_ALIASES = {'sdr'}
_CHAT_EFFECT_ALIASES = {'effects'}
_CHAT_HEALTH_ALIASES = {'probe', 'profile', 'profiles', 'fix', 'fix-chat'}
_DIAGRAM_KIND_ALIASES = {
    'math', 'sequence', 'tree', 'table', 'frame', 'box', 'note', 'flowchart',
    'graphdag', 'dag', 'graphplanar', 'planar',
}


def _has_flag(argv, *flags):
    return any(arg in flags for arg in argv)


def _rewrite_chat_argv(argv):
    """Translate `glyph-arts chat ...` into chat-safe concrete chart commands."""
    if not argv or argv[0] != 'chat':
        return argv
    rest = list(argv[1:])
    if not rest:
        return ['auto', '--no-color']
    if rest[0] in ('-h', '--help'):
        return ['--help']

    target = None
    if rest and rest[0] in _CHAT_HEALTH_ALIASES:
        return ['chat-health', rest[0], *rest[1:]]
    if rest and rest[0].lower() in _DIAGRAM_KIND_ALIASES:
        return ['diagram', '--no-color', '--diagram-kind', rest[0], *rest[1:]]
    if rest[0] in _CHAT_GROUP_ALIASES and len(rest) > 1:
        rest = rest[1:]
    if rest and rest[0] in _CHAT_EFFECT_ALIASES:
        target = 'effect'
        rest.pop(0)
    elif rest and rest[0] in (set(CMDS) | _MEDIA_TYPES):
        target = rest.pop(0)
    elif rest and not rest[0].startswith('-'):
        suffix = os.path.splitext(rest[0])[1].lower()
        if suffix in _IMAGE_EXTENSIONS:
            target = 'image'
            rest = ['--file', rest[0], *rest[1:]]
    if target is None:
        target = 'auto'

    rewritten = [target, *rest]
    if target == 'image' and not _has_flag(rewritten, '--chat'):
        rewritten.insert(1, '--chat')
    elif target != 'video' and not _has_flag(rewritten, '--no-color'):
        rewritten.insert(1, '--no-color')
    return rewritten


def _rewrite_diagram_argv(argv):
    """Allow `diagram sequence --json ...` despite argparse's nargs='*' edge."""
    if not argv or argv[0] != 'diagram':
        return argv
    out = [argv[0]]
    idx = 1
    while idx < len(argv):
        arg = argv[idx]
        if arg == '--diagram-kind':
            return argv
        if arg.lower() in _DIAGRAM_KIND_ALIASES:
            out.extend(['--diagram-kind', arg])
            out.extend(argv[idx + 1:])
            return out
        out.append(arg)
        idx += 1
    return out


def _plt_finalize(plt, title, w, h, theme, kw):
    """Apply common plotext settings and render."""
    if title:
        if kw.get('link_title'):
            title = _osc8_link(title, kw['link_title'])
        plt.title(title)
    plt.plotsize(w, h)
    _palette = _get_palette(theme)
    if _palette:
        if _palette.get('plt_base'):
            plt.theme(_palette['plt_base'])
        plt.canvas_color(_palette['canvas'])
        plt.axes_color(_palette['axes'])
        plt.ticks_color(_palette['ticks'])
    else:
        plt.theme(theme)
    if kw.get('xlabel'):
        plt.xlabel(kw['xlabel'])
    if kw.get('ylabel'):
        plt.ylabel(kw['ylabel'])
    if kw.get('xlim'):
        plt.xlim(*kw['xlim'])
    if kw.get('ylim'):
        plt.ylim(*kw['ylim'])
    if kw.get('xscale') == 'log':
        plt.xscale('log')
    if kw.get('yscale') == 'log':
        plt.yscale('log')
    if kw.get('output'):
        plt.save_fig(kw['output'], keep_colors=False)
    elif kw.get('no_color'):
        # plotext theme() must be set before plot calls to take effect; by the
        # time _plt_finalize runs, plot data is already buffered. Build the
        # output string and strip ANSI escapes ourselves -- works for any theme.
        import re as _re
        _ansi = _re.compile(r'\x1b\[[0-9;]*m')
        sys.stdout.write(_ansi.sub('', plt.build()))
        sys.stdout.write('\n')
    else:
        plt.show()


def _series_color(theme, index, explicit=None):
    if explicit:
        return explicit
    palette = _get_palette(theme)
    if not palette:
        return None
    series = palette.get('series') or []
    if not series:
        return None
    return series[index % len(series)]


def _statusline_values(d):
    if isinstance(d, list):
        if d and isinstance(d[0], dict):
            if 'y' in d[0]:
                return d[0]['y']
            if 'values' in d[0]:
                return d[0]['values']
        return d
    if isinstance(d, dict):
        if 'values' in d:
            return d['values']
        if 'y' in d:
            return d['y']
    return []


def _render_statusline(chart_type, d, title=''):
    import sparklines as sl
    text = ''
    if chart_type == 'sparkline':
        values = _statusline_values(d)
        spark = ''.join(sl.sparklines(values)) if values else ''
        label = title or (d.get('label', '') if isinstance(d, dict) else '')
        value = values[-1] if values else ''
        suffix = f' {label}: {value}' if label else ''
        text = f'{spark}{suffix}'
    elif chart_type == 'indicator':
        label = d.get('label', title or '')
        value = d.get('value', '')
        unit = d.get('unit', '')
        text = f'{label}: {value}{unit}' if label else f'{value}{unit}'
    elif chart_type == 'gauge':
        metrics = d if isinstance(d, list) else d.get('metrics', [d])
        parts = []
        for m in metrics:
            val = float(m['value'])
            mx = float(m.get('max', 100))
            pct = max(0.0, min(1.0, val / mx)) if mx else 0.0
            filled = round(pct * 10)
            parts.append(f"{m.get('label', '')} [{'█' * filled}{'░' * (10 - filled)}] {pct:.0%}")
        text = ' '.join(parts)
    print(text.replace('\n', ' ')[:80])


# ── 24-bit Braille engine (hires / radar) ────────────────────────────────────

_BRAILLE_DOTS = [[0x01, 0x08], [0x02, 0x10], [0x04, 0x20], [0x40, 0x80]]

_HIRES_PALETTE = [
    (0, 245, 212),
    (255, 107, 107),
    (255, 209, 102),
    (120, 180, 255),
    (200, 120, 255),
    (80, 240, 140),
]


class _HiresCanvas:
    """Per-dot 24-bit ANSI braille canvas.  2 px wide x 4 px tall per cell."""

    def __init__(self, w: int, h: int):
        self.cw, self.ch = w, h
        self.buf = [[0] * w for _ in range(h)]
        self.col: list = [[None] * w for _ in range(h)]

    def dot(self, px: int, py: int, c):
        cx, cy = px // 2, py // 4
        if 0 <= cx < self.cw and 0 <= cy < self.ch:
            self.buf[cy][cx] |= _BRAILLE_DOTS[py % 4][px % 2]
            if self.col[cy][cx] is None:
                self.col[cy][cx] = c

    def line(self, x0: int, y0: int, x1: int, y1: int, c):
        dx, dy = abs(x1 - x0), abs(y1 - y0)
        sx = 1 if x0 < x1 else -1
        sy = 1 if y0 < y1 else -1
        err = dx - dy
        while True:
            self.dot(x0, y0, c)
            if x0 == x1 and y0 == y1:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0 += sx
            if e2 < dx:
                err += dx
                y0 += sy

    def render(self, no_color: bool = False) -> list:
        out = []
        for cy in range(self.ch):
            row = ""
            for cx in range(self.cw):
                b = self.buf[cy][cx]
                c = self.col[cy][cx]
                ch = chr(0x2800 + b)
                if b and c and not no_color:
                    row += f"\033[38;2;{c[0]};{c[1]};{c[2]}m{ch}\033[0m"
                else:
                    row += "\u2800" if not b else ch
            out.append(row)
        return out


def _catmull_pixels(ys, xs, cx0, cy0, pw, ph, y_min, y_max, tension=0.35):
    """Catmull-Rom spline -> cubic Bezier -> pixel coordinate list."""
    n = len(ys)
    if n == 0:
        return []
    span = max(y_max - y_min, 1e-9)
    x_span = max(xs[-1] - xs[0], 1e-9) if len(xs) > 1 else 1.0

    def xp(xv):
        return cx0 + int((xv - xs[0]) / x_span * pw)

    def yp(v):
        return cy0 + ph - int((v - y_min) / span * ph)

    pts = [(xp(xs[i]), yp(ys[i])) for i in range(n)]
    result = []
    for i in range(len(pts) - 1):
        p0 = pts[max(0, i - 1)]
        p1 = pts[i]
        p2 = pts[i + 1]
        p3 = pts[min(len(pts) - 1, i + 2)]
        cp1x = p1[0] + (p2[0] - p0[0]) * tension
        cp1y = p1[1] + (p2[1] - p0[1]) * tension
        cp2x = p2[0] - (p3[0] - p1[0]) * tension
        cp2y = p2[1] - (p3[1] - p1[1]) * tension
        steps = max(abs(p2[0] - p1[0]), abs(p2[1] - p1[1]), 1) * 2
        for s in range(steps + 1):
            t = s / steps
            t2 = t * t
            t3 = t2 * t
            mt = 1 - t
            mt2 = mt * mt
            mt3 = mt2 * mt
            x = int(mt3 * p1[0] + 3 * mt2 * t * cp1x + 3 * mt * t2 * cp2x + t3 * p2[0])
            y = int(mt3 * p1[1] + 3 * mt2 * t * cp1y + 3 * mt * t2 * cp2y + t3 * p2[1])
            result.append((x, y))
    return result


# -- renderers ---------------------------------------------------------------

def _normalize_kline_dates(dates):
    """Convert common date formats to DD/MM/YYYY required by plotext."""
    from datetime import datetime
    result = []
    for s in dates:
        for fmt in ('%d/%m/%Y', '%Y-%m-%d', '%Y/%m/%d', '%m/%d/%Y'):
            try:
                result.append(datetime.strptime(s, fmt).strftime('%d/%m/%Y'))
                break
            except ValueError:
                continue
        else:
            result.append(s)
    return result


def kline(d, title, w, h, theme, **kw):
    """plotext candlestick K-line. Accepts DD/MM/YYYY or YYYY-MM-DD dates."""
    candle_style = kw.get('candle_style')
    if candle_style and candle_style != 'default':
        tier = _symbol_tier(kw)
        up = get_symbol('triangle_up', tier=tier)
        down = get_symbol('triangle_down', tier=tier)
        for date, open_, close in zip(d['dates'], d['open'], d['close'], strict=False):
            marker = up if close >= open_ else down
            print(f"{date} {marker} {open_} -> {close}")
        return
    import plotext as plt
    plt.clear_figure()
    plt.candlestick(_normalize_kline_dates(d['dates']), {
        'Open': d['open'], 'High': d['high'],
        'Low': d['low'],   'Close': d['close'],
    })
    _plt_finalize(plt, title, w, h, theme, kw)


def line(d, title, w, h, theme, **kw):
    """plotext multi-series line chart."""
    import plotext as plt
    plt.clear_figure()
    series = d if isinstance(d, list) else [d]
    for i, s in enumerate(series):
        x = s.get('x', list(range(len(s['y']))))
        label = s.get('label', '')
        if kw.get('link_data'):
            label = _osc8_link(label or f'S{i}', kw['link_data'])
        plt.plot(x, s['y'], label=label,
                 marker=s.get('marker'), color=_series_color(theme, i, s.get('color')))
    _plt_finalize(plt, title, w, h, theme, kw)


def scatter(d, title, w, h, theme, **kw):
    """plotext scatter plot. Same schema as line."""
    import plotext as plt
    plt.clear_figure()
    series = d if isinstance(d, list) else [d]
    marker_name = kw.get('marker')
    marker = get_symbol(_MARKER_SYMBOLS[marker_name], tier=_symbol_tier(kw)) if marker_name else None
    for i, s in enumerate(series):
        x = s.get('x', list(range(len(s['y']))))
        label = s.get('label', '')
        if kw.get('link_data'):
            label = _osc8_link(label or f'S{i}', kw['link_data'])
        plt.scatter(x, s['y'], label=label,
                    marker=marker or s.get('marker'), color=_series_color(theme, i, s.get('color')))
    _plt_finalize(plt, title, w, h, theme, kw)


def step(d, title, w, h, theme, **kw):
    """plotext staircase step chart -- x-point duplication creates stairs.
    Same schema as line. Use for discrete state changes (e.g. bid price, stock level).
    """
    import plotext as plt
    series = d if isinstance(d, list) else [d]
    for s in series:
        x = s.get('x', list(range(len(s['y']))))
        y = s['y']
        sx, sy = [], []
        for i in range(len(x)):
            sx.append(x[i])
            sy.append(y[i])
            if i + 1 < len(x):
                sx.append(x[i + 1])
                sy.append(y[i])
        plt.plot(sx, sy, label=s.get('label', ''),
                 marker=s.get('marker'), color=s.get('color'))
    _plt_finalize(plt, title, w, h, theme, kw)


def bar(d, title, w, h, theme, **kw):
    """plotext vertical/horizontal bar chart."""
    # Use textgraph for horizontal bars when orientation is horizontal
    if kw.get('orientation') == 'horizontal':
        return hbar(d, title, w, h, theme, **kw)
    import plotext as plt
    plt.clear_figure()
    plt.bar(d['labels'], d['values'],
            orientation=kw.get('orientation', 'vertical'))
    symbol_set = kw.get('symbol_set') or _style_to_bar_symbols(kw.get('visual_style'))
    if symbol_set:
        full, empty = _bar_symbols(symbol_set, _symbol_tier(kw))
        default_full = BLOCK['eighth_low_8']
        output = _capture_stdout(lambda: _plt_finalize(plt, title, w, h, theme, kw))
        sys.stdout.write(output.replace(default_full, full).replace(' ', empty if symbol_set in {'braille', 'shade'} else ' '))
        return
    _plt_finalize(plt, title, w, h, theme, kw)


def hbar(d, title, w, h, theme, **kw):
    """Horizontal bar chart using textgraph/ascii-graph.

    Uses textgraph.horizontal() for enhanced horizontal bars with labels.
    Falls back to ascii-graph or plotext.
    """
    labels = d.get('labels', [f'[{i}]' for i in range(len(d['values']))])
    values = d['values']

    if title:
        print(title)

    # Try textgraph.horizontal() first
    try:
        from textgraph import horizontal as textgraph_hbar
        data = list(zip(labels, values, strict=False))
        print(textgraph_hbar(data))
        return
    except ImportError:
        pass

    # Try ascii-graph
    try:
        from ascii_graph import Pyasciigraph
        g = Pyasciigraph()
        data = list(zip(labels, values, strict=False))
        for line in g.graph(title or 'bar', data):
            print(line)
        return
    except ImportError:
        pass

    # Fallback to plotext
    import plotext as plt
    plt.clear_figure()
    plt.bar(labels, values, orientation='horizontal')
    _plt_finalize(plt, '', w, h, theme, kw)


def pie(d, title, w, h, theme, **kw):
    """Rich percentage-bar pie breakdown. labels + values arrays of equal length."""
    from rich import box as rich_box
    from rich.console import Console
    from rich.table import Table
    total = sum(d['values']) or 1
    bar_w = 36
    colors = ['red', 'green', 'blue', 'yellow', 'magenta', 'cyan',
              'bright_red', 'bright_green', 'bright_blue']
    tbl = Table(title=title or None, box=rich_box.ROUNDED, show_lines=False)
    tbl.add_column('Label', style='bold')
    tbl.add_column('Pct', justify='right')
    tbl.add_column('Distribution', min_width=bar_w)
    tbl.add_column('Value', justify='right')
    for i, (label, val) in enumerate(zip(d['labels'], d['values'], strict=False)):
        pct = val / total * 100
        filled = round(pct / 100 * bar_w)
        color = colors[i % len(colors)]
        bar = f'[{color}]{"█" * filled}[/{color}]{"░" * (bar_w - filled)}'
        tbl.add_row(str(label), f'{pct:.1f}%', bar, str(val))
    Console().print(tbl)


def multibar(d, title, w, h, theme, **kw):
    """plotext grouped multi-series bar chart."""
    import plotext as plt
    xlabels = d['labels']
    values = [s['values'] for s in d['series']]
    slabels = [s.get('label', f'S{i}') for i, s in enumerate(d['series'])]
    plt.multiple_bar(xlabels, values, labels=slabels,
                     orientation=kw.get('orientation', 'vertical'))
    _plt_finalize(plt, title, w, h, theme, kw)


def stackedbar(d, title, w, h, theme, **kw):
    """plotext stacked bar chart."""
    import plotext as plt
    xlabels = d['labels']
    values = [s['values'] for s in d['series']]
    slabels = [s.get('label', f'S{i}') for i, s in enumerate(d['series'])]
    plt.stacked_bar(xlabels, values, labels=slabels,
                    orientation=kw.get('orientation', 'vertical'))
    _plt_finalize(plt, title, w, h, theme, kw)


def hist(d, title, w, h, theme, **kw):
    """plotext histogram -- single or multi-series."""
    import plotext as plt
    series = d if isinstance(d, list) else [d]
    for s in series:
        plt.hist(s['values'], bins=s.get('bins', 20),
                 label=s.get('label', ''), color=s.get('color'))
    _plt_finalize(plt, title, w, h, theme, kw)


def heatmap(d, title, w, h, theme, **kw):
    """plotext heatmap / correlation matrix.
    plotext.heatmap() requires a pandas DataFrame.
    """
    import pandas as pd
    import plotext as plt
    df = pd.DataFrame(
        d['matrix'],
        columns=d.get('xlabels'),
        index=d.get('ylabels'),
    )
    plt.heatmap(df)
    _plt_finalize(plt, title, w, h, theme, kw)


def spectrum(d, title, w, h, theme, **kw):
    """SDR-style RF spectrum with center/band/peak overlays."""
    if kw.get('statusline'):
        _render_statusline('spectrum', d, title)
        return
    from cli_charts.render.sdr_engine import render_spectrum

    print(render_spectrum(d, title=title, width=w, height=h), end="")


def waterfall(d, title, w, h, theme, **kw):
    """SDR-style waterfall intensity map."""
    if kw.get('statusline'):
        _render_statusline('waterfall', d, title)
        return
    from cli_charts.render.sdr_engine import render_waterfall

    print(render_waterfall(d, title=title, width=w, height=h), end="")


def box(d, title, w, h, theme, **kw):
    """plotext box plot (median/quartile/whisker).
    x-labels passed as first positional arg; data matrix as second.
    """
    import plotext as plt
    if 'quintuples' in d:
        # Pre-computed quantiles: list of 5-element lists
        plt.box(d.get('labels', []), d['quintuples'], quintuples=True)
    else:
        xlabels = d.get('labels', list(range(len(d['data']))))
        plt.box(xlabels, d['data'])
    _plt_finalize(plt, title, w, h, theme, kw)


def indicator(d, title, w, h, theme, **kw):
    """plotext big-number KPI display."""
    if kw.get('statusline'):
        _render_statusline('indicator', d, title)
        return
    import plotext as plt
    plt.indicator(d['value'], d.get('label', title or ''))
    _plt_finalize(plt, None, w, h, theme, kw)  # title already baked into label


def event(d, title, w, h, theme, **kw):
    """plotext event / timeline plot.
    Orientation comes from --orientation CLI flag (kw) not JSON data.
    """
    import plotext as plt
    plt.event_plot(d['data'],
                   orientation=kw.get('orientation', 'vertical'))
    _plt_finalize(plt, title, w, h, theme, kw)


def sparkline(d, title, w, h, theme, **kw):
    """sparklines unicode block chart -- single line.

    Uses textgraph.spark() for enhanced sparklines with multiple styles.
    Falls back to sparklines library if textgraph is unavailable.
    """
    if kw.get('statusline'):
        _render_statusline('sparkline', d, title)
        return
    if title:
        print(title)
    values = d['values']

    # Try textgraph.spark() first (better sparklines)
    try:
        from textgraph import spark as textgraph_spark
        print(textgraph_spark(values))
        return
    except ImportError:
        pass

    # Fallback to sparklines library
    import sparklines as sl
    for ln in sl.sparklines(values):
        print(ln)


def table(d, title, w, h, theme, **kw):
    """rich double-edge formatted table."""
    output = kw.get('output')
    if output and str(output).lower().endswith('.md'):
        from cli_charts.render.markdown_export import export_table
        export_table(d, output)
        return
    from rich import box as richbox
    from rich.console import Console
    from rich.table import Table
    no_color = kw.get('no_color', False)
    c = Console(no_color=no_color)
    box_style = getattr(richbox, d.get('box', 'DOUBLE_EDGE'), richbox.DOUBLE_EDGE)
    t = Table(title=title, box=box_style,
              caption=d.get('caption'),
              row_styles=d.get('row_styles'))
    for col in d.get('columns') or d.get('headers', []):
        if isinstance(col, dict):
            t.add_column(col['name'], style=col.get('style', 'white'),
                         footer=str(col.get('footer', '')))
        else:
            t.add_column(str(col))
    for row in d['rows']:
        t.add_row(*[str(v) for v in row])
    c.print(t)


def tree(d, title, w, h, theme, **kw):
    """rich Tree -- hierarchical / nested data."""
    from rich.console import Console
    from rich.tree import Tree as RichTree
    no_color = kw.get('no_color', False)
    c = Console(no_color=no_color)

    def _build(node, parent):
        label = node.get('label') or node.get('name') or str(node)
        style = node.get('style', '')
        branch = parent.add(f'[{style}]{label}[/{style}]' if style else label)
        for child in node.get('children', []):
            _build(child, branch)

    root_label = d.get('label') or d.get('name') or title or 'root'
    t = RichTree(root_label)
    for child in d.get('children', []):
        _build(child, t)
    c.print(t)


def panel(d, title, w, h, theme, **kw):
    """rich Panel -- bordered text / callout box."""
    from rich import box as richbox
    from rich.console import Console
    from rich.panel import Panel as RichPanel
    no_color = kw.get('no_color', False)
    c = Console(no_color=no_color)
    box_style = getattr(richbox, d.get('box', 'ROUNDED'), richbox.ROUNDED)
    p = RichPanel(d['content'],
                  title=d.get('title', title or None),
                  subtitle=d.get('subtitle'),
                  box=box_style)
    c.print(p)


def graph(d, title, w, h, theme, **kw):
    """PHART ASCII network graph."""
    del title, w, h, theme
    from cli_charts.render.graph_engine import render_graph

    style = kw.get('graph_style') or (d.get('node_style') if isinstance(d, dict) else None) or 'round'
    node_spacing = (d.get('node_spacing') if isinstance(d, dict) else None) or kw.get('graph_node_spacing') or 4
    layer_spacing = (d.get('layer_spacing') if isinstance(d, dict) else None) or kw.get('graph_layer_spacing') or 2
    rc = render_graph(
        d,
        output=kw.get('output') or None,
        graph_format=kw.get('graph_format') or (d.get('format') if isinstance(d, dict) else 'auto'),
        node_style=style,
        node_spacing=node_spacing,
        layer_spacing=layer_spacing,
        charset=kw.get('graph_charset') or 'unicode',
    )
    if rc:
        sys.exit(rc)


# -- textcharts integration ---------------------------------------------------

def comparison(d, title, w, h, theme, **kw):
    """textcharts comparison bar chart -- side-by-side bars for A/B testing.

    JSON: {"data":[{"label":"Python","baseline":85,"comparison":89.5}, ...]}
    """
    try:
        from textcharts import ComparisonBar, ComparisonBarData
        data = [
            ComparisonBarData(
                label=str(item['label']),
                baseline_value=item.get('baseline', 0),
                comparison_value=item.get('comparison', item.get('value', 0)),
                baseline_name=str(item.get('baseline_name', 'Baseline')),
                comparison_name=str(item.get('comparison_name', 'Comparison'))
            )
            for item in d.get('data', [])
        ]
        chart = ComparisonBar(data=data, title=title, options=_textcharts_options(kw))
        print(chart.render())
    except ImportError:
        print("ERROR:dep: pip install textcharts", file=sys.stderr)
        sys.exit(2)


def diverging(d, title, w, h, theme, **kw):
    """textcharts diverging bar chart -- positive/negative comparison.

    JSON: {"data":[{"label":"Product A","pct_change":25},{"label":"Product B","pct_change":-15}]}
    """
    try:
        from textcharts import DivergingBar, DivergingBarData
        data = [
            DivergingBarData(label=str(item['label']), pct_change=item.get('pct_change', item.get('value', 0)))
            for item in d.get('data', [])
        ]
        chart = DivergingBar(data=data, title=title, options=_textcharts_options(kw))
        print(chart.render())
    except ImportError:
        print("ERROR:dep: pip install textcharts", file=sys.stderr)
        sys.exit(2)


def summary(d, title, w, h, theme, **kw):
    """textcharts summary box -- key statistics at a glance."""
    try:
        from textcharts import SummaryBox, SummaryStats
        stats = SummaryStats()
        for key, value in d.get('stats', {}).items():
            setattr(stats, key, value)
        chart = SummaryBox(stats=stats, subject=title, options=_textcharts_options(kw))
        print(chart.render())
    except ImportError:
        print("ERROR:dep: pip install textcharts", file=sys.stderr)
        sys.exit(2)


def sparkline_table(d, title, w, h, theme, **kw):
    """textcharts sparkline table -- multiple rows with inline mini charts.

    JSON: {"columns":["Revenue"],"values":{"Jan":[100],"Feb":[120],"Mar":[110]}}
    Note: Use 'sparkline' command for simpler sparkline charts.
    """
    try:
        from textcharts import SparklineColumn, SparklineTable, SparklineTableData

        columns_data = d.get('columns', ['Value'])
        values = d.get('values', {})

        # Build columns with values dict
        columns = [SparklineColumn(name=str(col), values={}) for col in columns_data]

        # Build rows (labels) and populate column values
        rows = list(values.keys())

        for col_idx, col_name in enumerate(columns_data):
            for row_label in rows:
                if col_name in values and row_label in values[col_name]:
                    if col_idx < len(columns):
                        columns[col_idx].values[row_label] = values[col_name][row_label]

        data = SparklineTableData(rows=rows, columns=columns)
        chart = SparklineTable(data=data, title=title, options=_textcharts_options(kw))
        print(chart.render())
    except ImportError:
        print("ERROR:dep: pip install textcharts", file=sys.stderr)
        sys.exit(2)


def cdf_chart(d, title, w, h, theme, **kw):
    """textcharts CDF chart -- cumulative distribution function.

    JSON: {"series":[{"name":"A","values":[1,2,3,4,5]}]}
    """
    try:
        from textcharts import CDFChart, CDFSeriesData

        series = []
        for s in d.get('series', [{'name': 'data', 'values': d.get('values', [])}]):
            if isinstance(s, dict):
                series.append(CDFSeriesData(name=str(s.get('name', 'data')), values=s.get('values', [])))
            else:
                series.append(CDFSeriesData(name='data', values=s))

        if series:
            chart = CDFChart(data=series, title=title, options=_textcharts_options(kw))
            print(chart.render())
        else:
            print("(no data)", file=sys.stderr)
    except ImportError:
        print("ERROR:dep: pip install textcharts", file=sys.stderr)
        sys.exit(2)


def rank_table(d, title, w, h, theme, **kw):
    """Sorted ranking table with Rich.

    JSON: {"items":[{"label":"Python","value":89},{"label":"Rust","value":95}]}
    or {"values":{"Python":89,"Rust":95}} (items auto-generated from values keys)
    """
    from rich.console import Console
    from rich.table import Table

    no_color = kw.get('no_color', False)
    c = Console(no_color=no_color)
    t = Table(title=title)

    if d.get('items'):
        # Format 1: items with label/value pairs
        t.add_column("Rank", justify="center")
        t.add_column("Item")
        t.add_column("Value", justify="right")
        sorted_items = sorted(d.get('items', []), key=lambda x: x.get('value', 0), reverse=True)
        for idx, item in enumerate(sorted_items, 1):
            t.add_row(str(idx), str(item.get('label', item)), f"{item.get('value', 0):.1f}")
    else:
        # Format 2: values dict {"Name": score}
        values = d.get('values', {})
        t.add_column("Rank", justify="center")
        t.add_column("Item")
        t.add_column("Score", justify="right")
        sorted_items = sorted(values.items(), key=lambda x: x[1], reverse=True)
        for idx, (name, score) in enumerate(sorted_items, 1):
            t.add_row(str(idx), str(name), f"{score:.1f}")

    c.print(t)


def percentile(d, title, w, h, theme, **kw):
    """textcharts percentile ladder -- show value distribution.

    JSON: {"data":[{"name":"Response Time","p50":50,"p90":90,"p95":95,"p99":99}]}
    or {"series":[{"name":"A","values":[...]}]} to auto-calculate.
    """
    try:
        from textcharts import PercentileData, PercentileLadder

        if 'data' in d:
            # Direct percentile data
            data = [PercentileData(
                name=str(item['name']),
                p50=item.get('p50', 0),
                p90=item.get('p90', 0),
                p95=item.get('p95', 0),
                p99=item.get('p99', 0)
            ) for item in d.get('data', [])]
        elif 'series' in d:
            # Auto-calculate from values
            data = []
            for s in d.get('series', []):
                values = s.get('values', [])
                if values:
                    import numpy as np
                    arr = np.array(values)
                    data.append(PercentileData(
                        name=str(s.get('name', 'data')),
                        p50=np.percentile(arr, 50),
                        p90=np.percentile(arr, 90),
                        p95=np.percentile(arr, 95),
                        p99=np.percentile(arr, 99)
                    ))
        else:
            print("ERROR:schema: percentile requires 'data' or 'series'", file=sys.stderr)
            sys.exit(1)
            return

        chart = PercentileLadder(data=data, title=title, options=_textcharts_options(kw))
        print(chart.render())
    except ImportError:
        print("ERROR:dep: pip install textcharts", file=sys.stderr)
        sys.exit(2)


def boxplot_comparison(d, title, w, h, theme, **kw):
    """textcharts box plot -- statistical distribution comparison.

    JSON: {"series":[{"name":"A","values":[10,20,30,40,50]}]}
    """
    try:
        from textcharts import BoxPlot, BoxPlotSeries

        series = []
        for s in d.get('series', []):
            values = s.get('values', [])
            if values:
                series.append(BoxPlotSeries(name=str(s.get('name', 'data')), values=values))
            else:
                series.append(BoxPlotSeries(name=str(s.get('name', 'data')), values=[0]))

        if series:
            chart = BoxPlot(series=series, title=title, options=_textcharts_options(kw))
            print(chart.render())
        else:
            print("(no data)", file=sys.stderr)
    except ImportError:
        print("ERROR:dep: pip install textcharts", file=sys.stderr)
        sys.exit(2)


def stacked_bar_text(d, title, w, h, theme, **kw):
    """textcharts stacked bar chart -- composition over categories.

    JSON: {"data":[{"label":"Project A","segments":[{"label":"Backend","value":30},{"label":"Frontend","value":20}]}]}
    """
    try:
        from textcharts import StackedBar, StackedBarData, StackedBarSegment

        data = []
        for item in d.get('data', []):
            segments = [
                StackedBarSegment(phase_name=str(seg.get('label', 'Segment')), value=seg.get('value', 0))
                for seg in item.get('segments', [])
            ]
            data.append(StackedBarData(label=str(item.get('label', '')), segments=segments))

        if data:
            chart = StackedBar(data=data, title=title, options=_textcharts_options(kw))
            print(chart.render())
        else:
            print("(no data)", file=sys.stderr)
    except ImportError:
        print("ERROR:dep: pip install textcharts", file=sys.stderr)
        sys.exit(2)


def _textcharts_options(kw):
    """Build textcharts ChartOptions from keyword args."""
    try:
        from textcharts import ChartOptions
        return ChartOptions(
            width=kw.get('width'),
            use_color=not kw.get('no_color', False),
        )
    except ImportError:
        return None


def curve(d, title, w, h, theme, **kw):
    """drawille braille pixel canvas -- connected high-res curves.
    Points are auto-scaled to fit --width x --height.
    Uses Bresenham's line between consecutive points for smooth output.
    """
    import drawille
    points = d['points']
    if not points:
        print('(no points)', file=sys.stderr)
        return
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    # drawille: 2 pixels wide x 4 pixels tall per terminal cell
    canvas_w = max(1, w * 2 - 1)
    canvas_h = max(1, h * 4 - 1)

    def scale(v, lo, hi, size):
        return size // 2 if hi == lo else round((v - lo) / (hi - lo) * size)

    if title:
        print(title)
    c = drawille.Canvas()
    if len(points) == 1:
        c.set(scale(points[0][0], min_x, max_x, canvas_w),
              canvas_h - scale(points[0][1], min_y, max_y, canvas_h))
    else:
        for i in range(len(points) - 1):
            x1 = scale(points[i][0],     min_x, max_x, canvas_w)
            y1 = canvas_h - scale(points[i][1],     min_y, max_y, canvas_h)
            x2 = scale(points[i + 1][0], min_x, max_x, canvas_w)
            y2 = canvas_h - scale(points[i + 1][1], min_y, max_y, canvas_h)
            _canvas_line(c, x1, y1, x2, y2)
    print(c.frame())


def gauge(d, title, w, h, theme, **kw):
    """rich multi-metric progress bars (static gauge).
    Auto-colors: green <70%, yellow <90%, red >=90%.
    """
    if kw.get('statusline'):
        _render_statusline('gauge', d, title)
        return
    if kw.get('rich_progress'):
        from rich.console import Console
        from rich.progress import (
            BarColumn,
            MofNCompleteColumn,
            Progress,
            TaskProgressColumn,
            TextColumn,
            TimeRemainingColumn,
        )
        no_color = kw.get('no_color', False)
        console = Console(no_color=no_color, force_terminal=not no_color, legacy_windows=False)
        metrics = d if isinstance(d, list) else d.get('metrics', [d])
        progress = Progress(
            TextColumn("[bold]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            console=console,
        )
        with progress:
            for m in metrics:
                val = float(m['value'])
                mx = float(m.get('max', 100))
                progress.add_task(str(m.get('label', '')), total=mx, completed=val)
        return
    from rich import box as richbox
    from rich.console import Console
    from rich.table import Table
    no_color = kw.get('no_color', False)
    c = Console(no_color=no_color)
    metrics = d if isinstance(d, list) else d.get('metrics', [d])
    t = Table(title=title, box=richbox.SIMPLE, show_header=False, padding=(0, 1))
    t.add_column('Label', style='bold', min_width=12)
    t.add_column('Bar', min_width=32)
    t.add_column('Value', justify='right', min_width=10)
    style = _style_to_gauge(kw.get('gauge_style') or kw.get('visual_style') or 'bar')
    if style == 'bar':
        full, empty = BLOCK['eighth_low_8'], BLOCK['shade_light']
    elif style == 'ascii':
        full, empty = '#', '-'
    elif style == 'block':
        full, empty = BLOCK['eighth_low_8'], ' '
    elif style == 'shade':
        full, empty = BLOCK['eighth_low_8'], BLOCK['shade_light']
    elif style == 'half-circle':
        tier = _symbol_tier(kw)
        full = get_symbol('half_circle_left', tier=tier)
        empty = get_symbol('half_circle_right', tier=tier)
    elif style == 'full-circle':
        full, empty = get_symbol('circle', tier=_symbol_tier(kw)), ' '
    elif style == 'braille':
        full, empty = BRAILLE_ALL[255], BRAILLE_ALL[0]
    else:
        raise ValueError(f"unknown gauge style: {style!r}")
    for m in metrics:
        val = float(m['value'])
        mx  = float(m.get('max', 100))
        pct = max(0.0, min(1.0, val / mx)) if mx != 0 else 0.0
        bar_w = 30
        filled = round(pct * bar_w)
        auto_color = 'green' if pct < 0.7 else ('yellow' if pct < 0.9 else 'red')
        color = m.get('color', auto_color)
        bar = f'[{color}]{full * filled}{empty * (bar_w - filled)}[/{color}]'
        t.add_row(m.get('label', ''), bar, f'{val:.1f} / {mx:.0f}')
    c.print(t)


def dashboard(d, title, w, h, theme, **kw):
    """Delegates to cli_charts/dashboard.py via subprocess (Textual TUI or Rich static)."""
    import subprocess
    config = dict(d)
    if title:
        config['title'] = title
    dash_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dashboard.py')
    cmd = [sys.executable, dash_script, '--json', json.dumps(config)]
    if not sys.stdout.isatty():
        cmd.append('--no-interactive')
    result = subprocess.run(cmd)
    sys.exit(result.returncode)


def rich_live(d, title, w, h, theme, **kw):
    """Compose multiple charts into a Rich Live/Layout panel grid.

    Schema:
        {"panels": [{"type":"bar","title":"Left","data":{...}}, ...],
         "layout": "row" | "column",
         "frames": 1}

    frames=1: static single-frame snapshot via Console.print(layout) -- pipe/TTY safe.
    frames>1: animated refresh via Rich Live (needs a TTY); falls back to static when piped.
    Each panel's child chart renders via the same CMDS dispatcher, with stdout captured
    and replayed inside a Rich Panel so ANSI colors from plotext/hires/etc. survive.
    """
    from io import StringIO

    from rich import box as richbox
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.text import Text

    panels_spec = d.get('panels') or []
    if not panels_spec:
        print('ERROR:schema: rich_live requires non-empty "panels" list', file=sys.stderr)
        sys.exit(1)

    orientation = d.get('layout', 'row')
    if orientation not in ('row', 'column'):
        print(f'ERROR:schema: layout must be "row" or "column", got {orientation!r}', file=sys.stderr)
        sys.exit(1)

    frames = max(1, int(d.get('frames', 1)))
    no_color = kw.get('no_color', False)
    panel_failures = []

    def _render_panel_content(panel_spec):
        """Dispatch sub-chart and capture its stdout as a Rich-renderable Text."""
        name = panel_spec.get('title') or panel_spec.get('name') or panel_spec.get('id') or panel_spec.get('type')
        ptype = panel_spec.get('type')
        if ptype not in CMDS:
            panel_failures.append((name, -1))
            return Text(f'[unknown panel type: {ptype!r}]', style='red')
        if ptype in ('dashboard', 'rich_live'):
            panel_failures.append((name, -1))
            return Text(f'[cannot nest {ptype!r} inside rich_live]', style='red')
        pdata = panel_spec.get('data', {})
        ptitle = panel_spec.get('title', '')
        pw = panel_spec.get('width', max(20, w // max(1, len(panels_spec)) if orientation == 'row' else w))
        ph = panel_spec.get('height', max(8, h // max(1, len(panels_spec)) if orientation == 'column' else h))
        buf = StringIO()
        saved_stdout = sys.stdout
        sys.stdout = buf
        try:
            try:
                CMDS[ptype](pdata, ptitle, pw, ph, theme, no_color=no_color)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception as e:
                panel_failures.append((name, -1))
                return Text(f'[panel render failed: {type(e).__name__}: {e}]', style='red')
        finally:
            sys.stdout = saved_stdout
        captured = buf.getvalue().rstrip('\n')
        return Text.from_ansi(captured) if captured else Text('(empty)', style='dim')

    def _build_layout():
        lay = Layout()
        sub_layouts = []
        for idx, spec in enumerate(panels_spec):
            child = Layout(name=f'p{idx}')
            child.update(Panel(
                _render_panel_content(spec),
                title=spec.get('title') or None,
                box=richbox.ROUNDED,
            ))
            sub_layouts.append(child)
        if orientation == 'row':
            lay.split_row(*sub_layouts)
        else:
            lay.split_column(*sub_layouts)
        return lay

    console = Console(no_color=no_color, width=w if w else None)
    layout = _build_layout()

    if frames == 1 or not sys.stdout.isatty():
        if title:
            console.rule(title)
        console.print(layout)
        if panel_failures:
            print(f'ERROR:render: {len(panel_failures)} panel(s) failed: {panel_failures}',
                  file=sys.stderr)
            sys.exit(4)
        return

    import time

    from rich.live import Live
    refresh = float(d.get('refresh_per_second', 4))
    frame_delay = 1.0 / max(1.0, refresh)
    with Live(layout, refresh_per_second=refresh, console=console, transient=False):
        for _ in range(frames):
            layout = _build_layout()
            time.sleep(frame_delay)
    if panel_failures:
        print(f'ERROR:render: {len(panel_failures)} panel(s) failed: {panel_failures}',
              file=sys.stderr)
        sys.exit(4)


def confusion(d, title, w, h, theme, **kw):
    """plotext ML confusion matrix.
    actual/predicted must be lists of class labels (int or str).
    """
    import plotext as plt
    actual_raw, predicted_raw = d['actual'], d['predicted']
    # plotext treats string xticks as dates and rejects them with a
    # %d/%m/%Y validation error. Map string labels to int indices and
    # synthesize a labels=[...] list so the user sees the original strings.
    if any(isinstance(v, str) for v in actual_raw) or any(isinstance(v, str) for v in predicted_raw):
        labels_in = d.get('labels') or sorted({str(v) for v in (*actual_raw, *predicted_raw)})
        index = {v: i for i, v in enumerate(labels_in)}
        actual = [index[str(v)] for v in actual_raw]
        predicted = [index[str(v)] for v in predicted_raw]
        labels = labels_in
    else:
        actual, predicted, labels = actual_raw, predicted_raw, d.get('labels')
    try:
        plt.confusion_matrix(actual, predicted, labels=labels)
    except ZeroDivisionError:  # plotext bug: M==m when all matrix cells are equal
        from collections import Counter

        from rich.console import Console
        from rich.table import Table
        actual, predicted = d['actual'], d['predicted']
        labs = d.get('labels') or sorted(set(actual) | set(predicted))
        counts = Counter(zip(actual, predicted, strict=False))
        t = Table(title=title or 'Confusion Matrix')
        t.add_column('actual \\ predicted')
        for p in labs:
            t.add_column(str(p))
        for a in labs:
            t.add_row(str(a), *[str(counts.get((a, p), 0)) for p in labs])
        Console().print(t)
        return
    _plt_finalize(plt, title, w, h, theme, kw)


def banner(d, title, w, h, theme, **kw):
    """pyfiglet large ASCII art text banner."""
    import pyfiglet
    text = d.get('text', title or 'BANNER')
    font = d.get('font', 'big')
    result = pyfiglet.figlet_format(text, font=font, width=d.get('width', w))
    color = d.get('color')
    if color and not kw.get('no_color'):
        from rich.console import Console
        Console().print(f'[{color}]{result}[/{color}]', end='')
    else:
        print(result, end='')


def art_command(d, title, w, h, theme, **kw):
    """Composable text art command (argparse dispatch only)."""
    del d, title
    from cli_charts.render.art_engine import list_decors, list_fonts, render_art
    if kw.get('list_fonts'):
        list_fonts()
        sys.exit(0)
    if kw.get('list_decors'):
        list_decors()
        sys.exit(0)
    rc = render_art(
        kw.get('text', ''),
        kw.get('font', 'slant'),
        kw.get('decor'),
        kw.get('frame'),
        kw.get('gradient'),
        theme,
        w,
        h,
        kw.get('no_color', False),
        kw.get('output', ''),
        kw.get('justify'),
        kw.get('anim', False),
    )
    sys.exit(rc)


def diagram(d, title, w, h, theme, **kw):
    """Diagon-compatible structural diagram renderer."""
    del theme
    from cli_charts.render.diagram_engine import render_diagram

    if isinstance(d, dict):
        kind = kw.get('diagram_kind') or d.get('kind') or d.get('type')
        text = d.get('text') or d.get('source') or d.get('data') or ''
    else:
        kind = kw.get('diagram_kind')
        text = str(d)
    if not kind:
        raise ValueError('diagram needs a kind such as sequence/tree/table/flowchart/math')
    rc = render_diagram(
        kind,
        text,
        width=w,
        output=kw.get('output') or None,
        engine=kw.get('diagram_engine', 'auto'),
    )
    if rc:
        sys.exit(rc)
    if title and kw.get('statusline'):
        _render_statusline('diagram', {'label': title, 'value': 1}, title)


def mermaid(d, title, w, h, theme, **kw):
    """beautiful-mermaid-inspired Mermaid renderer for chat-safe diagrams."""
    del h, theme
    from cli_charts.render.mermaid_engine import render_mermaid

    source = d.get('source') or d.get('text') or d.get('data') if isinstance(d, dict) else str(d)
    print(render_mermaid(
        source,
        width=w,
        use_ascii=bool(kw.get('mermaid_ascii')),
        padding_x=int(kw.get('mermaid_padding_x') or 5),
        padding_y=int(kw.get('mermaid_padding_y') or 1),
        box_padding=int(kw.get('mermaid_box_padding') or 1),
        theme=kw.get('mermaid_theme') or 'zinc-dark',
    ), end="")


def plotext(d, title, w, h, theme, **kw):
    """plotext overlay renderer: error bars, date plots, text, lines, shapes."""
    from cli_charts.render.plotextx_engine import render_plotextx

    return render_plotextx(
        d,
        title=title,
        width=w,
        height=h,
        theme=theme,
        xlabel=kw.get('xlabel', ''),
        ylabel=kw.get('ylabel', ''),
        xlim=kw.get('xlim'),
        ylim=kw.get('ylim'),
        xscale=kw.get('xscale', 'linear'),
        yscale=kw.get('yscale', 'linear'),
        orientation=kw.get('orientation', 'vertical'),
        no_color=kw.get('no_color', False),
    )


def incplot(d, title, w, h, theme, **kw):
    """incplot-style auto renderer for JSON, JSONL, CSV, and TSV."""
    from cli_charts.render.incplot_engine import detect_incplot

    detected = detect_incplot(d, kw.get('prefer', ''))
    nested_kw = dict(kw)
    nested_kw.pop('prefer', None)
    return CMDS[detected.chart_type](detected.data, title, w, h, theme, **nested_kw)


def textplot(d, title, w, h, theme, **kw):
    """textplots-rs-style continuous function plot on a Braille canvas."""
    del theme, kw
    from cli_charts.render.braille_engine import render_textplot

    print(render_textplot(d, title=title, width=w, height=h), end="")


def turtle(d, title, w, h, theme, **kw):
    """drawille-style Turtle/Canvas renderer backed by Braille cells."""
    del theme, kw
    from cli_charts.render.braille_engine import render_turtle

    print(render_turtle(d, title=title, width=w, height=h), end="")


def effect(d, title, w, h, theme, **kw):
    """Chat-first visual effect presets composed from the renderer toolbox."""
    del h, theme
    from cli_charts.render.effect_engine import render_effect

    if isinstance(d, dict):
        data = d
        kind = kw.get('effect_kind') or d.get('kind') or d.get('effect') or ''
    else:
        data = {'text': str(d)}
        kind = kw.get('effect_kind') or ''
    print(render_effect(str(kind), data, title=title, width=w), end="")


def uniplot(d, title, w, h, theme, **kw):
    """uniplot scientific line/scatter with labeled axes.
    Same multi-series schema as 'line'. Set "lines":false per series for scatter.
    Respects --xlim, --ylim, --width, --height.
    """
    from uniplot import plot as uplot
    series = d if isinstance(d, list) else [d]
    ys = [s['y'] for s in series]
    xs = [s.get('x', list(range(len(s['y'])))) for s in series]
    labels = [s.get('label', f'S{i}') for i, s in enumerate(series)]
    lines = all(s.get('lines', True) for s in series)
    plot_kw = dict(
        legend_labels=labels,
        lines=lines,
        width=w,
        height=h,
    )
    if title:
        plot_kw['title'] = title
    if kw.get('xlim'):
        plot_kw['x_min'], plot_kw['x_max'] = kw['xlim']
    if kw.get('ylim'):
        plot_kw['y_min'], plot_kw['y_max'] = kw['ylim']
    if len(series) == 1:
        uplot(ys=ys[0], xs=xs[0], **plot_kw)
    else:
        uplot(ys=ys, xs=xs, **plot_kw)


def hires(d, title, w, h, theme, **kw):
    """24-bit colored braille renderer.  Catmull-Rom smooth curves + glow halos.
    Same multi-series schema as 'line'.  Each series accepts optional "color":[r,g,b]
    and "glow":false to disable the halo.
    """
    no_color = kw.get('no_color', False)
    series = d if isinstance(d, list) else [d]

    pw = w * 2 - 4
    ph = h * 4 - 4
    cx0, cy0 = 2, 0

    all_y = [v for s in series for v in s['y']]
    if not all_y:
        return
    y_range = max(all_y) - min(all_y)
    y_min = min(all_y) - y_range * 0.05
    y_max = max(all_y) + y_range * 0.05

    canvas = _HiresCanvas(w, h)

    for idx, s in enumerate(series):
        rgb = tuple(s['color']) if 'color' in s else _HIRES_PALETTE[idx % len(_HIRES_PALETTE)]
        dim = tuple(max(0, c // 5) for c in rgb)
        do_glow = s.get('glow', True) and not no_color
        ys = s['y']
        xs = s.get('x', list(range(len(ys))))
        pts = _catmull_pixels(ys, xs, cx0, cy0, pw, ph, y_min, y_max)
        if do_glow:
            for ox in (-1, 0, 1):
                for oy in (-1, 0, 1):
                    if ox == 0 and oy == 0:
                        continue
                    for px, py in pts:
                        canvas.dot(px + ox, py + oy, dim)
        for px, py in pts:
            canvas.dot(px, py, rgb)

    if title:
        print(title)
    for row in canvas.render(no_color):
        print(row)


def radar(d, title, w, h, theme, **kw):
    """Polar radar/spider chart on a 24-bit braille canvas.
    {"labels":["ATK","DEF","SPD","MGC","LCK"],
     "series":[{"label":"Hero","values":[80,60,90,70,50],"color":[0,245,212]}],
     "max":100}
    'max' defaults to the largest value across all series.
    """
    import math
    no_color = kw.get('no_color', False)
    labels = d['labels']
    series_list = d.get('series', [d])
    n_axes = len(labels)
    if n_axes < 3:
        print('ERROR:schema: radar requires at least 3 labels', file=sys.stderr)
        sys.exit(1)

    pw = w * 2
    ph = h * 4
    canvas = _HiresCanvas(w, h)
    cx = pw // 2
    cy = ph // 2
    r_max = min(cx, cy) - 8

    v_max = d.get('max', max(v for s in series_list for v in s['values']))
    GRID  = (32, 34, 55)
    AXIS  = (50, 52, 80)

    # Concentric rings
    for ring_pct in (0.25, 0.50, 0.75, 1.0):
        r = int(r_max * ring_pct)
        for i in range(n_axes):
            a1 = math.pi / 2 - 2 * math.pi * i / n_axes
            a2 = math.pi / 2 - 2 * math.pi * (i + 1) / n_axes
            x1 = cx + int(r * math.cos(a1))
            y1 = cy - int(r * math.sin(a1))
            x2 = cx + int(r * math.cos(a2))
            y2 = cy - int(r * math.sin(a2))
            canvas.line(x1, y1, x2, y2, GRID)

    # Axis spokes
    spoke_ends = []
    for i in range(n_axes):
        angle = math.pi / 2 - 2 * math.pi * i / n_axes
        ex = cx + int(r_max * math.cos(angle))
        ey = cy - int(r_max * math.sin(angle))
        spoke_ends.append((ex, ey, angle))
        canvas.line(cx, cy, ex, ey, AXIS)

    # Data polygons
    for idx, s in enumerate(series_list):
        vals = s['values']
        rgb = tuple(s['color']) if 'color' in s else _HIRES_PALETTE[idx % len(_HIRES_PALETTE)]
        dim = tuple(max(0, c // 5) for c in rgb)
        pts = []
        for i, v in enumerate(vals):
            pct = min(v / v_max, 1.0)
            angle = math.pi / 2 - 2 * math.pi * i / n_axes
            px = cx + int(r_max * pct * math.cos(angle))
            py = cy - int(r_max * pct * math.sin(angle))
            pts.append((px, py))
        pts.append(pts[0])
        # glow
        if not no_color:
            for j in range(len(pts) - 1):
                for ox in (-1, 0, 1):
                    for oy in (-1, 0, 1):
                        if ox == 0 and oy == 0:
                            continue
                        canvas.line(pts[j][0] + ox, pts[j][1] + oy,
                                    pts[j + 1][0] + ox, pts[j + 1][1] + oy, dim)
        for j in range(len(pts) - 1):
            canvas.line(pts[j][0], pts[j][1], pts[j + 1][0], pts[j + 1][1], rgb)

    if title:
        print(title)
    rows = canvas.render(no_color)
    for row in rows:
        print(row)

    # Print axis labels below chart
    label_line = "  ".join(
        f"\033[38;2;{_HIRES_PALETTE[0][0]};{_HIRES_PALETTE[0][1]};{_HIRES_PALETTE[0][2]}m{lbl}\033[0m"
        if not no_color else lbl
        for lbl in labels
    )
    print(label_line)

    # Legend
    if len(series_list) > 1 or series_list[0].get('label'):
        for idx, s in enumerate(series_list):
            lbl = s.get('label', f'S{idx}')
            rgb = tuple(s['color']) if 'color' in s else _HIRES_PALETTE[idx % len(_HIRES_PALETTE)]
            if no_color:
                print(f"  [{lbl}]")
            else:
                print(f"  \033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m\u2588\u2588 {lbl}\033[0m")


def plotille_chart(d, title, w, h, theme, **kw):
    """plotille Figure: composable braille chart with proper axis labels.
    Same multi-series schema as 'line'.  Each series supports "color":"bright_cyan" etc.
    plotille color names: bright_cyan bright_red bright_yellow bright_green white grey
    """
    try:
        import plotille
    except ImportError:
        print('ERROR:dep: pip install plotille', file=sys.stderr)
        sys.exit(2)

    series = d if isinstance(d, list) else [d]
    fig = plotille.Figure()
    fig.width = w
    fig.height = h
    if kw.get('xlabel'):
        fig.x_label = kw['xlabel']
    if kw.get('ylabel'):
        fig.y_label = kw['ylabel']
    if kw.get('xlim'):
        fig.set_x_limits(*kw['xlim'])
    if kw.get('ylim'):
        fig.set_y_limits(*kw['ylim'])

    colors = ['bright_cyan', 'bright_red', 'bright_yellow', 'bright_green',
              'bright_blue', 'bright_magenta']
    for idx, s in enumerate(series):
        ys = s['y']
        xs = s.get('x', list(range(len(ys))))
        color = s.get('color', colors[idx % len(colors)])
        label = s.get('label', f'S{idx}')
        fig.plot(xs, ys, lc=color, label=label)

    if title:
        print(title)
    print(fig.show(legend=True))


# -- helpers (data) ----------------------------------------------------------

def _lttb(xs: list, ys: list, n: int) -> tuple:
    """Largest-Triangle-Three-Buckets -- shape-preserving time-series downsample.
    Falls back to uniform stride if lttb package is not installed.
    """
    if sys.platform == "win32" and sys.version_info >= (3, 13):
        step = max(1, len(xs) // n)
        return xs[::step][:n], ys[::step][:n]
    try:
        import numpy as np
        from lttb import downsample as _lttb_ds
        data = np.column_stack([xs, ys])
        out = _lttb_ds(data, n)
        return out[:, 0].tolist(), out[:, 1].tolist()
    except ImportError:
        step = max(1, len(xs) // n)
        return xs[::step][:n], ys[::step][:n]


def _sample_indices(length: int, n: int) -> list:
    """Return ordered indices for sampling paired list fields together."""
    if length <= n:
        return list(range(length))
    xs = list(range(length))
    _, sampled = _lttb(xs, xs, n)
    indices = [int(i) for i in sampled]
    return sorted(dict.fromkeys(indices))


def _sample_data(data, n, chart_type=None):
    """Downsample to at most n points with type-aware strategy.

    - line/scatter/step/uniplot : LTTB per series (preserves visual shape)
    - kline/candlestick         : OHLC group aggregation (preserves extremes)
    - others                    : random sample any oversized flat list
    """
    if chart_type in ('line', 'scatter', 'step', 'uniplot'):
        series = data if isinstance(data, list) else [data]
        result = []
        for s in series:
            y = s.get('y', [])
            if len(y) <= n:
                result.append(s)
                continue
            x = s.get('x', list(range(len(y))))
            nx, ny = _lttb(x, y, n)
            result.append({**s, 'x': nx, 'y': ny})
        return result if isinstance(data, list) else result[0]
    if chart_type in ('kline', 'candlestick'):
        dates = data.get('dates', [])
        if len(dates) <= n:
            return data
        step = max(1, len(dates) // n)
        out = {'dates': [], 'open': [], 'high': [], 'low': [], 'close': []}
        for i in range(0, len(dates), step):
            end = min(i + step, len(dates))
            out['dates'].append(data['dates'][i])
            out['open'].append(data['open'][i])
            out['high'].append(max(data['high'][i:end]))
            out['low'].append(min(data['low'][i:end]))
            out['close'].append(data['close'][end - 1])
            if len(out['dates']) >= n:
                break
        return out
    # Generic fallback: random sample oversized lists; recurse into dicts
    if isinstance(data, list) and len(data) > n:
        return random.sample(data, n)
    if isinstance(data, dict):
        list_keys = [k for k, v in data.items() if isinstance(v, list)]
        list_lens = {len(data[k]) for k in list_keys}
        if len(list_keys) >= 2 and len(list_lens) == 1:
            length = next(iter(list_lens))
            if length > n:
                indices = _sample_indices(length, n)
                return {
                    k: ([v[i] for i in indices] if k in list_keys else v)
                    for k, v in data.items()
                }
        return {k: _sample_data(v, n) for k, v in data.items()}
    return data


# -- DuckDB loader -----------------------------------------------------------

def load_duckdb(sql, db_path, chart_type):
    import duckdb
    df = duckdb.connect(db_path).execute(sql).df()
    if chart_type == 'kline':
        col0 = df.columns[0]
        def _coerce_date(val):
            if hasattr(val, 'strftime'):
                return val.strftime('%d/%m/%Y')
            if isinstance(val, str):
                return val
            print(f'ERROR:schema: kline col0 must be date-like, got {type(val).__name__}',
                  file=sys.stderr)
            sys.exit(1)

        dates = [_coerce_date(d) for d in df[col0]]
        return {
            'dates': dates,
            'open':  df['open'].tolist(),
            'high':  df['high'].tolist(),
            'low':   df['low'].tolist(),
            'close': df['close'].tolist(),
        }
    if chart_type in ('line', 'scatter', 'step'):
        col0 = df.columns[0]
        return [{'label': c, 'x': df[col0].tolist(), 'y': df[c].tolist()}
                for c in df.columns[1:]]
    if chart_type in ('bar', 'pie'):
        cols = list(df.columns)
        return {'labels': df[cols[0]].astype(str).tolist(),
                'values': df[cols[1]].tolist()}
    if chart_type == 'table':
        return {'columns': list(df.columns),
                'rows': df.values.tolist()}
    if chart_type == 'hist':
        return [{'label': c, 'values': df[c].tolist()} for c in df.columns]
    if chart_type == 'heatmap':
        return {'matrix': df.values.tolist(),
                'xlabels': list(df.columns),
                'ylabels': list(df.index.astype(str))}
    if chart_type == 'curve':
        cols = list(df.columns)
        return {'points': list(zip(df[cols[0]].tolist(), df[cols[1]].tolist(), strict=False))}
    if chart_type == 'sparkline':
        return {'values': df.iloc[:, 0].tolist()}
    if chart_type == 'confusion':
        cols = list(df.columns)
        return {'actual': df[cols[0]].tolist(), 'predicted': df[cols[1]].tolist()}
    if chart_type == 'uniplot':
        col0 = df.columns[0]
        return [{'label': c, 'x': df[col0].tolist(), 'y': df[c].tolist()}
                for c in df.columns[1:]]
    # dashboard: not supported via DuckDB (composite type); graph: 2-col edge list; others: generic dict
    if chart_type == 'graph':
        cols = list(df.columns)
        return {'edges': list(zip(df[cols[0]].astype(str),
                                  df[cols[1]].astype(str), strict=False))}
    return df.to_dict(orient='list')


# -- registry ----------------------------------------------------------------

def animate_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("animate is dispatched by main()")


def record_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("record is dispatched by main()")


def record_replay_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("record-replay is dispatched by main()")


def to_hyperframes_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("to-hyperframes is dispatched by main()")


def to_ascii_motion_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("to-ascii-motion is dispatched by main()")


def code_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("code is dispatched by main()")


def status_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("status is dispatched by main()")


def splash_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("splash is dispatched by main()")


def demo_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("demo is dispatched by main()")


def gallery_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("gallery is dispatched by main()")


def auto_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("auto is dispatched by main()")


def live_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("live is dispatched by main()")


def doctor_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("doctor is dispatched by main()")


def install_backends_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("install-backends is dispatched by main()")


def fonts_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("fonts is dispatched by main()")


def chat_health_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("chat-health is dispatched by main()")


def wave_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("wave is dispatched by main()")


def serve_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("serve is dispatched by main()")


def formula(d, title, w, h, theme, **kw):
    """Formula source -> compact Unicode math text."""
    from cli_charts.markup import render_formula_panel

    spec = d if isinstance(d, (dict, list, str)) else str(d)
    if title and isinstance(spec, dict) and not spec.get("title"):
        spec = {**spec, "title": title}
    elif title and not isinstance(spec, dict):
        spec = {"title": title, "items": spec if isinstance(spec, list) else [spec]}
    print(render_formula_panel(spec), end="")


def formula_pretty(d, title, w, h, theme, **kw):
    """Formula source -> SymPy terminal pretty-printer."""
    from cli_charts.markup import render_formula_pretty

    spec = d if isinstance(d, (dict, list, str)) else str(d)
    if title and isinstance(spec, dict) and not spec.get("title"):
        spec = {**spec, "title": title}
    elif title and not isinstance(spec, dict):
        spec = {"title": title, "items": spec if isinstance(spec, list) else [spec]}
    print(render_formula_pretty(spec), end="")


def calibrate(d, title, w, h, theme, **kw):
    """Print chat/terminal width calibration rulers."""
    from cli_charts.markup import render_chat_calibration

    spec = d if isinstance(d, dict) else {}
    spec.setdefault("from", kw.get("calibrate_from", 96))
    spec.setdefault("to", kw.get("calibrate_to", 160))
    spec.setdefault("step", kw.get("calibrate_step", 8))
    spec.setdefault("glyph", kw.get("calibrate_glyph", "all"))
    spec.setdefault("terminal", kw.get("terminal", False))
    spec.setdefault("recommend", kw.get("recommend", False))
    print(render_chat_calibration(spec), end="")


CMDS = {
    'kline':      kline,
    'line':       line,
    'scatter':    scatter,
    'step':       step,
    'bar':        bar,
    'hbar':       hbar,
    'pie':        pie,
    'multibar':   multibar,
    'stackedbar': stackedbar,
    'hist':       hist,
    'heatmap':    heatmap,
    'spectrum':   spectrum,
    'waterfall':  waterfall,
    'box':        box,
    'indicator':  indicator,
    'event':      event,
    'confusion':  confusion,
    'sparkline':  sparkline,
    'table':      table,
    'tree':       tree,
    'panel':      panel,
    'gauge':      gauge,
    'dashboard':  dashboard,
    'incplot':    incplot,
    'graph':      graph,
    'diagram':    diagram,
    'formula':    formula,
    'formula-pretty': formula_pretty,
    'math':       formula,
    'math-pretty': formula_pretty,
    'calibrate':  calibrate,
    'mermaid':    mermaid,
    'plotext':    plotext,
    'textplot':   textplot,
    'turtle':     turtle,
    'effect':     effect,
    'curve':      curve,
    'uniplot':    uniplot,
    'banner':      banner,
    'art':         art_command,
    'candlestick': kline,
    'hires':       hires,
    'radar':       radar,
    'plotille':    plotille_chart,
    'rich_live':   rich_live,
    # textcharts types
    'comparison':      comparison,
    'diverging':       diverging,
    'summary':         summary,
    'sparkline-table': sparkline_table,
    'cdf':             cdf_chart,
    'rank':            rank_table,
    'percentile':       percentile,
    'boxplot':         boxplot_comparison,
    'stacked-text':    stacked_bar_text,
    'animate':     animate_command,
    'record':      record_command,
    'record-replay': record_replay_command,
    'to-hyperframes': to_hyperframes_command,
    'to-ascii-motion': to_ascii_motion_command,
    'code':        code_command,
    'status':      status_command,
    'splash':      splash_command,
    'demo':        demo_command,
    'gallery':     gallery_command,
    'auto':        auto_command,
    'live':        live_command,
    'doctor':      doctor_command,
    'install-backends': install_backends_command,
    'fonts':       fonts_command,
    'chat-health': chat_health_command,
    'wave':        wave_command,
    'serve':       serve_command,
}

# Single source of truth for chart-type docs. Order is intentional.
CHART_TYPES_BY_ENGINE: dict[str, list[str]] = {
    'incplot': ['incplot'],
    'plotext': [
        'kline', 'candlestick', 'line', 'scatter', 'step', 'bar', 'hbar', 'multibar',
        'stackedbar', 'hist', 'heatmap', 'box', 'indicator', 'event',
        'confusion', 'plotext',
    ],
    'sdr': ['spectrum', 'waterfall'],
    'rich': ['table', 'tree', 'panel', 'gauge', 'pie', 'dashboard', 'rich_live'],
    'diagram': ['diagram', 'formula', 'formula-pretty', 'math', 'math-pretty', 'mermaid'],
    'drawille': ['curve', 'hires', 'radar', 'textplot', 'turtle'],
    'plotille': ['plotille'],
    'uniplot': ['uniplot'],
    'textcharts': ['comparison', 'diverging', 'summary', 'sparkline-table', 'cdf', 'rank', 'percentile', 'boxplot', 'stacked-text'],
    'misc': ['graph', 'effect', 'sparkline', 'banner', 'art', 'animate', 'record', 'record-replay', 'to-hyperframes', 'to-ascii-motion', 'code', 'status', 'splash', 'demo', 'gallery', 'auto', 'live', 'doctor', 'install-backends', 'fonts', 'chat-health', 'wave', 'calibrate', 'serve'],
    'media': ['image', 'video'],
}

_CHART_TYPE_KEYS = {t for ts in CHART_TYPES_BY_ENGINE.values() for t in ts}
assert _CHART_TYPE_KEYS == set(CMDS) | _MEDIA_TYPES, \
    "CHART_TYPES_BY_ENGINE drift vs CMDS/media types"

CHART_TYPE_COUNT: int = len(_CHART_TYPE_KEYS)

EXPECTED_SCHEMAS = {
    'kline':      '{"dates":["DD/MM/YYYY",...], "open":[...], "high":[...], "low":[...], "close":[...]}',
    'line':       '[{"label":"A","x":[...],"y":[...]}] or {"label":"A","y":[...]}',
    'scatter':    '[{"label":"A","x":[...],"y":[...]}] or {"label":"A","y":[...]}',
    'step':       '[{"label":"A","x":[...],"y":[...]}] or {"label":"A","y":[...]}',
    'bar':        '{"labels":[...], "values":[...]}',
    'pie':        '{"labels":["A","B","C"], "values":[30,50,20]}',
    'multibar':   '{"labels":[...], "series":[{"label":"A","values":[...]}, ...]}',
    'stackedbar': '{"labels":[...], "series":[{"label":"A","values":[...]}, ...]}',
    'hist':       '{"values":[...], "bins":20} or [{"label":"A","values":[...]}, ...]',
    'heatmap':    '{"matrix":[[...]], "xlabels":[...], "ylabels":[...]}',
    'spectrum':   '{"freq":[99.0,...], "power":[-93,...], "center":99.3, "bandwidth":0.2}',
    'waterfall':  '{"matrix":[[...]], "xlabels":["99.0","99.6"], "ylabels":["t-1","now"], "min":-94, "max":-42}',
    'box':        '{"data":[[s1_vals],[s2_vals],...], "labels":["A","B",...]}',
    'indicator':  '{"value":23.4, "label":"Total Return %"}',
    'event':      '{"data":[x1,x2,...]}',
    'confusion':  '{"actual":[0,1,2,0], "predicted":[0,2,1,0], "labels":["Cat","Dog","Bird"]}',
    'sparkline':  '{"values":[1,3,5,2,8,4,6]}',
    'table':      '{"columns":[...], "rows":[[...], ...]}',
    'tree':       '{"label":"root","children":[{"label":"A","children":[...]}]}',
    'panel':      '{"content":"text here", "title":"optional", "box":"ROUNDED"}',
    'gauge':      '[{"label":"CPU","value":75,"max":100,"color":"red"}, ...] or {"metrics":[...]}',
    'dashboard':  '{"panels":[{"type":"gauge","data":{"label":"CPU","value":72,"max":100},"title":"CPU"},{"type":"sparkline","data":{"values":[1,3,5,2,8]},"title":"Load"}]}',
    'incplot':    'Raw JSON/JSONL/CSV/TSV auto plot. Supports prefer=bar|multibar|stackedbar|line|scatter|hist|table|kline via --prefer.',
    'graph':      '{"edges":[["A","B"],...], "directed":true, "node_style":"ROUND"}',
    'diagram':    'glyph-arts diagram sequence --json "Alice->Bob: Hello" or {"kind":"flowchart","text":"A -> B"}',
    'formula':    'Raw formula text or {"items":["E = mc^2", "\\\\int exp(-x^2) dx"]}; emits compact Unicode math',
    'formula-pretty': 'Raw formula text or {"items":["(a+b)/(c+d)", "Integral(exp(-x^2), x)"]}; emits SymPy multi-line math',
    'calibrate':  'glyph-arts chat calibrate --terminal --calibrate-glyph braille',
    'mermaid':    'Mermaid source text: graph/flowchart, sequenceDiagram, stateDiagram-v2, classDiagram, erDiagram, xychart-beta',
    'plotext':    '{"series":[{"type":"line|scatter|error|bar|hist|candlestick","x":[...],"y":[...]}],"texts":[...],"vlines":[...],"hlines":[...],"shapes":[...]}',
    'effect':     'glyph-arts effect gallery|pipeline|metrics|system-map|signal-panel|timeline|matrix|comparison|swimlane|kanban|quadrant|mindmap',
    'curve':      '{"points":[[x,y],...]}',
    'uniplot':    '[{"label":"A","x":[...],"y":[...]}] or {"label":"A","y":[...]}',
    'banner':      '{"text":"PROFIT","font":"big","color":"green"}',
    'art':         'glyph-arts art TEXT --font slant --decor barcode --frame double --gradient sunset',
    'candlestick': '{"dates":["DD/MM/YYYY",...], "open":[...], "high":[...], "low":[...], "close":[...]}',
    'hires':       '[{"label":"Q5","y":[3.5,9.2,9.4],"color":[0,245,212]},{"label":"Q1","y":[3.1,5.1,4.5],"color":[255,107,107]}]',
    'radar':       '{"labels":["ATK","DEF","SPD","MGC","LCK"],"series":[{"label":"Hero","values":[80,60,90,70,50],"color":[0,245,212]}],"max":100}',
    'textplot':    '{"expr":"sin(x) / x","xmin":-20,"xmax":20} or trailing expression text',
    'turtle':      '{"commands":[["forward",30],["right",90],["forward",30]]}',
    'plotille':    '[{"label":"A","x":[1,2,3,4],"y":[2,4,3,6],"color":"bright_cyan"}]',
    'rich_live':   '{"panels":[{"type":"bar","title":"Left","data":{"labels":["A","B"],"values":[1,2]}},{"type":"sparkline","title":"Right","data":{"values":[1,3,5,2,8]}}],"layout":"row","frames":1}',
    'animate':     'glyph-arts animate line --duration 5 --frames 30 --json \'[{"label":"DAU","x":[...],"y":[...]}]\'',
    'record':      "glyph-arts record demo.cast --cmd 'echo hi' --duration 1",
    'record-replay': 'glyph-arts record-replay demo.cast --output demo.gif',
    'to-hyperframes': "glyph-arts to-hyperframes --json '[{\"label\":\"x\",\"x\":[1,2],\"y\":[3,4]}]' --frames 30 --duration 5 --output-dir ./hf",
    'to-ascii-motion': "glyph-arts to-ascii-motion --json '[{\"label\":\"x\",\"x\":[1,2],\"y\":[3,4]}]' --formats html,mp4,svg --output-dir ./out",
    'code':        'glyph-arts code --file foo.py --lang python',
    'status':      'glyph-arts status --kind ok --message "All tests green"',
    'splash':      'glyph-arts splash',
    'demo':        'glyph-arts demo --speed fast',
    'gallery':     'glyph-arts gallery --output gallery.html',
    'auto':        "glyph-arts auto --json '[1,2,3]'",
    'live':        'glyph-arts live random --duration 10 --interval 0.2',
    'doctor':      'glyph-arts doctor',
    'install-backends': 'glyph-arts install-backends --target all [--run --yes]',
    'fonts':       'glyph-arts fonts install core',
    'chat-health': 'glyph-arts chat probe',
    'wave':        'glyph-arts wave render bar --json \'{"labels":["A"],"values":[3]}\'',
}

# Types where --width/--height/--theme have no effect
_NO_SIZE_THEME = {'table', 'tree', 'panel', 'graph', 'sparkline', 'gauge', 'banner', 'pie', 'dashboard', 'rich_live'}

PIXEL_SUPPORTED = frozenset({'bar', 'line', 'scatter'})
INTERACTIVE_SUPPORTED = frozenset({'line'})
_GLYPH_VISUAL_STYLES = {
    'auto',
    'ascii',
    'unicode',
    'braille',
    'block',
    'shade',
    'bar',
    'half-circle',
    'full-circle',
}
_DEPENDENCY_CORE = [
    'plotext',
    'rich',
    'uniplot',
    'pyfiglet',
    'sparklines',
    'duckdb',
    'pandas',
    'networkx',
    'phart',
]
_DEPENDENCY_MEDIA = (
    ('chafa', 'image/video high-fidelity render'),
    ('ffmpeg', 'video frame extract'),
    ('diagon', 'math/sequence/tree/flowchart diagrams'),
)
_DEPENDENCY_OPTIONAL = (
    ('PIL', 'image text fallback', 'Pillow'),
    ('drawille', 'curve chart', 'glyph-arts[braille]'),
    ('lttb', 'LTTB sampling', 'glyph-arts[lttb]'),
    ('textual', 'dashboard TUI', 'glyph-arts[tui]'),
)


def _build_cli_epilog():
    epilog_lines = [f'Chart types ({CHART_TYPE_COUNT}):']
    for engine, types in CHART_TYPES_BY_ENGINE.items():
        epilog_lines.append(f'  {engine:9}: {" ".join(types)}')
    epilog_lines.append("""
Examples:
  python chart.py kline --json '{"dates":["07/04/2026"],"open":[100],"high":[102],"low":[99],"close":[101]}'
  python chart.py scatter --json '[{"label":"A","x":[1,2,3],"y":[4,2,5]}]'
  python chart.py hist --json '{"values":[1,2,2,3,3,3,4,4,5],"bins":5}'
  python chart.py heatmap --json '{"matrix":[[1,2],[3,4]],"xlabels":["A","B"],"ylabels":["X","Y"]}'
  python chart.py spectrum --json '{"freq":[99.0,99.3,99.6],"power":[-93,-42,-93],"center":99.3,"bandwidth":0.2}'
  python chart.py waterfall --json '{"matrix":[[0,3,8,3,0],[0,2,9,4,0]],"xlabels":["99.0","99.6"],"ylabels":["t-1","now"]}'
  python chart.py diagram sequence --json 'Alice->Bob: Hello'
  python chart.py chat mermaid --json 'graph LR\nA[Start] --> B[Done]'
  python chart.py chat effects
  python chart.py effect signal-panel
  python chart.py chat image --file photo.jpg --width 80 --height 30
  python chart.py chat sequence --json 'Alice->Bob: Hello'
  python chart.py chat sdr spectrum --json '{"freq":[99.0,99.3,99.6],"power":[-93,-42,-93]}'
  python chart.py box --json '{"data":[[1,2,3,4,5],[2,3,4,5,6]],"labels":["A","B"]}'
  python chart.py sparkline --json '{"values":[1,3,5,2,8,4,6]}'
  python chart.py indicator --json '{"value":23.4,"label":"Total Return %"}'
  python chart.py confusion --json '{"actual":[0,1,2,0,1,2],"predicted":[0,2,2,0,0,1],"labels":["Cat","Dog","Bird"]}'
  python chart.py gauge --json '[{"label":"CPU","value":72,"max":100},{"label":"RAM","value":14,"max":32}]'
  python chart.py banner --json '{"text":"PROFIT","font":"big","color":"green"}'
  python chart.py uniplot --json '[{"label":"A","x":[1,2,3,4],"y":[2,4,3,6]},{"label":"B","y":[1,3,2,5]}]'
  python chart.py tree --json '{"label":"root","children":[{"label":"A"},{"label":"B","children":[{"label":"C"}]}]}'
  python chart.py panel --json '{"content":"Hello world","title":"Info","box":"ROUNDED"}'
  python chart.py multibar --json '{"labels":["Q1","Q2"],"series":[{"label":"Rev","values":[10,12]},{"label":"Cost","values":[8,9]}]}'
  python chart.py event --json '{"data":[1,3,5,8,13]}'
  python chart.py line --duckdb "SELECT trade_date, close FROM stock_daily LIMIT 60" --db /path/to/data.duckdb
  cat data.json | python chart.py line
""")
    return '\n'.join(epilog_lines)


def _print_dependency_status(include_optional=False):
    print('[core]')
    for pkg in _DEPENDENCY_CORE:
        try:
            __import__(pkg)
            status = 'OK'
        except ImportError:
            status = 'MISSING'
        print(f'  {pkg:<13} {status}')
    print('[media]')
    for tool, purpose in _DEPENDENCY_MEDIA:
        status = 'OK' if shutil.which(tool) else 'MISSING'
        print(f'  {tool:<13} {status}  ({purpose})')
    if include_optional:
        print('[optional]')
        for pkg, purpose, install in _DEPENDENCY_OPTIONAL:
            try:
                __import__(pkg)
                status = 'OK'
                hint = ''
            except ImportError:
                status = 'MISSING'
                hint = f'  -> pip install {install}'
            print(f'  {pkg:<13} {status}  ({purpose}){hint}')


def _print_style_list():
    print('Available styles per chart type:\n')
    for ctype in sorted(STYLE_ROUTES):
        engines = STYLE_ROUTES[ctype]
        parts = [f'{s} ({eng})' for s, eng in engines.items()]
        print(f'  {ctype:<12} {", ".join(parts)}')
    print(f'\nDefault style: {DEFAULT_STYLE}')
    print('Override: --style <name> or GLYPH_ARTS_STYLE=<name>')


def _handle_pre_parse_flags(raw_argv):
    if '--check-deps' in raw_argv:
        _print_dependency_status(include_optional='--all' in raw_argv)
        return True
    if '--list-styles' in raw_argv:
        _print_style_list()
        return True
    return False


def _apply_font_and_style_defaults(args):
    if args.font_tier is None:
        args.font_tier = detect_font_tier()
    if args.chat_profile != 'auto':
        from cli_charts.chat_health import chat_profile_tier

        args.font_tier = chat_profile_tier(args.chat_profile, args.font_tier)
        if args.chat_profile == 'ascii':
            args.no_color = True

    if args.style is None:
        env_style = os.environ.get('GLYPH_ARTS_STYLE', '').strip().lower()
        if env_style and env_style in _STYLES:
            args.style = env_style


def _load_ascii_motion_adapter():
    try:
        adapter = importlib.import_module("cli_charts.adapters.ascii_motion")
        client = importlib.import_module("cli_charts.mcp_clients.ascii_motion")
    except ImportError:
        print("error: --polish ascii-motion requires 'pip install glyph-arts[ai-motion]'", file=sys.stderr)
        sys.exit(2)
    if getattr(client, "ClientSession", None) is None:
        print("error: --polish ascii-motion requires 'pip install glyph-arts[ai-motion]'", file=sys.stderr)
        sys.exit(2)
    return adapter


def _require_ascii_motion_npx():
    npx = shutil.which("npx") or shutil.which("npx.cmd") or "npx"
    try:
        result = subprocess.run([npx, "ascii-motion-mcp", "--version"], capture_output=True, text=True)
    except FileNotFoundError:
        print("error: ascii-motion-mcp not found; install via 'npm i -g ascii-motion-mcp'", file=sys.stderr)
        sys.exit(3)
    if result.returncode != 0:
        print("error: ascii-motion-mcp not found; install via 'npm i -g ascii-motion-mcp'", file=sys.stderr)
        sys.exit(3)


def _render_ascii_motion_frames(chart_type, data, args, adapter, no_color=False):
    if chart_type not in CMDS or chart_type in {
        'animate', 'record', 'record-replay', 'to-hyperframes', 'to-ascii-motion',
    'code', 'status', 'splash', 'demo', 'gallery', 'auto', 'live', 'doctor', 'install-backends', 'fonts', 'chat-health', 'wave',
    }:
        print('ERROR:schema: to-ascii-motion needs a renderable chart type argument', file=sys.stderr)
        sys.exit(1)
    kw = dict(
        xlabel=args.xlabel,
        ylabel=args.ylabel,
        xlim=args.xlim,
        ylim=args.ylim,
        xscale=args.xscale,
        yscale=args.yscale,
        orientation=args.orientation,
        output='',
        no_color=no_color,
        font_tier=args.font_tier,
        marker=args.marker if chart_type == 'scatter' else None,
        symbol_set=args.symbols if chart_type == 'bar' else None,
        candle_style=args.candle_style if chart_type == 'kline' else 'default',
        gauge_style=args.gauge_style if chart_type == 'gauge' else 'bar',
    )
    text = _capture_stdout(lambda: CMDS[chart_type](data, args.title, args.width, args.height, args.theme, **kw))
    return [adapter.text_to_cells(text)]


def main(argv=None):
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    raw_argv = _rewrite_chat_argv(raw_argv)
    raw_argv = _rewrite_diagram_argv(raw_argv)
    epilog = _build_cli_epilog()
    p = argparse.ArgumentParser(
        description='glyph-arts -- terminal-visible charts and chat drawing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog)
    p.add_argument('type', choices=list(CMDS) + sorted(_MEDIA_TYPES), metavar='TYPE',
                   help='Chart type, or use `chat TYPE ...` for chat-safe drawing: ' + ' | '.join(CMDS) +
                        ' | image | video (media via Pillow/chafa/ffmpeg)')
    p.add_argument('art_text', nargs='*',
                   help='Text for TYPE=art (example: glyph-arts art SHIP IT)')
    p.add_argument('--json',        dest='data', help='JSON data string')
    p.add_argument('--file',        metavar='PATH',
                   help='Read JSON from a file path')
    p.add_argument('--duckdb',      metavar='SQL',
                   help='SQL query against a DuckDB database')
    p.add_argument('--db',          default=None,
                   help='DuckDB file path (required with --duckdb)')
    p.add_argument('--title',       default='')
    p.add_argument('--width',       type=int,
                   default=shutil.get_terminal_size((70, 20)).columns,
                   help='Chart width in terminal columns (ignored for table/tree/panel/graph/sparkline)')
    p.add_argument('--height',      type=int, default=20,
                   help='Chart height in terminal rows (ignored for table/tree/panel/graph/sparkline)')
    p.add_argument('--theme',       default='pro',
                   help='plotext theme: pro dark clear matrix retro elegant + brand palettes: claude linear tesla vercel (ignored for rich/graph/sparkline)')
    p.add_argument('--font-tier',   choices=['ascii', 'unicode', 'unicode-extended', 'nerd'],
                   default=None, help='Terminal font capability tier (default: auto-detect)')
    p.add_argument('--chat-profile', choices=['auto', 'ascii', 'safe', 'rich', 'max'],
                   default='auto', help='Chat glyph profile: auto, ascii, safe, rich, or max')
    p.add_argument('--font',        default='slant',
                   help='TYPE=art figlet font (default: slant). Use --list-fonts to see all.')
    p.add_argument('--decor',       default=None,
                   help='TYPE=art optional decoration (barcode/snake/dna/wave + 200+ from art lib). Use --list-decors to see all.')
    p.add_argument('--frame',       choices=['single', 'double', 'rounded', 'ascii', 'heavy', 'none'],
                   default=None, help='TYPE=art optional Rich frame')
    p.add_argument('--gradient',    choices=['sunset', 'viridis', 'ocean', 'rainbow', 'none'],
                   default=None, help='TYPE=art optional text gradient')
    p.add_argument('--justify',     choices=['left', 'center', 'right'],
                   default=None, help='TYPE=art figlet text alignment')
    p.add_argument('--anim',        action='store_true',
                   help='TYPE=art animation mode (requires art library; pip install glyph-arts[art])')
    p.add_argument('--list-fonts',  action='store_true',
                   help='TYPE=art: list all available figlet fonts')
    p.add_argument('--list-decors', action='store_true',
                   help='TYPE=art: list all available decorations')
    p.add_argument('--engine',      choices=['ascii', 'pixel', 'interactive'], default='ascii',
                   help='Render backend. ascii (default) = plotext/rich/drawille text art. '
                        'pixel = matplotlib + chafa true-color pixel chart (requires '
                        '`pip install glyph-arts[pixel]` + chafa system binary). '
                        'Phase A pixel support: bar/line/scatter only. '
                        'interactive = Textual keyboard-first TUI for line charts '
                        '(requires `pip install glyph-arts[interactive]`).')
    add_media_arguments(p)
    p.add_argument('--art', choices=['low', 'default', 'high'], default='default',
                   help='Visual fidelity tier (only with --engine pixel). low=block(compat). default=vhalf(btop-style). high=sextant(max resolution).')
    p.add_argument('--xlabel',      default='', help='X-axis label (plotext charts)')
    p.add_argument('--ylabel',      default='', help='Y-axis label (plotext charts)')
    p.add_argument('--xlim',        nargs=2, type=float, metavar=('MIN', 'MAX'),
                   help='X-axis limits')
    p.add_argument('--ylim',        nargs=2, type=float, metavar=('MIN', 'MAX'),
                   help='Y-axis limits')
    p.add_argument('--xscale',      choices=['linear', 'log'], default='linear')
    p.add_argument('--yscale',      choices=['linear', 'log'], default='linear')
    p.add_argument('--orientation', choices=['vertical', 'horizontal'],
                   default='vertical', help='Bar orientation (bar/multibar/stackedbar)')
    p.add_argument('--output',      default='',
                   help='Save chart to file (.png with pixel engine; .txt/.ansi/.html with ascii engine; .md for table)')
    p.add_argument('--format',      default=None,
                   help="Output format (reserved for future use)")
    p.add_argument('--output-dir',  default='',
                   help='TYPE=to-hyperframes/to-ascii-motion output directory')
    p.add_argument('--out-dir',     dest='output_dir',
                   help='Alias for --output-dir')
    p.add_argument('--formats',     default='html',
                   help='TYPE=to-ascii-motion comma-separated exports (html,mp4,gif,react,svg)')
    p.add_argument('--polish',      choices=['ascii-motion'], default='',
                   help='Route rendered chart through ASCII Motion polish')
    p.add_argument('--polish-style', default='retro',
                   help='ASCII Motion polish style (terminal, retro, matrix, minimalist, detailed, colorful)')
    p.add_argument('--cmd',         default='',
                   help='TYPE=record command to run inside asciinema')
    p.add_argument('--no-color',    action='store_true',
                   help='Disable ANSI colors (respects NO_COLOR env var)')
    p.add_argument('--marker',      choices=list(_MARKER_SYMBOLS), default=None,
                   help='TYPE=scatter marker symbol set')
    p.add_argument('--symbols',     default=None, metavar='SET',
                   help='TYPE=bar symbol set (block, progress, braille, arrows); '
                        'image symbols (ascii, shade, block, half) or chafa --symbols value; '
                        'video chafa --symbols value')
    p.add_argument('--candle-style', choices=['default', 'geom'], default='default',
                   help='TYPE=kline candle glyph style')
    p.add_argument('--gauge-style', choices=['bar', 'half-circle', 'full-circle', 'braille'],
                   default='bar', help='TYPE=gauge glyph style')
    p.add_argument('--style',       choices=sorted(set(_STYLES) | _GLYPH_VISUAL_STYLES),
                   default=None, help='Rendering style. Supports global style routing plus legacy glyph styles.')
    p.add_argument('--list-styles', action='store_true',
                   help='Show available styles for each chart type and exit')
    p.add_argument('--prefer',      choices=['sparkline', 'bar', 'multibar', 'stackedbar', 'line', 'scatter', 'hist', 'table', 'kline', 'candlestick'], default='',
                   help='TYPE=auto/incplot chart preference override')
    p.add_argument('--calibrate-from', dest='calibrate_from', type=int, default=96,
                   help='TYPE=calibrate starting ruler width')
    p.add_argument('--calibrate-to', dest='calibrate_to', type=int, default=160,
                   help='TYPE=calibrate ending ruler width')
    p.add_argument('--calibrate-step', dest='calibrate_step', type=int, default=8,
                   help='TYPE=calibrate ruler width step')
    p.add_argument('--calibrate-glyph', choices=['all', 'ascii', 'digits', 'braille', 'solid', 'mixed'], default='all',
                   help='TYPE=calibrate glyph family to print')
    p.add_argument('--terminal', action='store_true',
                   help='TYPE=calibrate measure current terminal columns')
    p.add_argument('--recommend', action='store_true',
                   help='TYPE=calibrate print preset recommendation rules')
    p.add_argument('--diagram-kind', choices=['math', 'sequence', 'tree', 'table', 'frame', 'box', 'note', 'flowchart', 'graphdag', 'dag', 'graphplanar', 'planar'],
                   default='', help='TYPE=diagram generator override')
    p.add_argument('--diagram-engine', choices=['auto', 'diagon', 'builtin'], default='auto',
                   help='TYPE=diagram backend. auto uses Diagon when installed, else builtin fallback.')
    p.add_argument('--mermaid-theme', choices=[
        'zinc-light', 'zinc-dark', 'tokyo-night', 'tokyo-night-storm',
        'tokyo-night-light', 'catppuccin-mocha', 'catppuccin-latte', 'nord',
        'nord-light', 'dracula', 'github-light', 'github-dark',
        'solarized-light', 'solarized-dark', 'one-dark',
    ], default='zinc-dark', help='TYPE=mermaid beautiful-mermaid-compatible theme name')
    p.add_argument('--mermaid-ascii', action='store_true',
                   help='TYPE=mermaid use ASCII connectors instead of Unicode')
    p.add_argument('--mermaid-padding-x', type=int, default=5,
                   help='TYPE=mermaid horizontal spacing between nodes')
    p.add_argument('--mermaid-padding-y', type=int, default=1,
                   help='TYPE=mermaid vertical spacing between nodes')
    p.add_argument('--mermaid-box-padding', type=int, default=1,
                   help='TYPE=mermaid node inner padding')
    p.add_argument('--graph-format', choices=['auto', 'json', 'edges', 'dot', 'graphml'], default='auto',
                   help='TYPE=graph input format override')
    p.add_argument('--graph-style', choices=['minimal', 'square', 'round', 'diamond'], default='round',
                   help='TYPE=graph PHART node style')
    p.add_argument('--graph-charset', choices=['unicode', 'ascii'], default='unicode',
                   help='TYPE=graph PHART character set')
    p.add_argument('--graph-node-spacing', type=int, default=4,
                   help='TYPE=graph horizontal node spacing')
    p.add_argument('--graph-layer-spacing', type=int, default=2,
                   help='TYPE=graph vertical layer spacing')
    p.add_argument('--effect-kind', choices=['gallery', 'pipeline', 'metrics', 'system-status', 'system-map', 'signal-panel', 'timeline', 'matrix', 'comparison', 'swimlane', 'kanban', 'quadrant', 'mindmap'],
                   default='', help='TYPE=effect preset override')
    p.add_argument('--fps',         type=int, default=12, metavar='N',
                   help='Video playback frames/sec for type=video (default: 12)')
    p.add_argument('--version',     action=_LazyVersionAction, help='Show glyph-arts version and exit')
    p.add_argument('--check-deps',  action='store_true',
                   help='Print dependency availability table and exit')
    p.add_argument('--all',         action='store_true',
                   help='With --check-deps: also show optional deps (braille/lttb/tui)')
    p.add_argument('--sample',      type=int, default=0, metavar='N',
                   help='Downsample any list longer than N in the input data')
    p.add_argument('--animate',    action='store_true',
                   help='Read stdin line-by-line and re-render chart after each value')
    p.add_argument('--refresh',    type=int, default=10, metavar='FPS',
                   help='Animation refresh rate in frames/sec (default: 10)')
    p.add_argument('--window',     type=int, default=50,  metavar='N',
                   help='Keep last N data points in view (0=unlimited, default: 50)')
    p.add_argument('--duration',   type=float, default=0, metavar='SEC',
                   help='Auto-stop after SEC seconds (0=until EOF/Ctrl-C)')
    p.add_argument('--interval',   type=float, default=0.2, metavar='SEC',
                   help='TYPE=live update interval in seconds (default: 0.2)')
    p.add_argument('--frames',     type=int, default=30, metavar='N',
                   help='TYPE=animate frame count (default: 30)')
    p.add_argument('--spinner',    default='',
                   help='TYPE=animate/status Rich spinner preset (dots, dots2, line, pong, ...)')
    p.add_argument('--rich-progress', action='store_true',
                   help='TYPE=gauge render with rich.progress Progress')
    p.add_argument('--lang',       default='',
                   help='TYPE=code syntax language (python, javascript, ...)')
    p.add_argument('--kind',       default='info',
                   help='TYPE=status kind: ok, warn, error, info, loading')
    p.add_argument('--message',    default='',
                   help='TYPE=status message text')
    p.add_argument('--link-data',  default='',
                   help='OSC 8 hyperlink URL for line/scatter data labels')
    p.add_argument('--link-title', default='',
                   help='OSC 8 hyperlink URL for the chart title')
    p.add_argument('--statusline', action='store_true',
                   help='Single-line ANSI-safe output for Claude Code statusLine.command')
    p.add_argument('--no-splash',  action='store_true',
                   help='Skip the first-run mascot splash')
    p.add_argument('--speed', choices=['fast', 'normal', 'slow'], default='normal',
                   help='TYPE=demo speed: fast=10s, normal=30s, slow=60s')
    p.add_argument('--no-clear', action='store_true',
                   help='TYPE=demo do not clear the terminal between sections')
    p.add_argument('--demo', action='store_true',
                   help='TYPE=dashboard use built-in dashboard demo')
    p.add_argument('--no-interactive', action='store_true',
                   help='TYPE=dashboard render static Rich dashboard instead of Textual TUI')
    p.add_argument('--chart', default='',
                   help='TYPE=gallery pre-select chart type')
    p.add_argument(
        '--target',
        choices=['all', 'chat', 'media', 'fonts', 'diagrams'],
        default='all',
        help='TYPE=install-backends install target',
    )
    p.add_argument(
        '--manager',
        choices=[
            'auto', 'download', 'scoop', 'choco', 'winget', 'brew', 'apt-get',
            'dnf', 'pacman', 'snap', 'x-cmd',
        ],
        default='auto',
        help='TYPE=install-backends package manager override',
    )
    p.add_argument('--run', action='store_true',
                   help='TYPE=install-backends execute the generated install commands')
    p.add_argument('--yes', action='store_true',
                   help='TYPE=install-backends confirm execution when used with --run')
    p.add_argument('--fix-chat', action='store_true',
                   help='TYPE=doctor print chat glyph/font remediation plan')
    p.add_argument('--font-dir', default='',
                   help='TYPE=fonts download/status directory (default: ~/.glyph-arts/fonts)')
    p.add_argument('--dry-run', action='store_true',
                   help='TYPE=wave print planned chart/wsh commands without running them')
    p.add_argument('--wave-format', choices=['html', 'txt', 'ansi'], default='html',
                   help='TYPE=wave render export format for wave render')
    p.add_argument('--wave-stdout', action='store_true',
                   help='TYPE=wave render also print the generated preview file')
    p.add_argument('--stdio', action='store_true',
                   help='TYPE=serve read newline-delimited JSON requests from stdin')
    if _handle_pre_parse_flags(raw_argv):
        sys.exit(0)

    args = p.parse_args(raw_argv)
    if args.type == 'serve':
        if not args.stdio:
            print('ERROR:schema: serve currently requires --stdio', file=sys.stderr)
            sys.exit(1)
        from cli_charts.serve_stdio import run_stdio_server

        sys.exit(run_stdio_server(main))

    _apply_font_and_style_defaults(args)

    if args.type == 'doctor':
        from cli_charts.installers import render_doctor
        print(render_doctor(fix_chat=args.fix_chat), end='')
        sys.exit(0)

    if args.type == 'install-backends':
        from cli_charts.installers import render_install_plan, run_install_plan
        manager = '' if args.manager == 'auto' else args.manager
        if args.run:
            sys.exit(run_install_plan(args.target, manager, yes=args.yes))
        print(render_install_plan(args.target, manager), end='')
        sys.exit(0)

    if args.type == 'fonts':
        from cli_charts.font_downloads import run_fonts_command
        sys.exit(run_fonts_command(args))

    if args.type == 'chat-health':
        from cli_charts.chat_health import run_chat_health_command
        sys.exit(run_chat_health_command(args))

    if args.type == 'wave':
        from cli_charts.adapters.waveterm import run_wave_command
        sys.exit(run_wave_command(args))

    if args.type == 'demo':
        from cli_charts.demo_engine import run_demo
        sys.exit(run_demo(speed=args.speed, clear=not args.no_clear))

    if args.type == 'gallery':
        from cli_charts.gallery_engine import run_gallery
        sys.exit(run_gallery(output=args.output or None,
                             chart=args.chart or None,
                             theme=args.theme if '--theme' in raw_argv else None))

    if args.type == 'splash':
        from cli_charts.splash import main as splash_main
        sys.exit(splash_main(['--no-splash'] if args.no_splash else []))

    from cli_charts.splash import maybe_play_first_run
    maybe_play_first_run(no_splash=args.no_splash)

    if args.type == 'live':
        from cli_charts.live_engine import run_live
        source = args.art_text[0] if args.art_text else 'random'
        no_color = args.no_color or bool(os.environ.get('NO_COLOR'))
        sys.exit(run_live(
            source,
            window=args.window,
            interval=args.interval,
            duration=args.duration,
            title=args.title,
            width=args.width,
            height=args.height,
            theme=args.theme,
            no_color=no_color,
        ))

    if args.type == 'code':
        if not args.file:
            print('ERROR:schema: code needs --file PATH', file=sys.stderr)
            sys.exit(1)
        if not args.lang:
            print('ERROR:schema: code needs --lang LANG', file=sys.stderr)
            sys.exit(1)
        from cli_charts.render.code_engine import render_code
        no_color = args.no_color or bool(os.environ.get('NO_COLOR'))
        code_theme = 'monokai' if args.theme == 'pro' else args.theme
        rc = render_code(args.file, args.lang, theme=code_theme, no_color=no_color)
        sys.exit(rc)

    if args.type == 'status':
        from cli_charts.render.status_engine import render_status
        no_color = args.no_color or bool(os.environ.get('NO_COLOR'))
        rc = render_status(
            args.kind,
            args.message or args.title or args.kind,
            spinner=args.spinner or 'dots',
            no_color=no_color,
        )
        sys.exit(rc)

    if args.type == 'dashboard' and args.demo:
        dash_script = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'dashboard.py')
        cmd = [sys.executable, dash_script, '--demo']
        if args.no_interactive:
            cmd.append('--no-interactive')
        result = subprocess.run(cmd)
        sys.exit(result.returncode)

    # Media types (image/video) bypass JSON loading -- they take a filesystem path.
    if args.type in _MEDIA_TYPES:
        sys.exit(dispatch_media(args))
        return

    if args.type == 'art':
        from cli_charts.render.art_engine import list_decors, list_fonts, render_art
        no_color = args.no_color or bool(os.environ.get('NO_COLOR'))
        if args.list_fonts:
            list_fonts()
            sys.exit(0)
        if args.list_decors:
            list_decors()
            sys.exit(0)
        rc = render_art(
            ' '.join(args.art_text),
            args.font,
            args.decor,
            args.frame,
            args.gradient,
            args.theme,
            args.width,
            args.height,
            no_color,
            args.output,
            args.justify,
            args.anim,
        )
        sys.exit(rc)

    if args.type == 'calibrate':
        calibrate(
            {},
            args.title,
            args.width,
            args.height,
            args.theme,
            calibrate_from=args.calibrate_from,
            calibrate_to=args.calibrate_to,
            calibrate_step=args.calibrate_step,
            calibrate_glyph=args.calibrate_glyph,
            terminal=args.terminal,
            recommend=args.recommend,
        )
        sys.exit(0)

    if args.type in {'incplot', 'textplot', 'turtle', 'formula', 'formula-pretty', 'math', 'math-pretty'}:
        if args.file:
            with open(args.file, encoding='utf-8') as _f:
                raw = _f.read().strip()
        elif args.data is not None:
            raw = args.data
        elif args.art_text:
            raw = ' '.join(args.art_text)
        else:
            raw = sys.stdin.read().strip()
        if not raw:
            print(f'ERROR:schema: {args.type} needs --json TEXT, --file PATH, stdin, or trailing text',
                  file=sys.stderr)
            sys.exit(1)
        data = raw
        if args.type != 'incplot':
            try:
                data = json.loads(raw)
            except json.JSONDecodeError:
                data = raw
        no_color = args.no_color or bool(os.environ.get('NO_COLOR'))
        render_kw = dict(
            xlabel=args.xlabel,
            ylabel=args.ylabel,
            xlim=args.xlim,
            ylim=args.ylim,
            xscale=args.xscale,
            yscale=args.yscale,
            orientation=args.orientation,
            output='',
            no_color=no_color,
            prefer=args.prefer,
        )
        if args.output:
            from cli_charts.render.export_engine import export_to_path

            buf = io.StringIO()
            with contextlib.redirect_stdout(buf):
                CMDS[args.type](data, args.title, args.width, args.height, args.theme, **render_kw)
            export_to_path(buf.getvalue(), args.output, no_color)
        else:
            CMDS[args.type](data, args.title, args.width, args.height, args.theme, **render_kw)
        sys.exit(0)

    if args.type == 'diagram':
        kind = args.diagram_kind or (args.art_text[0] if args.art_text else '')
        inline_text = ' '.join(args.art_text[1:]) if args.art_text and kind == args.art_text[0] else ''
        if args.file:
            with open(args.file, encoding='utf-8') as _f:
                raw = _f.read().strip()
        elif args.data is not None:
            raw = args.data
        elif inline_text:
            raw = inline_text
        else:
            raw = sys.stdin.read().strip()
        if not raw:
            print('ERROR:schema: diagram needs --json TEXT, --file PATH, stdin, or trailing text',
                  file=sys.stderr)
            sys.exit(1)
        data = raw
        try:
            parsed = json.loads(raw)
        except json.JSONDecodeError:
            parsed = None
        if isinstance(parsed, dict):
            data = parsed
            kind = kind or parsed.get('kind') or parsed.get('type') or ''
        if not kind:
            print('ERROR:schema: diagram needs a kind: math, sequence, tree, table, frame, note, flowchart, graphdag, graphplanar',
                  file=sys.stderr)
            sys.exit(1)
        rc = diagram(
            data,
            args.title,
            args.width,
            args.height,
            args.theme,
            output=args.output,
            diagram_kind=kind,
            diagram_engine=args.diagram_engine,
            statusline=args.statusline,
        )
        sys.exit(rc or 0)

    if args.type == 'mermaid':
        if args.file:
            with open(args.file, encoding='utf-8') as _f:
                raw = _f.read().strip()
        elif args.data is not None:
            raw = args.data
        elif args.art_text:
            raw = ' '.join(args.art_text)
        else:
            raw = sys.stdin.read().strip()
        if not raw:
            print('ERROR:schema: mermaid needs --json TEXT, --file PATH, stdin, or trailing text',
                  file=sys.stderr)
            sys.exit(1)
        rc = mermaid(
            raw,
            args.title,
            args.width,
            args.height,
            args.theme,
            mermaid_theme=args.mermaid_theme,
            mermaid_ascii=args.mermaid_ascii,
            mermaid_padding_x=args.mermaid_padding_x,
            mermaid_padding_y=args.mermaid_padding_y,
            mermaid_box_padding=args.mermaid_box_padding,
        )
        sys.exit(rc or 0)

    if args.type == 'effect':
        kind = args.effect_kind or (args.art_text[0] if args.art_text else '')
        inline_text = ' '.join(args.art_text[1:]) if args.art_text and kind == args.art_text[0] else ''
        raw = ''
        if args.file:
            with open(args.file, encoding='utf-8') as _f:
                raw = _f.read().strip()
        elif args.data is not None:
            raw = args.data
        elif inline_text:
            raw = inline_text
        data = {}
        if raw:
            try:
                parsed = json.loads(raw)
            except json.JSONDecodeError:
                parsed = {'text': raw}
            if isinstance(parsed, dict):
                data = parsed
            else:
                data = {'values': parsed}
        rc = effect(
            data,
            args.title,
            args.width,
            args.height,
            args.theme,
            output=args.output,
            effect_kind=kind or data.get('kind') or data.get('effect') or 'gallery',
            statusline=args.statusline,
        )
        sys.exit(rc or 0)

    if args.type == 'animate':
        if not args.art_text:
            print('ERROR:schema: animate needs a chart type '
                  '(line, bar, scatter, sparkline)', file=sys.stderr)
            sys.exit(1)
        chart_type = args.art_text[0]
        no_color = args.no_color or bool(os.environ.get('NO_COLOR'))
        if args.file:
            with open(args.file) as _f:
                raw = _f.read().strip()
        elif args.data:
            raw = args.data
        else:
            raw = sys.stdin.read().strip()
        if not raw:
            print('ERROR:schema: Provide --json, --file, or pipe JSON to stdin',
                  file=sys.stderr)
            sys.exit(1)
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f'ERROR:json: {exc}', file=sys.stderr)
            sys.exit(1)
        from cli_charts.render.animate_engine import render_animate
        rc = render_animate(
            chart_type,
            data,
            args.duration,
            args.frames,
            title=args.title,
            width=args.width,
            height=args.height,
            theme=args.theme,
            xlabel=args.xlabel,
            ylabel=args.ylabel,
            xlim=args.xlim,
            ylim=args.ylim,
            xscale=args.xscale,
            yscale=args.yscale,
            orientation=args.orientation,
            no_color=no_color,
            spinner=args.spinner,
        )
        sys.exit(rc)

    if args.type == 'record':
        if not args.art_text:
            print('ERROR:schema: record needs an output .cast path', file=sys.stderr)
            sys.exit(1)
        from cli_charts.render.record_engine import record
        rc = record(args.art_text[0], args.cmd, args.duration)
        sys.exit(rc)

    if args.type == 'record-replay':
        if not args.art_text:
            print('ERROR:schema: record-replay needs an input .cast path', file=sys.stderr)
            sys.exit(1)
        from cli_charts.render.record_engine import record_replay
        rc = record_replay(args.art_text[0], args.output)
        sys.exit(rc)

    if args.type == 'to-hyperframes':
        if not args.data:
            print('ERROR:schema: to-hyperframes needs --json SERIES_JSON', file=sys.stderr)
            sys.exit(1)
        if not args.output_dir:
            print('ERROR:schema: to-hyperframes needs --output-dir DIR', file=sys.stderr)
            sys.exit(1)
        from cli_charts.adapters.hyperframes import to_hyperframes
        no_color = args.no_color or bool(os.environ.get('NO_COLOR'))
        rc = to_hyperframes(
            args.data,
            args.frames,
            args.duration,
            args.output_dir,
            width=args.width,
            height=args.height,
            title=args.title,
            theme=args.theme,
            no_color=no_color,
        )
        sys.exit(rc)

    if args.type == 'to-ascii-motion':
        if not args.data and not args.file:
            print('ERROR:schema: to-ascii-motion needs --json SERIES_JSON or --file PATH', file=sys.stderr)
            sys.exit(1)
        if not args.output_dir:
            print('ERROR:schema: to-ascii-motion needs --output-dir DIR', file=sys.stderr)
            sys.exit(1)
        adapter = _load_ascii_motion_adapter()
        _require_ascii_motion_npx()
        if args.file:
            with open(args.file) as _f:
                raw = _f.read().strip()
        else:
            raw = args.data
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f'ERROR:json: {exc}', file=sys.stderr)
            sys.exit(1)
        frames = _render_ascii_motion_frames(
            args.art_text[0] if args.art_text else 'line',
            data,
            args,
            adapter,
            no_color=args.no_color or bool(os.environ.get('NO_COLOR')),
        )
        formats = [fmt.strip().lower() for fmt in args.formats.split(',') if fmt.strip()]
        project_dir = tempfile.mkdtemp(prefix='glyph-arts-ascii-motion-')
        import asyncio

        asyncio.run(adapter.to_ascii_motion(project_dir, frames, formats, args.output_dir, int(max(args.duration, 0.1) * 1000 / max(args.frames, 1))))
        return

    if args.animate:
        no_color = args.no_color or bool(os.environ.get('NO_COLOR'))
        kw = dict(xlabel=args.xlabel, ylabel=args.ylabel, xlim=args.xlim,
                  ylim=args.ylim, xscale=args.xscale, yscale=args.yscale,
                  orientation=args.orientation, output=args.output,
                  no_color=no_color, visual_style=args.style)
        _animate_stdin(args.type, args.title, args.width, args.height,
                       args.theme, args.refresh, args.window, args.duration, kw)
        return

    # Warn when size/theme options are silently ignored
    _default_width = shutil.get_terminal_size((70, 20)).columns
    if args.type in _NO_SIZE_THEME:
        ignored = []
        if args.width != _default_width:
            ignored.append('--width')
        if args.height != 20:
            ignored.append('--height')
        if args.theme != 'pro':
            ignored.append('--theme')
        if ignored:
            print(f"warning: {', '.join(ignored)} ignored for {args.type} charts",
                  file=sys.stderr)

    # Respect NO_COLOR env var (https://no-color.org)
    no_color = args.no_color or bool(os.environ.get('NO_COLOR'))

    try:
        if args.type == 'auto':
            if args.file:
                with open(args.file) as _f:
                    raw = _f.read().strip()
            elif args.data:
                raw = args.data
            else:
                raw = sys.stdin.read().strip()
            if not raw:
                print('ERROR:schema: Provide --json, --file, or pipe JSON/CSV/TSV to stdin',
                      file=sys.stderr)
                sys.exit(1)
            from cli_charts.auto_detect import detect_auto
            detected = detect_auto(raw, args.prefer)
            args.type = detected.chart_type
            data = detected.data
        elif args.duckdb:
            if not args.db:
                print('ERROR:schema: --db is required when using --duckdb '
                      '(e.g. --db /path/to/data.duckdb)', file=sys.stderr)
                sys.exit(1)
            import duckdb as _duckdb_mod  # noqa: F401
            data = load_duckdb(args.duckdb, args.db, args.type)
        else:
            if args.file:
                with open(args.file) as _f:
                    raw = _f.read().strip()
            elif args.data:
                raw = args.data
            else:
                raw = sys.stdin.read().strip()
            if not raw:
                print('ERROR:schema: Provide --json, --file, --duckdb, or pipe JSON to stdin',
                      file=sys.stderr)
                sys.exit(1)
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                if args.type == 'graph':
                    data = raw
                else:
                    print(f'ERROR:json: {exc}', file=sys.stderr)
                    sys.exit(1)

        if args.sample > 0:
            data = _sample_data(data, args.sample, chart_type=args.type)

        kw = dict(
            xlabel=args.xlabel,
            ylabel=args.ylabel,
            xlim=args.xlim,
            ylim=args.ylim,
            xscale=args.xscale,
            yscale=args.yscale,
            orientation=args.orientation,
            output=args.output,
            format=args.format,
            no_color=no_color,
            link_data=args.link_data,
            link_title=args.link_title,
            statusline=args.statusline,
            rich_progress=args.rich_progress,
            prefer=args.prefer,
            font_tier=args.font_tier,
            marker=args.marker if args.type == 'scatter' else None,
            symbol_set=args.symbols if args.type == 'bar' else None,
            visual_style=args.style,
            candle_style=args.candle_style if args.type == 'kline' else 'default',
            gauge_style=(
                args.style
                if args.type == 'gauge' and args.style in _GLYPH_VISUAL_STYLES
                else args.gauge_style if args.type == 'gauge' else 'bar'
            ),
            graph_format=args.graph_format,
            graph_style=args.graph_style,
            graph_charset=args.graph_charset,
            graph_node_spacing=args.graph_node_spacing,
            graph_layer_spacing=args.graph_layer_spacing,
            mermaid_theme=args.mermaid_theme,
            mermaid_ascii=args.mermaid_ascii,
            mermaid_padding_x=args.mermaid_padding_x,
            mermaid_padding_y=args.mermaid_padding_y,
            mermaid_box_padding=args.mermaid_box_padding,
            effect_kind=args.effect_kind,
        )

        # Style routing: redirect to alternate engine if --style is set
        _resolved_engine = resolve_engine(args.type, args.style) if args.style in _STYLES else None
        if _resolved_engine and args.engine == 'ascii':
            from cli_charts.render.style_router import render_styled
            rc = render_styled(
                args.type, _resolved_engine, args.style,
                data, args.title, args.width, args.height, args.theme, **kw
            )
            if rc is not None:
                sys.exit(rc)
            # rc=None means engine not yet implemented, fall through to default

        try:
            if args.engine == 'pixel':
                if args.type not in PIXEL_SUPPORTED:
                    print(f'WARNING: --engine pixel does not yet support {args.type!r} '
                          f'(Phase A: {sorted(PIXEL_SUPPORTED)}); falling back to ascii',
                          file=sys.stderr)
                else:
                    from cli_charts.render.matplotlib_engine import render_pixel
                    rc = render_pixel(
                        args.type, data, args.width, args.height,
                        title=args.title, theme=args.theme,
                        output=args.output, no_color=no_color, art=args.art,
                    )
                    sys.exit(rc)
            if args.engine == 'interactive':
                from cli_charts.render.interactive_engine import render_interactive
                rc = render_interactive(
                    args.type, data, args.width, args.height,
                    title=args.title, theme=args.theme, no_color=no_color,
                )
                sys.exit(rc)

            if args.polish == 'ascii-motion':
                adapter = _load_ascii_motion_adapter()
                _require_ascii_motion_npx()
                output = _capture_stdout(lambda: CMDS[args.type](data, args.title, args.width, args.height, args.theme, **kw))
                cells = adapter.text_to_cells(output)
                project_dir = tempfile.mkdtemp(prefix='glyph-arts-ascii-motion-')
                import asyncio

                asyncio.run(adapter.polish_frames(project_dir, [cells], style=args.polish_style))
                if args.output:
                    formats = [args.output.rsplit('.', 1)[-1].lower()] if '.' in args.output else ['html']
                    asyncio.run(adapter.to_ascii_motion(project_dir, [cells], formats, os.path.dirname(args.output) or '.'))
                return

            if args.output and args.type == 'table' and args.output.lower().endswith('.md'):
                CMDS[args.type](data, args.title, args.width, args.height, args.theme, **kw)
            elif args.output:
                from cli_charts.render.export_engine import export_to_path

                kw["output"] = ""
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    CMDS[args.type](
                        data, args.title, args.width, args.height, args.theme, **kw
                    )
                export_to_path(buf.getvalue(), args.output, no_color)
            else:
                CMDS[args.type](data, args.title, args.width, args.height, args.theme, **kw)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            print(f'ERROR:schema: Invalid {args.type} data schema: {exc}\n'
                  f'Expected: {EXPECTED_SCHEMAS.get(args.type, "?")}',
                  file=sys.stderr)
            sys.exit(1)

        if os.environ.get('CLI_CHARTS_LOG') == '1':
            try:
                entry = json.dumps({
                    'ts': datetime.datetime.now().isoformat(),
                    'type': args.type,
                    'title': args.title,
                })
                with open('.chart_history.jsonl', 'a') as _lf:
                    _lf.write(entry + '\n')
            except Exception:
                pass

    except ImportError as exc:
        pkg = str(exc).split("'")[1] if "'" in str(exc) else str(exc)
        print(f'ERROR:dep: pip install {pkg}', file=sys.stderr)
        sys.exit(2)
    except SystemExit:
        raise
    except Exception:
        import traceback
        last = traceback.format_exc().strip().splitlines()[-1]
        print(f'ERROR:render: {last}', file=sys.stderr)
        sys.exit(4)


# ---------------------------------------------------------------------------
# Animation helpers
# ---------------------------------------------------------------------------

_ANIMATE_TYPES = {'line', 'scatter', 'sparkline'}


def _animate_stdin(chart_type, title, w, h, theme, refresh, window, duration, kw):
    """Stream values from stdin and re-render chart after each point.

    Input format: one numeric value per line (whitespace-separated fields are
    accepted; only the last field is used as the Y value).
    """
    import collections
    import time

    import plotext as plt
    from rich.console import Console
    from rich.live import Live
    from rich.text import Text

    if chart_type not in _ANIMATE_TYPES:
        print(f'ERROR:schema: --animate supports: {", ".join(sorted(_ANIMATE_TYPES))}',
              file=sys.stderr)
        sys.exit(1)

    buf = collections.deque(maxlen=window if window > 0 else None)
    t_start = time.monotonic()
    console = Console()

    def make_frame():
        ys = list(buf)
        xs = list(range(len(ys)))
        label = (title + ' ' if title else '') + f'[n={len(ys)}]'
        if chart_type == 'sparkline':
            try:
                from sparklines import sparklines as _sparklines
                lines = _sparklines(ys)
                return '\n'.join(lines) + f'\n{label}'
            except ImportError:
                return label + '\n' + ' '.join(f'{v:.1f}' for v in ys[-20:])
        plt.clf()
        _plt_fn = {'line': 'plot', 'scatter': 'scatter'}.get(chart_type, chart_type)
        getattr(plt, _plt_fn)(xs, ys)
        plt.title(label)
        plt.plotsize(w - 2, h)
        _ap = _get_palette(theme)
        if _ap:
            if _ap.get('plt_base'):
                plt.theme(_ap['plt_base'])
            plt.canvas_color(_ap['canvas'])
            plt.axes_color(_ap['axes'])
            plt.ticks_color(_ap['ticks'])
        else:
            plt.theme(theme)
        return plt.build()

    try:
        with Live(console=console, refresh_per_second=refresh, screen=False) as live:
            for raw_line in sys.stdin:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    val = float(raw_line.split()[-1])
                except ValueError:
                    continue
                buf.append(val)
                if len(buf) >= 2:
                    live.update(Text.from_ansi(make_frame()))
                if duration > 0 and time.monotonic() - t_start >= duration:
                    break
    except KeyboardInterrupt:
        pass  # clean exit on Ctrl-C


if __name__ == '__main__':
    main()
