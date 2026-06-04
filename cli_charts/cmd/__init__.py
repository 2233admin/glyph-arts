"""Command registry bootstrap helpers.

The main ``glyph-arts`` CLI uses the legacy dispatcher in
``cli_charts.cmd._helpers``. Importing every command module here made all CLI
invocations pay the registry setup cost even when the registry was unused, so
registry population is now explicit via :func:`bootstrap`.
"""

from importlib import import_module

_MODULES = [
    "auto", "live", "incplot", "line", "bar", "kline", "scatter", "multibar", "stackedbar", "hist",
    "heatmap", "spectrum", "waterfall", "box", "indicator", "event", "confusion", "plotext", "sparkline",
    "pie", "table", "tree", "panel", "gauge", "dashboard", "graph", "diagram", "formula", "mermaid", "effect",
    "curve", "hires", "radar", "textplot", "turtle", "plotille", "uniplot", "banner", "art",
    "candlestick", "rich_live", "image", "video", "demo", "gallery",
    "splash", "status", "code", "animate", "record", "record_replay",
    "to_hyperframes", "to_ascii_motion", "step", "wave", "calibrate",
]

_BOOTSTRAPPED = False


def bootstrap() -> None:
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return
    for module in _MODULES:
        import_module(f"{__name__}.{module}")
    _BOOTSTRAPPED = True


load_all = bootstrap

__all__ = ["_MODULES", "bootstrap", "load_all"]
