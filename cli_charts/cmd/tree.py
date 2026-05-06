from cli_charts.cmd._helpers import tree
from cli_charts.registry import register

register("tree")(tree)