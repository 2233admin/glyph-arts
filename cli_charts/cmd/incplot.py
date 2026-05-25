from cli_charts.cmd._helpers import incplot
from cli_charts.registry import register

register("incplot")(incplot)
