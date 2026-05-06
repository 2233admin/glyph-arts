from cli_charts.cmd._helpers import heatmap
from cli_charts.registry import register

register("heatmap")(heatmap)