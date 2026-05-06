from cli_charts.cmd._helpers import dashboard
from cli_charts.registry import register

register("dashboard")(dashboard)