from cli_charts.cmd._helpers import code_command
from cli_charts.registry import register

register("code")(code_command)