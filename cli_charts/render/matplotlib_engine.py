"""matplotlib + chafa pixel render path."""

from __future__ import annotations

import io
import os
import shutil
import subprocess
import sys
from collections.abc import Sequence

PIXEL_SUPPORTED = frozenset({'bar', 'line', 'scatter'})


def _is_numeric_sequence(value):
    return (
        isinstance(value, Sequence)
        and not isinstance(value, (str, bytes, bytearray))
        and all(isinstance(item, (int, float)) and not isinstance(item, bool) for item in value)
    )


def _validate_data(chart_type, data):
    if chart_type == 'bar':
        if not isinstance(data, dict):
            raise ValueError('bar data must be a dict with labels + values')
        labels = data.get('labels')
        values = data.get('values')
        if (
            not isinstance(labels, list)
            or not all(isinstance(label, str) for label in labels)
            or not isinstance(values, list)
            or not _is_numeric_sequence(values)
            or len(labels) != len(values)
        ):
            raise ValueError('bar data must include equal-length labels and values lists')
        return labels, values

    # line / scatter accept list-of-series OR single-series dict
    series = data if isinstance(data, list) else [data] if isinstance(data, dict) else None
    if not series:
        raise ValueError(f'{chart_type} data must be a list of series or a single series dict')
    out = []
    for s in series:
        if not isinstance(s, dict):
            raise ValueError(f'{chart_type} each series must be a dict with x + y lists')
        x_values = s.get('x')
        y_values = s.get('y')
        if (
            not isinstance(x_values, list)
            or not isinstance(y_values, list)
            or not _is_numeric_sequence(x_values)
            or not _is_numeric_sequence(y_values)
            or len(x_values) != len(y_values)
        ):
            raise ValueError(f'{chart_type} each series needs equal-length numeric x and y lists')
        out.append((s.get('label', ''), x_values, y_values))
    return out


def _apply_theme(matplotlib, theme, no_color):
    if no_color:
        matplotlib.rcParams.update({
            'axes.facecolor': 'white',
            'figure.facecolor': 'white',
            'axes.edgecolor': 'black',
            'axes.labelcolor': 'black',
            'text.color': 'black',
            'xtick.color': 'black',
            'ytick.color': 'black',
            'grid.color': '#cccccc',
            'lines.color': 'black',
            'patch.facecolor': '#777777',
        })
        return

    if theme == 'pro':
        matplotlib.rcParams.update({
            'axes.facecolor': '#2a2a3e',
            'figure.facecolor': '#1e1e2e',
            'savefig.facecolor': '#1e1e2e',
            'axes.edgecolor': '#f8f8f2',
            'axes.labelcolor': '#f8f8f2',
            'text.color': '#f8f8f2',
            'xtick.color': '#f8f8f2',
            'ytick.color': '#f8f8f2',
            'grid.color': '#45475a',
            'lines.color': '#89dceb',
            'patch.facecolor': '#89dceb',
        })


def _build_figure(plt, chart_type, data, w, h, title):
    fig_w = max(4.0, float(w) / 10.0)
    fig_h = max(3.0, float(h) / 5.0)
    fig, ax = plt.subplots(figsize=(fig_w, fig_h), dpi=100)

    if title:
        fig.suptitle(title)

    if chart_type == 'bar':
        labels, values = _validate_data(chart_type, data)
        positions = range(len(labels))
        ax.bar(positions, values)
        ax.set_xticks(list(positions))
        ax.set_xticklabels(labels)
    elif chart_type in ('line', 'scatter'):
        series = _validate_data(chart_type, data)
        plotter = ax.plot if chart_type == 'line' else ax.scatter
        for label, x_values, y_values in series:
            plotter(x_values, y_values, label=label)
        if any(s[0] for s in series):
            ax.legend()
    else:
        raise ValueError(f'unsupported chart_type: {chart_type!r}')

    ax.grid(True, alpha=0.35)
    fig.tight_layout()
    return fig


def _figure_to_png(fig):
    png = io.BytesIO()
    fig.savefig(png, format='png', bbox_inches='tight')
    return png.getvalue()


def _detect_chafa_format() -> str:
    """Pick best chafa --format for the current terminal.

    Priority: kitty (Kitty Graphics Protocol) -> iterm (iTerm2 inline)
    -> sixel (WezTerm / mintty) -> symbols (universal Unicode fallback).
    Always returns 'symbols' when stdout is not a TTY (piping, Claude
    Code UI text panel, redirect to file) so output is greppable text.

    Override via GLYPH_ARTS_FORMAT env var (kitty|iterm|sixel|symbols).
    """
    override = os.environ.get('GLYPH_ARTS_FORMAT', '').strip().lower()
    if override in {'kitty', 'iterm', 'sixel', 'symbols'}:
        return override
    if not os.isatty(1):
        return 'symbols'
    term = os.environ.get('TERM', '').lower()
    term_program = os.environ.get('TERM_PROGRAM', '').lower()
    if 'kitty' in term or os.environ.get('KITTY_WINDOW_ID'):
        return 'kitty'
    if term_program == 'iterm.app':
        return 'iterm'
    if term_program == 'wezterm' or os.environ.get('WEZTERM_EXECUTABLE'):
        return 'sixel'
    # Warp graphics support is flag-gated and version-specific; symbols
    # is the safe default (still uses truecolor + Unicode block chars).
    # Windows Terminal also lacks native kitty/sixel — same default.
    return 'symbols'


def _pipe_to_chafa(png_bytes, w, h, no_color):
    """Pipe PNG to chafa, write its stdout, return 0 on success / 4 on failure."""
    fmt = _detect_chafa_format()
    cmd = ['chafa', '--size', f'{w}x{h}', '--format', fmt]
    if fmt == 'symbols':
        # block chars give the closest-to-pixel look on text-mode terminals
        cmd += ['--symbols', 'block']
    if no_color:
        cmd += ['--colors', 'none']
    cmd += ['-']
    try:
        result = subprocess.run(cmd, input=png_bytes, capture_output=True, timeout=10)
    except (OSError, subprocess.TimeoutExpired) as e:
        print(f'ERROR:render: chafa invocation failed: {e}', file=sys.stderr)
        return 4
    if result.returncode != 0:
        last = (result.stderr or b'').decode('utf-8', errors='replace').strip().splitlines()
        msg = last[-1] if last else f'chafa exit {result.returncode}'
        print(f'ERROR:render: {msg}', file=sys.stderr)
        return 4
    # Use os.write(fd=1) instead of sys.stdout.buffer.write — the package's
    # cli_charts/__init__.py calls sys.stdout.reconfigure(encoding='utf-8',
    # errors='replace') for Windows cp1252 safety, which on some Python
    # versions detaches the old BufferedWriter so `sys.stdout.buffer.write`
    # silently no-ops. Writing to fd 1 directly bypasses any TextIOWrapper.
    sys.stdout.flush()
    os.write(1, result.stdout)
    return 0


def render_pixel(chart_type, data, w, h, *, title='', theme='pro', output=None, no_color=False, **_unused):
    if chart_type not in PIXEL_SUPPORTED:
        print(f'ERROR:render: --engine pixel does not support {chart_type!r} '
              f'(Phase A: bar/line/scatter)', file=sys.stderr)
        return 1

    try:
        _validate_data(chart_type, data)
    except (TypeError, ValueError) as e:
        print(f'ERROR:schema: pixel engine input invalid: {e}', file=sys.stderr)
        return 1

    if shutil.which('chafa') is None:
        print('ERROR:dep: chafa not in PATH (install: scoop install chafa | '
              'brew install chafa | apt install chafa)', file=sys.stderr)
        return 2

    try:
        import matplotlib

        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        print('ERROR:dep: matplotlib not installed (pip install glyph-arts[pixel])',
              file=sys.stderr)
        return 2

    fig = None
    try:
        _apply_theme(matplotlib, theme, no_color)
        fig = _build_figure(plt, chart_type, data, w, h, title)
        # Note: argparse passes default='' (empty string), not None. Use
        # truthy check so unspecified --output falls through to chafa path.
        if output:
            fig.savefig(output)
            return 0

        png_bytes = _figure_to_png(fig)
        return _pipe_to_chafa(png_bytes, w, h, no_color)
    except (TypeError, ValueError) as e:
        print(f'ERROR:schema: pixel engine input invalid: {e}', file=sys.stderr)
        return 1
    except (ImportError, FileNotFoundError) as e:
        print(f'ERROR:dep: {e}', file=sys.stderr)
        return 2
    except Exception:
        import traceback
        last = traceback.format_exc().strip().splitlines()[-1]
        print(f'ERROR:render: matplotlib failed: {last}', file=sys.stderr)
        return 4
    finally:
        if fig is not None:
            plt.close(fig)
