"""ASCII mascot splash frames and 4-bit semantic color rendering."""

FRAME_ROWS = 11
FRAME_COLS = 78

ROLES = {
    "block_text",
    "border",
    "eyes",
    "head",
    "shine",
    "stars",
    "text",
    "accent",
    "dim",
}

ANSI_CODES = {
    "block_text": "37",
    "border": "90",
    "eyes": "97",
    "head": "36",
    "shine": "93",
    "stars": "95",
    "text": "39",
    "accent": "96",
    "dim": "30;1",
}

_LOGO = "GLYPH-ARTS"
_LEFT_PAD = 34


def _line(text: str = "", left_pad: int = 0) -> str:
    value = (" " * left_pad) + text
    return value[:FRAME_COLS].ljust(FRAME_COLS)


def _frame(label: str, shimmer: str = " ") -> str:
    stars = f"{shimmer}*{shimmer}" if shimmer != " " else " * "
    rows = [
        _line(),
        _line("+---------------- GLYPH ARTS ----------------+", 15),
        _line("|                                            |", 15),
        _line("|                                            |", 15),
        _line(label, _LEFT_PAD),
        _line("|                                            |", 15),
        _line(f"|                 {stars}        {stars}                 |", 15),
        _line("|                                            |", 15),
        _line("+--------------------------------------------+", 15),
        _line(),
        _line(),
    ]
    return "\n".join(rows)


_REVEAL_FRAMES = [_frame(_LOGO[:i]) for i in range(1, 11)]
_STATIC_FRAMES = [_frame(_LOGO) for _ in range(5)]
_SHIMMER_FRAMES = [_frame(_LOGO, shimmer) for shimmer in (".", " ", ".", " ", ".")]

FRAMES = _REVEAL_FRAMES + _STATIC_FRAMES + _SHIMMER_FRAMES


def _role_for_char(ch: str, row_idx: int) -> str:
    if ch in "+-|":
        return "border"
    if ch == "*":
        return "stars"
    if ch == ".":
        return "shine"
    if row_idx == 4 and ch != " ":
        return "block_text"
    if ch != " ":
        return "accent"
    return "text"


COLOR_MAP = [
    [[_role_for_char(ch, row_idx) for ch in row] for row_idx, row in enumerate(frame.splitlines())]
    for frame in FRAMES
]


def render_frame(index: int, tty: bool = True) -> str:
    """Render one frame as plain ASCII or ANSI-colored text."""
    frame = FRAMES[index]
    if not tty:
        return frame

    rendered_rows = []
    for row, role_row in zip(frame.splitlines(), COLOR_MAP[index], strict=True):
        parts = []
        current_role = None
        for ch, role in zip(row, role_row, strict=True):
            if role != current_role:
                parts.append(f"\x1b[{ANSI_CODES[role]}m")
                current_role = role
            parts.append(ch)
        parts.append("\x1b[0m")
        rendered_rows.append("".join(parts))
    return "\n".join(rendered_rows)
