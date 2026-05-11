"""Style-based rendering router.

Routes (chart_type, style) pairs to the appropriate engine renderer.
Returns exit code on success, or None to signal fallback to default engine.
"""
import sys
import warnings


def _warn_fallback(chart_type: str, style: str, engine: str, reason: str) -> None:
    warnings.warn(
        f"--style {style} ({engine}) not available for '{chart_type}': {reason}; "
        f"falling back to default",
        stacklevel=3,
    )


def _try_import(pkg: str) -> bool:
    try:
        __import__(pkg)
        return True
    except ImportError:
        return False


def _render_smooth(chart_type, data, title, w, h, theme, **kw):
    """Render using tplot (braille smooth curves). Fallback: plotille."""
    if _try_import("tplot"):
        import tplot
        series = data if isinstance(data, list) else [data]
        fig = tplot.Figure(width=w, height=h)
        for s in series:
            ys = s["y"]
            xs = s.get("x", list(range(len(ys))))
            label = s.get("label", "")
            fig.line(xs, ys, label=label)
        if title:
            print(title)
        fig.show()
        return 0

    if _try_import("plotille"):
        from cli_charts.cmd._helpers import plotille_chart
        plotille_chart(data, title, w, h, theme, **kw)
        return 0

    _warn_fallback(chart_type, "smooth", "tplot/plotille", "pip install tplot")
    return None


def _render_science(chart_type, data, title, w, h, theme, **kw):
    """Render using uniplot (scientific notation axes)."""
    if not _try_import("uniplot"):
        _warn_fallback(chart_type, "science", "uniplot", "pip install uniplot")
        return None
    from cli_charts.cmd._helpers import uniplot
    uniplot(data, title, w, h, theme, **kw)
    return 0


def _render_rgb(chart_type, data, title, w, h, theme, **kw):
    """Render using drawille with 24-bit RGB braille."""
    if not _try_import("drawille"):
        _warn_fallback(chart_type, "rgb", "drawille", "pip install drawille")
        return None
    from cli_charts.cmd._helpers import hires
    hires(data, title, w, h, theme, **kw)
    return 0


def _render_clean(chart_type, data, title, w, h, theme, **kw):
    """Render using textcharts (minimal ANSI bar/hist)."""
    if not _try_import("textcharts"):
        _warn_fallback(chart_type, "clean", "textcharts", "pip install textcharts")
        return None
    from textcharts import BarChart, BarData
    series = data if isinstance(data, list) else [data]
    if chart_type in ("bar", "hbar"):
        items = []
        for s in series:
            if "categories" in s and "values" in s:
                for cat, val in zip(s["categories"], s["values"]):
                    items.append(BarData(str(cat), val))
            elif "label" in s and "y" in s:
                items.append(BarData(s["label"], sum(s["y"]) / len(s["y"])))
        if not items:
            _warn_fallback(chart_type, "clean", "textcharts", "unsupported data shape")
            return None
        chart = BarChart(items, title=title or None)
        print(chart.render())
        return 0
    elif chart_type == "hist":
        values = []
        for s in series:
            values.extend(s.get("y", s.get("values", [])))
        if not values:
            return None
        from textcharts import Histogram
        chart = Histogram(values)
        if title:
            print(title)
        print(chart.render())
        return 0
    return None


def _render_retro(chart_type, data, title, w, h, theme, **kw):
    """Render using textgraph (retro sparkline/hbar)."""
    if not _try_import("textgraph"):
        _warn_fallback(chart_type, "retro", "textgraph", "pip install textgraph")
        return None
    if chart_type == "sparkline":
        from textgraph import spark as textgraph_spark
        series = data if isinstance(data, list) else [data]
        if title:
            print(title)
        for s in series:
            values = s.get("y", s.get("values", []))
            label = s.get("label", "")
            line = textgraph_spark(values)
            print(f"  {label}: {line}" if label else f"  {line}")
        return 0
    elif chart_type in ("bar", "hbar"):
        from textgraph import horizontal as textgraph_hbar
        series = data if isinstance(data, list) else [data]
        items = {}
        for s in series:
            if "categories" in s and "values" in s:
                for cat, val in zip(s["categories"], s["values"]):
                    items[cat] = val
            elif "label" in s and "y" in s:
                items[s["label"]] = sum(s["y"]) / len(s["y"])
        if not items:
            return None
        if title:
            print(title)
        print(textgraph_hbar(items, width=w))
        return 0
    return None


_RENDERERS = {
    "smooth": _render_smooth,
    "science": _render_science,
    "rgb": _render_rgb,
    "clean": _render_clean,
    "retro": _render_retro,
}


def render_styled(chart_type: str, engine: str, style: str,
                  data, title: str, w: int, h: int, theme: str, **kw) -> int | None:
    """Route to the appropriate style renderer.

    Returns exit code (0 on success), or None if the style/engine combo
    is not yet implemented (caller should fall through to default).
    """
    renderer = _RENDERERS.get(style)
    if renderer is None:
        print(f"WARNING: --style {style} not yet implemented; using default",
              file=sys.stderr)
        return None
    return renderer(chart_type, data, title, w, h, theme, **kw)
