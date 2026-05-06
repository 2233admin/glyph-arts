from cli_charts.cmd._helpers import multibar
from cli_charts.registry import register

register("multibar")(multibar)