from cli_charts.cmd._helpers import gauge
from cli_charts.registry import register

register("gauge")(gauge)