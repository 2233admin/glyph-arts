"""Cursor-home animation engine for static ASCII chart renderers."""

from __future__ import annotations

import contextlib
import copy
import io
import shutil
import sys
import time
from typing import Any

from rich.console import Console
from rich.spinner import SPINNERS, Spinner

ANIMATE_SUPPORTED = {"line", "bar", "scatter", "sparkline"}


def _slice_len(length: int, frame_index: int, frames: int) -> int:
    if length <= 0:
        return 0
    return max(1, round((frame_index + 1) / frames * length))


def _slice_series(series: dict[str, Any], take: int) -> dict[str, Any]:
    sliced = copy.deepcopy(series)
    if "x" in sliced and isinstance(sliced["x"], list):
        sliced["x"] = sliced["x"][:take]
    if "y" in sliced and isinstance(sliced["y"], list):
        sliced["y"] = sliced["y"][:take]
    return sliced


def _series_len(series: dict[str, Any]) -> int:
    y_values = series.get("y")
    if isinstance(y_values, list):
        return len(y_values)
    x_values = series.get("x")
    if isinstance(x_values, list):
        return len(x_values)
    return 0


def _interpolate_data(data: list[dict[str, Any]] | dict[str, Any], frames: int) -> list[Any]:
    """Build progressive data snapshots without mutating the caller's data."""
    if frames <= 0:
        return []

    states: list[Any] = []
    if isinstance(data, list):
        max_len = max(
            (_series_len(s) for s in data if isinstance(s, dict)),
            default=0,
        )
        for i in range(frames):
            take = _slice_len(max_len, i, frames)
            states.append([_slice_series(s, take) for s in data])
        return states

    if isinstance(data, dict):
        values = data.get("values")
        if isinstance(values, list):
            max_len = len(values)
            for i in range(frames):
                take = _slice_len(max_len, i, frames)
                state = copy.deepcopy(data)
                state["values"] = values[:take]
                if isinstance(state.get("labels"), list):
                    state["labels"] = state["labels"][:take]
                states.append(state)
            return states

    return [copy.deepcopy(data) for _ in range(frames)]


def _render_static(chart_type: str, data: Any, **kwargs: Any) -> str:
    from cli_charts.chart import CMDS

    width = int(kwargs.get("width") or shutil.get_terminal_size((70, 20)).columns)
    height = int(kwargs.get("height") or 20)
    title = str(kwargs.get("title") or "")
    theme = str(kwargs.get("theme") or "pro")
    render_kwargs = {
        "xlabel": kwargs.get("xlabel", ""),
        "ylabel": kwargs.get("ylabel", ""),
        "xlim": kwargs.get("xlim"),
        "ylim": kwargs.get("ylim"),
        "xscale": kwargs.get("xscale", "linear"),
        "yscale": kwargs.get("yscale", "linear"),
        "orientation": kwargs.get("orientation", "vertical"),
        "output": "",
        "no_color": bool(kwargs.get("no_color", False)),
    }
    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        CMDS[chart_type](data, title, width, height, theme, **render_kwargs)
    return buf.getvalue()


def render_animate(
    chart_type: str,
    data: list[dict[str, Any]] | dict[str, Any],
    duration: float,
    frames: int,
    spinner: str = "",
    **kwargs: Any,
) -> int:
    if chart_type not in ANIMATE_SUPPORTED:
        return 1
    if duration <= 0 or frames <= 0:
        return 1
    if spinner and spinner not in SPINNERS:
        print(f"ERROR:schema: unknown spinner: {spinner}", file=sys.stderr)
        return 1

    interpolated = _interpolate_data(data, frames)
    interval = duration / frames
    rich_spinner = Spinner(spinner) if spinner else None
    console = Console(no_color=bool(kwargs.get("no_color", False)))
    start = time.monotonic()
    sys.stdout.write("\x1b[?25l")
    try:
        for state in interpolated:
            sys.stdout.write("\x1b[H\x1b[2J")
            if rich_spinner is not None:
                console.print(rich_spinner.render(time.monotonic() - start))
            sys.stdout.write(_render_static(chart_type, state, **kwargs))
            sys.stdout.flush()
            time.sleep(interval)
        sys.stdout.write("\x1b[H\x1b[2J")
        sys.stdout.write(_render_static(chart_type, data, **kwargs))
        sys.stdout.flush()
    except KeyboardInterrupt:
        sys.stdout.write("\x1b[H\x1b[2J")
        sys.stdout.write(_render_static(chart_type, data, **kwargs))
        sys.stdout.flush()
    finally:
        sys.stdout.write("\x1b[?25h\n")
        sys.stdout.flush()
    return 0
