from cli_charts.cmd._helpers import auto_command
from cli_charts.registry import register

register("auto")(auto_command)
