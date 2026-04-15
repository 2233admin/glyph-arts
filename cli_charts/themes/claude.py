"""Claude (Anthropic) brand palette.

Anchored on Anthropic's signature terracotta coral (#CC785C) against a
warm near-black background.  Series colors cycle through warm naturals
(ember, amber, sage, sand, rose, sky) so multi-series charts feel cohesive
rather than garish.
"""

PALETTE: dict = {
    # canvas / background
    "canvas":   (15,  13,  11),   # almost black, warm tint

    # axes frame
    "axes":     (40,  35,  30),   # dark warm brown

    # tick labels + title
    "ticks":    (220, 210, 195),  # warm off-white

    # 8 data series colours
    "series": [
        (204, 120,  92),  # Claude coral  (primary brand)
        (222, 170,  90),  # amber
        (145, 185, 140),  # sage green
        ( 96, 160, 195),  # sky blue
        (195, 145, 175),  # dusty rose
        (230, 200, 130),  # sand gold
        (130, 175, 160),  # seafoam
        (180,  95,  80),  # deep ember
    ],

    # start from plotext "dark" then override colours above
    "plt_base": "dark",
}
