"""Rich status command."""

from __future__ import annotations

import sys
import time

from rich.console import Console
from rich.status import Status

STATUS_STYLES = {
    "ok": ("green", "[OK]"),
    "warn": ("yellow", "[WARN]"),
    "error": ("red", "[ERROR]"),
    "info": ("cyan", "[INFO]"),
    "loading": ("magenta", "[...]"),
}


def render_status(kind: str, message: str, *, spinner: str = "dots", no_color: bool = False) -> int:
    if kind not in STATUS_STYLES:
        print(
            f"ERROR:schema: kind must be one of: {', '.join(sorted(STATUS_STYLES))}",
            file=sys.stderr,
        )
        return 1

    style, label = STATUS_STYLES[kind]
    console = Console(no_color=no_color, force_terminal=not no_color, legacy_windows=False)
    try:
        with Status(message, spinner=spinner, console=console):
            time.sleep(0.01)
    except KeyError:
        print(f"ERROR:schema: unknown spinner: {spinner}", file=sys.stderr)
        return 1

    console.print(f"[{style}]{label}[/{style}] {message}")
    return 0
