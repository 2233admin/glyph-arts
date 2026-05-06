from cli_charts.cmd._helpers import scatter
from cli_charts.registry import register

register("scatter")(scatter)