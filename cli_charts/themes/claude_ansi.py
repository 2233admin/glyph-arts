"""Claude Code ANSI theme compatibility."""

from __future__ import annotations

import json
import os
from pathlib import Path
from typing import Any

DARK_ANSI = [
    "#000000", "#cd3131", "#0dbc79", "#e5e510", "#2472c8", "#bc3fbc", "#11a8cd", "#e5e5e5",
    "#666666", "#f14c4c", "#23d18b", "#f5f543", "#3b8eea", "#d670d6", "#29b8db", "#ffffff",
]
LIGHT_ANSI = [
    "#000000", "#cd3131", "#00a67d", "#949800", "#0451a5", "#bc05bc", "#0598bc", "#555555",
    "#666666", "#cd3131", "#14ce14", "#b5ba00", "#0451a5", "#bc05bc", "#0598bc", "#a5a5a5",
]


def _hex_to_rgb(value: str) -> tuple[int, int, int]:
    raw = value.strip().lstrip("#")
    if len(raw) != 6:
        raise ValueError(f"invalid hex color: {value!r}")
    return (int(raw[0:2], 16), int(raw[2:4], 16), int(raw[4:6], 16))


def _themes_dir() -> Path:
    try:
        fallback_home = str(Path.home())
    except RuntimeError:
        fallback_home = os.getcwd()
    home = os.environ.get("HOME") or os.environ.get("USERPROFILE") or fallback_home
    return Path(home) / ".claude" / "themes"


def _read_theme(slug: str) -> dict[str, Any] | None:
    path = _themes_dir() / f"{slug}-ansi.json"
    if not path.exists():
        path = _themes_dir() / f"{slug}.json"
    if not path.exists():
        return None
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _extract_ansi(theme: dict[str, Any]) -> list[str]:
    colors = theme.get("colors", theme)
    ansi = colors.get("ansi") or colors.get("ansiColors") or colors.get("terminalAnsi")
    if isinstance(ansi, dict):
        ordered = [
            "black", "red", "green", "yellow", "blue", "magenta", "cyan", "white",
            "brightBlack", "brightRed", "brightGreen", "brightYellow",
            "brightBlue", "brightMagenta", "brightCyan", "brightWhite",
        ]
        return [ansi[name] for name in ordered if name in ansi]
    if isinstance(ansi, list):
        return [str(color) for color in ansi]
    return []


def get_claude_ansi_palette(mode: str) -> dict:
    mode = "light" if mode == "light" else "dark"
    base_colors = LIGHT_ANSI if mode == "light" else DARK_ANSI
    theme = _read_theme(mode)
    colors = theme.get("colors", theme) if theme else {}
    ansi = _extract_ansi(theme) if theme else []
    series = [_hex_to_rgb(color) for color in (ansi or base_colors)]
    if len(series) < 16:
        series.extend(_hex_to_rgb(color) for color in base_colors[len(series):])
    bg = colors.get("background", "#ffffff" if mode == "light" else "#000000")
    fg = colors.get("foreground", "#111111" if mode == "light" else "#f0f0f0")
    return {
        "canvas": _hex_to_rgb(str(bg)),
        "axes": series[8] if len(series) > 8 else series[0],
        "ticks": _hex_to_rgb(str(fg)),
        "series": series[:16],
        "plt_base": "clear" if mode == "light" else "dark",
    }


CLAUDE_DARK_ANSI = get_claude_ansi_palette("dark")
CLAUDE_LIGHT_ANSI = get_claude_ansi_palette("light")
