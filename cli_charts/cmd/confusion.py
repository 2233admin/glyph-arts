from cli_charts.cmd._helpers import confusion
from cli_charts.registry import register

register("confusion")(confusion)