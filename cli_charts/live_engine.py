"""Small no-extra-dependency live demo engine."""

from __future__ import annotations

import collections
import random
import sys
import time
from collections.abc import Iterable


def run_live(
    source: str,
    *,
    window: int,
    interval: float,
    duration: float,
    title: str,
    width: int,
    height: int,
    theme: str,
    no_color: bool,
) -> int:
    """Render a sliding-window line chart from random values or stdin."""
    from rich.console import Console
    from rich.live import Live
    from rich.text import Text

    if source not in {"random", "stdin"}:
        print("ERROR:schema: live source must be random or stdin", file=sys.stderr)
        return 1

    values: collections.deque[float] = collections.deque(maxlen=window if window > 0 else None)
    console = Console(no_color=no_color)
    start = time.monotonic()

    def frame() -> Text:
        from cli_charts.cmd._helpers import _capture_stdout, line

        ys = list(values) or [0.0]
        data = {"label": title or source, "x": list(range(len(ys))), "y": ys}
        rendered = _capture_stdout(
            lambda: line(data, title or f"live {source}", width, height, theme, no_color=no_color)
        ).rstrip()
        return Text.from_ansi(rendered)

    try:
        with Live(frame(), console=console, refresh_per_second=max(1.0, 1.0 / max(interval, 0.01)), transient=False) as live:
            for value in _values(source):
                values.append(value)
                live.update(frame())
                if duration > 0 and time.monotonic() - start >= duration:
                    break
                time.sleep(max(0.0, interval))
    except KeyboardInterrupt:
        return 0
    return 0


def _values(source: str) -> Iterable[float]:
    if source == "random":
        current = 50.0
        while True:
            current = max(0.0, min(100.0, current + random.uniform(-8.0, 8.0)))
            yield current
    else:
        for line in sys.stdin:
            parts = line.strip().split()
            if not parts:
                continue
            try:
                yield float(parts[-1])
            except ValueError:
                continue
