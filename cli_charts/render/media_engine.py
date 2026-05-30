"""Terminal media renderers for images and video."""

from __future__ import annotations

import glob
import os
import shutil
import subprocess
import sys
import tempfile
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any

_TEXT_SYMBOL_SETS = {
    "ascii",
    "gray",
    "grayscale",
    "greyscale",
    "shade",
    "shades",
    "block",
    "blocks",
}
_HALF_SYMBOL_SETS = {"half", "vhalf", "upper-half", "upper_half", "color", "ansi"}

_ASCII_RAMP = " .:-=+*#%@"
_SHADE_RAMP = " .:-=+*#%@"
_UNICODE_SHADE_RAMP = " ░▒▓█"
_BLOCK_RAMP = " ▁▂▃▄▅▆▇█"
_IMAGE_MODES = {"auto", "raw", "detail", "edge", "silhouette"}
_IMAGE_STYLES = {
    "classic",
    "braille",
    "block",
    "edge",
    "dot-cross",
    "halftone",
    "particles",
    "retro-art",
    "terminal",
}
_COLOR_MODES = {"grayscale", "original", "full", "matrix", "amber", "custom"}
_DITHER_MODES = {"none", "floyd-steinberg", "bayer", "atkinson"}
_BACKGROUND_MODES = {"dark", "light", "transparent"}
_CHAFA_FORMATS = {"auto", "symbols", "sixels", "sixel", "kitty", "iterm"}
_CHAFA_COLOR_MODES = {"auto", "none", "2", "16", "240", "256", "full"}
_RATIO_PRESETS = {
    "original": None,
    "16:9": (16, 9),
    "4:3": (4, 3),
    "1:1": (1, 1),
    "3:4": (3, 4),
    "9:16": (9, 16),
}
_CLASSIC_RAMP = "$@B%8&WM#*oahkbdpqwmZO0QLCJUYXzcvunxrjft/\\|()1{}[]?-_+~<>i!lI;:,\"^`. "
_DOT_CROSS_RAMP = "█▓#X*x+:· "
_HALFTONE_RAMP = "@O0o·. "
_RETRO_RAMP = "█▓▒░#%=+:. "
_PARTICLE_CHARS = ["•", "·", "‧", "*", "∙", "+"]
_BRAILLE_DOTS = ((0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80))
_NAMED_COLORS = {
    "red": "#ff0000",
    "green": "#008000",
    "blue": "#0000ff",
    "yellow": "#ffff00",
    "cyan": "#00ffff",
    "magenta": "#ff00ff",
    "orange": "#ffa500",
    "purple": "#800080",
    "pink": "#ffc0cb",
    "lime": "#00ff00",
    "teal": "#008080",
    "navy": "#000080",
    "maroon": "#800000",
    "olive": "#808000",
    "coral": "#ff7f50",
    "salmon": "#fa8072",
    "gold": "#ffd700",
    "indigo": "#4b0082",
    "violet": "#ee82ee",
    "crimson": "#dc143c",
    "turquoise": "#40e0d0",
    "tomato": "#ff6347",
    "chocolate": "#d2691e",
    "firebrick": "#b22222",
    "dodgerblue": "#1e90ff",
    "limegreen": "#32cd32",
    "hotpink": "#ff69b4",
    "skyblue": "#87ceeb",
    "springgreen": "#00ff7f",
    "white": "#ffffff",
    "silver": "#c0c0c0",
    "gray": "#808080",
    "grey": "#808080",
}


@dataclass
class AsciiImage:
    chars: list[list[str]]
    brightness: list[list[int]]
    colors: list[list[tuple[int, int, int]]]

    @property
    def rows(self) -> int:
        return len(self.chars)

    @property
    def cols(self) -> int:
        return max((len(row) for row in self.chars), default=0)


def _load_pillow():
    try:
        from PIL import Image, ImageOps
    except ImportError:
        return None, None
    return Image, ImageOps


def _resample_filter(Image, name: str):
    resampling = getattr(Image, "Resampling", Image)
    return getattr(resampling, name)


def _fit_terminal_size(src_w: int, src_h: int, max_cols: int, max_rows: int) -> tuple[int, int]:
    """Fit image dimensions into terminal cells while preserving visual aspect."""
    max_cols = max(1, int(max_cols))
    max_rows = max(1, int(max_rows))
    src_w = max(1, int(src_w))
    src_h = max(1, int(src_h))

    # A terminal cell is roughly twice as tall as it is wide. Keeping that
    # correction here makes square images stay square in a monospace chat block.
    cell_aspect = 2.0
    cols = max_cols
    rows = max(1, round((src_h / src_w) * cols / cell_aspect))
    if rows > max_rows:
        rows = max_rows
        cols = max(1, round((src_w / src_h) * rows * cell_aspect))
    return min(cols, max_cols), min(rows, max_rows)


def _luminance(rgb: tuple[int, int, int]) -> int:
    r, g, b = rgb
    return round(0.2126 * r + 0.7152 * g + 0.0722 * b)


def _ansi_fg_bg(top: tuple[int, int, int], bottom: tuple[int, int, int]) -> str:
    tr, tg, tb = top
    br, bg, bb = bottom
    return f"\x1b[38;2;{tr};{tg};{tb};48;2;{br};{bg};{bb}m▀"


def _pick_text_ramp(symbols: str) -> str:
    normalized = (symbols or "").strip().lower()
    if normalized in {"shade", "shades"}:
        return _UNICODE_SHADE_RAMP
    if normalized in {"block", "blocks"}:
        return _BLOCK_RAMP
    return _ASCII_RAMP if normalized in {"ascii", "gray", "grayscale", "greyscale"} else _SHADE_RAMP


def _background_from_corners(image) -> tuple[int, int, int]:
    """Estimate a flat background color from the four image corners."""
    Image, _ = _load_pillow()
    sample_w = min(96, max(8, image.width))
    sample_h = min(96, max(8, image.height))
    small = image.resize((sample_w, sample_h), _resample_filter(Image, "BILINEAR"))
    margin = max(2, min(sample_w, sample_h) // 8)
    boxes = [
        (0, 0, margin, margin),
        (sample_w - margin, 0, sample_w, margin),
        (0, sample_h - margin, margin, sample_h),
        (sample_w - margin, sample_h - margin, sample_w, sample_h),
    ]
    pixels = []
    for box in boxes:
        pixels.extend(small.crop(box).getdata())
    count = max(1, len(pixels))
    return tuple(round(sum(pixel[i] for pixel in pixels) / count) for i in range(3))


def _mask_threshold(values: list[int]) -> int:
    if not values:
        return 28
    mean = sum(values) / len(values)
    variance = sum((value - mean) ** 2 for value in values) / len(values)
    # Corner samples describe background texture/noise. Anything clearly beyond
    # that is foreground. Clamp so flat backgrounds still crop, but gradients do
    # not explode into all-foreground.
    return round(max(18, min(80, mean + variance**0.5 * 3 + 8)))


def _foreground_mask(image):
    """Return a foreground mask by comparing pixels with the estimated background."""
    Image, _ = _load_pillow()
    from PIL import ImageChops, ImageFilter

    bg = _background_from_corners(image)
    bg_image = Image.new("RGB", image.size, bg)
    diff = ImageChops.difference(image.convert("RGB"), bg_image).convert("L")

    sample_w = min(96, max(8, diff.width))
    sample_h = min(96, max(8, diff.height))
    small = diff.resize((sample_w, sample_h), _resample_filter(Image, "BILINEAR"))
    margin = max(2, min(sample_w, sample_h) // 8)
    corner_values = []
    for x0, y0, x1, y1 in (
        (0, 0, margin, margin),
        (sample_w - margin, 0, sample_w, margin),
        (0, sample_h - margin, margin, sample_h),
        (sample_w - margin, sample_h - margin, sample_w, sample_h),
    ):
        corner_values.extend(small.crop((x0, y0, x1, y1)).getdata())
    threshold = _mask_threshold(corner_values)
    mask = diff.point(lambda value: 255 if value >= threshold else 0)
    return mask.filter(ImageFilter.MaxFilter(5)).filter(ImageFilter.MinFilter(3))


def _crop_to_mask(image, mask, *, padding_ratio: float = 0.045):
    bbox = mask.getbbox()
    if not bbox:
        return image, mask
    x0, y0, x1, y1 = bbox
    pad = max(1, round(max(image.width, image.height) * padding_ratio))
    x0 = max(0, x0 - pad)
    y0 = max(0, y0 - pad)
    x1 = min(image.width, x1 + pad)
    y1 = min(image.height, y1 + pad)
    if (x1 - x0) * (y1 - y0) >= image.width * image.height * 0.96:
        return image, mask
    crop = (x0, y0, x1, y1)
    return image.crop(crop), mask.crop(crop)


def _prepare_image_layers(image, mode: str, trim: bool):
    normalized_mode = "detail" if mode == "auto" else mode
    if normalized_mode == "raw":
        return image, None, normalized_mode
    mask = _foreground_mask(image)
    if trim:
        image, mask = _crop_to_mask(image, mask)
    return image, mask, normalized_mode


def _tone_to_char(value: int, ramp: str, *, min_index: int = 0) -> str:
    scale = max(1, len(ramp) - 1 - min_index)
    index = min_index + max(0, min(255, value)) * scale // 255
    return ramp[min(len(ramp) - 1, index)]


def _crop_to_ratio(image, ratio: str):
    target = _RATIO_PRESETS.get(ratio)
    if target is None:
        return image
    target_w, target_h = target
    image_w, image_h = image.size
    image_aspect = image_w / image_h
    target_aspect = target_w / target_h
    if image_aspect > target_aspect:
        new_w = round(image_h * target_aspect)
        x0 = (image_w - new_w) // 2
        return image.crop((x0, 0, x0 + new_w, image_h))
    new_h = round(image_w / target_aspect)
    y0 = (image_h - new_h) // 2
    return image.crop((0, y0, image_w, y0 + new_h))


def _fit_style_size(image, w: int, h: int, style: str) -> tuple[int, int]:
    cols, rows = _fit_terminal_size(image.width, image.height, w, h)
    if style == "braille":
        cols = max(1, min(cols, max(1, image.width // 2)))
    return cols, rows


def _grid_from_image(image, cols: int, rows: int, *, invert: bool = False) -> tuple[list[list[int]], list[list[tuple[int, int, int]]]]:
    Image, _ = _load_pillow()
    resized = image.convert("RGB").resize((cols, rows), _resample_filter(Image, "LANCZOS"))
    brightness: list[list[int]] = []
    colors: list[list[tuple[int, int, int]]] = []
    for y in range(rows):
        brow = []
        crow = []
        for x in range(cols):
            rgb = resized.getpixel((x, y))
            lum = _luminance(rgb)
            brow.append(255 - lum if invert else lum)
            crow.append(rgb)
        brightness.append(brow)
        colors.append(crow)
    return brightness, colors


def _quantize(value: float, levels: int) -> float:
    step = 255.0 / max(levels - 1, 1)
    return max(0.0, min(255.0, round(value / step) * step))


def _apply_dither_grid(
    brightness: list[list[int]],
    algorithm: str,
    levels: int,
    strength: float,
) -> list[list[int]]:
    if algorithm == "none":
        return brightness
    rows = len(brightness)
    cols = max((len(row) for row in brightness), default=0)
    data = [[float(brightness[y][x]) for x in range(cols)] for y in range(rows)]
    if algorithm == "bayer":
        bayer4 = (
            (0, 8, 2, 10),
            (12, 4, 14, 6),
            (3, 11, 1, 9),
            (15, 7, 13, 5),
        )
        step = 255.0 / max(levels - 1, 1)
        for y in range(rows):
            for x in range(cols):
                offset = ((bayer4[y % 4][x % 4] / 16.0) - 0.5) * step * strength
                data[y][x] = _quantize(data[y][x] + offset, levels)
        return [[round(v) for v in row] for row in data]

    if algorithm not in {"floyd-steinberg", "atkinson"}:
        return brightness

    for y in range(rows):
        for x in range(cols):
            old_value = data[y][x]
            new_value = _quantize(old_value, levels)
            data[y][x] = new_value
            error = (old_value - new_value) * strength
            if algorithm == "floyd-steinberg":
                for nx, ny, weight in ((x + 1, y, 7 / 16), (x - 1, y + 1, 3 / 16), (x, y + 1, 5 / 16), (x + 1, y + 1, 1 / 16)):
                    if 0 <= nx < cols and 0 <= ny < rows:
                        data[ny][nx] = max(0.0, min(255.0, data[ny][nx] + error * weight))
            else:
                share = error / 8
                for nx, ny in ((x + 1, y), (x + 2, y), (x - 1, y + 1), (x, y + 1), (x + 1, y + 1), (x, y + 2)):
                    if 0 <= nx < cols and 0 <= ny < rows:
                        data[ny][nx] = max(0.0, min(255.0, data[ny][nx] + share))
    return [[round(v) for v in row] for row in data]


def _chars_from_ramp(brightness: list[list[int]], ramp: str) -> list[list[str]]:
    max_index = len(ramp) - 1
    return [[ramp[min(max_index, max(0, value) * max_index // 255)] for value in row] for row in brightness]


def _block_chars(brightness: list[list[int]]) -> list[list[str]]:
    return _chars_from_ramp([[255 - value for value in row] for row in brightness], "█▓▒░ ")


def _braille_chars(image, cols: int, rows: int, *, invert: bool = False) -> list[list[str]]:
    Image, _ = _load_pillow()
    dot_cols = max(2, cols * 2)
    dot_rows = max(4, rows * 4)
    resized = image.convert("L").resize((dot_cols, dot_rows), _resample_filter(Image, "LANCZOS"))
    chars = []
    for cy in range(rows):
        line = []
        for cx in range(cols):
            codepoint = 0x2800
            for dy in range(4):
                for dx in range(2):
                    lum = resized.getpixel((cx * 2 + dx, cy * 4 + dy))
                    value = 255 - lum if invert else lum
                    if value < 128:
                        codepoint |= _BRAILLE_DOTS[dy][dx]
            line.append(chr(codepoint))
        chars.append(line)
    return chars


def _edge_chars(image, cols: int, rows: int, *, invert: bool = False) -> list[list[str]]:
    Image, _ = _load_pillow()
    gray = image.convert("L").resize((cols, rows), _resample_filter(Image, "LANCZOS"))
    values = [[255 - gray.getpixel((x, y)) if invert else gray.getpixel((x, y)) for x in range(cols)] for y in range(rows)]
    chars = []
    for y in range(rows):
        line = []
        for x in range(cols):
            left = values[y][max(0, x - 1)]
            right = values[y][min(cols - 1, x + 1)]
            up = values[max(0, y - 1)][x]
            down = values[min(rows - 1, y + 1)][x]
            gx = right - left
            gy = down - up
            mag = abs(gx) + abs(gy)
            if mag < 42:
                line.append(" ")
            elif abs(gx) > abs(gy) * 1.8:
                line.append("|")
            elif abs(gy) > abs(gx) * 1.8:
                line.append("—")
            elif gx * gy > 0:
                line.append("\\")
            else:
                line.append("/")
        chars.append(line)
    return chars


def _particles_chars(brightness: list[list[int]]) -> list[list[str]]:
    import random

    rng = random.Random(42)
    chars = []
    for row in brightness:
        line = []
        for value in row:
            dark = (255 - value) / 255
            if rng.random() < dark * 0.9:
                line.append(_PARTICLE_CHARS[min(len(_PARTICLE_CHARS) - 1, int(dark * len(_PARTICLE_CHARS)))])
            else:
                line.append(" ")
        chars.append(line)
    return chars


def _parse_color(value: str | None) -> tuple[int, int, int]:
    color = (value or "white").strip().lower().lstrip("#")
    if color in _NAMED_COLORS:
        color = _NAMED_COLORS[color].lstrip("#")
    if len(color) != 6:
        raise ValueError(f"invalid color: {value!r}")
    return int(color[0:2], 16), int(color[2:4], 16), int(color[4:6], 16)


def _apply_color_mode(
    brightness: list[list[int]],
    colors: list[list[tuple[int, int, int]]],
    mode: str,
    background: str,
    custom_color: str | None,
) -> list[list[tuple[int, int, int]]]:
    if mode in {"original", "full"}:
        return colors
    if mode == "matrix":
        return [[(0, value, 0) for value in row] for row in brightness]
    if mode == "amber":
        return [[(value, round(value * 0.6), 0) for value in row] for row in brightness]
    if mode == "custom":
        r, g, b = _parse_color(custom_color)
        return [[(round(value / 255 * r), round(value / 255 * g), round(value / 255 * b)) for value in row] for row in brightness]
    if background == "light":
        return [[(255 - value, 255 - value, 255 - value) for value in row] for row in brightness]
    return [[(value, value, value) for value in row] for row in brightness]


def _build_ascii_image(
    image,
    cols: int,
    rows: int,
    *,
    style: str,
    color_mode: str,
    background: str,
    custom_color: str | None,
    dither: str,
    dither_strength: float,
    invert: bool,
) -> AsciiImage:
    if style == "retro-art":
        style = "block"
        color_mode = "amber" if color_mode == "grayscale" else color_mode
        dither = "atkinson" if dither == "none" else dither
        dither_strength = max(dither_strength, 0.9)
    elif style == "terminal":
        style = "classic"
        color_mode = "matrix" if color_mode == "grayscale" else color_mode

    brightness, colors = _grid_from_image(image, cols, rows, invert=invert)
    ramp_levels = {
        "classic": len(_CLASSIC_RAMP),
        "dot-cross": len(_DOT_CROSS_RAMP),
        "halftone": len(_HALFTONE_RAMP),
        "block": 5,
        "particles": len(_PARTICLE_CHARS),
    }.get(style, 10)
    brightness = _apply_dither_grid(brightness, dither, ramp_levels, dither_strength)

    if style == "braille":
        chars = _braille_chars(image, cols, rows, invert=invert)
    elif style == "edge":
        chars = _edge_chars(image, cols, rows, invert=invert)
    elif style == "block":
        chars = _block_chars(brightness)
    elif style == "dot-cross":
        chars = _chars_from_ramp(brightness, _DOT_CROSS_RAMP)
    elif style == "halftone":
        chars = _chars_from_ramp(brightness, _HALFTONE_RAMP)
    elif style == "particles":
        chars = _particles_chars(brightness)
    else:
        chars = _chars_from_ramp(brightness, _CLASSIC_RAMP)

    render_colors = _apply_color_mode(brightness, colors, color_mode, background, custom_color)
    return AsciiImage(chars=chars, brightness=brightness, colors=render_colors)


def _ascii_text(art: AsciiImage, *, rstrip: bool = True) -> str:
    lines = ["".join(row).rstrip() if rstrip else "".join(row) for row in art.chars]
    return "\n".join(lines).rstrip() + "\n"


def _ansi_text(art: AsciiImage) -> str:
    lines = []
    for y, row in enumerate(art.chars):
        parts = []
        for x, ch in enumerate(row):
            r, g, b = art.colors[y][x]
            parts.append(f"\x1b[38;2;{r};{g};{b}m{ch}")
        parts.append("\x1b[0m")
        lines.append("".join(parts).rstrip())
    return "\n".join(lines).rstrip() + "\n"


def _html_escape(text: str) -> str:
    import html

    return html.escape(text, quote=False)


def _write_ascii_export(
    art: AsciiImage,
    output: str,
    *,
    background: str,
    no_color: bool,
    font_size: int,
) -> int:
    suffix = Path(output).suffix.lower()
    if suffix in {"", ".txt"}:
        Path(output).write_text(_ascii_text(art), encoding="utf-8")
        return 0
    if suffix == ".ansi":
        Path(output).write_text(_ascii_text(art) if no_color else _ansi_text(art), encoding="utf-8")
        return 0
    if suffix == ".md":
        Path(output).write_text("```text\n" + _ascii_text(art).rstrip() + "\n```\n", encoding="utf-8")
        return 0
    if suffix == ".html":
        Path(output).write_text(_ascii_html(art, background=background, no_color=no_color, font_size=font_size), encoding="utf-8")
        return 0
    if suffix == ".svg":
        Path(output).write_text(_ascii_svg(art, background=background, no_color=no_color, font_size=font_size), encoding="utf-8")
        return 0
    if suffix == ".png":
        return _ascii_png(art, output, background=background, no_color=no_color, font_size=font_size)
    if suffix == ".gif":
        return _ascii_gif(art, output, background=background, no_color=no_color, font_size=font_size)
    if suffix == ".tsx":
        Path(output).write_text(_ascii_tsx(art, background=background, no_color=no_color), encoding="utf-8")
        return 0
    print(f"ERROR:schema: unsupported image output suffix: {suffix}", file=sys.stderr)
    return 1


def _background_css(background: str) -> str:
    return {"dark": "#000000", "light": "#ffffff", "transparent": "transparent"}.get(background, "#000000")


def _ascii_html(art: AsciiImage, *, background: str, no_color: bool, font_size: int) -> str:
    bg = _background_css(background)
    fg = "#111111" if background == "light" else "#f7f7f7"
    lines = []
    for y, row in enumerate(art.chars):
        parts = []
        for x, ch in enumerate(row):
            escaped = _html_escape(ch)
            if no_color:
                parts.append(escaped)
            else:
                r, g, b = art.colors[y][x]
                parts.append(f'<span style="color:rgb({r},{g},{b})">{escaped}</span>')
        lines.append("".join(parts))
    body = "\n".join(lines)
    return f"""<!DOCTYPE html>
<html lang="en">
<meta charset="UTF-8">
<title>glyph-arts image</title>
<style>
body {{ margin: 0; background: {bg}; color: {fg}; padding: 20px; }}
pre {{ font: {font_size}px/1 monospace; letter-spacing: 0; white-space: pre; }}
</style>
<pre>{body}</pre>
</html>
"""


def _ascii_svg(art: AsciiImage, *, background: str, no_color: bool, font_size: int) -> str:
    char_w = font_size * 0.62
    char_h = font_size
    width = max(1, art.cols) * char_w
    height = max(1, art.rows) * char_h
    bg = _background_css(background)
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width:.0f} {height:.0f}" width="{width:.0f}" height="{height:.0f}">',
    ]
    if background != "transparent":
        parts.append(f'<rect width="100%" height="100%" fill="{bg}"/>')
    for y, row in enumerate(art.chars):
        for x, ch in enumerate(row):
            if ch == " ":
                continue
            if no_color:
                fill = "#111111" if background == "light" else "#f7f7f7"
            else:
                r, g, b = art.colors[y][x]
                fill = f"rgb({r},{g},{b})"
            parts.append(
                f'<text x="{x * char_w:.1f}" y="{(y + 0.85) * char_h:.1f}" '
                f'font-family="monospace" font-size="{font_size}" fill="{fill}">{_html_escape(ch)}</text>'
            )
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


def _ascii_png(art: AsciiImage, output: str, *, background: str, no_color: bool, font_size: int) -> int:
    image = _ascii_pil_image(art, background=background, no_color=no_color, font_size=font_size)
    image.save(output)
    return 0


def _ascii_gif(art: AsciiImage, output: str, *, background: str, no_color: bool, font_size: int) -> int:
    image = _ascii_pil_image(art, background=background, no_color=no_color, font_size=font_size)
    if image.mode == "RGBA":
        image = image.convert("RGB")
    image.save(output, format="GIF")
    return 0


def _ascii_pil_image(art: AsciiImage, *, background: str, no_color: bool, font_size: int):
    Image, _ = _load_pillow()
    from PIL import ImageDraw, ImageFont

    font: Any
    try:
        font = ImageFont.truetype("CascadiaMono.ttf", font_size)
    except OSError:
        try:
            font = ImageFont.truetype("consola.ttf", font_size)
        except OSError:
            font = ImageFont.load_default()
    char_w = max(1, round(font_size * 0.62))
    char_h = max(1, round(font_size * 1.15))
    mode = "RGBA" if background == "transparent" else "RGB"
    bg = (0, 0, 0, 0) if background == "transparent" else (255, 255, 255) if background == "light" else (0, 0, 0)
    image = Image.new(mode, (max(1, art.cols) * char_w, max(1, art.rows) * char_h), bg)
    draw = ImageDraw.Draw(image)
    plain_color = (16, 16, 16) if background == "light" else (245, 245, 245)
    for y, row in enumerate(art.chars):
        for x, ch in enumerate(row):
            if ch == " ":
                continue
            color = plain_color if no_color else art.colors[y][x]
            draw.text((x * char_w, y * char_h), ch, fill=color, font=font)
    return image


def _ascii_tsx(art: AsciiImage, *, background: str, no_color: bool) -> str:
    import json

    rows = ["".join(row) for row in art.chars]
    colors = art.colors
    bg = _background_css(background)
    fg = "#111111" if background == "light" else "#f7f7f7"
    rows_json = json.dumps(rows, ensure_ascii=False)
    colors_json = json.dumps(colors)
    return f"""import React from "react";

type AsciiArtProps = {{
  className?: string;
  style?: React.CSSProperties;
}};

const ROWS = {rows_json};
const COLORS = {colors_json};
const NO_COLOR = {str(bool(no_color)).lower()};
const BG = {json.dumps(bg)};
const FG = {json.dumps(fg)};

export function AsciiArt({{ className, style }}: AsciiArtProps) {{
  return (
    <pre
      className={{className}}
      style={{{{
        margin: 0,
        background: BG,
        color: FG,
        fontFamily: "monospace",
        lineHeight: 1,
        letterSpacing: 0,
        whiteSpace: "pre",
        ...style,
      }}}}
    >
      {{ROWS.map((row, y) => (
        <React.Fragment key={{y}}>
          {{Array.from(row).map((ch, x) => (
            <span
              key={{x}}
              style={{NO_COLOR ? undefined : {{ color: `rgb(${{COLORS[y][x][0]}},${{COLORS[y][x][1]}},${{COLORS[y][x][2]}})` }}}}
            >
              {{ch}}
            </span>
          ))}}
          {{y < ROWS.length - 1 ? "\\n" : ""}}
        </React.Fragment>
      ))}}
    </pre>
  );
}}

export default AsciiArt;
"""


def _render_pillow_text(image, cols: int, rows: int, symbols: str, *, mode: str = "raw", trim: bool = False) -> str:
    Image, ImageOps = _load_pillow()
    from PIL import ImageFilter

    ramp = _pick_text_ramp(symbols)
    image, mask, mode = _prepare_image_layers(image, mode, trim)
    gray = ImageOps.autocontrast(image.convert("L"), cutoff=1)
    gray_small = gray.resize((cols, rows), _resample_filter(Image, "LANCZOS"))
    mask_small = mask.resize((cols, rows), _resample_filter(Image, "BOX")) if mask is not None else None
    edge_small = None
    if mode in {"detail", "edge"}:
        edge = ImageOps.autocontrast(gray.filter(ImageFilter.FIND_EDGES))
        edge_small = edge.resize((cols, rows), _resample_filter(Image, "LANCZOS"))

    chars = []
    for y in range(rows):
        line = []
        for x in range(cols):
            cover = mask_small.getpixel((x, y)) if mask_small is not None else 255
            if mask_small is not None and cover < 22:
                line.append(" ")
                continue
            if mode == "silhouette":
                value = cover
                min_index = 1
            elif mode == "edge":
                value = edge_small.getpixel((x, y)) if edge_small is not None else 0
                if value < 28:
                    line.append(" ")
                    continue
                min_index = 1
            elif mode == "detail":
                gray_value = gray_small.getpixel((x, y))
                edge_value = edge_small.getpixel((x, y)) if edge_small is not None else 0
                value = max(36, min(255, round(gray_value * 0.82 + edge_value * 0.42)))
                min_index = 1
            else:
                value = gray_small.getpixel((x, y))
                min_index = 0
            line.append(_tone_to_char(value, ramp, min_index=min_index))
        chars.append("".join(line).rstrip())
    return "\n".join(chars).rstrip() + "\n"


def _render_pillow_half(image, cols: int, rows: int, *, mode: str = "raw", trim: bool = False) -> str:
    Image, _ = _load_pillow()
    image, _mask, _mode = _prepare_image_layers(image, mode, trim)
    rgb = image.convert("RGB").resize((cols, rows * 2), _resample_filter(Image, "LANCZOS"))
    lines = []
    for row in range(rows):
        y0 = row * 2
        y1 = min(y0 + 1, rows * 2 - 1)
        line = []
        for x in range(cols):
            line.append(_ansi_fg_bg(rgb.getpixel((x, y0)), rgb.getpixel((x, y1))))
        line.append("\x1b[0m")
        lines.append("".join(line))
    return "\n".join(lines) + "\n"


def _normalize_chafa_format(value: str) -> str:
    normalized = (value or "auto").strip().lower()
    if normalized not in _CHAFA_FORMATS:
        raise ValueError(f"unknown chafa format: {value!r}")
    return "sixels" if normalized == "sixel" else normalized


def _normalize_chafa_colors(value: str) -> str:
    normalized = (value or "auto").strip().lower()
    if normalized not in _CHAFA_COLOR_MODES:
        raise ValueError(f"unknown chafa colors: {value!r}")
    return normalized


def _detect_chafa_format(value: str = "auto", *, chat: bool = False, output: str | None = None) -> str:
    requested = _normalize_chafa_format(value)
    if requested != "auto":
        return "symbols" if chat and requested != "symbols" else requested
    override = os.environ.get("GLYPH_ARTS_CHAFA_FORMAT") or os.environ.get("GLYPH_ARTS_FORMAT", "")
    if override:
        requested = _normalize_chafa_format(override)
        return "symbols" if chat and requested != "symbols" else requested
    if chat or output or not os.isatty(1):
        return "symbols"
    from cli_charts.terminal_profiles import detect_terminal_profile

    profile = detect_terminal_profile()
    if profile.chafa_format in _CHAFA_FORMATS:
        return _normalize_chafa_format(profile.chafa_format)
    term = os.environ.get("TERM", "").lower()
    term_program = os.environ.get("TERM_PROGRAM", "").lower()
    if "kitty" in term or os.environ.get("KITTY_WINDOW_ID"):
        return "kitty"
    if term_program == "iterm.app":
        return "iterm"
    if term_program == "wezterm" or os.environ.get("WEZTERM_EXECUTABLE"):
        return "sixels"
    return "symbols"


def _build_chafa_cmd(
    w: int,
    h: int,
    *,
    symbols: str = "braille",
    no_color: bool = False,
    chafa_format: str = "auto",
    chafa_colors: str = "auto",
    chafa_args: list[str] | None = None,
    chat: bool = False,
    output: str | None = None,
) -> list[str]:
    fmt = _detect_chafa_format(chafa_format, chat=chat, output=output)
    colors = _normalize_chafa_colors(chafa_colors)
    cmd = ["chafa", "--size", f"{w}x{h}", "--format", fmt]
    if fmt == "symbols" and symbols:
        cmd += ["--symbols", symbols]
    if no_color:
        cmd += ["--colors", "none"]
    elif colors != "auto":
        cmd += ["--colors", colors]
    elif fmt == "symbols":
        cmd += ["--colors", "full"]
    for arg in chafa_args or []:
        if arg:
            cmd.append(arg)
    return cmd


def render_image_pillow(
    path: str,
    w: int,
    h: int,
    *,
    symbols: str = "ascii",
    no_color: bool = False,
    output: str | None = None,
    mode: str = "auto",
    trim: bool = True,
    image_style: str = "classic",
    color_mode: str = "grayscale",
    custom_color: str | None = None,
    background: str = "dark",
    ratio: str = "original",
    dither: str = "none",
    dither_strength: float = 0.8,
    font_size: int = 14,
    invert: bool = False,
    random_style: bool = False,
) -> int:
    """Render an image with Pillow only.

    This path is intentionally chat-friendly: `--no-color --symbols ascii`
    produces plain text that survives Markdown code blocks and AI chat panes.
    """
    Image, ImageOps = _load_pillow()
    if Image is None:
        print("ERROR:dep: Pillow not installed -- install with `pip install Pillow`", file=sys.stderr)
        return 2
    if mode not in _IMAGE_MODES:
        print(f"ERROR:schema: unknown image mode: {mode}", file=sys.stderr)
        return 1
    if image_style not in _IMAGE_STYLES:
        print(f"ERROR:schema: unknown image style: {image_style}", file=sys.stderr)
        return 1
    if color_mode not in _COLOR_MODES:
        print(f"ERROR:schema: unknown color mode: {color_mode}", file=sys.stderr)
        return 1
    if background not in _BACKGROUND_MODES:
        print(f"ERROR:schema: unknown background: {background}", file=sys.stderr)
        return 1
    if ratio not in _RATIO_PRESETS:
        print(f"ERROR:schema: unknown ratio: {ratio}", file=sys.stderr)
        return 1
    if dither not in _DITHER_MODES:
        print(f"ERROR:schema: unknown dither: {dither}", file=sys.stderr)
        return 1
    if color_mode == "custom":
        try:
            _parse_color(custom_color)
        except ValueError as exc:
            print(f"ERROR:schema: {exc}", file=sys.stderr)
            return 1

    try:
        with Image.open(path) as opened:
            image = ImageOps.exif_transpose(opened).convert("RGB")
    except OSError as exc:
        print(f"ERROR:render: cannot read image: {exc}", file=sys.stderr)
        return 4

    if random_style:
        import random

        rng = random.Random(Path(path).name)
        image_style = rng.choice(sorted(_IMAGE_STYLES))
        color_mode = rng.choice(["grayscale", "matrix", "amber"])
        dither = rng.choice(["none", "bayer", "atkinson"])

    if image_style == "retro-art":
        color_mode = "amber" if color_mode == "grayscale" else color_mode
        dither = "atkinson" if dither == "none" else dither
    elif image_style == "terminal":
        color_mode = "matrix" if color_mode == "grayscale" else color_mode

    image = _crop_to_ratio(image, ratio)
    fit_image = image
    if trim and mode != "raw":
        fit_image, _, _ = _prepare_image_layers(image, mode, True)
    cols, rows = _fit_style_size(fit_image, w, h, image_style)
    normalized = (symbols or "").strip().lower()

    # Keep the first-generation half-block renderer as a fast color-pixel mode.
    if not output and not no_color and normalized in _HALF_SYMBOL_SETS and image_style == "classic":
        rendered = _render_pillow_half(image, cols, rows, mode=mode, trim=trim)
        sys.stdout.write(rendered)
        return 0

    prepared = fit_image if trim and mode != "raw" else image
    art = _build_ascii_image(
        prepared,
        cols,
        rows,
        style=image_style,
        color_mode=color_mode,
        background=background,
        custom_color=custom_color,
        dither=dither,
        dither_strength=dither_strength,
        invert=invert,
    )

    if output:
        return _write_ascii_export(art, output, background=background, no_color=no_color, font_size=font_size)
    if no_color or normalized in _TEXT_SYMBOL_SETS:
        sys.stdout.write(_ascii_text(art))
    else:
        sys.stdout.write(_ansi_text(art))
    return 0


def render_image_chafa(
    path: str,
    w: int,
    h: int,
    *,
    symbols: str = "braille",
    no_color: bool = False,
    output: str | None = None,
    chat: bool = False,
    chafa_format: str = "auto",
    chafa_colors: str = "auto",
    chafa_args: list[str] | None = None,
) -> int:
    """Render an image file to the terminal by shelling out to chafa."""
    if not shutil.which("chafa"):
        print("ERROR:dep: chafa not found -- install from https://hpjansson.org/chafa/", file=sys.stderr)
        return 2
    try:
        cmd = _build_chafa_cmd(
            w,
            h,
            symbols=symbols,
            no_color=no_color,
            chafa_format=chafa_format,
            chafa_colors=chafa_colors,
            chafa_args=chafa_args,
            chat=chat,
            output=output,
        )
    except ValueError as exc:
        print(f"ERROR:schema: {exc}", file=sys.stderr)
        return 1
    cmd.append(path)

    if output:
        result = subprocess.run(cmd, capture_output=True)
        if result.returncode != 0:
            lines = (result.stderr or b"").decode("utf-8", errors="replace").strip().splitlines()
            msg = lines[-1] if lines else "chafa exited non-zero"
            print(f"ERROR:render: {msg}", file=sys.stderr)
            return 4
        Path(output).write_bytes(result.stdout)
        return 0

    result = subprocess.run(cmd)
    if result.returncode != 0:
        print(f"ERROR:render: chafa exit {result.returncode}", file=sys.stderr)
        return 4
    return 0


def render_image(
    path: str,
    w: int,
    h: int,
    *,
    symbols: str = "braille",
    no_color: bool = False,
    output: str | None = None,
    engine: str = "auto",
    chat: bool = False,
    mode: str = "auto",
    trim: bool = True,
    image_style: str = "classic",
    color_mode: str = "grayscale",
    custom_color: str | None = None,
    background: str = "dark",
    ratio: str = "original",
    dither: str = "none",
    dither_strength: float = 0.8,
    font_size: int = 14,
    invert: bool = False,
    random_style: bool = False,
    chafa_format: str = "auto",
    chafa_colors: str = "auto",
    chafa_symbols: str | None = None,
    chafa_args: list[str] | None = None,
) -> int:
    """Render an image with chafa when available, otherwise Pillow fallback."""
    normalized_engine = (engine or "auto").strip().lower()
    if normalized_engine not in {"auto", "chafa", "pillow"}:
        print(f"ERROR:schema: unknown media engine: {engine}", file=sys.stderr)
        return 1

    normalized_symbols = (symbols or "").strip().lower()
    prefer_pillow = (
        chat
        or bool(output)
        or normalized_symbols in _TEXT_SYMBOL_SETS
        or normalized_symbols in _HALF_SYMBOL_SETS
        or image_style != "classic"
        or color_mode != "grayscale"
        or background != "dark"
        or ratio != "original"
        or dither != "none"
        or invert
        or random_style
    )

    if normalized_engine == "pillow" or (normalized_engine == "auto" and (prefer_pillow or not shutil.which("chafa"))):
        fallback_symbols = "ascii" if chat and normalized_symbols in {"", "braille"} else symbols
        return render_image_pillow(
            path,
            w,
            h,
            symbols=fallback_symbols,
            no_color=no_color or chat,
            output=output,
            mode=mode,
            trim=trim,
            image_style=image_style,
            color_mode=color_mode,
            custom_color=custom_color,
            background=background,
            ratio=ratio,
            dither=dither,
            dither_strength=dither_strength,
            font_size=font_size,
            invert=invert,
            random_style=random_style,
        )

    return render_image_chafa(
        path,
        w,
        h,
        symbols=chafa_symbols or symbols or "braille",
        no_color=no_color,
        output=output,
        chat=chat,
        chafa_format=chafa_format,
        chafa_colors=chafa_colors,
        chafa_args=chafa_args,
    )


_VIDEO_EXPORT_SUFFIXES = {".gif", ".mp4", ".webm", ".mov"}


def render_video_export(
    path: str,
    output: str,
    w: int,
    h: int,
    *,
    fps: int = 12,
    duration: float = 0.0,
    max_frames: int = 0,
    image_style: str = "classic",
    color_mode: str = "original",
    background: str = "dark",
    custom_color: str | None = None,
    dither: str = "none",
    dither_strength: float = 0.8,
    invert: bool = False,
    trim: bool = False,
    font_size: int = 14,
) -> int:
    """Export a video or animated GIF as an animated ASCII art file.

    Each frame is rendered through the Pillow ASCII pipeline so all
    ``--image-style``, ``--color-mode``, and ``--dither`` options apply.
    Output format is determined by the *output* file suffix:

    - ``.gif``  — Pillow animated GIF (no ffmpeg encoder needed for output)
    - ``.mp4``  — H.264 yuv420p via ffmpeg (widest player support)
    - ``.webm`` — VP9 yuv444p via ffmpeg (full-colour, no chroma sub-sampling)
    - ``.mov``  — ProRes 4444 via ffmpeg (lossless-quality, professional)
    """
    Image, ImageOps = _load_pillow()
    if Image is None:
        print("ERROR:dep: Pillow not installed -- pip install Pillow", file=sys.stderr)
        return 2
    if not shutil.which("ffmpeg"):
        print("ERROR:dep: ffmpeg not found -- required for video export", file=sys.stderr)
        return 2

    suffix = Path(output).suffix.lower()
    if suffix not in _VIDEO_EXPORT_SUFFIXES:
        print(
            f"ERROR:schema: unsupported animation output suffix '{suffix}'; "
            f"use one of: {', '.join(sorted(_VIDEO_EXPORT_SUFFIXES))}",
            file=sys.stderr,
        )
        return 1

    no_color = color_mode == "grayscale"

    with tempfile.TemporaryDirectory(prefix="glyph_vanim_") as tmp:
        # ── 1. Decode source into individual PNG frames ──────────────────────
        src_path = Path(path)
        animated_gif = False
        try:
            with Image.open(src_path) as probe:
                animated_gif = probe.format == "GIF" and getattr(probe, "is_animated", False)
        except OSError:
            pass

        frame_paths: list[str] = []
        if animated_gif:
            with Image.open(src_path) as gif:
                total = getattr(gif, "n_frames", 1)
                limit = max_frames if max_frames > 0 else total
                for idx in range(min(total, limit)):
                    gif.seek(idx)
                    out_path = os.path.join(tmp, f"frame_{idx:06d}.png")
                    gif.convert("RGB").save(out_path)
                    frame_paths.append(out_path)
        else:
            ff_cmd = [
                "ffmpeg", "-loglevel", "error", "-y",
                "-i", str(src_path),
                "-vf", f"fps={fps}",
            ]
            if duration and duration > 0:
                ff_cmd += ["-t", str(duration)]
            if max_frames and max_frames > 0:
                ff_cmd += ["-frames:v", str(max_frames)]
            ff_cmd.append(os.path.join(tmp, "frame_%06d.png"))
            result = subprocess.run(ff_cmd, capture_output=True, text=True)
            if result.returncode != 0:
                lines = (result.stderr or "").strip().splitlines()
                print(f"ERROR:render: {lines[-1] if lines else 'ffmpeg decode failed'}", file=sys.stderr)
                return 4
            frame_paths = sorted(glob.glob(os.path.join(tmp, "frame_*.png")))

        if not frame_paths:
            print("ERROR:render: source produced no frames", file=sys.stderr)
            return 4

        # ── 2. Render each frame through the ASCII pipeline ─────────────────
        pil_frames: list[Any] = []
        for frame_path in frame_paths:
            try:
                with Image.open(frame_path) as im:
                    image = im.convert("RGB")
            except OSError as exc:
                print(f"ERROR:render: cannot read frame: {exc}", file=sys.stderr)
                return 4
            if trim:
                image, _, _ = _prepare_image_layers(image, "auto", True)
            cols, rows = _fit_style_size(image, w, h, image_style)
            art = _build_ascii_image(
                image, cols, rows,
                style=image_style,
                color_mode=color_mode,
                background=background,
                custom_color=custom_color,
                dither=dither,
                dither_strength=dither_strength,
                invert=invert,
            )
            pil_frames.append(
                _ascii_pil_image(art, background=background, no_color=no_color, font_size=font_size)
            )

        if not pil_frames:
            print("ERROR:render: no frames rendered", file=sys.stderr)
            return 4

        # ── 3. Assemble output ───────────────────────────────────────────────
        if suffix == ".gif":
            frame_ms = max(20, round(1000 / max(fps, 1)))
            first, *rest = pil_frames
            first_rgb = first.convert("RGB") if first.mode == "RGBA" else first
            rest_rgb = [f.convert("RGB") if f.mode == "RGBA" else f for f in rest]
            first_rgb.save(
                output,
                format="GIF",
                save_all=True,
                append_images=rest_rgb,
                duration=frame_ms,
                loop=0,
                optimize=False,
            )
            return 0

        # Video via ffmpeg: write rendered PNGs then encode
        enc_dir = os.path.join(tmp, "enc")
        os.makedirs(enc_dir)
        for idx, img in enumerate(pil_frames):
            img.convert("RGB").save(os.path.join(enc_dir, f"r_{idx:06d}.png"))

        if suffix == ".webm":
            enc_args = ["-c:v", "libvpx-vp9", "-pix_fmt", "yuv444p", "-crf", "20", "-b:v", "0", "-row-mt", "1"]
            tail_args: list[str] = []
        elif suffix == ".mov":
            enc_args = ["-c:v", "prores_ks", "-profile:v", "4444", "-pix_fmt", "yuva444p10le", "-q:v", "11"]
            tail_args = []
        else:
            enc_args = ["-c:v", "libx264", "-pix_fmt", "yuv420p", "-crf", "18", "-preset", "slow"]
            tail_args = ["-movflags", "+faststart"]

        enc_cmd = (
            ["ffmpeg", "-y", "-loglevel", "error", "-framerate", str(fps),
             "-i", os.path.join(enc_dir, "r_%06d.png")]
            + enc_args + tail_args + [output]
        )
        result = subprocess.run(enc_cmd, capture_output=True, text=True)
        if result.returncode != 0:
            lines = (result.stderr or "").strip().splitlines()
            print(f"ERROR:render: {lines[-1] if lines else 'ffmpeg encode failed'}", file=sys.stderr)
            return 4

    return 0


def render_video(
    path: str,
    w: int,
    h: int,
    *,
    fps: int = 12,
    symbols: str = "braille",
    duration: float = 0.0,
    max_frames: int = 0,
    output: str = "",
    no_color: bool = False,
    chat: bool = False,
    image_style: str = "classic",
    color_mode: str = "original",
    background: str = "dark",
    custom_color: str | None = None,
    dither: str = "none",
    dither_strength: float = 0.8,
    invert: bool = False,
    trim: bool = False,
    font_size: int = 14,
    chafa_format: str = "symbols",
    chafa_colors: str = "auto",
    chafa_symbols: str | None = None,
    chafa_args: list[str] | None = None,
) -> int:
    """Play a video in the terminal, or export to an animated file.

    When *output* ends with ``.gif``, ``.mp4``, ``.webm``, or ``.mov`` the
    video is rendered frame-by-frame and saved to that file instead of being
    played in the terminal.
    """
    if output and Path(output).suffix.lower() in _VIDEO_EXPORT_SUFFIXES:
        return render_video_export(
            path, output, w, h,
            fps=fps,
            duration=duration,
            max_frames=max_frames,
            image_style=image_style,
            color_mode=color_mode,
            background=background,
            custom_color=custom_color,
            dither=dither,
            dither_strength=dither_strength,
            invert=invert,
            trim=trim,
            font_size=font_size,
        )
    """Play a video in the terminal: ffmpeg extracts frames, chafa renders each."""
    if not shutil.which("chafa"):
        print("ERROR:dep: chafa not found", file=sys.stderr)
        return 2
    if not shutil.which("ffmpeg"):
        print("ERROR:dep: ffmpeg not found -- required for video input", file=sys.stderr)
        return 2

    with tempfile.TemporaryDirectory(prefix="clichart_frames_") as tmp:
        ff = ["ffmpeg", "-loglevel", "error", "-y", "-i", path, "-vf", f"fps={fps}"]
        if duration and duration > 0:
            ff += ["-t", str(duration)]
        ff.append(os.path.join(tmp, "f_%05d.png"))
        result = subprocess.run(ff, capture_output=True, text=True)
        if result.returncode != 0:
            lines = (result.stderr or "").strip().splitlines()
            msg = lines[-1] if lines else "ffmpeg exited non-zero"
            print(f"ERROR:render: {msg}", file=sys.stderr)
            return 4

        frames = sorted(glob.glob(os.path.join(tmp, "f_*.png")))
        if not frames:
            print("ERROR:render: ffmpeg produced no frames", file=sys.stderr)
            return 4

        delay = 1.0 / fps if fps > 0 else 1.0 / 12
        is_tty = sys.stdout.isatty()
        try:
            chafa_cmd = _build_chafa_cmd(
                w,
                h,
                symbols=chafa_symbols or symbols,
                no_color=no_color,
                chafa_format=chafa_format,
                chafa_colors=chafa_colors,
                chafa_args=chafa_args,
                chat=chat,
            )
        except ValueError as exc:
            print(f"ERROR:schema: {exc}", file=sys.stderr)
            return 1

        if is_tty:
            sys.stdout.write("\x1b[?25l")
            sys.stdout.flush()
        try:
            for frame in frames:
                t0 = time.time()
                if is_tty:
                    sys.stdout.write("\x1b[H")
                    sys.stdout.flush()
                result = subprocess.run(chafa_cmd + [frame], capture_output=True, text=True)
                if result.returncode != 0:
                    lines = (result.stderr or "").strip().splitlines()
                    msg = lines[-1] if lines else "chafa exited non-zero"
                    print(f"ERROR:render: {msg}", file=sys.stderr)
                    return 4
                sys.stdout.write(result.stdout)
                elapsed = time.time() - t0
                if elapsed < delay:
                    time.sleep(delay - elapsed)
        except KeyboardInterrupt:
            pass
        finally:
            if is_tty:
                sys.stdout.write("\x1b[?25h")
                sys.stdout.flush()
    return 0
