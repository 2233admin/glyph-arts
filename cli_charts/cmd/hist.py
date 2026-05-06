from cli_charts.cmd._helpers import hist
from cli_charts.registry import register

register("hist")(hist)