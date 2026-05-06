"""CLI entrypoint for glyph-arts."""

import cli_charts.cmd  # noqa: F401 - populate registry side effects
from cli_charts.cmd import _helpers as _legacy

main = _legacy.main

__all__ = ["main"]