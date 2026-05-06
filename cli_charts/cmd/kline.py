from cli_charts.cmd._helpers import kline
from cli_charts.registry import register

register("kline")(kline)