"""cli_charts.charts -- shared, chart-type-agnostic helpers.

Extracted from the legacy god-file cli_charts/cmd/_helpers.py as part of the
charts-split refactor. Phase 1 moves only non-chart helpers here; chart bodies
(line, bar, scatter, ...) stay in cmd/_helpers.py until later phases.
"""
from . import _utils
