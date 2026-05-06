from cli_charts.cmd._helpers import banner
from cli_charts.registry import register

register("banner")(banner)