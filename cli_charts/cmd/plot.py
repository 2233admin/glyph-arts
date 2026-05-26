from cli_charts.cmd._helpers import plot_command  # type: ignore[attr-defined]
from cli_charts.registry import register

register("plot")(plot_command)
