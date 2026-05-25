from __future__ import annotations

import re
import sys
from typing import Any

from cli_charts.themes import get_palette

ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def render_plotextx(
    data: Any,
    *,
    title: str = "",
    width: int = 70,
    height: int = 20,
    theme: str = "pro",
    xlabel: str = "",
    ylabel: str = "",
    xlim: list[float] | tuple[float, float] | None = None,
    ylim: list[float] | tuple[float, float] | None = None,
    xscale: str = "linear",
    yscale: str = "linear",
    orientation: str = "vertical",
    no_color: bool = False,
) -> int:
    """Render plotext's richer overlay API from a compact JSON schema."""
    import plotext as plt

    if not isinstance(data, dict):
        data = {"series": data}

    if "colorize" in data:
        text = str(data.get("colorize") or "")
        if no_color:
            print(text)
        else:
            print(plt.colorize(
                text,
                color=data.get("color"),
                background=data.get("background"),
                style=data.get("style"),
            ))
        return 0

    plt.clear_figure()
    _apply_date_form(plt, data.get("date_form"))
    _apply_series(plt, data, orientation=orientation)
    _apply_overlays(plt, data)
    _finish(
        plt,
        title=data.get("title") or title,
        width=width,
        height=height,
        theme=data.get("theme") or theme,
        xlabel=data.get("xlabel") or xlabel,
        ylabel=data.get("ylabel") or ylabel,
        xlim=data.get("xlim") or xlim,
        ylim=data.get("ylim") or ylim,
        xscale=data.get("xscale") or xscale,
        yscale=data.get("yscale") or yscale,
        no_color=no_color,
    )
    return 0


def _as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def _apply_date_form(plt: Any, spec: Any) -> None:
    if not spec:
        return
    if isinstance(spec, str):
        plt.date_form(spec)
    elif isinstance(spec, dict):
        plt.date_form(spec.get("input") or spec.get("input_form"), spec.get("output") or spec.get("output_form"))


def _series_list(data: dict[str, Any]) -> list[dict[str, Any]]:
    raw = data.get("series", data.get("plots"))
    if raw is None:
        if "y" in data or "values" in data:
            raw = [data]
        else:
            raw = []
    if isinstance(raw, dict):
        return [raw]
    if isinstance(raw, list) and raw and not isinstance(raw[0], dict):
        return [{"type": "line", "y": raw}]
    return list(raw or [])


def _xy(series: dict[str, Any]) -> tuple[list[Any], list[Any]]:
    y = series.get("y", series.get("values", []))
    x = series.get("x", series.get("labels"))
    if x is None:
        x = list(range(len(y)))
    return list(x), list(y)


def _apply_series(plt: Any, data: dict[str, Any], *, orientation: str) -> None:
    for index, series in enumerate(_series_list(data)):
        kind = str(series.get("type") or series.get("kind") or "line").lower()
        label = str(series.get("label") or series.get("name") or "")
        color = series.get("color")
        marker = series.get("marker")

        if kind in {"line", "plot"}:
            x, y = _xy(series)
            plt.plot(x, y, label=label, marker=marker, color=color)
        elif kind == "scatter":
            x, y = _xy(series)
            plt.scatter(x, y, label=label, marker=marker, color=color)
        elif kind in {"error", "errorbar", "error-bar"}:
            x, y = _xy(series)
            plt.error(
                x,
                y,
                xerr=series.get("xerr"),
                yerr=series.get("yerr"),
                xside=series.get("xside"),
                yside=series.get("yside"),
                label=label or f"error-{index + 1}",
                color=color,
            )
        elif kind == "bar":
            labels = series.get("labels", series.get("x", []))
            values = series.get("values", series.get("y", []))
            plt.bar(labels, values, label=label, orientation=series.get("orientation", orientation), color=color)
        elif kind in {"hist", "histogram"}:
            values = series.get("values", series.get("y", []))
            plt.hist(values, bins=series.get("bins", data.get("bins", 20)), label=label, color=color)
        elif kind in {"candlestick", "kline"}:
            dates = series.get("dates", data.get("dates", []))
            plt.candlestick(
                dates,
                {
                    "Open": series.get("open", data.get("open", [])),
                    "High": series.get("high", data.get("high", [])),
                    "Low": series.get("low", data.get("low", [])),
                    "Close": series.get("close", data.get("close", [])),
                },
                label=label,
                colors=series.get("colors"),
                orientation=series.get("orientation"),
            )
        else:
            raise ValueError(f"unsupported plotext series type: {kind!r}")


def _apply_overlays(plt: Any, data: dict[str, Any]) -> None:
    for item in _as_list(data.get("vlines") or data.get("vertical_lines")):
        if isinstance(item, dict):
            plt.vertical_line(item.get("value", item.get("x")), color=item.get("color"), xside=item.get("xside"))
        else:
            plt.vertical_line(item)
    for item in _as_list(data.get("hlines") or data.get("horizontal_lines")):
        if isinstance(item, dict):
            plt.horizontal_line(item.get("value", item.get("y")), color=item.get("color"), yside=item.get("yside"))
        else:
            plt.horizontal_line(item)
    for item in _as_list(data.get("texts") or data.get("annotations")):
        if not isinstance(item, dict):
            continue
        plt.text(
            str(item.get("text", item.get("label", ""))),
            item.get("x", 0),
            item.get("y", 0),
            color=item.get("color"),
            background=item.get("background"),
            style=item.get("style"),
            orientation=item.get("orientation"),
            alignment=item.get("alignment"),
            xside=item.get("xside"),
            yside=item.get("yside"),
        )
    for item in _as_list(data.get("shapes")):
        if not isinstance(item, dict):
            continue
        kind = str(item.get("type") or item.get("kind") or "rectangle").lower()
        common = {
            "marker": item.get("marker"),
            "color": item.get("color"),
            "lines": item.get("lines"),
            "fill": item.get("fill"),
            "label": item.get("label"),
            "xside": item.get("xside"),
            "yside": item.get("yside"),
        }
        if kind in {"rect", "rectangle"}:
            plt.rectangle(x=item.get("x"), y=item.get("y"), **common)
        elif kind == "polygon":
            plt.polygon(
                x=item.get("x"),
                y=item.get("y"),
                radius=item.get("radius"),
                sides=item.get("sides"),
                **common,
            )
        else:
            raise ValueError(f"unsupported plotext shape type: {kind!r}")


def _finish(
    plt: Any,
    *,
    title: str,
    width: int,
    height: int,
    theme: str,
    xlabel: str,
    ylabel: str,
    xlim: list[float] | tuple[float, float] | None,
    ylim: list[float] | tuple[float, float] | None,
    xscale: str,
    yscale: str,
    no_color: bool,
) -> None:
    if title:
        plt.title(title)
    plt.plotsize(width, height)
    palette = get_palette(theme)
    if palette:
        if palette.get("plt_base"):
            plt.theme(palette["plt_base"])
        plt.canvas_color(palette["canvas"])
        plt.axes_color(palette["axes"])
        plt.ticks_color(palette["ticks"])
    else:
        plt.theme(theme)
    if xlabel:
        plt.xlabel(xlabel)
    if ylabel:
        plt.ylabel(ylabel)
    if xlim:
        plt.xlim(*xlim)
    if ylim:
        plt.ylim(*ylim)
    if xscale == "log":
        plt.xscale("log")
    if yscale == "log":
        plt.yscale("log")
    if no_color:
        sys.stdout.write(ANSI_RE.sub("", plt.build()))
        sys.stdout.write("\n")
    else:
        plt.show()
