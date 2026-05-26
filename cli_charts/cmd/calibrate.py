from cli_charts.cmd._helpers import calibrate
from cli_charts.registry import register

register("calibrate")(calibrate)
