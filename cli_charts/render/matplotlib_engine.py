"""matplotlib + chafa pixel render path."""

from __future__ import annotations

import io
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
    if not isinstance(data, dict):
        raise ValueError('data must be a dict')

    if chart_type == 'bar':
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

    x_values = data.get('x')
    y_values = data.get('y')
    if (
        not isinstance(x_values, list)
        or not isinstance(y_values, list)
        or not _is_numeric_sequence(x_values)
        or not _is_numeric_sequence(y_values)
        or len(x_values) != len(y_values)
    ):
        raise ValueError(f'{chart_type} data must include equal-length numeric x and y lists')
    return x_values, y_values


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
    elif chart_type == 'line':
        x_values, y_values = _validate_data(chart_type, data)
        ax.plot(x_values, y_values)
    elif chart_type == 'scatter':
        x_values, y_values = _validate_data(chart_type, data)
        ax.scatter(x_values, y_values)
    else:
        raise ValueError(f'unsupported chart_type: {chart_type!r}')

    ax.grid(True, alpha=0.35)
    fig.tight_layout()
    return fig


def _figure_to_png(fig):
    png = io.BytesIO()
    fig.savefig(png, format='png', bbox_inches='tight')
    return png.getvalue()


def _pipe_to_chafa(png_bytes, w, h, no_color):
    cmd = ['chafa', '--size', f'{w}x{h}'] + (['--colors', 'none'] if no_color else []) + ['-']
    result = subprocess.run(cmd, input=png_bytes, capture_output=True, timeout=10)
    sys.stdout.buffer.write(result.stdout)
    sys.stdout.flush()
    return result.returncode == 0


def render_pixel(chart_type, data, w, h, *, title='', theme='pro', output=None, no_color=False, **_unused):
    if chart_type not in PIXEL_SUPPORTED:
        return 1

    try:
        _validate_data(chart_type, data)
    except (TypeError, ValueError):
        return 1

    if shutil.which('chafa') is None:
        return 2

    try:
        import matplotlib

        matplotlib.use('Agg')
        import matplotlib.pyplot as plt
    except ImportError:
        return 2

    fig = None
    try:
        _apply_theme(matplotlib, theme, no_color)
        fig = _build_figure(plt, chart_type, data, w, h, title)
        if output is not None:
            fig.savefig(output)
            return 0

        png_bytes = _figure_to_png(fig)
        return 0 if _pipe_to_chafa(png_bytes, w, h, no_color) else 4
    except (TypeError, ValueError):
        return 1
    except (ImportError, FileNotFoundError):
        return 2
    except Exception:
        return 4
    finally:
        if fig is not None:
            plt.close(fig)
