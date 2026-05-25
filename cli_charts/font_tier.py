"""Terminal font capability detection for glyph-arts."""

from __future__ import annotations

import os

from cli_charts.terminal_profiles import detect_terminal_profile

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

    return detect_terminal_profile().font_tier
