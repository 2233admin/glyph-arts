from cli_charts.cmd._helpers import chat
from cli_charts.registry import register

register("chat")(chat)
