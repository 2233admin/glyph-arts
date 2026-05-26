"""Command registry bootstrap."""

from importlib import import_module

_MODULES = [
    "line", "spectrum", "bar", "kline", "scatter", "multibar", "stackedbar", "hist",
    "heatmap", "waterfall", "box", "indicator", "event", "confusion", "sparkline",
    "pie", "table", "chat", "tree", "panel", "gauge", "dashboard", "graph",
    "curve", "hires", "radar", "plotille", "uniplot", "banner", "art",
    "candlestick", "rich_live", "image", "video", "demo", "gallery",
    "splash", "status", "code", "animate", "record", "record_replay",
    "to_hyperframes", "to_ascii_motion", "step", "plot",
]

for _module in _MODULES:
    import_module(f"{__name__}.{_module}")

__all__ = ["_MODULES"]
