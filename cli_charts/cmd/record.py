from cli_charts.cmd._helpers import record_command
from cli_charts.registry import register

register("record")(record_command)