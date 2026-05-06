from cli_charts.cmd._helpers import to_hyperframes_command
from cli_charts.registry import register

register("to-hyperframes")(to_hyperframes_command)