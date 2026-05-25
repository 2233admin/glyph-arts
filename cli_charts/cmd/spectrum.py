from cli_charts.cmd._helpers import spectrum
from cli_charts.registry import register

register("spectrum")(spectrum)
