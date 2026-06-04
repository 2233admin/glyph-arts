from cli_charts.cmd._helpers import to_drawio_command
from cli_charts.registry import register

register("to-drawio")(to_drawio_command)
