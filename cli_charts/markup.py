"""Structured markup helpers for chat-safe artifacts."""

from __future__ import annotations

import html
import io
import json
import os
import re
import shutil
import subprocess
import tempfile
from collections.abc import Mapping
from pathlib import Path
from typing import Any

import regex
from tabulate import tabulate
from wcwidth import wcswidth

ANSI_RE = re.compile(r"\x1b\[[0-?]*[ -/]*[@-~]")

TABLE_FORMATS = {
    "github": "github",
    "grid": "grid",
    "heavy_grid": "heavy_grid",
    "pipe": "pipe",
    "rounded_grid": "rounded_grid",
}

MERMAID_THEMES = {
    "default": {"theme": "default"},
    "dark": {"theme": "dark"},
    "cyber": {
        "theme": "base",
        "themeVariables": {
            "background": "#0b1020",
            "primaryColor": "#00f5d4",
            "primaryTextColor": "#111827",
            "lineColor": "#ff4d6d",
            "fontFamily": "ui-monospace, SFMono-Regular, Menlo, monospace",
        },
    },
    "incident": {
        "theme": "base",
        "themeVariables": {
            "background": "#111827",
            "primaryColor": "#f97316",
            "primaryTextColor": "#111827",
            "secondaryColor": "#fee2e2",
            "lineColor": "#ef4444",
        },
    },
    "report": {
        "theme": "base",
        "themeVariables": {
            "background": "#ffffff",
            "primaryColor": "#dbeafe",
            "primaryTextColor": "#111827",
            "secondaryColor": "#f3f4f6",
            "lineColor": "#2563eb",
        },
    },
}


def strip_ansi(value: object) -> str:
    return ANSI_RE.sub("", str(value))


def visible_width(value: object) -> int:
    width = wcswidth(strip_ansi(value))
    return max(width, 0)


def graphemes(value: object) -> list[str]:
    return regex.findall(r"\X", str(value))


def wrap_visible(value: object, width: int) -> str:
    if width <= 0:
        return str(value)
    lines: list[str] = []
    current: list[str] = []
    current_width = 0
    for cluster in graphemes(value):
        if cluster == "\n":
            lines.append("".join(current))
            current = []
            current_width = 0
            continue
        cluster_width = visible_width(cluster)
        if current and current_width + cluster_width > width:
            lines.append("".join(current))
            current = [cluster]
            current_width = cluster_width
        else:
            current.append(cluster)
            current_width += cluster_width
    lines.append("".join(current))
    return "\n".join(lines)


def render_chat_calibration(spec: dict[str, Any] | None = None) -> str:
    """Emit pasteable rulers for measuring chat-window monospace width."""
    spec = spec or {}
    terminal_cols = int(spec.get("terminal_cols", 0) or 0)
    if spec.get("terminal") and not terminal_cols:
        terminal_cols = _detect_terminal_columns()
    if spec.get("widths"):
        widths = spec["widths"]
    elif terminal_cols:
        widths = _terminal_calibration_widths(terminal_cols)
    else:
        widths = _calibration_widths(
            int(spec.get("from", 96)),
            int(spec.get("to", 160)),
            int(spec.get("step", 8)),
        )
    if isinstance(widths, str):
        widths = [int(part.strip()) for part in widths.split(",") if part.strip()]
    glyph = str(spec.get("glyph", "all"))
    recommend = bool(spec.get("recommend", False))
    rows: list[str] = []
    if terminal_cols:
        safe = max(1, terminal_cols - 2)
        rows.extend([
            f"terminal columns = {terminal_cols}",
            f"safe inline width = {safe}",
            "",
        ])
    if recommend:
        rows.extend([
            "Pick the largest width whose ruler stays on one visual line.",
            "Recommended presets after measuring W:",
            "inline = floor(W * 0.85), hd = floor(W * 0.95), max = W",
            "",
        ])
    for raw_width in widths:
        width = int(raw_width)
        rows.append(f"{width}:")
        if glyph in {"all", "ascii", "digits"}:
            rows.append(_repeating_digits(width))
        if glyph in {"all", "braille", "solid"}:
            rows.append("⣿" * width)
        if glyph in {"all", "braille", "mixed"}:
            rows.append("⠿⣶⣿⣤" * (width // 4) + "⠿⣶⣿⣤"[: width % 4])
        rows.append("")
    return "\n".join(rows).rstrip() + "\n"


SUPERSCRIPT = str.maketrans("0123456789+-=()nix", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱˣ")
SUBSCRIPT = str.maketrans("0123456789+-=()nix", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₙᵢₓ")
LATEX_TOKENS = {
    r"\alpha": "α",
    r"\beta": "β",
    r"\gamma": "γ",
    r"\delta": "δ",
    r"\Delta": "Δ",
    r"\theta": "θ",
    r"\lambda": "λ",
    r"\mu": "μ",
    r"\pi": "π",
    r"\sigma": "σ",
    r"\Sigma": "Σ",
    r"\sum": "∑",
    r"\prod": "∏",
    r"\int": "∫",
    r"\infty": "∞",
    r"\partial": "∂",
    r"\nabla": "∇",
    r"\times": "×",
    r"\cdot": "·",
    r"\le": "≤",
    r"\ge": "≥",
    r"\ne": "≠",
    r"\approx": "≈",
    r"\to": "→",
    r"\rightarrow": "→",
}


def render_formula_panel(spec: dict[str, Any] | str | list[str]) -> str:
    """Render formulas as text, not raster pixels.

    This is the right path when the formula source is available. Raster image
    rendering remains a fallback for screenshots/scans only.
    """
    if isinstance(spec, str):
        formulas = [spec]
        title = ""
    elif isinstance(spec, list):
        formulas = [str(item) for item in spec]
        title = ""
    else:
        raw = spec.get("formula", spec.get("expr", spec.get("body", spec.get("items", []))))
        formulas = raw if isinstance(raw, list) else [raw]
        formulas = [str(item) for item in formulas]
        title = str(spec.get("title", ""))
    rows = [title] if title else []
    rows.extend(_unicode_formula(formula) for formula in formulas)
    return "\n".join(row for row in rows if row).rstrip() + "\n"


def render_formula_pretty(spec: dict[str, Any] | str | list[str]) -> str:
    """Render formula source through SymPy pretty-printing when possible."""
    formulas, title = _formula_items(spec)
    rows = [title] if title else []
    for formula in formulas:
        rows.append(_sympy_pretty_formula(formula))
    return "\n\n".join(row for row in rows if row).rstrip() + "\n"


def _formula_items(spec: dict[str, Any] | str | list[str]) -> tuple[list[str], str]:
    if isinstance(spec, str):
        return [spec], ""
    if isinstance(spec, list):
        return [str(item) for item in spec], ""
    raw = spec.get("formula", spec.get("expr", spec.get("body", spec.get("items", []))))
    formulas = raw if isinstance(raw, list) else [raw]
    return [str(item) for item in formulas], str(spec.get("title", ""))


def _unicode_formula(expr: str) -> str:
    text = expr.strip().strip("$")
    text = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1)/(\2)", text)
    text = re.sub(r"\\sqrt\{([^{}]+)\}", r"√(\1)", text)
    for source, target in sorted(LATEX_TOKENS.items(), key=lambda item: len(item[0]), reverse=True):
        text = text.replace(source, target)
    text = re.sub(r"\^\{([^{}]+)\}", lambda m: _translate_if_possible(m.group(1), SUPERSCRIPT, "^{" + m.group(1) + "}"), text)
    text = re.sub(r"_\{([^{}]+)\}", lambda m: _translate_if_possible(m.group(1), SUBSCRIPT, "_{" + m.group(1) + "}"), text)
    text = re.sub(r"\^([A-Za-z0-9+\-=()])", lambda m: _translate_if_possible(m.group(1), SUPERSCRIPT, "^" + m.group(1)), text)
    text = re.sub(r"_([A-Za-z0-9+\-=()])", lambda m: _translate_if_possible(m.group(1), SUBSCRIPT, "_" + m.group(1)), text)
    return text


def _sympy_pretty_formula(expr: str) -> str:
    try:
        import sympy as sp
        from sympy.parsing.sympy_parser import (
            convert_xor,
            implicit_multiplication_application,
            parse_expr,
            standard_transformations,
        )
    except ImportError:
        raise RuntimeError("sympy is required for chat formula-pretty; install glyph-arts[markup]") from None

    source = _sympy_source(expr)
    transformations = standard_transformations + (implicit_multiplication_application, convert_xor)
    locals_map = {
        "E": sp.Symbol("E"),
        "e": sp.E,
        "i": sp.I,
        "pi": sp.pi,
        "inf": sp.oo,
        "infty": sp.oo,
        "oo": sp.oo,
    }
    try:
        if "=" in source and "==" not in source:
            left, right = source.split("=", 1)
            parsed = sp.Eq(
                parse_expr(left, local_dict=locals_map, transformations=transformations),
                parse_expr(right, local_dict=locals_map, transformations=transformations),
                evaluate=False,
            )
        else:
            parsed = parse_expr(source, local_dict=locals_map, transformations=transformations)
        return sp.pretty(parsed, use_unicode=True)
    except Exception:
        return _unicode_formula(expr)


def _sympy_source(expr: str) -> str:
    text = expr.strip().strip("$")
    text = re.sub(r"\\frac\{([^{}]+)\}\{([^{}]+)\}", r"(\1)/(\2)", text)
    text = re.sub(r"\\sqrt\{([^{}]+)\}", r"sqrt(\1)", text)
    replacements = {
        r"\cdot": "*",
        r"\times": "*",
        r"\pi": "pi",
        r"\infty": "oo",
        r"\int": "Integral",
        r"\sum": "Sum",
    }
    for source, target in replacements.items():
        text = text.replace(source, target)
    text = text.replace("^", "**")
    return text


def _translate_if_possible(value: str, table: Mapping[int, int | str | None], fallback: str) -> str:
    translated = value.translate(table)
    return translated if translated != value or all(ord(ch) in table for ch in value) else fallback


def _calibration_widths(start: int, stop: int, step: int) -> list[int]:
    if step <= 0:
        raise ValueError("calibration step must be positive")
    if start <= 0 or stop <= 0:
        raise ValueError("calibration widths must be positive")
    if stop < start:
        raise ValueError("calibration end must be >= start")
    return list(range(start, stop + 1, step))


def _terminal_calibration_widths(columns: int) -> list[int]:
    if columns <= 0:
        raise ValueError("terminal columns must be positive")
    candidates = [
        columns - 32,
        columns - 16,
        columns - 8,
        columns - 2,
        columns,
    ]
    return sorted({width for width in candidates if width > 0})


def _detect_terminal_columns(fallback: int = 80) -> int:
    for name in ("GLYPH_ARTS_COLS", "COLUMNS"):
        value = os.environ.get(name)
        if value:
            try:
                parsed = int(value)
            except ValueError:
                continue
            if parsed > 0:
                return parsed
    return shutil.get_terminal_size((fallback, 20)).columns


def _repeating_digits(width: int) -> str:
    digits = "1234567890"
    return (digits * ((width // len(digits)) + 1))[:width]


def _headers_and_rows(data: Any) -> tuple[list[str], list[list[str]]]:
    if isinstance(data, list):
        if not data:
            return [], []
        if all(isinstance(row, dict) for row in data):
            headers = list(dict.fromkeys(key for row in data for key in row))
            dict_rows = [[str(row.get(header, "")) for header in headers] for row in data]
            return [str(header) for header in headers], dict_rows
        return [], [[str(cell) for cell in row] if isinstance(row, (list, tuple)) else [str(row)] for row in data]

    columns = data.get("columns") or data.get("headers") or []
    rows_in = data.get("rows") or []
    headers = [str(col.get("name", "")) if isinstance(col, dict) else str(col) for col in columns]
    rows: list[list[str]] = []
    for row in rows_in:
        if isinstance(row, dict):
            rows.append([str(row.get(header, "")) for header in headers])
        else:
            values = [str(value) for value in row]
            if len(values) < len(headers):
                values.extend("" for _ in range(len(headers) - len(values)))
            rows.append(values[: len(headers)] if headers else values)
    return headers, rows


def _wrap_table_cells(rows: list[list[str]], maxcolwidths: list[int | None] | None) -> list[list[str]]:
    if not maxcolwidths:
        return rows
    wrapped: list[list[str]] = []
    for row in rows:
        wrapped_row: list[str] = []
        for index, cell in enumerate(row):
            col_width = maxcolwidths[index] if index < len(maxcolwidths) else None
            wrapped_row.append(wrap_visible(cell, col_width) if col_width else cell)
        wrapped.append(wrapped_row)
    return wrapped


def render_table(data: Any, format: str = "rounded_grid", maxcolwidths: list[int | None] | None = None) -> str:
    table_format = TABLE_FORMATS.get(format, format)
    headers, rows = _headers_and_rows(data)
    if table_format in {"github", "pipe"}:
        headers, rows = _escape_markdown_table(headers, rows)
    rows = _wrap_table_cells(rows, maxcolwidths)
    rendered = tabulate(
        rows,
        headers=headers,
        tablefmt=table_format,
        maxcolwidths=maxcolwidths,
        disable_numparse=True,
    )
    return rendered + ("\n" if rendered else "")


def _escape_markdown_table(headers: list[str], rows: list[list[str]]) -> tuple[list[str], list[list[str]]]:
    def cell(value: object) -> str:
        text = strip_ansi(value)
        return text.replace("\\", "\\\\").replace("|", "\\|").replace("\n", "<br>")

    return [cell(header) for header in headers], [[cell(value) for value in row] for row in rows]


def build_mermaid_flowchart(spec: Any, theme: str = "default") -> str:
    if isinstance(spec, str):
        return spec if spec.endswith("\n") else spec + "\n"
    direction = spec.get("direction", "TD")
    lines = [_mermaid_init(theme), f"flowchart {direction}"]
    for node in spec.get("nodes", []):
        if isinstance(node, str):
            lines.append(f"    {node}")
            continue
        node_id = _mermaid_id(node["id"])
        label = _mermaid_label(node.get("label", node["id"]))
        shape = node.get("shape", "rect")
        lines.append(f"    {node_id}{_node_shape(label, shape)}")
    for edge in spec.get("edges", []):
        if isinstance(edge, str):
            lines.append(f"    {edge}")
            continue
        source = _mermaid_id(edge.get("from") or edge.get("source"))
        target = _mermaid_id(edge.get("to") or edge.get("target"))
        label = edge.get("label")
        arrow = edge.get("arrow", "-->")
        if label:
            lines.append(f"    {source} {arrow}|{_mermaid_label(label)}| {target}")
        else:
            lines.append(f"    {source} {arrow} {target}")
    return "\n".join(lines) + "\n"


def render_svg_card(spec: dict[str, Any]) -> str:
    width = int(spec.get("width", 560))
    height = int(spec.get("height", 220))
    title = str(spec.get("title", ""))
    subtitle = str(spec.get("subtitle", ""))
    body = spec.get("body", [])
    if isinstance(body, str):
        body = [body]
    background = str(spec.get("background", "#111827"))
    accent = str(spec.get("accent", "#00f5d4"))
    foreground = str(spec.get("foreground", "#f9fafb"))

    try:
        import drawsvg as draw
    except ImportError:
        return _svg_card_string(width, height, title, subtitle, body, background, accent, foreground)

    drawing = draw.Drawing(width, height, origin=(0, 0), displayInline=False)
    drawing.append(draw.Rectangle(0, 0, width, height, rx=10, ry=10, fill=background))
    drawing.append(draw.Rectangle(0, 0, 10, height, fill=accent))
    drawing.append(draw.Text(title, 28, 32, 56, fill=foreground, font_family="Inter, Arial, sans-serif", font_weight="700"))
    if subtitle:
        drawing.append(draw.Text(subtitle, 16, 34, 86, fill=accent, font_family="Inter, Arial, sans-serif"))
    y = 124
    for line in body:
        drawing.append(draw.Text(str(line), 16, 34, y, fill=foreground, font_family="Inter, Arial, sans-serif"))
        y += 26
    return drawing.as_svg()


def render_svg_fallback(svg_source: str, width: int = 80, no_color: bool = False) -> str:
    chafa = shutil.which("chafa") or shutil.which("chafa.exe")
    if not chafa:
        scoop_chafa = Path.home() / "scoop" / "shims" / "chafa.exe"
        if scoop_chafa.exists():
            chafa = str(scoop_chafa)
    if not chafa:
        return svg_source
    with tempfile.TemporaryDirectory(prefix="glyph-arts-svg-") as tmp:
        path = Path(tmp) / "card.svg"
        path.write_text(svg_source, encoding="utf-8")
        cols = max(1, int(width))
        rows = max(1, round(cols / 4))
        cmd = [
            chafa,
            "--format",
            "symbols",
            "--symbols",
            "block",
            "--size",
            f"{cols}x{rows}",
        ]
        if no_color:
            cmd.extend(["--colors", "none"])
        cmd.append(str(path))
        result = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        return result.stdout if result.returncode == 0 and result.stdout else svg_source


def render_raster_textual(image: str | Path, width: int = 80, height: int | None = None) -> str:
    try:
        from rich.console import Console
        from textual_image.renderable import Image
    except ImportError as exc:
        raise ImportError("textual-image") from exc

    cols = max(1, int(width))
    rows = max(1, int(height) if height is not None else round(cols / 2))
    renderable = Image(str(image), width=cols, height=rows)
    console = Console(file=io.StringIO(), force_terminal=False, color_system=None, width=cols, record=True)
    console.print(renderable)
    return console.export_text()


def render_markdown_panel(spec: dict[str, Any]) -> str:
    kind = spec.get("kind", "blockquote")
    title = str(spec.get("title", "")).strip()
    body = spec.get("body", spec.get("content", ""))
    if isinstance(body, list):
        body_text = "\n".join(str(line) for line in body)
    else:
        body_text = str(body)
    if kind == "details":
        summary = title or "Details"
        return f"<details>\n<summary>{html.escape(summary)}</summary>\n\n{body_text}\n\n</details>\n"
    quote_lines = [f"> **{title}**"] if title else []
    quote_lines.extend(f"> {line}" if line else ">" for line in body_text.splitlines())
    return "\n".join(quote_lines) + "\n"


def _mermaid_init(theme: str) -> str:
    config = MERMAID_THEMES.get(theme, MERMAID_THEMES["default"])
    return f"%%{{init: {json.dumps(config, separators=(',', ':'))} }}%%"


def _mermaid_id(value: object) -> str:
    return re.sub(r"\W+", "_", str(value)).strip("_") or "node"


def _mermaid_label(value: object) -> str:
    return str(value).replace('"', r"\"").replace("\n", "<br>")


def _node_shape(label: str, shape: str) -> str:
    if shape == "round":
        return f'("{label}")'
    if shape == "stadium":
        return f'(["{label}"])'
    if shape == "diamond":
        return f'{{"{label}"}}'
    if shape == "circle":
        return f'(("{label}"))'
    return f'["{label}"]'


def _svg_card_string(
    width: int,
    height: int,
    title: str,
    subtitle: str,
    body: list[Any],
    background: str,
    accent: str,
    foreground: str,
) -> str:
    body_lines = []
    y = 124
    for line in body:
        body_lines.append(
            f'<text x="34" y="{y}" fill="{foreground}" font-size="16" font-family="Inter,Arial,sans-serif">'
            f"{html.escape(str(line))}</text>"
        )
        y += 26
    subtitle_line = (
        f'<text x="34" y="86" fill="{accent}" font-size="16" font-family="Inter,Arial,sans-serif">'
        f"{html.escape(subtitle)}</text>"
        if subtitle
        else ""
    )
    return (
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" viewBox="0 0 {width} {height}">'
        f'<rect width="{width}" height="{height}" rx="10" fill="{background}"/>'
        f'<rect width="10" height="{height}" fill="{accent}"/>'
        f'<text x="32" y="56" fill="{foreground}" font-size="28" font-weight="700" '
        f'font-family="Inter,Arial,sans-serif">{html.escape(title)}</text>'
        f"{subtitle_line}{''.join(body_lines)}</svg>\n"
    )
