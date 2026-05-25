from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

from cli_charts.render.text_layout import center_text, display_width, pad_right, wrap_display

EFFECT_KINDS = [
    "gallery",
    "pipeline",
    "metrics",
    "system-map",
    "signal-panel",
    "timeline",
    "matrix",
    "comparison",
    "swimlane",
    "kanban",
    "quadrant",
    "mindmap",
]

_RAMP = " .:-=+*#%@"
_SPARK = "▁▂▃▄▅▆▇█"


def _width(width: int | None, *, minimum: int = 44, maximum: int = 100) -> int:
    if width is None:
        return 72
    return max(minimum, min(maximum, int(width)))


def _string(value: object) -> str:
    return "" if value is None else str(value)


def _wrap(text: object, width: int) -> list[str]:
    value = _string(text).rstrip()
    if not value.strip():
        return [""]
    if display_width(value) <= width:
        return [value]
    return wrap_display(value, width)


def _box(title: str, lines: Sequence[str], width: int) -> str:
    inner = max(12, width - 4)
    title_text = f" {title.strip()} " if title else ""
    if title_text:
        title_width = max(0, inner - display_width(title_text))
        top = "┌" + title_text + "─" * title_width + "┐"
    else:
        top = "┌" + "─" * inner + "┐"
    body: list[str] = []
    for line in lines:
        for part in _wrap(line, inner - 2):
            body.append("│ " + pad_right(part, inner - 2) + " │")
    return "\n".join([top, *body, "└" + "─" * inner + "┘"])


def _label_bar(label: str, value: float, maximum: float = 100.0, width: int = 18) -> str:
    maximum = maximum or 1.0
    ratio = max(0.0, min(1.0, value / maximum))
    filled = int(round(ratio * width))
    bar = "█" * filled + "░" * (width - filled)
    return f"{pad_right(label, 10)} {bar} {value:>5.1f}"


def _sparkline(values: Iterable[float], width: int = 24) -> str:
    vals = [float(v) for v in values]
    if not vals:
        return ""
    if len(vals) > width:
        step = len(vals) / width
        vals = [vals[int(i * step)] for i in range(width)]
    lo = min(vals)
    hi = max(vals)
    span = hi - lo or 1.0
    return "".join(_SPARK[min(len(_SPARK) - 1, max(0, int((v - lo) / span * (len(_SPARK) - 1))))] for v in vals)


def _heat(matrix: Sequence[Sequence[float]], width: int) -> list[str]:
    rows = [[float(v) for v in row] for row in matrix if row]
    if not rows:
        return []
    flat = [v for row in rows for v in row]
    lo = min(flat)
    hi = max(flat)
    span = hi - lo or 1.0
    max_cols = max(8, min(width, max(len(row) for row in rows)))
    out: list[str] = []
    for row in rows:
        if len(row) > max_cols:
            step = len(row) / max_cols
            row = [row[int(i * step)] for i in range(max_cols)]
        out.append("".join(_RAMP[min(len(_RAMP) - 1, max(0, int((v - lo) / span * (len(_RAMP) - 1))))] for v in row))
    return out


def _sample_values(n: int, *, phase: float = 0.0) -> list[float]:
    return [50 + 28 * math.sin((i + phase) / 2.2) + 12 * math.sin((i + phase) / 0.9) for i in range(n)]


def _render_pipeline(data: dict, width: int) -> str:
    steps = data.get("steps") or ["Capture", "Route", "Render", "Verify", "Reply"]
    steps = [_string(step) for step in steps]
    box_width = max(12, min(width - 12, max(len(step) for step in steps) + 6, 26))
    pad = " " * max(0, (width - 6 - box_width) // 2)
    lines: list[str] = []
    for idx, step in enumerate(steps):
        lines.append(pad + "┌" + "─" * box_width + "┐")
        lines.append(pad + "│ " + step.center(box_width - 2) + " │")
        lines.append(pad + "└" + "─" * box_width + "┘")
        if idx < len(steps) - 1:
            lines.append(pad + " " * (box_width // 2) + "│")
            lines.append(pad + " " * (box_width // 2) + "▼")
    return _box(_string(data.get("title") or "Pipeline Effect"), lines, width)


def _render_metrics(data: dict, width: int) -> str:
    metrics = data.get("metrics") or [
        {"label": "Render", "value": 92},
        {"label": "Verify", "value": 100},
        {"label": "Width", "value": 74},
    ]
    values = data.get("values") or _sample_values(28)
    lines = [_label_bar(_string(item.get("label")), float(item.get("value", 0))) for item in metrics]
    lines.append("")
    lines.append("trend     " + _sparkline(values, width=28))
    return _box(_string(data.get("title") or "Metrics Card"), lines, width)


def _render_system_map(data: dict, width: int) -> str:
    nodes = data.get("nodes") or ["User", "Agent", "glyph-arts", "Verifier", "Chat"]
    edges = data.get("edges") or [
        ["User", "Agent"],
        ["Agent", "glyph-arts"],
        ["glyph-arts", "Verifier"],
        ["Verifier", "Chat"],
    ]
    node_line = "   ".join(f"({node})" for node in nodes[:4])
    lines = [node_line[: max(12, width - 8)]]
    for left, right, *rest in edges:
        label = f" {rest[0]} " if rest else " "
        lines.append(f"{left} ─{label}→ {right}")
    return _box(_string(data.get("title") or "System Map"), lines, width)


def _render_signal_panel(data: dict, width: int) -> str:
    spectrum = data.get("spectrum") or _sample_values(42, phase=2.0)
    waterfall = data.get("waterfall") or [
        _sample_values(42, phase=phase) for phase in (0, 2, 4, 6, 8, 10)
    ]
    spectrum_line = _sparkline(spectrum, width=min(42, width - 22))
    heat_lines = _heat(waterfall, min(42, width - 22))
    lines = ["spectrum  " + spectrum_line, "waterfall"]
    lines.extend("  " + line for line in heat_lines)
    lines.append("range     -94..-42 dB")
    return _box(_string(data.get("title") or "Signal Panel"), lines, width)


def _render_timeline(data: dict, width: int) -> str:
    events = data.get("events") or [
        ["t-3", "input received"],
        ["t-2", "renderer selected"],
        ["t-1", "visual verified"],
        ["now", "reply in chat"],
    ]
    lines = []
    for idx, event in enumerate(events):
        when, label = event[0], event[1]
        connector = "└─" if idx == len(events) - 1 else "├─"
        lines.append(f"{connector} {when:<6} {label}")
        if idx < len(events) - 1:
            lines.append("│")
    return _box(_string(data.get("title") or "Timeline"), lines, width)


def _render_matrix(data: dict, width: int) -> str:
    matrix = data.get("matrix") or [
        [math.sin(x / 2 + y) * 40 + math.cos(x / 5) * 20 + 50 for x in range(44)]
        for y in range(10)
    ]
    lines = _heat(matrix, min(54, width - 8))
    lines.append("legend    " + _RAMP)
    return _box(_string(data.get("title") or "Density Matrix"), lines, width)


def _render_comparison(data: dict, width: int) -> str:
    labels = data.get("labels") or ["ascii", "diagram", "sdr", "image"]
    before = data.get("before") or [20, 35, 45, 30]
    after = data.get("after") or [68, 82, 74, 88]
    lines = []
    for label, left, right in zip(labels, before, after, strict=False):
        left_bar = "▒" * int(float(left) / 10)
        right_bar = "█" * int(float(right) / 10)
        lines.append(f"{label:<10} {left_bar:<10} → {right_bar:<10} {float(right):>5.1f}")
    return _box(_string(data.get("title") or "Before / After"), lines, width)


def _render_swimlane(data: dict, width: int) -> str:
    lanes = data.get("lanes") or ["User", "Agent", "Tool", "Chat"]
    events = data.get("events") or [
        ["User", "Agent", "ask"],
        ["Agent", "Tool", "render"],
        ["Tool", "Agent", "stdout"],
        ["Agent", "Chat", "reply"],
    ]
    lane_width = max(8, min(13, (width - 14) // max(1, len(lanes))))
    gap = 1
    base_width = len(lanes) * lane_width + (len(lanes) - 1) * gap
    centers = [idx * (lane_width + gap) + lane_width // 2 for idx in range(len(lanes))]
    header = " " * base_width
    header_chars = list(header)
    for idx, lane in enumerate(lanes):
        start = idx * (lane_width + gap)
        name = center_text(lane, lane_width)
        header_chars[start:start + lane_width] = list(name)
    header = "".join(header_chars)
    rails = "".join("│" if idx in centers else " " for idx in range(base_width))
    lines = [header, rails]
    lane_index = {_string(lane): idx for idx, lane in enumerate(lanes)}
    for src, dst, label in events:
        src_idx = lane_index.get(_string(src), 0)
        dst_idx = lane_index.get(_string(dst), min(1, len(lanes) - 1))
        row = [" "] * base_width
        src_pos = centers[src_idx]
        dst_pos = centers[dst_idx]
        row[src_pos] = "●"
        if src_pos < dst_pos:
            for pos in range(src_pos + 1, dst_pos):
                row[pos] = "─"
            row[dst_pos] = "▶"
        elif src_pos > dst_pos:
            for pos in range(dst_pos + 1, src_pos):
                row[pos] = "─"
            row[dst_pos] = "◀"
        lines.append("".join(row) + f"  {label}")
        lines.append(rails)
    return _box(_string(data.get("title") or "Swimlane"), lines, width)


def _render_kanban(data: dict, width: int) -> str:
    columns = data.get("columns") or {
        "TODO": ["shape effect", "add docs"],
        "DOING": ["verify output"],
        "DONE": ["chat route", "tests green"],
    }
    names = list(columns)
    col_width = max(10, min(18, (width - 10) // max(1, len(names))))
    max_rows = max(len(columns[name]) for name in names)
    lines = [" ".join(center_text(name, col_width) for name in names)]
    lines.append(" ".join("─" * col_width for _ in names))
    for row in range(max_rows):
        cells = []
        for name in names:
            tasks = columns[name]
            marker = "✓" if name.upper() == "DONE" else "◐" if name.upper() == "DOING" else "□"
            text = f"{marker} {tasks[row]}" if row < len(tasks) else ""
            cells.append(pad_right(text, col_width))
        lines.append(" ".join(cells))
    return _box(_string(data.get("title") or "Kanban"), lines, width)


def _render_quadrant(data: dict, width: int) -> str:
    labels = data.get("labels") or {
        "top_left": "quick wins",
        "top_right": "big bets",
        "bottom_left": "chores",
        "bottom_right": "traps",
    }
    cell = max(12, min(22, (width - 28) // 2))
    lines = [
        "impact ↑",
        "High   │ " + pad_right(labels.get("top_left"), cell) + "│ " + pad_right(labels.get("top_right"), cell),
        "       ├" + "─" * (cell + 1) + "┼" + "─" * (cell + 1),
        "Low    │ " + pad_right(labels.get("bottom_left"), cell) + "│ " + pad_right(labels.get("bottom_right"), cell),
        "       └" + "─" * (cell + 1) + "┴" + "─" * (cell + 1) + "→ effort",
    ]
    return _box(_string(data.get("title") or "Quadrant"), lines, width)


def _render_mindmap(data: dict, width: int) -> str:
    center = _string(data.get("center") or "Chat Drawing")
    branches = [_string(branch) for branch in data.get("branches", ["image ASCII", "diagrams", "SDR", "verifier"])]
    left = branches[1] if len(branches) > 1 else "diagrams"
    right = branches[2] if len(branches) > 2 else "SDR"
    top = branches[0] if branches else "image ASCII"
    bottom = branches[3] if len(branches) > 3 else "verifier"
    center_pad = max(0, (width - display_width(center) - 8) // 2)
    lines = [
        " " * center_pad + top,
        " " * (center_pad + max(0, len(center) // 2)) + "│",
        f"{left} ── {center} ── {right}",
        " " * (center_pad + max(0, len(center) // 2)) + "│",
        " " * center_pad + bottom,
    ]
    return _box(_string(data.get("title") or "Mindmap"), lines, width)


def _render_gallery(width: int) -> str:
    panels = [
        _render_pipeline({"steps": ["Ask", "Route", "Draw", "Verify"]}, width),
        _render_metrics({}, width),
        _render_signal_panel({}, width),
        _render_timeline({}, width),
        _render_matrix({}, width),
        _render_comparison({}, width),
        _render_swimlane({}, width),
        _render_kanban({}, width),
        _render_quadrant({}, width),
        _render_mindmap({}, width),
    ]
    header = _box("Effect Gallery", [
        "glyph-arts chat effects",
        "Presets: pipeline, metrics, system-map, signal-panel, timeline, matrix, comparison, swimlane, kanban, quadrant, mindmap",
    ], width)
    return "\n\n".join([header, *panels])


def render_effect(kind: str, data: dict | None = None, *, title: str = "", width: int = 72) -> str:
    data = dict(data or {})
    kind = (kind or data.get("kind") or data.get("effect") or "gallery").strip().lower()
    width = _width(width)
    if title and "title" not in data:
        data["title"] = title
    if kind == "gallery":
        return _render_gallery(width)
    if kind == "pipeline":
        return _render_pipeline(data, width)
    if kind == "metrics":
        return _render_metrics(data, width)
    if kind == "system-map":
        return _render_system_map(data, width)
    if kind == "signal-panel":
        return _render_signal_panel(data, width)
    if kind == "timeline":
        return _render_timeline(data, width)
    if kind == "matrix":
        return _render_matrix(data, width)
    if kind == "comparison":
        return _render_comparison(data, width)
    if kind == "swimlane":
        return _render_swimlane(data, width)
    if kind == "kanban":
        return _render_kanban(data, width)
    if kind == "quadrant":
        return _render_quadrant(data, width)
    if kind == "mindmap":
        return _render_mindmap(data, width)
    raise ValueError(f"unknown effect kind: {kind!r}; expected one of {', '.join(EFFECT_KINDS)}")
