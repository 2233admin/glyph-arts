from cli_charts.cmd._helpers import indicator
from cli_charts.registry import register

register("indicator")(indicator)