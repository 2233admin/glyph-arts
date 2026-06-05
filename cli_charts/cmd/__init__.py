"""Command registry bootstrap helpers.

The main ``glyph-arts`` CLI uses the legacy dispatcher in
``cli_charts.cmd._helpers``. Importing every command module here made all CLI
invocations pay the registry setup cost even when the registry was unused, so
registry population is now explicit via :func:`bootstrap`.
"""

from importlib import import_module

_MODULES = [
    "auto", "live", "incplot",
    "cli_charts.charts.series.line", "cli_charts.charts.series.bar",
    "cli_charts.charts.series.kline", "cli_charts.charts.series.scatter",
    "cli_charts.charts.series.multibar", "cli_charts.charts.series.stackedbar",
    "cli_charts.charts.series.hist", "cli_charts.charts.series.heatmap",
    "cli_charts.charts.series.spectrum", "cli_charts.charts.series.waterfall",
    "cli_charts.charts.series.box", "cli_charts.charts.series.indicator",
    "cli_charts.charts.series.event", "confusion", "plotext",
    "cli_charts.charts.series.sparkline", "pie", "table", "tree", "gauge",
    "diagram", "mermaid", "effect",
    "cli_charts.charts.series.curve", "hires", "radar", "textplot", "turtle", "plotille",
    "uniplot", "banner", "art", "candlestick", "image", "video", "demo", "gallery",
    "code", "animate", "record", "record_replay",
    "to_hyperframes", "to_ascii_motion", "cli_charts.charts.series.step", "serve",
    # Phase 3a — aggregates + composite + algebra
    "cli_charts.charts.aggregates.comparison",
    "cli_charts.charts.aggregates.diverging",
    "cli_charts.charts.aggregates.summary",
    "cli_charts.charts.aggregates.sparkline_table",
    "cli_charts.charts.aggregates.cdf_chart",
    "cli_charts.charts.aggregates.rank_table",
    "cli_charts.charts.aggregates.percentile",
    "cli_charts.charts.aggregates.boxplot_comparison",
    "cli_charts.charts.aggregates.stacked_bar_text",
    "cli_charts.charts.aggregates.graph",
    "cli_charts.charts.composite.panel",
    "cli_charts.charts.composite.dashboard",
    "cli_charts.charts.composite.rich_live",
    "cli_charts.charts.algebra.formula",
    "cli_charts.charts.algebra.formula_pretty",
    "cli_charts.charts.algebra.calibrate",
    "cli_charts.charts.algebra.status_command",
    "cli_charts.charts.algebra.splash_command",
    "cli_charts.charts.algebra.wave_command",
]

_BOOTSTRAPPED = False


def bootstrap() -> None:
    global _BOOTSTRAPPED
    if _BOOTSTRAPPED:
        return
    for module in _MODULES:
        if module.startswith("cli_charts."):
            import_module(module)
        else:
            import_module(f"{__name__}.{module}")
    _BOOTSTRAPPED = True


load_all = bootstrap

__all__ = ["_MODULES", "bootstrap", "load_all"]
