"""One-shot mascot splash with a first-run sentinel."""

from __future__ import annotations

import argparse
import os
import sys
import time
from collections.abc import Callable
from pathlib import Path
from typing import TextIO

from .mascot import FRAMES, render_frame

SENTINEL = ".cache/glyph-arts/splash-shown"
FRAME_DELAY = 0.075


def sentinel_path() -> Path:
    return Path.home() / SENTINEL


def _disabled(no_splash: bool = False) -> bool:
    return no_splash or os.environ.get("GLYPH_ARTS_NO_SPLASH") == "1"


def play_splash(stdout: TextIO = sys.stdout, sleep: Callable[[float], None] | None = None) -> bool:
    if not stdout.isatty():
        return False

    sleeper = sleep or time.sleep
    try:
        stdout.write("\x1b[?25l")
        for idx in range(len(FRAMES)):
            stdout.write("\x1b[H\x1b[J")
            stdout.write(render_frame(idx, tty=True))
            stdout.flush()
            sleeper(FRAME_DELAY)
        stdout.write("\n")
        stdout.flush()
    except KeyboardInterrupt:
        return True
    finally:
        stdout.write("\x1b[?25h")
        stdout.flush()
    return True


def _write_sentinel() -> None:
    path = sentinel_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text("shown\n", encoding="ascii")


def maybe_play_first_run(
    no_splash: bool = False,
    stdout: TextIO = sys.stdout,
    sleep: Callable[[float], None] | None = None,
) -> bool:
    if _disabled(no_splash):
        return False
    if not stdout.isatty():
        return False
    if sentinel_path().exists():
        return False
    played = play_splash(stdout=stdout, sleep=sleep)
    if played:
        _write_sentinel()
    return played


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Play the glyph-arts mascot splash")
    parser.add_argument("--no-splash", action="store_true", help="Skip the splash")
    args = parser.parse_args(argv)
    if _disabled(args.no_splash):
        return 0
    play_splash(sys.stdout)
    return 0
