from cli_charts.cmd._helpers import plot_command
from cli_charts.registry import register

register("plot")(plot_command)
