"""OSC 8 hyperlink helpers."""

from __future__ import annotations

import os
import sys


def supports_osc8() -> bool:
    """Best-effort OSC 8 capability detection."""
    if os.environ.get("GLYPH_ARTS_OSC8") == "1":
        return True
    if os.environ.get("GLYPH_ARTS_OSC8") == "0":
        return False
    if not sys.stdout.isatty():
        return False
    term_program = os.environ.get("TERM_PROGRAM", "").lower()
    if term_program in {"iterm.app", "wezterm", "vscode", "ghostty"}:
        return True
    if os.environ.get("WT_SESSION") or os.environ.get("VTE_VERSION"):
        return True
    return False


def link(label: object, url: str, *, force: bool | None = None) -> str:
    """Return *label* as an OSC 8 hyperlink, or a readable fallback."""
    text = str(label)
    if not url:
        return text
    enabled = supports_osc8() if force is None else force
    if not enabled:
        return f"{text} ({url})"
    return f"\x1b]8;;{url}\x1b\\{text}\x1b]8;;\x1b\\"


def link_labels(labels: list[object], urls: str | list[str]) -> list[str]:
    if isinstance(urls, str):
        return [link(label, urls) for label in labels]
    return [link(label, urls[i]) if i < len(urls) else str(label) for i, label in enumerate(labels)]
