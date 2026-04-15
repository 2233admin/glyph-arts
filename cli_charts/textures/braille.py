"""Braille texture -- smooth sub-cell resolution curves.

Uses plotext's "braille" marker family (U+2800-U+28FF Braille Patterns).
Each terminal cell carries a 2x4 dot grid (8 sub-pixels), giving line
charts and scatter plots the smoothest appearance possible in a terminal.
Ideal for continuous signals (audio, sensor data, mathematical functions).
"""

TEXTURE: dict = {
    "point_marker": "braille",  # plotext named marker -> 2x4 braille dots
    "fill_marker":  "braille",  # braille fill for bar charts (lighter look)
    "description":  "Braille Unicode -- smoothest curves, finest sub-cell resolution",
}
