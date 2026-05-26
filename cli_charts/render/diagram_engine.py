"""Diagram rendering backend for chat-safe structure drawings."""

from __future__ import annotations

import csv
import os
import re
import shutil
import subprocess
import sys
from ast import literal_eval
from dataclasses import dataclass
from io import StringIO
from pathlib import Path

from cli_charts.render.text_layout import center_text, display_width, fit_text, pad_right


@dataclass(frozen=True)
class DiagramGenerator:
    key: str
    diagon_name: str
    title: str
    aliases: tuple[str, ...] = ()


CORE_GENERATORS = (
    DiagramGenerator("math", "Math", "Math"),
    DiagramGenerator("sequence", "Sequence", "Sequence Diagram"),
    DiagramGenerator("tree", "Tree", "Tree"),
    DiagramGenerator("table", "Table", "Table"),
    DiagramGenerator("frame", "Frame", "Frame", aliases=("box", "note")),
    DiagramGenerator("flowchart", "Flowchart", "Flowchart"),
    DiagramGenerator("graphdag", "GraphDAG", "GraphDAG", aliases=("dag",)),
    DiagramGenerator("graphplanar", "GraphPlanar", "GraphPlanar", aliases=("planar",)),
)

_GENERATOR_BY_KEY = {generator.key: generator for generator in CORE_GENERATORS}
_GENERATOR_ALIAS = {
    alias: generator.key
    for generator in CORE_GENERATORS
    for alias in generator.aliases
    if alias not in {"box", "note"}
}
_BUILTIN_EXTENSION_KEYS = {"box", "note"}

DIAGON_GENERATORS = {
    generator.key: generator.diagon_name
    for generator in CORE_GENERATORS
} | {"box": "Frame", "note": "Frame"}

BUILTIN_GENERATORS = set(_GENERATOR_BY_KEY) | _BUILTIN_EXTENSION_KEYS

_GREEK = {
    "alpha": "α",
    "beta": "β",
    "gamma": "γ",
    "delta": "δ",
    "epsilon": "ε",
    "theta": "θ",
    "lambda": "λ",
    "mu": "μ",
    "pi": "π",
    "sigma": "σ",
    "phi": "φ",
    "omega": "ω",
}
_MATH_OPERATORS = {
    "sum": "Σ",
    "prod": "Π",
    "int": "∫",
}
_SUP = str.maketrans("0123456789+-=()nixy", "⁰¹²³⁴⁵⁶⁷⁸⁹⁺⁻⁼⁽⁾ⁿⁱˣʸ")
_SUB = str.maketrans("0123456789+-=()nixy", "₀₁₂₃₄₅₆₇₈₉₊₋₌₍₎ₙᵢₓᵧ")


def normalize_diagram_kind(kind: str) -> str:
    key = (kind or "").strip().lower().replace("-", "").replace("_", "")
    key = _GENERATOR_ALIAS.get(key, key)
    if key not in _GENERATOR_BY_KEY and key not in _BUILTIN_EXTENSION_KEYS:
        supported = ", ".join(sorted(set(DIAGON_GENERATORS) | set(_GENERATOR_ALIAS)))
        raise ValueError(f"unknown diagram kind: {kind!r}; supported: {supported}")
    return key


def diagram_capabilities() -> list[dict[str, object]]:
    return [
        {
            "key": generator.key,
            "diagon": generator.diagon_name,
            "title": generator.title,
            "aliases": list(generator.aliases),
            "builtin": generator.key in BUILTIN_GENERATORS,
        }
        for generator in CORE_GENERATORS
    ]


def render_diagram(
    kind: str,
    text: str,
    *,
    width: int = 70,
    output: str | None = None,
    engine: str = "auto",
) -> int:
    key = normalize_diagram_kind(kind)
    source = text.replace("\\n", "\n").rstrip("\n")
    if not source:
        print("ERROR:schema: diagram input must not be empty", file=sys.stderr)
        return 1

    result = None
    if engine in {"auto", "diagon"}:
        result = _render_diagon(key, source)
        if result is None and engine == "diagon":
            print(
                "ERROR:dep: diagon binary not found; install Diagon or use --diagram-engine builtin",
                file=sys.stderr,
            )
            return 2
        if isinstance(result, tuple):
            code, stdout, stderr = result
            if code != 0:
                print(stderr.strip() or f"ERROR:render: diagon {DIAGON_GENERATORS[key]} failed", file=sys.stderr)
                if engine == "diagon":
                    return code or 4
            elif stdout.strip():
                return _emit(stdout, output)

    if key not in BUILTIN_GENERATORS:
        print(
            f"ERROR:dep: {DIAGON_GENERATORS[key]} needs the Diagon binary; "
            "builtin fallback supports math/sequence/tree/table/frame/flowchart/graphdag/graphplanar",
            file=sys.stderr,
        )
        return 2
    return _emit(_render_builtin(key, source, width), output)


def _render_diagon(kind: str, source: str) -> tuple[int, str, str] | None:
    binary = os.environ.get("GLYPH_ARTS_DIAGON") or shutil.which("diagon") or shutil.which("diagon.exe")
    if not binary:
        return None
    proc = subprocess.run(
        [binary, DIAGON_GENERATORS[kind]],
        input=source,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=15,
    )
    return proc.returncode, proc.stdout, proc.stderr


def _emit(text: str, output: str | None) -> int:
    rendered = text.rstrip("\n") + "\n"
    if output:
        Path(output).write_text(rendered, encoding="utf-8")
    else:
        print(rendered, end="")
    return 0


def _box_lines(lines: list[str], title: str = "") -> str:
    body = lines or [""]
    width = max(display_width(line) for line in body)
    if title:
        width = max(width, display_width(title) + 2)
    top = "┌" + "─" * (width + 2) + "┐"
    bottom = "└" + "─" * (width + 2) + "┘"
    out = [top]
    if title:
        out.append("│ " + center_text(title, width) + " │")
        out.append("├" + "─" * (width + 2) + "┤")
    out.extend("│ " + pad_right(line, width) + " │" for line in body)
    out.append(bottom)
    return "\n".join(out) + "\n"


def _render_builtin(kind: str, source: str, width: int) -> str:
    if kind == "math":
        return _math(source)
    if kind == "sequence":
        return _sequence(source)
    if kind == "tree":
        return _tree(source)
    if kind == "table":
        return _table(source)
    if kind == "frame":
        return _frame(source)
    if kind == "box":
        return _box_lines(source.splitlines())
    if kind == "note":
        return _note(source)
    if kind == "graphplanar":
        return _graph_planar(source, width=width)
    if kind == "graphdag":
        return _graph_dag(source, width=width)
    return _flow(source, title="Flowchart", width=width)


def verify_equal_width_box(text: str) -> bool:
    """Return true when every non-empty line in a boxed diagram has equal width."""
    lines = [line for line in text.splitlines() if line]
    return bool(lines) and len({display_width(line) for line in lines}) == 1


def _math(source: str) -> str:
    lines: list[str] = []
    for raw in source.splitlines():
        item = raw.strip()
        if not item:
            continue
        lines.extend(_render_math_expression(item))
    return _box_lines(lines or [""], title="Math")


def _render_math_expression(expr: str) -> list[str]:
    matrix = _parse_math_matrix(expr)
    if matrix:
        return _render_math_matrix(matrix)
    parts = _split_math_terms(expr)
    blocks: list[list[str]] = []
    has_tall = False
    for op, term in parts:
        if op:
            blocks.append(["", op, ""])
        fraction = _split_top_level_fraction(term)
        if fraction:
            num, den = (_format_math_inline(part.strip()) for part in fraction)
            width = max(display_width(num), display_width(den), 1)
            blocks.append([center_text(num, width), "─" * width, center_text(den, width)])
            has_tall = True
        else:
            blocks.append(["", _format_math_inline(term.strip()), ""])
    if not has_tall:
        return [" ".join(block[1] for block in blocks if block[1]).strip()]
    rows = []
    for row in range(3):
        rows.append(" ".join(pad_right(block[row], max(display_width(part) for part in block)) for block in blocks).rstrip())
    return rows


def _parse_math_matrix(expr: str) -> list[list[str]] | None:
    text = expr.strip()
    body = ""
    if text.startswith("matrix(") and text.endswith(")"):
        body = text[len("matrix("):-1]
    elif text.startswith("[[") and text.endswith("]]"):
        try:
            parsed = literal_eval(text)
        except (SyntaxError, ValueError):
            parsed = None
        if isinstance(parsed, list) and all(isinstance(row, list) for row in parsed):
            rows = [[_format_math_inline(str(cell)) for cell in row] for row in parsed]
            return rows if rows else None
    if not body:
        return None
    rows = []
    for row in body.split(";"):
        cells = [_format_math_inline(cell.strip()) for cell in row.split(",")]
        rows.append([cell for cell in cells if cell])
    return rows if rows else None


def _render_math_matrix(rows: list[list[str]]) -> list[str]:
    col_count = max(len(row) for row in rows)
    widths = [
        max(display_width(row[col]) if col < len(row) else 0 for row in rows)
        for col in range(col_count)
    ]
    brackets = [
        ("⎡", "⎤"),
        ("⎢", "⎥"),
        ("⎣", "⎦"),
    ]
    out = []
    for idx, row in enumerate(rows):
        if len(rows) == 1:
            left, right = "[", "]"
        else:
            left, right = brackets[1]
            if idx == 0:
                left, right = brackets[0]
            if idx == len(rows) - 1:
                left, right = brackets[2]
        cells = [
            center_text(row[col] if col < len(row) else "", widths[col])
            for col in range(col_count)
        ]
        out.append(f"{left} {'  '.join(cells)} {right}")
    return out


def _split_math_terms(expr: str) -> list[tuple[str, str]]:
    parts: list[tuple[str, str]] = []
    depth = 0
    current = []
    op = ""
    for idx, char in enumerate(expr):
        if char in "({[":
            depth += 1
        elif char in ")}]":
            depth = max(0, depth - 1)
        if depth == 0 and char in "+-" and idx > 0:
            previous = expr[idx - 1]
            next_char = expr[idx + 1] if idx + 1 < len(expr) else ""
            if char == "-" and (previous == "<" or next_char == ">"):
                current.append(char)
                continue
            if previous not in "eE*/^_":
                term = "".join(current).strip()
                if term:
                    parts.append((op, term))
                op = char
                current = []
                continue
        current.append(char)
    term = "".join(current).strip()
    if term:
        parts.append((op, term))
    return parts or [("", expr)]


def _split_top_level_fraction(term: str) -> tuple[str, str] | None:
    depth = 0
    for idx, char in enumerate(term):
        if char in "({[":
            depth += 1
        elif char in ")}]":
            depth = max(0, depth - 1)
        elif char == "/" and depth == 0:
            left = term[:idx].strip()
            right = term[idx + 1:].strip()
            if left and right:
                return left, right
    return None


def _format_math_inline(expr: str) -> str:
    out = expr
    out = _replace_named_math(out)
    out = out.replace("<=", "≤").replace(">=", "≥").replace("!=", "≠").replace("==", "=")
    out = out.replace("=>", "⇒").replace("->", "→").replace("<-", "←").replace("+-", "±")
    out = out.replace("*", "·")
    out = _replace_function(out, "sqrt", "√")
    out = _replace_script(out, "^", _SUP)
    out = _replace_script(out, "_", _SUB)
    return out


def _replace_named_math(expr: str) -> str:
    out = re.sub(r"\\?\b(?:infty|infinity|inf)\b", "∞", expr)
    for name, symbol in _GREEK.items():
        out = re.sub(rf"(?<![A-Za-z])\\?{re.escape(name)}(?=(_|\^|\b))", symbol, out)
    for name, symbol in _MATH_OPERATORS.items():
        out = re.sub(rf"(?<![A-Za-z])\\?{re.escape(name)}(?=(_|\^|\b))", symbol, out)
    return out


def _replace_function(expr: str, name: str, symbol: str) -> str:
    out = expr
    marker = name + "("
    while marker in out:
        start = out.find(marker)
        inner_start = start + len(marker)
        end = _find_matching_paren(out, inner_start - 1)
        if end == -1:
            break
        inner = out[inner_start:end]
        out = out[:start] + symbol + "(" + inner + ")" + out[end + 1:]
    return out


def _find_matching_paren(expr: str, start: int) -> int:
    depth = 0
    for idx in range(start, len(expr)):
        if expr[idx] == "(":
            depth += 1
        elif expr[idx] == ")":
            depth -= 1
            if depth == 0:
                return idx
    return -1


def _replace_script(expr: str, marker: str, table: dict[int, int]) -> str:
    out = []
    idx = 0
    while idx < len(expr):
        if expr[idx] != marker or idx + 1 >= len(expr):
            out.append(expr[idx])
            idx += 1
            continue
        idx += 1
        if idx < len(expr) and expr[idx] == "{":
            end = expr.find("}", idx + 1)
            if end != -1:
                out.append(_format_script_text(expr[idx + 1:end], table))
                idx = end + 1
                continue
        out.append(expr[idx].translate(table))
        idx += 1
    return "".join(out)


def _format_script_text(text: str, table: dict[int, int]) -> str:
    out = []
    idx = 0
    while idx < len(text):
        char = text[idx]
        if char in "^_" and idx + 1 < len(text):
            idx += 1
            if text[idx] == "{":
                end = text.find("}", idx + 1)
                if end != -1:
                    out.append(_format_script_text(text[idx + 1:end], table))
                    idx = end + 1
                    continue
            out.append(text[idx].translate(table))
            idx += 1
            continue
        out.append(char.translate(table))
        idx += 1
    return "".join(out)


def _sequence(source: str) -> str:
    messages: list[tuple[str, str, str, str]] = []
    participants: list[str] = []
    for line in source.splitlines():
        item = line.strip()
        if not item:
            continue
        if item.startswith(("participant ", "actor ")):
            name = item.split(maxsplit=1)[1].strip()
            if " as " in name:
                name = name.rsplit(" as ", 1)[-1].strip()
            if name not in participants:
                participants.append(name)
            continue
        parsed = _parse_sequence_message(item)
        if parsed is None:
            if item not in participants:
                participants.append(item)
            continue
        left, right, arrow, message = parsed
        for name in (left, right):
            if name not in participants:
                participants.append(name)
        messages.append((left, right, arrow, message))
    if not participants:
        return ""
    lane_w = max(8, min(14, max(display_width(name) for name in participants) + 4))
    centers = [idx * (lane_w + 2) + lane_w // 2 for idx in range(len(participants))]
    total_w = len(participants) * lane_w + max(0, len(participants) - 1) * 2
    header = "  ".join(center_text(name, lane_w) for name in participants)
    rails = "".join("│" if idx in centers else " " for idx in range(total_w))
    out = [header, rails]
    index = {name: idx for idx, name in enumerate(participants)}
    summaries = []
    for left, right, arrow, message in messages:
        src = centers[index[left]]
        dst = centers[index[right]]
        row = [" "] * total_w
        row[src] = "├"
        line_char = "┄" if "--" in arrow else "─"
        if src < dst:
            for pos in range(src + 1, dst):
                row[pos] = line_char
            row[dst] = "►"
        else:
            for pos in range(dst + 1, src):
                row[pos] = line_char
            row[dst] = "◄"
        out.append("".join(row))
        if message:
            label_row = [" "] * total_w
            start, end = sorted((src, dst))
            available = max(0, end - start - 1)
            label = center_text(fit_text(message, available), available)
            for offset, char in enumerate(label):
                if start + 1 + offset < end:
                    label_row[start + 1 + offset] = char
            if any(char.strip() for char in label_row):
                out.append("".join(label_row))
        out.append(rails)
        summaries.append(f"{left} -> {right}" + (f" : {message}" if message else ""))
    if summaries:
        out.append("")
        out.extend(summaries)
    return _box_lines(out, title="Sequence Diagram")


_SEQUENCE_ARROW_RE = re.compile(r"^\s*(.*?)\s*(<<--|<<-|-->>|->>|-->|->|=>|<--|<-)\s*(.*?)\s*$")


def _parse_sequence_message(item: str) -> tuple[str, str, str, str] | None:
    message = ""
    head = item
    if ":" in item:
        head, message = item.split(":", 1)
        message = message.strip()
    match = _SEQUENCE_ARROW_RE.match(head)
    if not match:
        return None
    left, arrow, right = (part.strip() for part in match.groups())
    if arrow.startswith("<") or arrow.startswith("<<"):
        left, right = right, left
    return left, right, arrow, message


def _tree(source: str) -> str:
    lines = [line.rstrip() for line in source.splitlines() if line.strip()]
    if not lines:
        return ""
    if all("/" in line and not line.startswith(" ") for line in lines):
        root: dict[str, dict] = {}
        for line in lines:
            node = root
            for part in [part for part in line.strip("/").split("/") if part]:
                node = node.setdefault(part, {})
        return _render_tree_node(root).rstrip() + "\n"
    entries = [
        (len(line) - len(line.lstrip(" ")), line.strip())
        for line in lines
    ]
    if len({indent for indent, _text in entries}) <= 1:
        return _render_tree_nodes([{"text": text, "children": []} for _indent, text in entries]).rstrip() + "\n"
    return _render_tree_nodes(_parse_indented_tree(entries)).rstrip() + "\n"


def _render_tree_node(node: dict[str, dict], prefix: str = "") -> str:
    out = []
    items = list(node.items())
    for idx, (name, child) in enumerate(items):
        last = idx == len(items) - 1
        connector = "└── " if last else "├── "
        out.append(prefix + connector + name)
        extension = "    " if last else "│   "
        if child:
            out.append(_render_tree_node(child, prefix + extension))
    return "\n".join(out)


def _parse_indented_tree(entries: list[tuple[int, str]]) -> list[dict[str, object]]:
    root: list[dict[str, object]] = []
    indents = sorted({indent for indent, _text in entries})
    levels = {indent: idx for idx, indent in enumerate(indents)}
    stack: list[tuple[int, dict[str, object]]] = []
    for indent, text in entries:
        level = levels[indent]
        node: dict[str, object] = {"text": text, "children": []}
        while stack and stack[-1][0] >= level:
            stack.pop()
        if stack:
            children = stack[-1][1]["children"]
            if isinstance(children, list):
                children.append(node)
        else:
            root.append(node)
        stack.append((level, node))
    return root


def _render_tree_nodes(nodes: list[dict[str, object]], prefix: str = "") -> str:
    out = []
    for idx, node in enumerate(nodes):
        last = idx == len(nodes) - 1
        text = str(node["text"])
        connector = "└── " if last else "├── "
        out.append(prefix + connector + text)
        children = node.get("children", [])
        if isinstance(children, list) and children:
            extension = "    " if last else "│   "
            out.append(_render_tree_nodes(children, prefix + extension))
    return "\n".join(out)


def _table(source: str) -> str:
    rows = []
    for line in source.splitlines():
        stripped = line.strip()
        if not stripped:
            continue
        if "|" in stripped:
            cells = [cell.strip() for cell in stripped.strip("|").split("|")]
        else:
            cells = next(csv.reader(StringIO(stripped)))
        rows.append(cells)
    if not rows:
        return ""
    widths = [
        max(display_width(row[i]) if i < len(row) else 0 for row in rows)
        for i in range(max(len(row) for row in rows))
    ]
    top = "┌" + "┬".join("─" * (width + 2) for width in widths) + "┐"
    mid = "├" + "┼".join("─" * (width + 2) for width in widths) + "┤"
    bottom = "└" + "┴".join("─" * (width + 2) for width in widths) + "┘"
    out = [top]
    for idx, row in enumerate(rows):
        out.append("│ " + " │ ".join(pad_right(row[i] if i < len(row) else "", widths[i]) for i in range(len(widths))) + " │")
        if idx == 0:
            out.append(mid)
    out.append(bottom)
    return "\n".join(out) + "\n"


def _frame(source: str) -> str:
    body = source.splitlines() or [""]
    numbered = [f"{idx + 1:>2} │ {line}" for idx, line in enumerate(body)]
    return _box_lines(numbered, title="Frame")


def _note(source: str) -> str:
    lines = [line.rstrip() for line in source.splitlines()]
    label = "NOTE"
    if lines:
        candidate = lines[0].strip()
        label_like = candidate.isupper() or (len(lines) > 1 and bool(candidate) and not any(ch.isspace() for ch in candidate))
        if label_like and display_width(candidate) <= 16:
            label = lines.pop(0).strip()
    body = [line for line in lines if line.strip()] or [""]
    left_w = max(6, display_width(label) + 2)
    right_w = max(display_width(line) for line in body)
    top = "┌" + "─" * left_w + "┬" + "─" * (right_w + 2) + "┐"
    bottom = "└" + "─" * left_w + "┴" + "─" * (right_w + 2) + "┘"
    mid = len(body) // 2
    out = [top]
    for idx, line in enumerate(body):
        label_cell = center_text(label, left_w) if idx == mid else " " * left_w
        out.append("│" + label_cell + "│ " + pad_right(line, right_w) + " │")
    out.append(bottom)
    return "\n".join(out) + "\n"


def _flow(source: str, *, title: str, width: int) -> str:
    nodes, edges = _parse_flow_edges(source)
    if not nodes:
        return ""
    chain = _linear_chain(nodes, [(left, right) for left, right, _label in edges])
    if chain and len(chain) == len(nodes):
        lines: list[str] = []
        for idx, node in enumerate(chain):
            lines.extend(_mini_box(fit_text(node, max(8, width - 6))))
            if idx < len(chain) - 1:
                label = next((label for left, right, label in edges if left == node and right == chain[idx + 1]), "")
                if label:
                    lines.append(f"  │ {fit_text(label, max(1, width - 8))}")
                else:
                    lines.append("  │")
                lines.append("  ▼")
        return _box_lines(lines, title=title)

    adjacency: dict[str, list[tuple[str, str]]] = {node: [] for node in nodes}
    for left, right, label in edges:
        adjacency.setdefault(left, []).append((right, label))
        adjacency.setdefault(right, [])
    lines = []
    for node in nodes:
        label = fit_text(node, max(8, width - 8))
        outgoing = adjacency.get(node, [])
        if not outgoing:
            lines.append(f"[{label}]")
            continue
        lines.append(f"[{label}]")
        for idx, (right, edge_label) in enumerate(outgoing):
            branch = "└" if idx == len(outgoing) - 1 else "├"
            edge_text = f" {edge_label} " if edge_label else " "
            lines.append(f"  {branch}─{edge_text}→ [{fit_text(right, max(8, width - 16))}]")
    return _box_lines(lines, title=title)


def _mini_box(text: str) -> list[str]:
    w = display_width(text)
    return [
        "┌" + "─" * (w + 2) + "┐",
        "│ " + pad_right(text, w) + " │",
        "└" + "─" * (w + 2) + "┘",
    ]


def _parse_flow_edges(source: str) -> tuple[list[str], list[tuple[str, str, str]]]:
    nodes: list[str] = []
    edges: list[tuple[str, str, str]] = []
    for line in source.splitlines():
        item = line.strip().rstrip(";")
        if not item:
            continue
        if "->" in item or "=>" in item:
            arrow = "->" if "->" in item else "=>"
            parts = [part.strip() for part in item.split(arrow) if part.strip()]
            clean_parts = []
            for part in parts:
                label = ""
                if ":" in part:
                    part, label = [piece.strip() for piece in part.split(":", 1)]
                clean_parts.append((part, label))
                if part and part not in nodes:
                    nodes.append(part)
            for (left, _left_label), (right, right_label) in zip(clean_parts, clean_parts[1:], strict=False):
                edges.append((left, right, right_label))
        else:
            if item not in nodes:
                nodes.append(item)
    return nodes, edges


def _linear_chain(nodes: list[str], edges: list[tuple[str, str]]) -> list[str]:
    if not edges:
        return nodes
    outgoing: dict[str, list[str]] = {}
    incoming: dict[str, int] = {node: 0 for node in nodes}
    for left, right in edges:
        outgoing.setdefault(left, []).append(right)
        incoming[right] = incoming.get(right, 0) + 1
    if any(len(values) > 1 for values in outgoing.values()):
        return []
    roots = [node for node in nodes if incoming.get(node, 0) == 0]
    if len(roots) != 1:
        return []
    chain = [roots[0]]
    seen = {roots[0]}
    while outgoing.get(chain[-1]):
        nxt = outgoing[chain[-1]][0]
        if nxt in seen:
            return []
        chain.append(nxt)
        seen.add(nxt)
    return chain


def _parse_graph_edges(source: str) -> tuple[list[str], list[tuple[str, str]]]:
    nodes: list[str] = []
    edges: list[tuple[str, str]] = []
    for item in _iter_graph_statements(source):
        if not item:
            continue
        arrow = "->" if "->" in item else "--" if "--" in item else "=>"
        if arrow in item:
            parts = [part.strip() for part in item.split(arrow) if part.strip()]
            for left, right in zip(parts, parts[1:], strict=False):
                left = _clean_graph_node(left)
                right = _clean_graph_node(right)
                edges.append((left, right))
                for node in (left, right):
                    if node not in nodes:
                        nodes.append(node)
        elif item not in nodes:
            nodes.append(_clean_graph_node(item))
    return nodes, edges


def _iter_graph_statements(source: str) -> list[str]:
    text = source.replace("{", "\n").replace("}", "\n")
    text = re.sub(r"\b(?:strict\s+)?(?:di)?graph\b[^\n]*", "", text, flags=re.IGNORECASE)
    statements: list[str] = []
    for line in text.splitlines():
        for part in line.split(";"):
            item = part.strip()
            if item:
                statements.append(item)
    return statements


def _clean_graph_node(node: str) -> str:
    cleaned = re.sub(r"\[.*?\]", "", node).strip().strip('"')
    return cleaned


def _graph_dag(source: str, *, width: int) -> str:
    nodes, edges = _parse_graph_edges(source)
    if not nodes:
        return ""
    levels = _dag_levels(nodes, edges)
    lines: list[str] = []
    for idx, level in enumerate(levels):
        boxes = [fit_text(node, max(8, min(18, width // max(1, len(level)) - 4))) for node in level]
        lines.append("   ".join(f"[{node}]" for node in boxes))
        if idx < len(levels) - 1:
            lines.append("   ".join("│" for _ in level))
            lines.append("   ".join("▼" for _ in level))
    if edges:
        lines.append("")
        lines.extend(f"{left} -> {right}" for left, right in edges)
    return _box_lines(lines, title="GraphDAG")


def _dag_levels(nodes: list[str], edges: list[tuple[str, str]]) -> list[list[str]]:
    incoming_count = {node: 0 for node in nodes}
    adjacency: dict[str, list[str]] = {node: [] for node in nodes}
    for left, right in edges:
        adjacency.setdefault(left, []).append(right)
        incoming_count[right] = incoming_count.get(right, 0) + 1
        incoming_count.setdefault(left, 0)
    queue = [node for node in nodes if incoming_count.get(node, 0) == 0] or nodes[:1]
    level_of = {node: 0 for node in queue}
    seen = set(queue)
    while queue:
        node = queue.pop(0)
        for right in adjacency.get(node, []):
            level_of[right] = max(level_of.get(right, 0), level_of[node] + 1)
            incoming_count[right] = incoming_count.get(right, 1) - 1
            if incoming_count[right] <= 0 and right not in seen:
                queue.append(right)
                seen.add(right)
    for node in nodes:
        level_of.setdefault(node, 0 if node not in seen else level_of[node])
    max_level = max(level_of.values(), default=0)
    return [
        [node for node in nodes if level_of[node] == level]
        for level in range(max_level + 1)
        if any(level_of[node] == level for node in nodes)
    ]


def _graph_planar(source: str, *, width: int) -> str:
    nodes, edges = _parse_graph_edges(source)
    if not nodes:
        return ""
    if len(nodes) >= 4:
        a, b, c, d = [fit_text(node, 12) for node in nodes[:4]]
        top = f"({a})" + "─" * 8 + f"({b})"
        mid = "  │" + " " * max(8, display_width(top) - 6) + "│"
        bottom = f"({d})" + "─" * 8 + f"({c})"
        lines = [top, mid, bottom]
    elif len(nodes) == 3:
        a, b, c = [fit_text(node, 12) for node in nodes]
        lines = [f"    ({a})", "   ╱   ╲", f"({b})───({c})"]
    else:
        lines = [f"({node})" for node in nodes]
    if edges:
        lines.append("")
        lines.extend(f"{left} -- {right}" for left, right in edges)
    return _box_lines(lines, title="GraphPlanar")
