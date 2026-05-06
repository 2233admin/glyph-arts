from cli_charts.cmd._helpers import plotille_chart
from cli_charts.registry import register

register("plotille")(plotille_chart)