from cli_charts.cmd._helpers import rich_live
from cli_charts.registry import register

register("rich_live")(rich_live)