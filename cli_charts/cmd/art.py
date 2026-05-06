from cli_charts.cmd._helpers import art_command
from cli_charts.registry import register

register("art")(art_command)