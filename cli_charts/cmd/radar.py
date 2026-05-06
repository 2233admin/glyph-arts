from cli_charts.cmd._helpers import radar
from cli_charts.registry import register

register("radar")(radar)