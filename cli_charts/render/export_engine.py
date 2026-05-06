"""Text export helpers for rendered terminal charts."""

from __future__ import annotations

import html
import re
from pathlib import Path

ANSI_RE = re.compile(r"\x1b\[([0-9;]*)m")

ANSI_16 = {
    30: "#000000",
    31: "#cc0000",
    32: "#4e9a06",
    33: "#c4a000",
    34: "#3465a4",
    35: "#75507b",
    36: "#06989a",
    37: "#d3d7cf",
    90: "#555753",
    91: "#ef2929",
    92: "#8ae234",
    93: "#fce94f",
    94: "#729fcf",
    95: "#ad7fa8",
    96: "#34e2e2",
    97: "#eeeeec",
}

ANSI_256_BASE = [
    "#000000",
    "#800000",
    "#008000",
    "#808000",
    "#000080",
    "#800080",
    "#008080",
    "#c0c0c0",
    "#808080",
    "#ff0000",
    "#00ff00",
    "#ffff00",
    "#0000ff",
    "#ff00ff",
    "#00ffff",
    "#ffffff",
]


def _strip_ansi(content: str) -> str:
    return ANSI_RE.sub("", content)


def _ansi_256_to_hex(code: int) -> str | None:
    if 0 <= code < len(ANSI_256_BASE):
        return ANSI_256_BASE[code]
    if 16 <= code <= 231:
        n = code - 16
        r = n // 36
        g = (n % 36) // 6
        b = n % 6
        levels = [0, 95, 135, 175, 215, 255]
        return f"#{levels[r]:02x}{levels[g]:02x}{levels[b]:02x}"
    if 232 <= code <= 255:
        level = 8 + (code - 232) * 10
        return f"#{level:02x}{level:02x}{level:02x}"
    return None


def _sgr_to_color(params: list[int]) -> str | None:
    color: str | None = None
    i = 0
    while i < len(params):
        code = params[i]
        if code == 0 or code == 39:
            color = None
            i += 1
        elif code in ANSI_16:
            color = ANSI_16[code]
            i += 1
        elif code == 38 and i + 2 < len(params) and params[i + 1] == 5:
            color = _ansi_256_to_hex(params[i + 2])
            i += 3
        elif code == 38 and i + 4 < len(params) and params[i + 1] == 2:
            r, g, b = params[i + 2 : i + 5]
            color = f"#{r:02x}{g:02x}{b:02x}"
            i += 5
        else:
            i += 1
    return color


def _ansi_to_html(content: str, no_color: bool) -> str:
    if no_color:
        return html.escape(_strip_ansi(content))

    parts: list[str] = []
    pos = 0
    current_color: str | None = None
    span_open = False

    for match in ANSI_RE.finditer(content):
        parts.append(html.escape(content[pos : match.start()]))
        raw_params = match.group(1)
        params = [0] if raw_params == "" else [
            int(part) for part in raw_params.split(";") if part
        ]
        next_color = _sgr_to_color(params)
        if next_color != current_color:
            if span_open:
                parts.append("</span>")
                span_open = False
            current_color = next_color
            if current_color is not None:
                parts.append(f'<span style="color:{current_color}">')
                span_open = True
        pos = match.end()

    parts.append(html.escape(content[pos:]))
    if span_open:
        parts.append("</span>")
    return "".join(parts)


def export_to_path(content: str, path: str, no_color: bool) -> None:
    """Write terminal render content according to the output path suffix."""
    output = Path(path)
    suffix = output.suffix.lower()

    if suffix == ".txt":
        rendered = _strip_ansi(content)
    elif suffix == ".ansi":
        rendered = content
    elif suffix == ".html":
        body = _ansi_to_html(content, no_color)
        rendered = (
            '<pre style="background:#1a1a2e;color:#f8f8f2;'
            f'font-family:monospace">{body}</pre>\n'
        )
    else:
        raise ValueError(
            f"unsupported output extension {suffix or '<none>'}; "
            "expected .txt, .ansi, or .html"
        )

    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(rendered, encoding="utf-8")
