from __future__ import annotations

import re

from cli_charts.render.text_layout import center_text, display_width, fit_text, pad_right

MERMAID_THEMES = [
    "zinc-light",
    "zinc-dark",
    "tokyo-night",
    "tokyo-night-storm",
    "tokyo-night-light",
    "catppuccin-mocha",
    "catppuccin-latte",
    "nord",
    "nord-light",
    "dracula",
    "github-light",
    "github-dark",
    "solarized-light",
    "solarized-dark",
    "one-dark",
]

_EDGE_RE = re.compile(r"^\s*(?P<src>.+?)\s*(?:-->|---|==>|-.->|--|->)\s*(?P<dst>.+?)\s*$")
_NODE_RE = re.compile(r"^(?P<id>[A-Za-z0-9_:-]+)(?P<bracket>[\[\{\(])(?P<label>.*)(?P<close>[\]\}\)])$")


def render_mermaid(
    source: str,
    *,
    width: int = 72,
    use_ascii: bool = False,
    padding_x: int = 5,
    padding_y: int = 1,
    box_padding: int = 1,
    theme: str = "zinc-dark",
) -> str:
    lines = [line.rstrip() for line in source.replace("\\n", "\n").splitlines() if line.strip()]
    if not lines:
        raise ValueError("mermaid input must not be empty")
    head = lines[0].strip()
    body = lines[1:]
    if head.startswith(("graph ", "flowchart ")):
        return _render_flowchart(head, body, width, use_ascii=use_ascii, padding_x=padding_x, box_padding=box_padding)
    if head == "sequenceDiagram":
        return _render_sequence(body, width, use_ascii=use_ascii, padding_x=padding_x)
    if head.startswith("stateDiagram"):
        return _render_edge_box("State", body, width, use_ascii=use_ascii)
    if head == "classDiagram":
        return _render_class(body, width, use_ascii=use_ascii)
    if head == "erDiagram":
        return _render_edge_box("ER Diagram", body, width, use_ascii=use_ascii)
    if head.startswith("xychart-beta"):
        return _render_xychart([head, *body], width, use_ascii=use_ascii)
    return _render_edge_box("Mermaid", lines, width, use_ascii=use_ascii)


def _chars(use_ascii: bool) -> dict[str, str]:
    if use_ascii:
        return {
            "tl": "+", "tr": "+", "bl": "+", "br": "+", "h": "-", "v": "|",
            "arrow": "->", "down": "v", "tee": "+",
        }
    return {
        "tl": "┌", "tr": "┐", "bl": "└", "br": "┘", "h": "─", "v": "│",
        "arrow": "────►", "down": "▼", "tee": "┼",
    }


def _box(label: str, *, use_ascii: bool, width: int | None = None, shape: str = "rect", padding: int = 1) -> list[str]:
    ch = _chars(use_ascii)
    text = fit_text(_clean_label(label), width or 24)
    inner = max(display_width(text) + padding * 2, 3)
    if width is not None:
        inner = max(3, width)
    if shape == "decision" and not use_ascii:
        return [
            "╭" + ch["h"] * inner + "╮",
            ch["v"] + center_text(text, inner) + ch["v"],
            "╰" + ch["h"] * inner + "╯",
        ]
    return [
        ch["tl"] + ch["h"] * inner + ch["tr"],
        ch["v"] + center_text(text, inner) + ch["v"],
        ch["bl"] + ch["h"] * inner + ch["br"],
    ]


def _frame(title: str, lines: list[str], width: int, *, use_ascii: bool) -> str:
    ch = _chars(use_ascii)
    body = lines or [""]
    inner = min(max(display_width(title) + 2, *(display_width(line) for line in body)), max(24, width - 4))
    top = ch["tl"] + f" {title} " + ch["h"] * max(0, inner - display_width(title) - 2) + ch["tr"]
    bottom = ch["bl"] + ch["h"] * inner + ch["br"]
    out = [top]
    for line in body:
        out.append(ch["v"] + pad_right(line, inner) + ch["v"])
    out.append(bottom)
    return "\n".join(out) + "\n"


def _clean_label(raw: str) -> str:
    value = raw.strip().strip(";").strip()
    match = _NODE_RE.match(value)
    if match:
        return match.group("label").strip('"')
    return value.strip('"')


def _node_id(raw: str) -> str:
    value = raw.strip().strip(";").strip()
    match = _NODE_RE.match(value)
    if match:
        return match.group("id")
    return value.strip('"')


def _node_shape(raw: str) -> str:
    match = _NODE_RE.match(raw.strip().strip(";"))
    if match and match.group("bracket") == "{":
        return "decision"
    return "rect"


def _parse_edge(line: str) -> tuple[str, str, str] | None:
    clean = line.strip().rstrip(";")
    if not clean or clean.startswith(("linkStyle", "classDef", "style ")):
        return None
    label = ""
    if "|" in clean:
        before, middle, after = clean.split("|", 2)
        label = middle.strip()
        clean = before + after
    match = _EDGE_RE.match(clean)
    if not match:
        return None
    src = match.group("src").strip()
    dst = match.group("dst").strip()
    if not src or not dst or src == dst:
        return None
    return src, dst, label


def _render_flowchart(head: str, body: list[str], width: int, *, use_ascii: bool, padding_x: int, box_padding: int) -> str:
    ch = _chars(use_ascii)
    direction = head.split(maxsplit=1)[1].strip().upper() if len(head.split()) > 1 else "TD"
    raw_edges = [edge for line in body if (edge := _parse_edge(line))]
    labels: dict[str, str] = {}
    shapes: dict[str, str] = {}
    edges: list[tuple[str, str, str]] = []
    for src, dst, label in raw_edges:
        src_id = _node_id(src)
        dst_id = _node_id(dst)
        labels.setdefault(src_id, _clean_label(src))
        labels.setdefault(dst_id, _clean_label(dst))
        shapes.setdefault(src_id, _node_shape(src))
        shapes.setdefault(dst_id, _node_shape(dst))
        edges.append((src_id, dst_id, label))
    if not edges:
        nodes = [_clean_label(line) for line in body if line.strip()]
        return _frame("Mermaid Flowchart", nodes, width, use_ascii=use_ascii)
    chain = _linear_chain(edges)
    if direction in {"LR", "RL"}:
        boxes = []
        for node in chain:
            label = labels.get(node, _clean_label(node))
            shape = shapes.get(node, "rect")
            node_box = _box(label, use_ascii=use_ascii, width=max(5, display_width(label) + box_padding * 2), shape=shape, padding=box_padding)
            boxes.append(node_box)
        gap = " " * max(1, padding_x // 2)
        arrow = gap + ch["arrow"] + gap
        spacer = " " * display_width(arrow)
        rows = []
        for row in range(3):
            joiner = arrow if row == 1 else spacer
            rows.append(joiner.join(box[row] for box in boxes))
        return "\n".join(rows).rstrip() + "\n"
    lines: list[str] = []
    for idx, node in enumerate(chain):
        lines.extend(_box(labels.get(node, _clean_label(node)), use_ascii=use_ascii, shape=shapes.get(node, "rect"), padding=box_padding))
        if idx < len(chain) - 1:
            label = _edge_label(edges, node, chain[idx + 1])
            if label:
                lines.append(center_text(label, max(8, display_width(label))))
            lines.append(center_text(ch["down"], 8))
    return _frame("Mermaid Flowchart", lines, width, use_ascii=use_ascii)


def _linear_chain(edges: list[tuple[str, str, str]]) -> list[str]:
    chain = [edges[0][0], edges[0][1]]
    for src, dst, _label in edges[1:]:
        if chain[-1] == src:
            chain.append(dst)
        elif dst not in chain:
            chain.extend([src, dst])
    seen: list[str] = []
    for node in chain:
        if node not in seen:
            seen.append(node)
    return seen


def _edge_label(edges: list[tuple[str, str, str]], src: str, dst: str) -> str:
    for left, right, label in edges:
        if left == src and right == dst:
            return label
    return ""


def _render_sequence(body: list[str], width: int, *, use_ascii: bool, padding_x: int) -> str:
    ch = _chars(use_ascii)
    rows: list[str] = []
    for line in body:
        clean = line.strip()
        if not clean or clean.startswith(("participant", "actor", "autonumber")):
            continue
        if ":" in clean:
            route, message = clean.split(":", 1)
        else:
            route, message = clean, ""
        if "-->>" in route:
            left, right = route.split("-->>", 1)
            arrow = "<--" if use_ascii else "◄" + "─" * max(2, padding_x)
        elif "->>" in route:
            left, right = route.split("->>", 1)
            arrow = "-->" if use_ascii else "─" * max(2, padding_x) + "►"
        else:
            parsed = _parse_edge(route.replace("->", " --> "))
            if not parsed:
                rows.append(clean)
                continue
            left, right, _ = parsed
            arrow = ch["arrow"]
        rows.append(f"{left.strip()} {arrow} {right.strip()}" + (f" : {message.strip()}" if message.strip() else ""))
    return _frame("Mermaid Sequence", rows, width, use_ascii=use_ascii)


def _render_edge_box(title: str, body: list[str], width: int, *, use_ascii: bool) -> str:
    lines: list[str] = []
    for line in body:
        clean = line.strip().rstrip(";")
        if not clean or clean.startswith(("[*]", "classDef", "style ")):
            if clean:
                lines.append(clean)
            continue
        parsed = _parse_edge(clean.replace(":", " : "))
        if parsed:
            src, dst, label = parsed
            lines.append(f"{_clean_label(src)} -> {_clean_label(dst)}" + (f" : {label}" if label else ""))
        else:
            lines.append(clean)
    return _frame(title, lines, width, use_ascii=use_ascii)


def _render_class(body: list[str], width: int, *, use_ascii: bool) -> str:
    classes: dict[str, list[str]] = {}
    edges: list[str] = []
    for line in body:
        clean = line.strip()
        if not clean:
            continue
        if "<|--" in clean:
            left, right = [part.strip() for part in clean.split("<|--", 1)]
            edges.append(f"{left} <|-- {right}")
            continue
        if ":" in clean:
            name, member = [part.strip() for part in clean.split(":", 1)]
            classes.setdefault(name, []).append(member)
            continue
        classes.setdefault(clean, [])
    lines = edges[:]
    for name, members in classes.items():
        lines.append("")
        lines.extend(_box(name, use_ascii=use_ascii, width=max(12, display_width(name) + 4)))
        lines.extend("  " + member for member in members)
    return _frame("Mermaid Class", lines, width, use_ascii=use_ascii)


def _render_xychart(lines: list[str], width: int, *, use_ascii: bool) -> str:
    labels: list[str] = []
    series: list[tuple[str, str, list[float]]] = []
    title = "Mermaid XY Chart"
    horizontal = False
    for line in lines:
        clean = line.strip()
        if clean.startswith("xychart-beta") and "horizontal" in clean:
            horizontal = True
        if clean.startswith("title "):
            title = clean.removeprefix("title ").strip().strip('"')
        elif clean.startswith("x-axis") and "[" in clean and "]" in clean:
            labels = [item.strip() for item in clean.split("[", 1)[1].split("]", 1)[0].split(",")]
        elif clean.startswith(("bar ", "line ")) and "[" in clean and "]" in clean:
            kind, rest = clean.split(maxsplit=1)
            name = kind
            before_bracket = rest.split("[", 1)[0].strip().strip('"')
            if before_bracket:
                name = before_bracket
            vals = [float(item.strip()) for item in clean.split("[", 1)[1].split("]", 1)[0].split(",") if item.strip()]
            series.append((kind, name, vals))
    if not series:
        return _frame(title, ["xychart-beta needs bar [...] or line [...]"], width, use_ascii=use_ascii)
    return _render_xy_horizontal(title, labels, series, width, use_ascii=use_ascii) if horizontal else _render_xy_vertical(title, labels, series, width, use_ascii=use_ascii)


def _render_xy_vertical(title: str, labels: list[str], series: list[tuple[str, str, list[float]]], width: int, *, use_ascii: bool) -> str:
    count = max(len(values) for _kind, _name, values in series)
    labels = labels or [str(i + 1) for i in range(count)]
    chart_height = 8
    cell_w = max(3, min(6, (max(24, width - 14)) // max(1, count)))
    max_val = max((max(values) for _kind, _name, values in series if values), default=1.0) or 1.0
    bar_series = next((values for kind, _name, values in series if kind == "bar"), [])
    line_series = [(name, values) for kind, name, values in series if kind == "line"]
    rows: list[str] = []
    for level in range(chart_height, 0, -1):
        row_cells: list[str] = []
        for idx in range(count):
            cell = _bar_cell(bar_series[idx] if idx < len(bar_series) else 0.0, level, chart_height, max_val, cell_w, use_ascii=use_ascii)
            row_cells.append(cell)
        rows.append(" ".join(row_cells).rstrip())
    if line_series:
        rows = _overlay_xy_lines(rows, line_series, count, cell_w, chart_height, max_val, use_ascii=use_ascii)
    rows.append(" ".join(center_text(labels[idx] if idx < len(labels) else str(idx + 1), cell_w) for idx in range(count)).rstrip())
    rows.extend(_xy_legend(series, use_ascii=use_ascii))
    return _frame(title, rows, width, use_ascii=use_ascii)


def _render_xy_horizontal(title: str, labels: list[str], series: list[tuple[str, str, list[float]]], width: int, *, use_ascii: bool) -> str:
    count = max(len(values) for _kind, _name, values in series)
    labels = labels or [str(i + 1) for i in range(count)]
    max_val = max((max(values) for _kind, _name, values in series if values), default=1.0) or 1.0
    bar_series = next((values for kind, _name, values in series if kind == "bar"), [])
    line_series = [(name, values) for kind, name, values in series if kind == "line"]
    bar_w = max(16, min(34, width - 26))
    rows: list[str] = []
    for idx in range(count):
        label = labels[idx] if idx < len(labels) else str(idx + 1)
        value = bar_series[idx] if idx < len(bar_series) else 0.0
        bar = _rounded_horizontal_bar(value, max_val, bar_w, use_ascii=use_ascii)
        overlay = list(bar)
        for _name, values in line_series:
            if idx < len(values):
                pos = min(bar_w - 1, max(0, int(round(values[idx] / max_val * (bar_w - 1)))))
                overlay[pos] = "x" if use_ascii else "●"
        rows.append(f"{pad_right(label, 10)} {''.join(overlay)} {value:g}")
    rows.extend(_xy_legend(series, use_ascii=use_ascii))
    return _frame(title, rows, width, use_ascii=use_ascii)


def _bar_cell(value: float, level: int, height: int, max_val: float, cell_w: int, *, use_ascii: bool) -> str:
    bar_h = int(round(value / max_val * height)) if max_val else 0
    if bar_h < level:
        return " " * cell_w
    if use_ascii:
        return "#" * cell_w
    if level == bar_h:
        return center_text("╭" + "─" * max(1, cell_w - 2) + "╮", cell_w)
    if level == 1:
        return center_text("╰" + "─" * max(1, cell_w - 2) + "╯", cell_w)
    return "█" * cell_w


def _rounded_horizontal_bar(value: float, max_val: float, width: int, *, use_ascii: bool) -> str:
    fill = int(round(value / (max_val or 1.0) * width))
    fill = max(0, min(width, fill))
    if use_ascii:
        return "#" * fill + " " * (width - fill)
    if fill <= 0:
        return " " * width
    if fill == 1:
        return "●" + " " * (width - 1)
    return "╭" + "─" * max(0, fill - 2) + "╮" + " " * (width - fill)


def _line_glyph(values: list[float], idx: int, *, use_ascii: bool) -> str:
    if use_ascii:
        return "*"
    prev_v = values[idx - 1] if idx > 0 else values[idx]
    cur_v = values[idx]
    next_v = values[idx + 1] if idx + 1 < len(values) else values[idx]
    if prev_v < cur_v > next_v:
        return "╮"
    if prev_v > cur_v < next_v:
        return "╰"
    if prev_v < cur_v <= next_v:
        return "╭"
    if prev_v >= cur_v > next_v:
        return "╯"
    return "●"


def _overlay_xy_lines(
    rows: list[str],
    line_series: list[tuple[str, list[float]]],
    count: int,
    cell_w: int,
    chart_height: int,
    max_val: float,
    *,
    use_ascii: bool,
) -> list[str]:
    plot_w = count * cell_w + max(0, count - 1)
    grid = [list(pad_right(row, plot_w)) for row in rows]
    for _name, values in line_series:
        points = []
        for idx in range(min(count, len(values))):
            level = max(1, int(round(values[idx] / (max_val or 1.0) * chart_height)))
            level = min(chart_height, level)
            x = idx * (cell_w + 1) + cell_w // 2
            y = chart_height - level
            points.append((x, y, idx))
        for left, right in zip(points, points[1:], strict=False):
            x0, y0, _idx0 = left
            x1, y1, _idx1 = right
            span = max(1, x1 - x0)
            for x in range(x0 + 1, x1):
                t = (x - x0) / span
                y = round(y0 + (y1 - y0) * t)
                glyph = "-" if use_ascii else "─" if y0 == y1 else "╲" if y1 > y0 else "╱"
                if 0 <= y < len(grid) and 0 <= x < len(grid[y]):
                    grid[y][x] = glyph
        for x, y, idx in points:
            if 0 <= y < len(grid) and 0 <= x < len(grid[y]):
                grid[y][x] = _line_glyph(values, idx, use_ascii=use_ascii)
    return ["".join(row).rstrip() for row in grid]


def _xy_legend(series: list[tuple[str, str, list[float]]], *, use_ascii: bool) -> list[str]:
    if len(series) <= 1:
        return []
    parts = []
    for kind, name, _values in series:
        marker = "#" if use_ascii and kind == "bar" else "*" if use_ascii else "█" if kind == "bar" else "╭"
        parts.append(f"{marker} {name}")
    return ["legend  " + "   ".join(parts)]
