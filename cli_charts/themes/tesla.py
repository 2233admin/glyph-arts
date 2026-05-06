# This palette is inspired by Tesla, Inc.'s publicly published brand guidelines. glyph-arts is not affiliated with or endorsed by Tesla, Inc.
"""Tesla brand palette.

Tesla's minimal high-tech aesthetic: deep navy (#171A20) background with a
viridis data gradient for perceptual contrast in pixel output.
"""

GRADIENT = ['#440154', '#3b528b', '#21908c', '#5dc863', '#fde725']

PALETTE: dict = {
    # canvas / background
    "canvas":   (23,  26,  32),   # Tesla's #171A20 near-black navy

    # axes frame
    "axes":     (45,  50,  60),   # dark steel

    # tick labels + title
    "ticks":    (210, 215, 222),  # cool silver-white

    # 5 data series colours
    "series": [
        (68,   1,  84),
        (59,  82, 139),
        (33, 144, 140),
        (93, 200,  99),
        (253, 231, 37),
    ],
    "gradient": GRADIENT,

    "plt_base": "dark",
}
