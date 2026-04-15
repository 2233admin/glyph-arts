"""Block texture -- solid full-block Unicode fill.

Uses plotext's built-in "dot" marker (maps to U+2588 FULL BLOCK █).
Maximum density: every terminal cell is filled.  Best for bar charts
where you want bold, unambiguous category boundaries.
"""

TEXTURE: dict = {
    "point_marker": "dot",    # plotext named marker -> █ full block
    "fill_marker":  "dot",    # bar/histogram fill
    "description":  "Solid full-block fill -- maximum density, highest contrast",
}
