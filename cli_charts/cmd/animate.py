from cli_charts.cmd._helpers import animate_command
from cli_charts.registry import register

register("animate")(animate_command)