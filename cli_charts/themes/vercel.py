"""Vercel brand palette.

Vercel's famously minimal identity: pure black background, white primary,
electric blue (#0070F3) as accent.  Series colours stay high-contrast
against the black canvas so dashboards read cleanly at small sizes.
"""

PALETTE: dict = {
    # canvas / background
    "canvas":   (  0,   0,   0),  # pure black

    # axes frame
    "axes":     ( 35,  35,  35),  # dark charcoal

    # tick labels + title
    "ticks":    (234, 234, 234),  # near-white

    # 8 data series colours
    "series": [
        (  0, 112, 243),  # Vercel blue   (primary brand)
        (255, 255, 255),  # pure white
        (  0, 220, 220),  # cyan
        (240,  60, 120),  # hot pink
        (255, 200,   0),  # yellow
        (100, 200, 100),  # green
        (180,  80, 240),  # purple
        (255, 130,  30),  # orange
    ],

    # start from "clear" (white bg) then fully override -- pure black needs
    # canvas override applied before any plt call adds content
    "plt_base": "clear",
}
