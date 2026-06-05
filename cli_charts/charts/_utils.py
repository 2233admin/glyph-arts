"""cli_charts.charts._utils -- non-chart helpers extracted from cmd/_helpers.py.

Pure relocation: functions and one class moved verbatim. Imports rewritten to
resolve at the new package level. Public behavior unchanged.
"""
import contextlib
import datetime
import io
import os
import random
import sys

from cli_charts.font_tier import detect_font_tier
from cli_charts.osc8 import link as _osc8_link
from cli_charts.symbols import BLOCK, BRAILLE_ALL, get_symbol
from cli_charts.themes import get_palette as _get_palette


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


def _rewrite_chat_argv(argv, cmds):
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
    elif rest and rest[0] in (set(cmds) | _MEDIA_TYPES):
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
                    row += "⠀" if not b else ch
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
