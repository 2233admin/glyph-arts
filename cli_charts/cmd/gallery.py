from cli_charts.cmd._helpers import gallery_command
from cli_charts.registry import register

register("gallery")(gallery_command)