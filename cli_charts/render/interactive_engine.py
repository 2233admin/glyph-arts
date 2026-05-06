"""Textual interactive chart render path."""

from __future__ import annotations

import sys
from dataclasses import dataclass
from typing import Any

from cli_charts.render.matplotlib_engine import _validate_data

INTERACTIVE_SUPPORTED = frozenset({"line"})


@dataclass(frozen=True)
class Point:
    x: float
    values: tuple[tuple[str, float], ...]


def _normalize_line_data(data: Any) -> list[Point]:
    series = _validate_data("line", data)
    if not series:
        raise ValueError("line data must contain at least one series")

    first_x = list(series[0][1])
    points: list[Point] = []
    for pos, x_value in enumerate(first_x):
        values: list[tuple[str, float]] = []
        for series_idx, (label, x_values, y_values) in enumerate(series):
            if len(x_values) != len(first_x):
                raise ValueError("interactive line series must have equal point counts")
            if x_values[pos] != x_value:
                raise ValueError("interactive line series must share x values")
            values.append((label or f"series {series_idx + 1}", float(y_values[pos])))
        points.append(Point(float(x_value), tuple(values)))
    return points


def _format_number(value: float) -> str:
    if value.is_integer():
        return str(int(value))
    return f"{value:g}"


def _footer(points: list[Point], cursor_idx: int, zoom_factor: float) -> str:
    point = points[cursor_idx]
    zoom = 1.0 / zoom_factor if zoom_factor else 1.0
    if len(point.values) == 1:
        label, y_value = point.values[0]
        return (
            f"cursor: x={_format_number(point.x)} y={_format_number(y_value)} "
            f"series={label} | zoom={zoom:g}x | press q to exit"
        )
    pairs = ", ".join(f"{label}={_format_number(y_value)}" for label, y_value in point.values)
    return f"cursor: x={_format_number(point.x)} | {pairs} | zoom={zoom:g}x | press q to exit"


def _window_bounds(length: int, zoom_factor: float, zoom_center: int) -> tuple[int, int]:
    visible = max(2, min(length, int(round(length * zoom_factor))))
    if visible >= length:
        return 0, length
    left = max(0, min(length - visible, zoom_center - visible // 2))
    return left, left + visible


def _build_plot(
    plt: Any,
    series: list[tuple[str, list[float], list[float]]],
    w: int,
    h: int,
    title: str,
    zoom_factor: float,
    zoom_center: int,
) -> str:
    length = len(series[0][1])
    left, right = _window_bounds(length, zoom_factor, zoom_center)
    plt.clear_figure()
    plt.plotsize(max(20, w), max(6, h - 3))
    if title:
        plt.title(title)
    for label, x_values, y_values in series:
        kwargs = {"label": label} if label else {}
        plt.plot(x_values[left:right], y_values[left:right], **kwargs)
    return plt.build()


def _run_textual(
    textual_app: Any,
    textual_widget: Any,
    reactive: Any,
    plt: Any,
    series: list[tuple[str, list[float], list[float]]],
    points: list[Point],
    w: int,
    h: int,
    title: str,
) -> None:
    App = textual_app.App
    Static = textual_widget.Static

    class ChartView(Static):  # type: ignore[misc,valid-type]
        cursor_idx = reactive(0)

        def __init__(self) -> None:
            super().__init__("")

        def on_mouse_move(self, event: Any) -> None:
            width = max(1, self.size.width - 1)
            idx = round(max(0, min(width, event.x)) / width * (len(points) - 1))
            self.app.cursor_idx = int(idx)
            self.app.zoom_center = int(idx)
            self.app.refresh_chart()

    class InteractiveLineApp(App):  # type: ignore[misc,valid-type]
        BINDINGS = [
            ("left,h", "cursor_left", "Cursor left"),
            ("right,l", "cursor_right", "Cursor right"),
            ("+,=", "zoom_in", "Zoom in"),
            ("-,_", "zoom_out", "Zoom out"),
            ("r", "reset", "Reset"),
            ("q,escape", "quit", "Quit"),
        ]

        cursor_idx = reactive(0)
        zoom_factor = reactive(1.0)
        zoom_center = reactive(0)

        def compose(self) -> Any:
            self.chart = ChartView()
            self.footer = Static("")
            yield self.chart
            yield self.footer

        def on_mount(self) -> None:
            self.refresh_chart()

        def on_key(self, event: Any) -> None:
            key = event.key
            if key in {"left", "h"}:
                self.action_cursor_left()
            elif key in {"right", "l"}:
                self.action_cursor_right()
            elif key in {"+", "="}:
                self.action_zoom_in()
            elif key in {"-", "_"}:
                self.action_zoom_out()
            elif key == "r":
                self.action_reset()
            elif key in {"q", "escape"}:
                self.exit()

        def refresh_chart(self) -> None:
            self.cursor_idx = max(0, min(len(points) - 1, int(self.cursor_idx)))
            self.zoom_center = max(0, min(len(points) - 1, int(self.zoom_center)))
            plot = _build_plot(plt, series, w, h, title, float(self.zoom_factor), int(self.zoom_center))
            self.chart.update(plot)
            self.footer.update(_footer(points, int(self.cursor_idx), float(self.zoom_factor)))

        def action_cursor_left(self) -> None:
            self.cursor_idx = max(0, int(self.cursor_idx) - 1)
            self.zoom_center = int(self.cursor_idx)
            self.refresh_chart()

        def action_cursor_right(self) -> None:
            self.cursor_idx = min(len(points) - 1, int(self.cursor_idx) + 1)
            self.zoom_center = int(self.cursor_idx)
            self.refresh_chart()

        def action_zoom_in(self) -> None:
            self.zoom_factor = max(0.01, float(self.zoom_factor) * 0.5)
            self.zoom_center = int(self.cursor_idx)
            self.refresh_chart()

        def action_zoom_out(self) -> None:
            self.zoom_factor = min(1.0, float(self.zoom_factor) * 2.0)
            self.zoom_center = int(self.cursor_idx)
            self.refresh_chart()

        def action_reset(self) -> None:
            self.cursor_idx = 0
            self.zoom_factor = 1.0
            self.zoom_center = 0
            self.refresh_chart()

    InteractiveLineApp().run()


def render_interactive(
    chart_type: str,
    data: Any,
    w: int,
    h: int,
    *,
    title: str = "",
    theme: str = "pro",
    no_color: bool = False,
    **_unused: Any,
) -> int:
    del theme, no_color
    if chart_type not in INTERACTIVE_SUPPORTED:
        print("ERROR:render: --engine interactive only supports line (Phase A MVP)", file=sys.stderr)
        return 1

    try:
        raw_series = _validate_data(chart_type, data)
        points = _normalize_line_data(data)
    except (TypeError, ValueError) as e:
        print(f"ERROR:schema: interactive engine input invalid: {e}", file=sys.stderr)
        return 1

    try:
        import plotext as plt
        from textual import app as textual_app
        from textual import widgets as textual_widget
        from textual.reactive import reactive
    except ImportError:
        print("ERROR:dep: textual not installed (pip install glyph-arts[interactive])", file=sys.stderr)
        return 2

    try:
        series = [(label, list(x_values), list(y_values)) for label, x_values, y_values in raw_series]
        _run_textual(textual_app, textual_widget, reactive, plt, series, points, w, h, title)
        return 0
    except Exception as e:
        print(f"ERROR:render: interactive engine failed: {e}", file=sys.stderr)
        return 4
