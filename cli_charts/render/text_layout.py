from __future__ import annotations

import re
import unicodedata

ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")


def strip_ansi(text: str) -> str:
    return ANSI_RE.sub("", text)


def char_width(char: str) -> int:
    if not char:
        return 0
    if char == "\t":
        return 4
    category = unicodedata.category(char)
    if category in {"Mn", "Me", "Cf"}:
        return 0
    if unicodedata.combining(char):
        return 0
    if unicodedata.east_asian_width(char) in {"F", "W"}:
        return 2
    return 1


def display_width(text: object) -> int:
    return sum(char_width(char) for char in strip_ansi(str(text)))


def fit_text(text: object, width: int, *, ellipsis: str = "…") -> str:
    value = str(text)
    if width <= 0:
        return ""
    if display_width(value) <= width:
        return value
    ellipsis_width = display_width(ellipsis)
    limit = max(0, width - ellipsis_width)
    out = []
    used = 0
    for char in value:
        char_w = char_width(char)
        if used + char_w > limit:
            break
        out.append(char)
        used += char_w
    return "".join(out) + ellipsis


def pad_right(text: object, width: int) -> str:
    value = fit_text(text, width)
    return value + " " * max(0, width - display_width(value))


def pad_left(text: object, width: int) -> str:
    value = fit_text(text, width)
    return " " * max(0, width - display_width(value)) + value


def center_text(text: object, width: int) -> str:
    value = fit_text(text, width)
    remaining = max(0, width - display_width(value))
    left = remaining // 2
    right = remaining - left
    return " " * left + value + " " * right


def wrap_display(text: object, width: int) -> list[str]:
    value = str(text).rstrip()
    if not value.strip():
        return [""]
    lines: list[str] = []
    for paragraph in value.splitlines() or [value]:
        words = paragraph.split(" ")
        current = ""
        for word in words:
            candidate = word if not current else current + " " + word
            if display_width(candidate) <= width:
                current = candidate
                continue
            if current:
                lines.append(current)
                current = ""
            if display_width(word) <= width:
                current = word
                continue
            chunk = ""
            for char in word:
                if display_width(chunk + char) > width:
                    lines.append(chunk)
                    chunk = char
                else:
                    chunk += char
            current = chunk
        lines.append(current)
    return lines or [""]
