#!/usr/bin/env python3
"""glyph-arts: terminal-visible chart toolkit for Claude Code.

Usage: python chart.py <type> [options]
Types (29):
  plotext  : kline line scatter step bar multibar stackedbar hist heatmap box indicator event confusion
  rich     : table tree panel gauge pie dashboard rich_live
  braille  : curve hires radar
  plotille : plotille
  uniplot  : uniplot
  misc     : graph sparkline banner
  media    : image video   (via chafa / ffmpeg -- requires --file PATH)

Animation (--animate):
  Stream values from stdin line-by-line; chart re-renders after each point.
  Supported types: line, scatter, sparkline
  Flags: --refresh FPS (default 10), --window N (default 50), --duration SEC
"""
import sys
import os
import json
import argparse
import shutil
import random
import datetime
import subprocess

try:
    from importlib.metadata import version as _pkg_version
    _VERSION = _pkg_version("glyph-arts")
except Exception:
    try:
        from pathlib import Path as _Path
        _VERSION = (_Path(__file__).parent.parent / "VERSION").read_text().strip()
    except Exception:
        _VERSION = "2.4.1"


# -- helpers -----------------------------------------------------------------

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


# -- media renderers (chafa + ffmpeg) ----------------------------------------

_MEDIA_TYPES = {'image', 'video'}


def _render_image(path, w, h, symbols='braille', no_color=False):
    """Render an image file to the terminal by shelling out to chafa.

    Why chafa instead of reinventing: chafa 1.18 ships 2x4 braille sub-pixels
    with 24-bit truecolor, outperforming any pure-Python renderer. See HANDOFF
    2026-04-14 for the architectural split (charts = native, media = chafa).
    """
    import subprocess
    if not shutil.which('chafa'):
        print('ERROR:dep: chafa not found -- install from https://hpjansson.org/chafa/',
              file=sys.stderr)
        sys.exit(2)
    cmd = ['chafa', '--size', f'{w}x{h}', '--symbols', symbols]
    if no_color:
        cmd += ['--colors', 'none']
    cmd.append(path)
    subprocess.run(cmd, check=True)


def _render_video(path, w, h, fps=12, symbols='braille', duration=0.0, no_color=False):
    """Play a video in the terminal: ffmpeg extracts frames, chafa renders each.

    Frames are extracted to a tempdir upfront (bounded by --duration if set),
    then streamed at the target fps. Cursor hidden during playback; restored
    on exit or Ctrl-C. Not suitable for hours-long input -- prefer clipping
    first with ffmpeg -ss/-t.
    """
    import subprocess
    import tempfile
    import time
    import glob

    if not shutil.which('chafa'):
        print('ERROR:dep: chafa not found', file=sys.stderr)
        sys.exit(2)
    if not shutil.which('ffmpeg'):
        print('ERROR:dep: ffmpeg not found -- required for video input',
              file=sys.stderr)
        sys.exit(2)

    with tempfile.TemporaryDirectory(prefix='clichart_frames_') as tmp:
        ff = ['ffmpeg', '-loglevel', 'error', '-y', '-i', path,
              '-vf', f'fps={fps}']
        if duration and duration > 0:
            ff += ['-t', str(duration)]
        ff.append(os.path.join(tmp, 'f_%05d.png'))
        subprocess.run(ff, check=True)

        frames = sorted(glob.glob(os.path.join(tmp, 'f_*.png')))
        if not frames:
            print('ERROR:render: ffmpeg produced no frames', file=sys.stderr)
            sys.exit(4)

        delay = 1.0 / fps if fps > 0 else 1.0 / 12
        is_tty = sys.stdout.isatty()
        chafa_cmd = ['chafa', '--size', f'{w}x{h}', '--symbols', symbols,
                     '--format', 'symbols']
        if no_color:
            chafa_cmd += ['--colors', 'none']

        if is_tty:
            sys.stdout.write('\x1b[?25l')  # hide cursor
            sys.stdout.flush()
        try:
            for frame in frames:
                t0 = time.time()
                if is_tty:
                    sys.stdout.write('\x1b[H')  # cursor home (less flicker than \x1b[2J)
                    sys.stdout.flush()
                subprocess.run(chafa_cmd + [frame], check=True)
                elapsed = time.time() - t0
                if elapsed < delay:
                    time.sleep(delay - elapsed)
        except KeyboardInterrupt:
            pass
        finally:
            if is_tty:
                sys.stdout.write('\x1b[?25h')  # show cursor
                sys.stdout.flush()


def _plt_finalize(plt, title, w, h, theme, kw):
    """Apply common plotext settings and render."""
    if title:
        plt.title(title)
    plt.plotsize(w, h)
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
    else:
        plt.show()


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
    import plotext as plt
    plt.candlestick(_normalize_kline_dates(d['dates']), {
        'Open': d['open'], 'High': d['high'],
        'Low': d['low'],   'Close': d['close'],
    })
    _plt_finalize(plt, title, w, h, theme, kw)


def line(d, title, w, h, theme, **kw):
    """plotext multi-series line chart."""
    import plotext as plt
    series = d if isinstance(d, list) else [d]
    for s in series:
        x = s.get('x', list(range(len(s['y']))))
        plt.plot(x, s['y'], label=s.get('label', ''),
                 marker=s.get('marker'), color=s.get('color'))
    _plt_finalize(plt, title, w, h, theme, kw)


def scatter(d, title, w, h, theme, **kw):
    """plotext scatter plot. Same schema as line."""
    import plotext as plt
    series = d if isinstance(d, list) else [d]
    for s in series:
        x = s.get('x', list(range(len(s['y']))))
        plt.scatter(x, s['y'], label=s.get('label', ''),
                    marker=s.get('marker'), color=s.get('color'))
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
    import plotext as plt
    plt.bar(d['labels'], d['values'],
            orientation=kw.get('orientation', 'vertical'))
    _plt_finalize(plt, title, w, h, theme, kw)


def pie(d, title, w, h, theme, **kw):
    """Rich percentage-bar pie breakdown. labels + values arrays of equal length."""
    from rich.console import Console
    from rich.table import Table
    from rich import box as rich_box
    total = sum(d['values']) or 1
    bar_w = 36
    colors = ['red', 'green', 'blue', 'yellow', 'magenta', 'cyan',
              'bright_red', 'bright_green', 'bright_blue']
    tbl = Table(title=title or None, box=rich_box.ROUNDED, show_lines=False)
    tbl.add_column('Label', style='bold')
    tbl.add_column('Pct', justify='right')
    tbl.add_column('Distribution', min_width=bar_w)
    tbl.add_column('Value', justify='right')
    for i, (label, val) in enumerate(zip(d['labels'], d['values'])):
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
    import plotext as plt
    import pandas as pd
    df = pd.DataFrame(
        d['matrix'],
        columns=d.get('xlabels'),
        index=d.get('ylabels'),
    )
    plt.heatmap(df)
    _plt_finalize(plt, title, w, h, theme, kw)


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
    """sparklines unicode block chart -- single line."""
    import sparklines as sl
    if title:
        print(title)
    for ln in sl.sparklines(d['values']):
        print(ln)


def table(d, title, w, h, theme, **kw):
    """rich double-edge formatted table."""
    from rich.console import Console
    from rich.table import Table
    from rich import box as richbox
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
        label = node.get('label', str(node))
        style = node.get('style', '')
        branch = parent.add(f'[{style}]{label}[/{style}]' if style else label)
        for child in node.get('children', []):
            _build(child, branch)

    root_label = d.get('label', title or 'root')
    t = RichTree(root_label)
    for child in d.get('children', []):
        _build(child, t)
    c.print(t)


def panel(d, title, w, h, theme, **kw):
    """rich Panel -- bordered text / callout box."""
    from rich.console import Console
    from rich.panel import Panel as RichPanel
    from rich import box as richbox
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
    from phart import ASCIIRenderer, LayoutOptions, NodeStyle
    import networkx as nx
    G = nx.DiGraph() if d.get('directed', True) else nx.Graph()
    for node in d.get('nodes', []):
        G.add_node(node['id'] if isinstance(node, dict) else node)
    G.add_edges_from(d['edges'])
    style_name = d.get('node_style', 'ROUND').upper()
    style = getattr(NodeStyle, style_name, NodeStyle.ROUND)
    opts = LayoutOptions(
        node_style=style,
        node_spacing=d.get('node_spacing', 4),
        layer_spacing=d.get('layer_spacing', 2),
    )
    print(ASCIIRenderer(G, options=opts).render())


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
    from rich.console import Console
    from rich.table import Table
    from rich import box as richbox
    no_color = kw.get('no_color', False)
    c = Console(no_color=no_color)
    metrics = d if isinstance(d, list) else d.get('metrics', [d])
    t = Table(title=title, box=richbox.SIMPLE, show_header=False, padding=(0, 1))
    t.add_column('Label', style='bold', min_width=12)
    t.add_column('Bar', min_width=32)
    t.add_column('Value', justify='right', min_width=10)
    for m in metrics:
        val = float(m['value'])
        mx  = float(m.get('max', 100))
        pct = max(0.0, min(1.0, val / mx)) if mx != 0 else 0.0
        bar_w = 30
        filled = round(pct * bar_w)
        auto_color = 'green' if pct < 0.7 else ('yellow' if pct < 0.9 else 'red')
        color = m.get('color', auto_color)
        bar = f'[{color}]{"█" * filled}{"░" * (bar_w - filled)}[/{color}]'
        t.add_row(m.get('label', ''), bar, f'{val:.1f} / {mx:.0f}')
    c.print(t)


def dashboard(d, title, w, h, theme, **kw):
    """Delegates to scripts/dashboard.py via subprocess (Textual TUI or Rich static)."""
    import subprocess
    config = dict(d)
    if title:
        config['title'] = title
    dash_script = os.path.join(os.path.dirname(__file__), 'dashboard.py')
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
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.text import Text
    from rich import box as richbox

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

    def _render_panel_content(panel_spec):
        """Dispatch sub-chart and capture its stdout as a Rich-renderable Text."""
        ptype = panel_spec.get('type')
        if ptype not in CMDS:
            return Text(f'[unknown panel type: {ptype!r}]', style='red')
        if ptype in ('dashboard', 'rich_live'):
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
            except SystemExit:
                pass
            except Exception as e:
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
        return

    from rich.live import Live
    import time
    refresh = float(d.get('refresh_per_second', 4))
    frame_delay = 1.0 / max(1.0, refresh)
    with Live(layout, refresh_per_second=refresh, console=console, transient=False):
        for _ in range(frames):
            layout = _build_layout()
            time.sleep(frame_delay)


def confusion(d, title, w, h, theme, **kw):
    """plotext ML confusion matrix.
    actual/predicted must be lists of class labels (int or str).
    """
    import plotext as plt
    plt.confusion_matrix(d['actual'], d['predicted'],
                         labels=d.get('labels'))
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
        title=title or '',
        legend_labels=labels,
        lines=lines,
        width=w,
        height=h,
    )
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
    try:
        import numpy as np
        from lttb import downsample as _lttb_ds
        data = np.column_stack([xs, ys])
        out = _lttb_ds(data, n)
        return out[:, 0].tolist(), out[:, 1].tolist()
    except ImportError:
        step = max(1, len(xs) // n)
        return xs[::step][:n], ys[::step][:n]


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
        return {k: _sample_data(v, n) for k, v in data.items()}
    return data


# -- DuckDB loader -----------------------------------------------------------

def load_duckdb(sql, db_path, chart_type):
    import duckdb
    df = duckdb.connect(db_path).execute(sql).df()
    if chart_type == 'kline':
        col0 = df.columns[0]
        dates = [d.strftime('%d/%m/%Y') for d in df[col0]]
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
        return {'points': list(zip(df[cols[0]].tolist(), df[cols[1]].tolist()))}
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
                                  df[cols[1]].astype(str)))}
    return df.to_dict(orient='list')


# -- registry ----------------------------------------------------------------

CMDS = {
    'kline':      kline,
    'line':       line,
    'scatter':    scatter,
    'step':       step,
    'bar':        bar,
    'pie':        pie,
    'multibar':   multibar,
    'stackedbar': stackedbar,
    'hist':       hist,
    'heatmap':    heatmap,
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
    'graph':      graph,
    'curve':      curve,
    'uniplot':    uniplot,
    'banner':      banner,
    'candlestick': kline,
    'hires':       hires,
    'radar':       radar,
    'plotille':    plotille_chart,
    'rich_live':   rich_live,
}

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
    'graph':      '{"edges":[["A","B"],...], "directed":true, "node_style":"ROUND"}',
    'curve':      '{"points":[[x,y],...]}',
    'uniplot':    '[{"label":"A","x":[...],"y":[...]}] or {"label":"A","y":[...]}',
    'banner':      '{"text":"PROFIT","font":"big","color":"green"}',
    'candlestick': '{"dates":["DD/MM/YYYY",...], "open":[...], "high":[...], "low":[...], "close":[...]}',
    'hires':       '[{"label":"Q5","y":[3.5,9.2,9.4],"color":[0,245,212]},{"label":"Q1","y":[3.1,5.1,4.5],"color":[255,107,107]}]',
    'radar':       '{"labels":["ATK","DEF","SPD","MGC","LCK"],"series":[{"label":"Hero","values":[80,60,90,70,50],"color":[0,245,212]}],"max":100}',
    'plotille':    '[{"label":"A","x":[1,2,3,4],"y":[2,4,3,6],"color":"bright_cyan"}]',
    'rich_live':   '{"panels":[{"type":"bar","title":"Left","data":{"labels":["A","B"],"values":[1,2]}},{"type":"sparkline","title":"Right","data":{"values":[1,3,5,2,8]}}],"layout":"row","frames":1}',
}

# Types where --width/--height/--theme have no effect
_NO_SIZE_THEME = {'table', 'tree', 'panel', 'graph', 'sparkline', 'gauge', 'banner', 'pie', 'dashboard', 'rich_live'}


# -- main --------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        description='glyph-arts -- terminal-visible charts for Claude Code',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Chart types (27):
  plotext  : kline line scatter step bar multibar stackedbar hist heatmap box indicator event confusion
  rich     : table tree panel gauge pie dashboard rich_live
  braille  : curve hires radar
  plotille : plotille
  uniplot  : uniplot
  misc     : graph sparkline banner

Examples:
  python chart.py kline --json '{"dates":["07/04/2026"],"open":[100],"high":[102],"low":[99],"close":[101]}'
  python chart.py scatter --json '[{"label":"A","x":[1,2,3],"y":[4,2,5]}]'
  python chart.py hist --json '{"values":[1,2,2,3,3,3,4,4,5],"bins":5}'
  python chart.py heatmap --json '{"matrix":[[1,2],[3,4]],"xlabels":["A","B"],"ylabels":["X","Y"]}'
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
    p.add_argument('type', choices=list(CMDS) + sorted(_MEDIA_TYPES), metavar='TYPE',
                   help='Chart type: ' + ' | '.join(CMDS) +
                        ' | image | video (media via chafa/ffmpeg)')
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
                   help='plotext theme: pro dark clear matrix (ignored for rich/graph/sparkline)')
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
                   help='Save chart to file instead of displaying (plotext only)')
    p.add_argument('--no-color',    action='store_true',
                   help='Disable ANSI colors (respects NO_COLOR env var)')
    p.add_argument('--symbols',     default='braille', metavar='SET',
                   help='chafa --symbols value for image/video (default: braille; '
                        'e.g. block, ascii, all, half)')
    p.add_argument('--fps',         type=int, default=12, metavar='N',
                   help='Video playback frames/sec for type=video (default: 12)')
    p.add_argument('--version',     action='version', version=f'glyph-arts {_VERSION}')
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
    if '--check-deps' in sys.argv:
        _CORE = ['plotext', 'rich', 'uniplot', 'pyfiglet',
                 'sparklines', 'duckdb', 'pandas', 'networkx', 'phart']
        _OPT = [
            ('drawille', 'curve chart',   'glyph-arts[braille]'),
            ('lttb',     'LTTB sampling', 'glyph-arts[lttb]'),
            ('textual',  'dashboard TUI', 'glyph-arts[tui]'),
        ]
        print('[core]')
        for pkg in _CORE:
            try:
                __import__(pkg)
                status = 'OK'
            except ImportError:
                status = 'MISSING'
            print(f'  {pkg:<13} {status}')
        print('[media]')
        for tool, purpose in (('chafa', 'image/video render'),
                              ('ffmpeg', 'video frame extract')):
            status = 'OK' if shutil.which(tool) else 'MISSING'
            print(f'  {tool:<13} {status}  ({purpose})')
        if '--all' in sys.argv:
            print('[optional]')
            for pkg, purpose, install in _OPT:
                try:
                    __import__(pkg)
                    status = 'OK'
                    hint = ''
                except ImportError:
                    status = 'MISSING'
                    hint = f'  -> pip install {install}'
                print(f'  {pkg:<13} {status}  ({purpose}){hint}')
        sys.exit(0)

    args = p.parse_args()

    # Media types (image/video) bypass JSON loading -- they take a filesystem path.
    if args.type in _MEDIA_TYPES:
        path = args.file or args.data
        if not path:
            print(f'ERROR:schema: {args.type} needs a path via --file PATH or --json PATH',
                  file=sys.stderr)
            sys.exit(1)
        if not os.path.exists(path):
            print(f'ERROR:schema: file not found: {path}', file=sys.stderr)
            sys.exit(1)
        no_color = args.no_color or bool(os.environ.get('NO_COLOR'))
        try:
            if args.type == 'image':
                _render_image(path, args.width, args.height, args.symbols, no_color)
            else:
                _render_video(path, args.width, args.height, args.fps,
                              args.symbols, args.duration, no_color)
        except subprocess.CalledProcessError as exc:
            print(f'ERROR:render: chafa/ffmpeg exit {exc.returncode}', file=sys.stderr)
            sys.exit(4)
        return

    if args.animate:
        no_color = args.no_color or bool(os.environ.get('NO_COLOR'))
        kw = dict(xlabel=args.xlabel, ylabel=args.ylabel, xlim=args.xlim,
                  ylim=args.ylim, xscale=args.xscale, yscale=args.yscale,
                  orientation=args.orientation, output=args.output,
                  no_color=no_color)
        _animate_stdin(args.type, args.title, args.width, args.height,
                       args.theme, args.refresh, args.window, args.duration, kw)
        return

    # Warn when size/theme options are silently ignored
    _default_width = shutil.get_terminal_size((70, 20)).columns
    if args.type in _NO_SIZE_THEME:
        ignored = []
        if args.width != _default_width: ignored.append('--width')
        if args.height != 20:            ignored.append('--height')
        if args.theme != 'pro':          ignored.append('--theme')
        if ignored:
            print(f"warning: {', '.join(ignored)} ignored for {args.type} charts",
                  file=sys.stderr)

    # Respect NO_COLOR env var (https://no-color.org)
    no_color = args.no_color or bool(os.environ.get('NO_COLOR'))

    try:
        if args.duckdb:
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
            no_color=no_color,
        )

        try:
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
    except Exception as exc:
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
    from rich.live import Live
    from rich.console import Console
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
