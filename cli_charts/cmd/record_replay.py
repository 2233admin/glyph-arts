from cli_charts.cmd._helpers import record_replay_command
from cli_charts.registry import register

register("record-replay")(record_replay_command)