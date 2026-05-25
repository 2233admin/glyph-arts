from collections.abc import Callable

CMDS: dict[str, Callable[..., object]] = {}
EXPECTED_SCHEMAS: dict[str, str] = {}

STYLES = ("fast", "smooth", "science", "rgb", "clean", "retro", "rich", "art")

STYLE_ENGINES: dict[str, str] = {
    "fast": "plotext",
    "smooth": "tplot",
    "science": "uniplot",
    "rgb": "drawille",
    "clean": "textcharts",
    "retro": "textgraph",
    "rich": "rich",
    "art": "figlet",
}

STYLE_ROUTES: dict[str, dict[str, str]] = {
    "line":      {"fast": "plotext", "smooth": "tplot", "science": "uniplot", "rgb": "drawille"},
    "scatter":   {"fast": "plotext", "smooth": "tplot", "science": "uniplot", "rgb": "drawille"},
    "curve":     {"fast": "plotext", "smooth": "tplot", "rgb": "drawille"},
    "bar":       {"fast": "plotext", "clean": "textcharts", "retro": "textgraph"},
    "hist":      {"fast": "plotext", "science": "uniplot", "clean": "textcharts"},
    "sparkline": {"fast": "plotext", "retro": "textgraph"},
    "hbar":      {"fast": "plotext", "retro": "textgraph"},
    "kline":     {"fast": "plotext"},
    "pie":       {"fast": "plotext"},
    "table":     {"fast": "plotext", "rich": "rich"},
    "gauge":     {"fast": "plotext"},
    "radar":     {"fast": "plotext"},
    "heatmap":   {"fast": "plotext"},
}

DEFAULT_STYLE = "fast"


def styles_for(chart_type: str) -> list[str]:
    """Return available styles for a chart type, or all styles if not mapped."""
    routes = STYLE_ROUTES.get(chart_type)
    if routes:
        return list(routes.keys())
    return [DEFAULT_STYLE]


def resolve_engine(chart_type: str, style: str | None) -> str | None:
    """Resolve which engine to use for a (chart_type, style) pair.

    Returns the engine name, or None if the style is not supported for this type
    (caller should fallback to default).
    """
    if not style or style == DEFAULT_STYLE:
        return None
    routes = STYLE_ROUTES.get(chart_type, {})
    return routes.get(style)


def register(name: str, schema_hint: str = ""):
    def decorator(func: Callable[..., object]) -> Callable[..., object]:
        CMDS[name] = func
        EXPECTED_SCHEMAS[name] = schema_hint
        return func

    return decorator