"""Chat-safe SDR-style terminal renderers."""

from __future__ import annotations

from collections.abc import Iterable
from typing import Any

_WATERFALL_RAMP = " .:-=+*#%@"


def _coerce_floats(values: Iterable[Any], name: str) -> list[float]:
    out: list[float] = []
    for value in values:
        out.append(float(value))
    if not out:
        raise ValueError(f"{name} must not be empty")
    return out


def _pick(data: dict, *names: str):
    for name in names:
        if name in data and data[name] is not None:
            return data[name]
    return None


def _format_num(value: float) -> str:
    text = f"{value:.2f}"
    return text.rstrip("0").rstrip(".")


def _scale(value: float, low: float, high: float, size: int) -> int:
    if size <= 1 or high == low:
        return 0
    ratio = (value - low) / (high - low)
    return max(0, min(size - 1, round(ratio * (size - 1))))


def _resample(values: list[float], size: int) -> list[float]:
    if size <= 0:
        return []
    if len(values) == size:
        return list(values)
    if len(values) == 1:
        return [values[0]] * size
    out = []
    for idx in range(size):
        pos = idx * (len(values) - 1) / max(1, size - 1)
        lo = int(pos)
        hi = min(lo + 1, len(values) - 1)
        frac = pos - lo
        out.append(values[lo] * (1 - frac) + values[hi] * frac)
    return out


def _series(data: dict) -> tuple[list[float], list[float]]:
    powers = _pick(data, "power", "powers", "y", "values")
    if powers is None:
        raise ValueError("spectrum needs power/y/values")
    y = _coerce_floats(powers, "power")
    freqs = _pick(data, "freq", "freqs", "frequency", "frequencies", "x")
    if freqs is None:
        x = [float(i) for i in range(len(y))]
    else:
        x = _coerce_floats(freqs, "frequency")
    if len(x) != len(y):
        raise ValueError("frequency and power lengths must match")
    return x, y


def render_spectrum(data: dict, title: str = "", width: int = 70, height: int = 20) -> str:
    """Render a fixed-width RF spectrum with center/band/peak overlays."""
    x, y = _series(data)
    title = title or str(data.get("title") or "RF-Spectrum")
    width = max(36, int(width or 70))
    height = max(10, int(height or 20))

    xmin = float(_pick(data, "xmin", "min_freq") or min(x))
    xmax = float(_pick(data, "xmax", "max_freq") or max(x))
    ymin = float(_pick(data, "ymin", "min_power") or min(y))
    ymax = float(_pick(data, "ymax", "max_power") or max(y))
    if ymin == ymax:
        ymin -= 1
        ymax += 1

    left = max(6, len(_format_num(ymin)) + 1, len(_format_num(ymax)) + 1)
    plot_w = max(12, width - left - 2)
    plot_h = max(5, height - 7)
    canvas = [[" " for _ in range(plot_w)] for _ in range(plot_h)]

    center = _pick(data, "center", "center_freq")
    bandwidth = _pick(data, "bandwidth", "bw")
    if center is not None:
        c = _scale(float(center), xmin, xmax, plot_w)
        for row in range(plot_h):
            canvas[row][c] = "│"
    if center is not None and bandwidth is not None:
        half = float(bandwidth) / 2
        for freq in (float(center) - half, float(center) + half):
            col = _scale(freq, xmin, xmax, plot_w)
            for row in range(0, plot_h, 2):
                canvas[row][col] = "┆"

    points = sorted(zip(x, y, strict=True), key=lambda pair: pair[0])
    for freq, power in points:
        col = _scale(freq, xmin, xmax, plot_w)
        row = plot_h - 1 - _scale(power, ymin, ymax, plot_h)
        canvas[row][col] = "•"

    peak_idx = max(range(len(y)), key=y.__getitem__)
    peak_col = _scale(x[peak_idx], xmin, xmax, plot_w)
    peak_row = max(0, plot_h - 1 - _scale(y[peak_idx], ymin, ymax, plot_h) - 1)
    canvas[peak_row][peak_col] = "▲"

    tick_rows = {0: ymax, plot_h // 2: (ymax + ymin) / 2, plot_h - 1: ymin}
    lines = [title.center(width)]
    lines.append(" " * left + "┌" + "─" * plot_w + "┐")
    for row, cells in enumerate(canvas):
        label = _format_num(tick_rows[row]).rjust(left) if row in tick_rows else " " * left
        lines.append(f"{label}┤{''.join(cells)}│")
    lines.append(" " * left + "└" + "─" * plot_w + "┘")

    axis = [" "] * (left + plot_w + 2)
    for freq, text in ((xmin, _format_num(xmin)), (xmax, _format_num(xmax))):
        pos = left + 1 + _scale(freq, xmin, xmax, plot_w)
        start = max(0, min(len(axis) - len(text), pos - len(text) // 2))
        axis[start:start + len(text)] = list(text)
    if center is not None:
        text = _format_num(float(center))
        pos = left + 1 + _scale(float(center), xmin, xmax, plot_w)
        start = max(0, min(len(axis) - len(text), pos - len(text) // 2))
        axis[start:start + len(text)] = list(text)
    lines.append("".join(axis).rstrip())

    meta = []
    if center is not None:
        meta.append(f"center={_format_num(float(center))}")
    if bandwidth is not None:
        meta.append(f"bw={_format_num(float(bandwidth))}")
    meta.append(f"peak={_format_num(x[peak_idx])}/{_format_num(y[peak_idx])}dB")
    lines.append(" " * left + " ".join(meta))
    ylabel = str(data.get("ylabel") or "Power (dB)")
    xlabel = str(data.get("xlabel") or "Frequency")
    lines.append(f"{ylabel:<{left + 1}}{xlabel.center(plot_w)}")
    return "\n".join(lines).rstrip() + "\n"


def _matrix(data: dict) -> list[list[float]]:
    rows = _pick(data, "matrix", "rows", "values")
    if rows is None:
        raise ValueError("waterfall needs matrix/rows/values")
    matrix = [_coerce_floats(row, "waterfall row") for row in rows]
    if not matrix:
        raise ValueError("waterfall matrix must not be empty")
    width = len(matrix[0])
    if width == 0:
        raise ValueError("waterfall rows must not be empty")
    for row in matrix:
        if len(row) != width:
            raise ValueError("waterfall rows must have the same length")
    return matrix


def render_waterfall(data: dict, title: str = "", width: int = 70, height: int = 20) -> str:
    """Render an SDR waterfall as a dense ASCII intensity map."""
    matrix = _matrix(data)
    title = title or str(data.get("title") or "RF-Waterfall")
    width = max(32, int(width or 70))
    height = max(8, int(height or 20))
    ylabels = [str(v) for v in data.get("ylabels", [])]
    if len(ylabels) != len(matrix):
        ylabels = [f"t-{len(matrix) - i - 1}" if i < len(matrix) - 1 else "now" for i in range(len(matrix))]
    label_w = max(4, max(len(label) for label in ylabels) + 1)
    plot_w = max(12, width - label_w)
    max_rows = max(1, height - 5)
    if len(matrix) > max_rows:
        step = len(matrix) / max_rows
        picked = [min(len(matrix) - 1, int(i * step)) for i in range(max_rows)]
        matrix = [matrix[i] for i in picked]
        ylabels = [ylabels[i] for i in picked]

    flat = [value for row in matrix for value in row]
    vmin = float(_pick(data, "min", "vmin", "db_min") if _pick(data, "min", "vmin", "db_min") is not None else min(flat))
    vmax = float(_pick(data, "max", "vmax", "db_max") if _pick(data, "max", "vmax", "db_max") is not None else max(flat))
    if vmin == vmax:
        vmin -= 1
        vmax += 1

    lines = [title.center(width)]
    for label, row in zip(ylabels, matrix, strict=True):
        cells = []
        for value in _resample(row, plot_w):
            idx = _scale(value, vmin, vmax, len(_WATERFALL_RAMP))
            cells.append(_WATERFALL_RAMP[idx])
        lines.append(f"{label:<{label_w}}{''.join(cells)}")

    xlabels = [str(v) for v in data.get("xlabels", []) if str(v)]
    if xlabels:
        left_label = xlabels[0]
        right_label = xlabels[-1]
    else:
        left_label = _format_num(float(data.get("xmin", 0)))
        right_label = _format_num(float(data.get("xmax", len(matrix[0]) - 1)))
    axis = f"{left_label:<{plot_w // 2}}{right_label:>{plot_w - plot_w // 2}}"
    lines.append(" " * label_w + axis[:plot_w])
    lines.append(" " * label_w + f"range {_format_num(vmin)}..{_format_num(vmax)} dB")
    return "\n".join(lines).rstrip() + "\n"
