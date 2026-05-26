"""Terminal media rendering helpers.

Image/video rendering is adapter territory: glyph-arts keeps charts native, and
delegates pixel media to proven terminal renderers.
"""

from __future__ import annotations

import contextlib
import os
import shutil
import subprocess
import sys
import tempfile
from collections.abc import Iterator


IMAGE_CHAT_PRESETS: dict[str, dict[str, object]] = {
    'chat': {
        'width': 72,
        'height': 36,
        'symbols': 'braille',
        'no_color': True,
        'fit': 'subject',
        'filter_style': 'anime',
    },
    'chat-hd': {
        'width': 96,
        'height': 48,
        'symbols': 'braille',
        'no_color': True,
        'fit': 'subject',
        'filter_style': 'anime',
    },
    'chat-max': {
        'width': 120,
        'height': 60,
        'symbols': 'braille',
        'no_color': True,
        'fit': 'subject',
        'filter_style': 'anime',
    },
    'chat-4k': {
        'width': 132,
        'height': 66,
        'symbols': 'braille',
        'no_color': True,
        'fit': 'subject',
        'filter_style': 'anime',
    },
    'terminal': {
        'width': 0,
        'height': 0,
        'symbols': 'braille',
        'no_color': True,
        'fit': 'subject',
        'filter_style': 'anime',
    },
}


def resolve_image_options(
    w: int,
    h: int,
    symbols: str | None = None,
    no_color: bool = False,
    fit: str = 'contain',
    filter_style: str = 'none',
    preset: str = '',
    cols: int = 0,
) -> tuple[int, int, str, bool, str, str]:
    """Resolve image render settings, with chat presets as opinionated defaults."""
    if preset in {'', 'raw'}:
        return w, h, symbols or 'braille', no_color, fit, filter_style
    if preset == 'terminal':
        width = max(1, _detect_terminal_columns(cols) - 2)
        height = max(1, round(width * 0.5))
        resolved_filter = filter_style if filter_style not in {'', 'none'} else 'anime'
        return width, height, symbols or 'braille', True, 'subject', resolved_filter
    try:
        spec = IMAGE_CHAT_PRESETS[preset]
    except KeyError:
        print(f'ERROR:render: unknown image preset: {preset}', file=sys.stderr)
        sys.exit(2)
    return (
        int(spec['width']),
        int(spec['height']),
        str(spec['symbols']),
        bool(spec['no_color']),
        str(spec['fit']),
        str(spec['filter_style']),
    )


def _detect_terminal_columns(cols: int = 0, fallback: int = 80) -> int:
    if cols > 0:
        return cols
    for name in ('GLYPH_ARTS_COLS', 'COLUMNS'):
        value = os.environ.get(name)
        if value:
            try:
                parsed = int(value)
            except ValueError:
                continue
            if parsed > 0:
                return parsed
    return shutil.get_terminal_size((fallback, 20)).columns


def build_chafa_image_cmd(w: int, h: int, symbols: str, no_color: bool = False) -> list[str]:
    cmd = ['chafa', '--format', 'symbols', '--size', f'{w}x{h}', '--symbols', _symbols_for_mode(symbols, no_color)]
    if no_color:
        cmd += ['--colors', 'none']
    return cmd


def _symbols_for_mode(symbols: str, no_color: bool) -> str:
    if no_color and symbols in {'block', 'half', 'solid'}:
        return 'braille'
    return symbols


def render_image(path: str, w: int, h: int, symbols: str = 'braille',
                 no_color: bool = False, fit: str = 'contain',
                 filter_style: str = 'none') -> None:
    if not shutil.which('chafa'):
        print('ERROR:dep: chafa not found -- install from https://hpjansson.org/chafa/',
              file=sys.stderr)
        sys.exit(2)

    cmd = build_chafa_image_cmd(w, h, symbols, no_color)
    with _prepared_image_path(path, fit, filter_style) as render_path:
        result = subprocess.run(cmd + [render_path], capture_output=True, text=True)
    if result.returncode != 0:
        lines = (result.stderr or '').strip().splitlines()
        msg = lines[-1] if lines else 'chafa exited non-zero'
        print(f'ERROR:render: {msg}', file=sys.stderr)
        sys.exit(4)
    sys.stdout.write(result.stdout)


@contextlib.contextmanager
def _prepared_image_path(path: str, fit: str, filter_style: str = 'none') -> Iterator[str]:
    if fit != 'subject' and filter_style in {'', 'none'}:
        yield path
        return

    with tempfile.TemporaryDirectory(prefix='glyph_image_') as tmp:
        prepared = _subject_crop_path(path, fit, tmp)
        yield _filtered_image_path(prepared, filter_style, tmp)


def _subject_crop_path(path: str, fit: str, tmp: str) -> str:
    if fit != 'subject':
        return path

    crop = _detect_subject_crop(path)
    ffmpeg = shutil.which('ffmpeg')
    if crop is None or not ffmpeg:
        return path

    x, y, w, h = crop
    out = os.path.join(tmp, 'subject.png')
    result = subprocess.run(
        [
            ffmpeg, '-loglevel', 'error', '-y', '-i', path,
            '-vf', f'crop={w}:{h}:{x}:{y}', out,
        ],
        capture_output=True,
        text=True,
    )
    return out if result.returncode == 0 and os.path.exists(out) else path


def _filtered_image_path(path: str, filter_style: str, tmp: str) -> str:
    if filter_style in {'', 'none'}:
        return path
    if filter_style not in {'anime', 'ink'}:
        print(f'ERROR:render: unknown image filter: {filter_style}', file=sys.stderr)
        sys.exit(2)
    try:
        from PIL import Image, ImageFilter, ImageOps
    except ImportError:
        print(f'ERROR:dep: Pillow is required for --filter {filter_style}', file=sys.stderr)
        sys.exit(2)

    out = os.path.join(tmp, f'filter-{filter_style}.png')
    with Image.open(path) as im:
        gray = ImageOps.autocontrast(im.convert('L'), cutoff=2)
        if filter_style == 'ink':
            gray = ImageOps.invert(gray)
        sharp = gray.filter(ImageFilter.UnsharpMask(radius=1, percent=180, threshold=2))
        sharp.quantize(colors=5).convert('L').save(out)
    return out


def _detect_subject_crop(path: str) -> tuple[int, int, int, int] | None:
    ffmpeg = shutil.which('ffmpeg')
    ffprobe = shutil.which('ffprobe')
    if not ffmpeg or not ffprobe:
        return None

    size = _probe_image_size(path, ffprobe)
    if size is None:
        return None
    width, height = size
    if width <= 0 or height <= 0:
        return None

    sample_max = 180
    if width >= height:
        sample_w = sample_max
        sample_h = max(1, round(height * sample_max / width))
    else:
        sample_h = sample_max
        sample_w = max(1, round(width * sample_max / height))

    result = subprocess.run(
        [
            ffmpeg, '-loglevel', 'error', '-i', path,
            '-vf', f'scale={sample_w}:{sample_h},format=rgb24',
            '-f', 'rawvideo', '-',
        ],
        capture_output=True,
    )
    if result.returncode != 0:
        return None

    bbox = _foreground_bbox_from_rgb(result.stdout, sample_w, sample_h)
    if bbox is None:
        return None

    min_x, min_y, max_x, max_y = bbox
    pad_x = max(2, round((max_x - min_x) * 0.08))
    pad_y = max(2, round((max_y - min_y) * 0.08))
    min_x = max(0, min_x - pad_x)
    min_y = max(0, min_y - pad_y)
    max_x = min(sample_w, max_x + pad_x)
    max_y = min(sample_h, max_y + pad_y)

    x = max(0, round(min_x * width / sample_w))
    y = max(0, round(min_y * height / sample_h))
    crop_w = min(width - x, max(1, round((max_x - min_x) * width / sample_w)))
    crop_h = min(height - y, max(1, round((max_y - min_y) * height / sample_h)))

    # Avoid accidental micro-crops on flat images or diagrams.
    if crop_w * crop_h < width * height * 0.12:
        return None
    if crop_w >= width * 0.96 and crop_h >= height * 0.96:
        return None
    return x, y, crop_w, crop_h


def _probe_image_size(path: str, ffprobe: str) -> tuple[int, int] | None:
    result = subprocess.run(
        [
            ffprobe, '-v', 'error', '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height', '-of', 'csv=p=0:s=x',
            path,
        ],
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        return None
    text = (result.stdout or '').strip().splitlines()
    if not text or 'x' not in text[0]:
        return None
    left, right = text[0].split('x', 1)
    try:
        return int(left), int(right)
    except ValueError:
        return None


def _foreground_bbox_from_rgb(rgb: bytes, width: int, height: int,
                              threshold: float = 48.0) -> tuple[int, int, int, int] | None:
    expected = width * height * 3
    if len(rgb) < expected or width <= 0 or height <= 0:
        return None

    patch = max(1, min(width, height) // 16)
    corners: list[tuple[int, int, int]] = []
    for y0 in (0, height - patch):
        for x0 in (0, width - patch):
            for y in range(y0, y0 + patch):
                for x in range(x0, x0 + patch):
                    corners.append(_rgb_at(rgb, width, x, y))
    bg = _median_rgb(corners)
    bg_luma = _luma(bg)

    xs: list[int] = []
    ys: list[int] = []
    for y in range(height):
        row = y * width * 3
        for x in range(width):
            i = row + x * 3
            color = rgb[i], rgb[i + 1], rgb[i + 2]
            if _distance(color, bg) >= threshold and _luma(color) >= bg_luma + 8:
                xs.append(x)
                ys.append(y)

    if len(xs) < max(12, width * height // 250):
        return None
    return min(xs), min(ys), max(xs) + 1, max(ys) + 1


def _rgb_at(rgb: bytes, width: int, x: int, y: int) -> tuple[int, int, int]:
    i = (y * width + x) * 3
    return rgb[i], rgb[i + 1], rgb[i + 2]


def _median_rgb(colors: list[tuple[int, int, int]]) -> tuple[int, int, int]:
    if not colors:
        return 0, 0, 0
    return tuple(sorted(channel)[len(channel) // 2]
                 for channel in zip(*colors, strict=True))  # type: ignore[return-value]


def _distance(a: tuple[int, int, int], b: tuple[int, int, int]) -> float:
    return ((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2 + (a[2] - b[2]) ** 2) ** 0.5


def _luma(color: tuple[int, int, int]) -> float:
    return color[0] * 0.2126 + color[1] * 0.7152 + color[2] * 0.0722
