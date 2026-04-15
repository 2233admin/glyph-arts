"""Tesla brand palette.

Tesla's minimal high-tech aesthetic: deep navy (#171A20) background with
the signature red (#E82127) as primary data colour.  Supporting series use
cool metallics and electric accents.
"""

PALETTE: dict = {
    # canvas / background
    "canvas":   (23,  26,  32),   # Tesla's #171A20 near-black navy

    # axes frame
    "axes":     (45,  50,  60),   # dark steel

    # tick labels + title
    "ticks":    (210, 215, 222),  # cool silver-white

    # 8 data series colours
    "series": [
        (232,  33,  39),  # Tesla red    (primary brand)
        (200, 210, 220),  # platinum silver
        ( 65, 145, 215),  # electric blue
        ( 50, 195, 130),  # green (Model 3 trim)
        (245, 195,  55),  # amber (indicator yellow)
        (150, 160, 175),  # steel grey
        (220, 100,  50),  # copper orange
        (100, 180, 240),  # ice blue
    ],

    "plt_base": "dark",
}
