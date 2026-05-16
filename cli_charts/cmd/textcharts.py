"""textcharts integration command."""
from cli_charts.cmd._helpers import (
    boxplot_comparison,
    cdf_chart,
    comparison,
    diverging,
    percentile,
    rank_table,
    sparkline_table,
    stacked_bar_text,
    summary,
)
from cli_charts.registry import register

register("comparison")(comparison)
register("diverging")(diverging)
register("summary")(summary)
register("sparkline-table")(sparkline_table)
register("cdf")(cdf_chart)
register("rank")(rank_table)
register("percentile")(percentile)
register("boxplot")(boxplot_comparison)
register("stacked-text")(stacked_bar_text)
