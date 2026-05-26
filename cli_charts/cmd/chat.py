from cli_charts.cmd._helpers import chat  # type: ignore[attr-defined]
from cli_charts.registry import register

register("chat")(chat)
