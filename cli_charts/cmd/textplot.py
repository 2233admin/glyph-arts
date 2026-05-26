from cli_charts.cmd._helpers import textplot
from cli_charts.registry import register

register("textplot")(textplot)
