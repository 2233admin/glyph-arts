"""Shade texture -- half-density block shading.

Uses U+2593 DARK SHADE (▓) for bar fills and plotext's "sd" (standard-
definition half-block ▀▄) for point markers.  Visually lighter than
full-block while remaining clearly readable.  Good default for dashboard
panels where multiple charts share the same screen space.
"""

TEXTURE: dict = {
    "point_marker": "sd",   # plotext named marker -> half-block ▀▄ chars
    "fill_marker":  "\u2593",  # U+2593 DARK SHADE ▓
    "description":  "Half-density shade blocks -- balanced visual weight",
}
