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
from .linear import PALETTE as _LINEAR
from .tesla  import PALETTE as _TESLA
from .vercel import PALETTE as _VERCEL

CUSTOM_THEMES: dict[str, dict] = {
    "claude": _CLAUDE,
    "linear": _LINEAR,
    "tesla":  _TESLA,
    "vercel": _VERCEL,
}


def get_palette(name: str) -> dict | None:
    """Return the palette dict for *name*, or None if it's a built-in plotext theme."""
    return CUSTOM_THEMES.get(name)
