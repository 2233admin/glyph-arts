"""Terminal font capability detection for glyph-arts."""

from __future__ import annotations

import os

FontTier = str

_TIERS = {"ascii", "unicode", "unicode-extended", "nerd"}


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def detect_font_tier() -> FontTier:
    """Return the safest symbol tier for the current terminal."""
    override = os.environ.get("GLYPH_ARTS_FONT_TIER", "").strip().lower()
    if override in _TIERS:
        return override

    if _truthy(os.environ.get("NERD_FONT")):
        return "nerd"

    term_program = os.environ.get("TERM_PROGRAM", "")
    if term_program == "WarpTerminal":
        return "unicode-extended"
    if term_program == "vscode":
        return "unicode"

    if os.environ.get("WT_SESSION"):
        return "unicode"

    return "unicode"
