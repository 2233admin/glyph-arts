from cli_charts.cmd._helpers import pie
from cli_charts.registry import register

register("pie")(pie)