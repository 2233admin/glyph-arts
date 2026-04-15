"""Hatch texture -- lightweight cross-hatch pattern.

Uses U+2591 LIGHT SHADE (░) for bar fills and a simple "+" cross for
point markers.  The lowest visual weight of the four textures -- useful
when multiple overlapping series would otherwise create a solid mass, or
when the background colour already provides structure (e.g. the matrix
or retro plotext themes).
"""

TEXTURE: dict = {
    "point_marker": "+",        # simple ASCII cross
    "fill_marker":  "\u2591",   # U+2591 LIGHT SHADE ░
    "description":  "Light hatch -- minimum fill weight, good for overlapping series",
}
