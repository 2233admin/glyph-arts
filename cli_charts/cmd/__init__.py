"""Command registry bootstrap."""

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

for _module in _MODULES:
    import_module(f"{__name__}.{_module}")

__all__ = ["_MODULES"]
