from __future__ import annotations

import math
from collections.abc import Iterable
from typing import Any

from cli_charts.symbols import braille_dots

_DOT_BITS = ((0x01, 0x08), (0x02, 0x10), (0x04, 0x20), (0x40, 0x80))


class BrailleCanvas:
    """Tiny dependency-free drawille-compatible Braille canvas."""

    def __init__(self, width: int, height: int) -> None:
        self.width = max(1, int(width))
        self.height = max(1, int(height))
        self.pixel_width = self.width * 2
        self.pixel_height = self.height * 4
        self._cells = [[0 for _ in range(self.width)] for _ in range(self.height)]

    def set(self, x: float, y: float) -> None:
        px, py = int(round(x)), int(round(y))
        if not (0 <= px < self.pixel_width and 0 <= py < self.pixel_height):
            return
        self._cells[py // 4][px // 2] |= _DOT_BITS[py % 4][px % 2]

    def unset(self, x: float, y: float) -> None:
        px, py = int(round(x)), int(round(y))
        if not (0 <= px < self.pixel_width and 0 <= py < self.pixel_height):
            return
        self._cells[py // 4][px // 2] &= ~_DOT_BITS[py % 4][px % 2]

    def toggle(self, x: float, y: float) -> None:
        px, py = int(round(x)), int(round(y))
        if not (0 <= px < self.pixel_width and 0 <= py < self.pixel_height):
            return
        self._cells[py // 4][px // 2] ^= _DOT_BITS[py % 4][px % 2]

    def line(self, x0: float, y0: float, x1: float, y1: float) -> None:
        x0_i, y0_i = int(round(x0)), int(round(y0))
        x1_i, y1_i = int(round(x1)), int(round(y1))
        dx = abs(x1_i - x0_i)
        dy = abs(y1_i - y0_i)
        sx = 1 if x0_i < x1_i else -1
        sy = 1 if y0_i < y1_i else -1
        err = dx - dy
        while True:
            self.set(x0_i, y0_i)
            if x0_i == x1_i and y0_i == y1_i:
                break
            e2 = 2 * err
            if e2 > -dy:
                err -= dy
                x0_i += sx
            if e2 < dx:
                err += dx
                y0_i += sy

    def frame(self) -> str:
        return "\n".join("".join(braille_dots(cell) for cell in row).rstrip() for row in self._cells).rstrip() + "\n"


def render_textplot(data: Any, *, title: str = "", width: int = 70, height: int = 20) -> str:
    """Render a textplots-rs-style continuous function plot on Braille cells."""
    spec = {"expr": str(data)} if not isinstance(data, dict) else data
    expr = str(spec.get("expr") or spec.get("function") or spec.get("y") or "sin(x)")
    xmin = float(spec.get("xmin", spec.get("x_min", -10.0)))
    xmax = float(spec.get("xmax", spec.get("x_max", 10.0)))
    samples = max(16, int(spec.get("samples", width * 4)))
    points = _sample_expression(expr, xmin, xmax, samples)
    if not points:
        raise ValueError("textplot expression produced no finite points")
    ys = [y for _x, y in points]
    ymin = float(spec.get("ymin", spec.get("y_min", min(ys))))
    ymax = float(spec.get("ymax", spec.get("y_max", max(ys))))
    if ymin == ymax:
        ymin -= 1.0
        ymax += 1.0

    canvas = BrailleCanvas(width, height)

    def sx(value: float) -> float:
        return (value - xmin) / (xmax - xmin or 1.0) * (canvas.pixel_width - 1)

    def sy(value: float) -> float:
        return (ymax - value) / (ymax - ymin or 1.0) * (canvas.pixel_height - 1)

    if ymin <= 0 <= ymax:
        y0 = sy(0)
        canvas.line(0, y0, canvas.pixel_width - 1, y0)
    if xmin <= 0 <= xmax:
        x0 = sx(0)
        canvas.line(x0, 0, x0, canvas.pixel_height - 1)

    last: tuple[float, float] | None = None
    for x, y in points:
        current = (sx(x), sy(y))
        if last is None:
            canvas.set(*current)
        else:
            canvas.line(last[0], last[1], current[0], current[1])
        last = current

    header = title or spec.get("title") or f"y = {expr}"
    footer = f"x=[{xmin:g},{xmax:g}] y=[{ymin:g},{ymax:g}]"
    return f"{header}\n{canvas.frame()}{footer}\n"


def render_turtle(data: Any, *, title: str = "", width: int = 70, height: int = 20) -> str:
    """Render drawille-style turtle commands on a Braille canvas."""
    spec = data if isinstance(data, dict) else {"commands": data}
    commands = spec.get("commands") or spec.get("path") or []
    if isinstance(commands, str):
        commands = _parse_turtle_text(commands)

    canvas = BrailleCanvas(width, height)
    x = float(spec.get("x", canvas.pixel_width / 2))
    y = float(spec.get("y", canvas.pixel_height / 2))
    heading = float(spec.get("heading", 0.0))
    pen = bool(spec.get("pen", True))
    canvas.set(x, y)

    for raw in commands:
        name, args = _command(raw)
        if name in {"forward", "fd", "f"}:
            distance = float(args[0])
            nx = x + math.cos(math.radians(heading)) * distance
            ny = y - math.sin(math.radians(heading)) * distance
            if pen:
                canvas.line(x, y, nx, ny)
            x, y = nx, ny
        elif name in {"back", "backward", "bk", "b"}:
            distance = -float(args[0])
            nx = x + math.cos(math.radians(heading)) * distance
            ny = y - math.sin(math.radians(heading)) * distance
            if pen:
                canvas.line(x, y, nx, ny)
            x, y = nx, ny
        elif name in {"left", "lt"}:
            heading += float(args[0])
        elif name in {"right", "rt"}:
            heading -= float(args[0])
        elif name in {"goto", "move", "setpos"}:
            nx, ny = float(args[0]), float(args[1])
            if pen:
                canvas.line(x, y, nx, ny)
            x, y = nx, ny
        elif name in {"line"}:
            x0, y0, x1, y1 = map(float, args[:4])
            canvas.line(x0, y0, x1, y1)
            x, y = x1, y1
        elif name in {"dot", "set"}:
            canvas.set(float(args[0]), float(args[1]))
        elif name in {"unset"}:
            canvas.unset(float(args[0]), float(args[1]))
        elif name in {"toggle"}:
            canvas.toggle(float(args[0]), float(args[1]))
        elif name in {"penup", "pu", "up"}:
            pen = False
        elif name in {"pendown", "pd", "down"}:
            pen = True
        elif name in {"home"}:
            nx, ny = canvas.pixel_width / 2, canvas.pixel_height / 2
            if pen:
                canvas.line(x, y, nx, ny)
            x, y = nx, ny
        else:
            raise ValueError(f"unsupported turtle command: {name!r}")

    return (f"{title or spec.get('title')}\n" if title or spec.get("title") else "") + canvas.frame()


def _sample_expression(expr: str, xmin: float, xmax: float, samples: int) -> list[tuple[float, float]]:
    env = {name: getattr(math, name) for name in dir(math) if not name.startswith("_")}
    env.update({"abs": abs, "min": min, "max": max, "pow": pow})
    points: list[tuple[float, float]] = []
    for idx in range(samples):
        x = xmin + (xmax - xmin) * idx / max(1, samples - 1)
        env["x"] = x
        try:
            y = float(eval(expr, {"__builtins__": {}}, env))  # noqa: S307 - constrained math namespace
        except Exception:
            continue
        if math.isfinite(y):
            points.append((x, y))
    return points


def _parse_turtle_text(text: str) -> list[list[str]]:
    commands: list[list[str]] = []
    for line in text.replace(";", "\n").splitlines():
        parts = line.strip().split()
        if parts:
            commands.append(parts)
    return commands


def _command(raw: Any) -> tuple[str, list[Any]]:
    if isinstance(raw, str):
        parts = raw.strip().split()
        if not parts:
            return "", []
        return parts[0].lower(), parts[1:]
    if isinstance(raw, dict):
        name = str(raw.get("cmd") or raw.get("command") or raw.get("op") or raw.get("type") or "").lower()
        if "args" in raw:
            args = _as_list(raw["args"])
        elif name in {"goto", "move", "setpos", "dot", "set", "unset", "toggle"}:
            args = [raw.get("x", 0), raw.get("y", 0)]
        elif name == "line":
            args = [raw.get("x0", 0), raw.get("y0", 0), raw.get("x1", 0), raw.get("y1", 0)]
        else:
            args = [raw.get("value", raw.get("distance", raw.get("angle", 0)))]
        return name, args
    if isinstance(raw, Iterable):
        parts = list(raw)
        if not parts:
            return "", []
        return str(parts[0]).lower(), parts[1:]
    return "", []


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else [value]
