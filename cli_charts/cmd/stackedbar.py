from cli_charts.cmd._helpers import stackedbar
from cli_charts.registry import register

register("stackedbar")(stackedbar)