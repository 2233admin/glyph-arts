"""Linear brand palette.

Linear's design language: near-black void background, precise indigo
primary (#5E6AD2), clean typography.  Series colours lean cool-toned
(indigo, violet, teal, sky, green, amber) matching Linear's issue-label
spectrum.
"""

PALETTE: dict = {
    # canvas / background
    "canvas":   (13,  13,  19),   # Linear's characteristic void-black

    # axes frame
    "axes":     (30,  30,  45),   # dark indigo tint

    # tick labels + title
    "ticks":    (194, 197, 215),  # cool blue-white

    # 8 data series colours
    "series": [
        ( 94, 106, 210),  # Linear indigo  (primary brand)
        (130,  80, 220),  # violet
        ( 50, 185, 185),  # teal
        ( 75, 160, 230),  # sky blue
        ( 80, 200, 120),  # mint green
        (240, 185,  60),  # amber
        (220,  90, 130),  # rose
        (155, 125, 240),  # lavender
    ],

    "plt_base": "dark",
}
