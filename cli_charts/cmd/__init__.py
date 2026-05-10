"""Command registry bootstrap."""

from importlib import import_module

_MODULES = [
    "line", "bar", "kline", "scatter", "multibar", "stackedbar", "hist",
    "heatmap", "box", "indicator", "event", "confusion", "sparkline",
    "pie", "table", "tree", "panel", "gauge", "dashboard", "graph",
    "curve", "hires", "radar", "plotille", "uniplot", "banner", "art",
    "candlestick", "rich_live", "image", "video", "demo", "gallery",
    "splash", "status", "code", "animate", "record", "record_replay",
    "to_hyperframes", "to_ascii_motion", "step", "mermaid",
]

for _module in _MODULES:
    import_module(f"{__name__}.{_module}")

__all__ = ["_MODULES"]