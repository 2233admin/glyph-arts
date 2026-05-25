from cli_charts.cmd._helpers import waterfall
from cli_charts.registry import register

register("waterfall")(waterfall)
