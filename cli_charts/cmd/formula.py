from cli_charts.cmd._helpers import formula, formula_pretty
from cli_charts.registry import register

register("formula")(formula)
register("math")(formula)
register("formula-pretty")(formula_pretty)
register("math-pretty")(formula_pretty)
