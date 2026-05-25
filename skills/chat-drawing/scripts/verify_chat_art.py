from __future__ import annotations

import argparse
import json
import re
import sys
import unicodedata
from pathlib import Path

ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")
BOX_CHARS = set("\u250c\u2510\u2514\u2518\u2502\u2500\u251c\u2524\u252c\u2534\u253c")


def _configure_stdio() -> None:
    for stream in (sys.stdin, sys.stdout, sys.stderr):
        reconfigure = getattr(stream, "reconfigure", None)
        if reconfigure is not None:
            reconfigure(encoding="utf-8", errors="replace")


def _char_width(char: str) -> int:
    if char == "\t":
        return 4
    if unicodedata.category(char) in {"Mn", "Me", "Cf"} or unicodedata.combining(char):
        return 0
    if unicodedata.east_asian_width(char) in {"F", "W"}:
        return 2
    return 1


def _display_width(text: str) -> int:
    return sum(_char_width(char) for char in text)


def _read_text(path: str | None) -> str:
    if path:
        return Path(path).read_text(encoding="utf-8")
    return sys.stdin.read()


def _visible_len(line: str) -> int:
    return _display_width(ANSI_RE.sub("", line))


def _box_line_lengths(lines: list[str]) -> list[int]:
    return [_visible_len(line) for line in lines if any(char in BOX_CHARS for char in line)]


def verify(
    text: str,
    *,
    max_width: int | None,
    required_labels: list[str],
    allow_ansi: bool,
    equal_box_width: bool,
) -> tuple[bool, list[str], dict[str, int | bool]]:
    errors: list[str] = []
    lines = text.splitlines()
    non_empty_lines = [line for line in lines if line.strip()]

    if not non_empty_lines:
        errors.append("output is empty")

    has_ansi = bool(ANSI_RE.search(text))
    if has_ansi and not allow_ansi:
        errors.append("output contains ANSI escape codes")

    widths = [_visible_len(line) for line in lines]
    max_seen_width = max(widths, default=0)
    if max_width is not None and max_seen_width > max_width:
        errors.append(f"output width {max_seen_width} exceeds max width {max_width}")

    for label in required_labels:
        if label and label not in text:
            errors.append(f"missing required label: {label}")

    box_widths = _box_line_lengths(lines)
    if equal_box_width and box_widths and len(set(box_widths)) != 1:
        errors.append("box or frame lines are not equal width")

    stats: dict[str, int | bool] = {
        "lines": len(lines),
        "non_empty_lines": len(non_empty_lines),
        "max_width": max_seen_width,
        "has_ansi": has_ansi,
        "box_lines": len(box_widths),
    }
    return not errors, errors, stats


def main(argv: list[str] | None = None) -> int:
    _configure_stdio()
    parser = argparse.ArgumentParser(description="Verify chat-visible ASCII/Unicode art before replying.")
    parser.add_argument("path", nargs="?", help="Text file to verify. Reads stdin when omitted.")
    parser.add_argument("--max-width", type=int, default=None)
    parser.add_argument("--require-label", action="append", default=[])
    parser.add_argument("--allow-ansi", action="store_true")
    parser.add_argument("--equal-box-width", action="store_true")
    args = parser.parse_args(argv)

    text = _read_text(args.path)
    ok, errors, stats = verify(
        text,
        max_width=args.max_width,
        required_labels=args.require_label,
        allow_ansi=args.allow_ansi,
        equal_box_width=args.equal_box_width,
    )
    payload = {"ok": ok, "errors": errors, "stats": stats}
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
