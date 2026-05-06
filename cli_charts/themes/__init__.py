"""Brand palette themes for glyph-arts.

Custom themes that extend plotext's built-in theme system with 24-bit RGB
brand palettes. Applied via --theme claude|linear|tesla|vercel.

Each palette dict has the keys:
    canvas  (R,G,B)  -- chart background
    axes    (R,G,B)  -- axes frame
    ticks   (R,G,B)  -- tick labels and title text
    series  list of (R,G,B)  -- data series colors (8 entries)
    plt_base  str|None  -- plotext base theme to start from, then override
"""

from .claude import PALETTE as _CLAUDE
from .claude_ansi import CLAUDE_DARK_ANSI as _CLAUDE_DARK_ANSI
from .claude_ansi import CLAUDE_LIGHT_ANSI as _CLAUDE_LIGHT_ANSI
from .linear import PALETTE as _LINEAR
from .subagent_rainbow import PALETTE as _SUBAGENT_RAINBOW
from .tesla import PALETTE as _TESLA
from .vercel import PALETTE as _VERCEL

CUSTOM_THEMES: dict[str, dict] = {
    "claude": _CLAUDE,
    "claude-dark-ansi": _CLAUDE_DARK_ANSI,
    "claude-light-ansi": _CLAUDE_LIGHT_ANSI,
    "linear": _LINEAR,
    "subagent-rainbow": _SUBAGENT_RAINBOW,
    "tesla":  _TESLA,
    "vercel": _VERCEL,
}


def get_palette(name: str) -> dict | None:
    """Return the palette dict for *name*, or None if it's a built-in plotext theme."""
    return CUSTOM_THEMES.get(name)


def get_gradient(name: str) -> list[str] | None:
    """Return a theme's gradient as hex strings, if one is defined."""
    palette = get_palette(name)
    if not palette:
        return None
    gradient = palette.get("gradient")
    if gradient:
        return list(gradient)
    series = palette.get("series")
    if not series:
        return None
    return ["#{:02x}{:02x}{:02x}".format(*rgb) for rgb in series]
