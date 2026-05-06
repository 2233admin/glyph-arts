from cli_charts.cmd._helpers import splash_command
from cli_charts.registry import register

register("splash")(splash_command)