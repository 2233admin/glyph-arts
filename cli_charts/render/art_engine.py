"""Composable text art renderer for the ``glyph-arts art`` command."""
from __future__ import annotations

import sys
from io import StringIO

import pyfiglet
from rich import box as rich_box
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

try:
    import art as _art

    _HAS_ART = True
except ImportError:
    _art = None
    _HAS_ART = True


ART_FONTS = frozenset(pyfiglet.FigletFont.getFonts())
ART_GRADIENTS = {
    "sunset": ["#FF6B6B", "#FFA500", "#FFD700"],
    "ocean": ["#001E5C", "#00B4D8", "#90E0EF"],
    "viridis": ["#440154", "#3b528b", "#21908c", "#5dc863", "#fde725"],
    "rainbow": ["#FF0000", "#FF7F00", "#FFFF00", "#00FF00", "#0000FF", "#4B0082", "#9400D3"],
}
ART_FRAMES = {
    "single": rich_box.SQUARE,
    "double": rich_box.DOUBLE,
    "rounded": rich_box.ROUNDED,
    "ascii": rich_box.ASCII,
    "heavy": rich_box.HEAVY,
}

_DECORS = frozenset({"barcode", "snake", "dna", "random", "wave"})


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    value = value.lstrip("#")
    return int(value[0:2], 16), int(value[2:4], 16), int(value[4:6], 16)


def _lerp(a: int, b: int, t: float) -> int:
    return round(a + (b - a) * t)


def _color_at(stops: list[str], t: float) -> str:
    if len(stops) == 1:
        return stops[0]
    scaled = t * (len(stops) - 1)
    idx = min(int(scaled), len(stops) - 2)
    local = scaled - idx
    c0 = _hex_to_rgb(stops[idx])
    c1 = _hex_to_rgb(stops[idx + 1])
    rgb = tuple(_lerp(c0[i], c1[i], local) for i in range(3))
    return f"#{rgb[0]:02X}{rgb[1]:02X}{rgb[2]:02X}"


def _gradient_text(value: str, gradient: str | None, no_color: bool) -> str | Text:
    if no_color or not gradient or gradient == "none":
        return value
    stops = ART_GRADIENTS.get(gradient)
    if not stops:
        return value
    chars = [ch for ch in value if ch != "\n"]
    total = max(len(chars) - 1, 1)
    seen = 0
    out = Text()
    for ch in value:
        if ch == "\n":
            out.append(ch)
            continue
        out.append(ch, style=_color_at(stops, seen / total))
        seen += 1
    return out


def _decorate(value: str, decor: str | None) -> str:
    if not decor or decor == "none":
        return value
    if decor == "random":
        decor = "wave"
    try:
        line = _art.decor(decor) if _art is not None else _fallback_decor(decor)
    except Exception:
        return value
    line = str(line).rstrip("\n")
    if not line:
        return value
    return f"{line}\n{value.rstrip()}\n{line}\n"


def _fallback_decor(decor: str) -> str:
    return {
        "barcode": "|||| ||| || ||||| |||",
        "snake": "~^~^~^~^~^~^~^~^~^~",
        "dna": "AT CG TA GC AT CG TA GC",
        "wave": "~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~",
    }.get(decor, "")


def _render_to_string(renderable: object, width: int, no_color: bool) -> str:
    stream = StringIO()
    console = Console(
        file=stream,
        width=max(width, 20),
        force_terminal=not no_color,
        color_system=None if no_color else "truecolor",
        no_color=no_color,
        highlight=False,
    )
    console.print(renderable, end="")
    return stream.getvalue()


def render_art(
    text: str,
    font: str,
    decor: str | None,
    frame: str | None,
    gradient: str | None,
    theme: str,
    w: int,
    h: int,
    no_color: bool,
    output: str,
) -> int:
    del theme, h
    if not text:
        print("ERROR:schema: art requires non-empty text", file=sys.stderr)
        return 1
    if not _HAS_ART:
        print("ERROR:dep: art not installed (pip install glyph-arts[art])", file=sys.stderr)
        return 2
    if font not in ART_FONTS:
        available = ", ".join(sorted(ART_FONTS)[:12])
        print(f"ERROR:schema: unknown font {font}; available: {available}, ...", file=sys.stderr)
        return 1
    if decor and decor not in _DECORS:
        print(f"ERROR:schema: unknown decor {decor}; available: barcode, dna, random, snake, wave", file=sys.stderr)
        return 1

    try:
        rendered = pyfiglet.figlet_format(text, font=font, width=w).rstrip("\n")
    except pyfiglet.FontNotFound:
        rendered = _art.text2art(text, font=font).rstrip("\n") if _art else text

    rendered = _decorate(rendered, decor)
    body = _gradient_text(rendered, gradient, no_color)
    frame_name = None if frame in (None, "none") else frame
    renderable: object = body
    if frame_name:
        renderable = Panel(body, box=ART_FRAMES[frame_name], expand=False)

    result = _render_to_string(renderable, w, no_color)
    if output:
        with open(output, "w", encoding="utf-8") as f:
            f.write(result)
    else:
        sys.stdout.write(result)
    return 0
