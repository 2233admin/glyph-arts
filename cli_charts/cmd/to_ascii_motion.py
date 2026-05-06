from cli_charts.cmd._helpers import to_ascii_motion_command
from cli_charts.registry import register

register("to-ascii-motion")(to_ascii_motion_command)