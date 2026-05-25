from cli_charts.cmd._helpers import wave_command
from cli_charts.registry import register

register("wave")(wave_command)
