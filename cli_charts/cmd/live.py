from cli_charts.cmd._helpers import live_command
from cli_charts.registry import register

register("live")(live_command)
