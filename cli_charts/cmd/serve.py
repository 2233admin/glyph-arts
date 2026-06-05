from cli_charts.cmd._helpers import serve_command
from cli_charts.registry import register

register("serve")(serve_command)
