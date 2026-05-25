from cli_charts.cmd._helpers import diagram
from cli_charts.registry import register

register("diagram")(diagram)
