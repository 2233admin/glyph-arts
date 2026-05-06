from cli_charts.cmd._helpers import demo_command
from cli_charts.registry import register

register("demo")(demo_command)