"""Claude Code subagent named-color palette."""

NAMED_COLORS = {
    "red": (239, 68, 68),
    "blue": (59, 130, 246),
    "green": (34, 197, 94),
    "yellow": (234, 179, 8),
    "purple": (168, 85, 247),
    "orange": (249, 115, 22),
    "pink": (236, 72, 153),
    "cyan": (6, 182, 212),
}

PALETTE: dict = {
    "canvas": (12, 12, 12),
    "axes": (70, 70, 70),
    "ticks": (235, 235, 235),
    "series": list(NAMED_COLORS.values()),
    "plt_base": "dark",
}
