from cli_charts.cmd._helpers import uniplot
from cli_charts.registry import register

register("uniplot")(uniplot)