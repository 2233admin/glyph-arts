from cli_charts.cmd._helpers import status_command
from cli_charts.registry import register

register("status")(status_command)