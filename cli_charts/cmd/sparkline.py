from cli_charts.cmd._helpers import sparkline
from cli_charts.registry import register

register("sparkline")(sparkline)