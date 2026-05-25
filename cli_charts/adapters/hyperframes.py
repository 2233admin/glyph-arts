"""HyperFrames asset adapter.

Generates a progressive line-chart PNG sequence plus the small metadata files
HyperFrames needs. HyperFrames itself is intentionally not a Python dependency.
"""

from __future__ import annotations

import html
import json
import struct
import sys
import zlib
from pathlib import Path
from typing import Any

from cli_charts.render.matplotlib_engine import _apply_theme, _build_figure, _validate_data


def _load_series(series_json: str) -> Any:
    try:
        data = json.loads(series_json)
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {exc}") from exc
    _validate_data("line", data)
    return data


def _progressive_slice(data: Any, frame_number: int, frames: int) -> Any:
    series = data if isinstance(data, list) else [data]
    sliced = []
    for item in series:
        x_values = item["x"]
        y_values = item["y"]
        point_count = max(1, round(frame_number * len(y_values) / frames))
        next_item = dict(item)
        next_item["x"] = x_values[:point_count]
        next_item["y"] = y_values[:point_count]
        sliced.append(next_item)
    return sliced if isinstance(data, list) else sliced[0]


def _write_manifest(output_dir: Path, files: list[str], frames: int, duration_ms: int, fps: int) -> None:
    manifest = {
        "version": "1.0",
        "frames": frames,
        "duration_ms": duration_ms,
        "fps": fps,
        "tracks": [{"type": "image-sequence", "files": files}],
    }
    (output_dir / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def _write_composition(output_dir: Path, files: list[str], frames: int, duration_ms: int) -> None:
    lines = [
        "<!DOCTYPE html>",
        "<html data-hyperframes-composition>",
        "<head><meta charset='utf-8'><title>glyph-arts animation</title></head>",
        "<body>",
        f"  <div data-track='image-sequence' data-frames='{frames}' data-duration='{duration_ms}'>",
    ]
    for index, filename in enumerate(files):
        data_time = round(index * duration_ms / frames)
        lines.append(f"    <img src='{html.escape(filename, quote=True)}' data-time='{data_time}'>")
    lines.extend([
        "  </div>",
        "</body>",
        "</html>",
    ])
    (output_dir / "composition.html").write_text("\n".join(lines) + "\n", encoding="utf-8")


def _png_chunk(kind: bytes, data: bytes) -> bytes:
    return struct.pack(">I", len(data)) + kind + data + struct.pack(">I", zlib.crc32(kind + data) & 0xFFFFFFFF)


def _draw_line(pixels: bytearray, width: int, height: int, start: tuple[int, int], end: tuple[int, int], color: bytes) -> None:
    x0, y0 = start
    x1, y1 = end
    dx = abs(x1 - x0)
    dy = -abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx + dy
    while True:
        if 0 <= x0 < width and 0 <= y0 < height:
            pos = (y0 * width + x0) * 3
            pixels[pos:pos + 3] = color
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 >= dy:
            err += dy
            x0 += sx
        if e2 <= dx:
            err += dx
            y0 += sy


def _write_fallback_png(path: Path, data: Any, width_cells: int, height_cells: int) -> None:
    width = max(320, width_cells * 8)
    height = max(220, height_cells * 12)
    margin = 32
    pixels = bytearray(b"\x1e\x1e\x2e" * width * height)
    axis = b"\xf8\xf8\xf2"
    cyan = b"\x89\xdc\xeb"
    _draw_line(pixels, width, height, (margin, height - margin), (width - margin, height - margin), axis)
    _draw_line(pixels, width, height, (margin, margin), (margin, height - margin), axis)

    series = _validate_data("line", data)
    all_x = [x for _label, xs, _ys in series for x in xs]
    all_y = [y for _label, _xs, ys in series for y in ys]
    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(all_y), max(all_y)
    x_span = max(x_max - x_min, 1e-9)
    y_span = max(y_max - y_min, 1e-9)

    def point(x_value: float, y_value: float) -> tuple[int, int]:
        x = margin + round((x_value - x_min) / x_span * (width - 2 * margin))
        y = height - margin - round((y_value - y_min) / y_span * (height - 2 * margin))
        return x, y

    for _label, xs, ys in series:
        points = [point(x_value, y_value) for x_value, y_value in zip(xs, ys, strict=False)]
        for start, end in zip(points, points[1:], strict=False):
            _draw_line(pixels, width, height, start, end, cyan)
        for x, y in points:
            _draw_line(pixels, width, height, (x - 2, y), (x + 2, y), cyan)
            _draw_line(pixels, width, height, (x, y - 2), (x, y + 2), cyan)

    raw = b"".join(b"\x00" + pixels[row * width * 3:(row + 1) * width * 3] for row in range(height))
    png = (
        b"\x89PNG\r\n\x1a\n"
        + _png_chunk(b"IHDR", struct.pack(">IIBBBBB", width, height, 8, 2, 0, 0, 0))
        + _png_chunk(b"IDAT", zlib.compress(raw, 9))
        + _png_chunk(b"IEND", b"")
    )
    path.write_bytes(png)


def to_hyperframes(
    series_json: str,
    frames: int,
    duration_s: float,
    output_dir: str | Path,
    *,
    width: int = 80,
    height: int = 20,
    title: str = "",
    theme: str = "pro",
    no_color: bool = False,
) -> int:
    """Generate PNG frames and HyperFrames metadata for a line chart."""
    if frames <= 0:
        print("ERROR:schema: --frames must be greater than 0", file=sys.stderr)
        return 1
    if duration_s <= 0:
        print("ERROR:schema: --duration must be greater than 0", file=sys.stderr)
        return 1

    try:
        data = _load_series(series_json)
    except ValueError as exc:
        print(f"ERROR:schema: {exc}", file=sys.stderr)
        return 1

    mpl: Any | None
    pyplot: Any | None
    try:
        import matplotlib as _mpl

        _mpl.use("Agg")
        import matplotlib.pyplot as _pyplot
    except ImportError:
        mpl = None
        pyplot = None
    else:
        mpl = _mpl
        pyplot = _pyplot

    out_dir = Path(output_dir)
    duration_ms = round(duration_s * 1000)
    fps = int(frames / duration_s)
    files = [f"frame_{index:03d}.png" for index in range(1, frames + 1)]

    try:
        out_dir.mkdir(parents=True, exist_ok=True)
        if mpl is not None:
            _apply_theme(mpl, theme, no_color)
        for frame_number, filename in enumerate(files, start=1):
            frame_data = _progressive_slice(data, frame_number, frames)
            if pyplot is None:
                _write_fallback_png(out_dir / filename, frame_data, width, height)
            else:
                fig = _build_figure(pyplot, "line", frame_data, width, height, title, theme)
                try:
                    fig.savefig(out_dir / filename)
                finally:
                    pyplot.close(fig)
        _write_manifest(out_dir, files, frames, duration_ms, fps)
        _write_composition(out_dir, files, frames, duration_ms)
    except (OSError, TypeError, ValueError) as exc:
        print(f"ERROR:render: {exc}", file=sys.stderr)
        return 4
    return 0
