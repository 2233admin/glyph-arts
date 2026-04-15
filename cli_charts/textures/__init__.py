"""Terminal texture sets for glyph-arts.

A texture controls *how* data is drawn (marker characters, fill density)
independently of colour.  Applied via --texture block|braille|shade|hatch.

Each texture dict has the keys:
    point_marker  str   -- plotext marker name or Unicode char for
                           line/scatter/step data points
    fill_marker   str   -- marker used for bar/histogram bar fill
    description   str   -- human-readable one-liner
"""

from .block   import TEXTURE as _BLOCK
from .braille import TEXTURE as _BRAILLE
from .shade   import TEXTURE as _SHADE
from .hatch   import TEXTURE as _HATCH

CUSTOM_TEXTURES: dict[str, dict] = {
    "block":   _BLOCK,
    "braille": _BRAILLE,
    "shade":   _SHADE,
    "hatch":   _HATCH,
}

# Default texture (matches plotext's own default visual)
DEFAULT = "block"


def get_texture(name: str) -> dict | None:
    """Return the texture dict for *name*, or None if unknown."""
    return CUSTOM_TEXTURES.get(name)
