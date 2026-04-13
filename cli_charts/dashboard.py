#!/usr/bin/env python3
"""dashboard.py -- Textual TUI dashboard with Rich static fallback.

Panel types: gauge | sparkline | table | metric | bar
Layout: auto-grid (<=4 -> 2col, >4 -> 3col) or manual via panel["row"]

Usage:
  python dashboard.py --demo
  python dashboard.py --demo --no-interactive
  python dashboard.py --json '{"panels":[...]}'
  python dashboard.py --file config.json
  cat config.json | python dashboard.py
"""
import argparse
import json
import sys
from typing import Any


DEMO_CONFIG = {
    "title": "System Monitor",
    "panels": [
        {"id": "cpu", "title": "CPU Usage", "type": "gauge",
         "data": {"value": 73, "total": 100, "label": "CPU"}},
        {"id": "mem", "title": "Memory", "type": "gauge",
         "data": {"value": 5.4, "total": 16, "label": "RAM (GB)"}},
        {"id": "req", "title": "Requests/s", "type": "sparkline",
         "data": {"values": [120, 145, 132, 178, 201, 189, 220, 198, 215, 240],
                  "label": "rps"}},
        {"id": "lat", "title": "P99 Latency", "type": "metric",
         "data": {"value": 142, "unit": "ms", "label": "P99 Latency",
                  "delta": "-8.3%"}},
        {"id": "err", "title": "Error Rate by Service", "type": "bar",
         "data": {"labels": ["api-gw", "auth", "db", "cache", "worker"],
                  "values": [2, 0, 5, 1, 3]}},
        {"id": "svc", "title": "Service Status", "type": "table",
         "data": {"headers": ["Service", "Status", "Uptime"],
                  "rows": [
                      ["api-gw", "OK", "99.9%"],
                      ["auth", "OK", "100%"],
                      ["db-01", "WARN", "97.2%"],
                      ["cache", "OK", "99.8%"],
                      ["worker", "FAIL", "81.0%"],
                  ]}},
    ],
}


# ---------------------------------------------------------------------------
# Rich markup renderers (shared by TUI and static mode)
# ---------------------------------------------------------------------------

_STATUS_COLORS = {"OK": "green", "WARN": "yellow", "FAIL": "red"}


def render_gauge(data: dict | list) -> str:
    metrics = data if isinstance(data, list) else [data]
    lines = []
    bar_w = 24
    for m in metrics:
        val = float(m.get("value", 0))
        total = float(m.get("total", m.get("max", 100)) or 100)
        pct = max(0.0, min(1.0, val / total)) if total else 0.0
        filled = round(pct * bar_w)
        color = "green" if pct < 0.7 else ("yellow" if pct < 0.9 else "red")
        bar = f"[{color}]{'█' * filled}{'░' * (bar_w - filled)}[/{color}]"
        label = m.get("label", "")
        lines.append(f"{label:<12} {bar} [bold]{val:.1f}[/bold]/{total:.0f}")
    return "\n".join(lines)


def render_sparkline(data: dict) -> str:
    vals = data.get("values", [])
    label = data.get("label", "")
    try:
        import sparklines as sl
        spark = " ".join(sl.sparklines(vals))
    except ImportError:
        if not vals:
            return "(no data)"
        mx = max(vals) or 1
        blocks = "\u2581\u2582\u2583\u2584\u2585\u2586\u2587\u2588"
        spark = "".join(blocks[min(7, int(v / mx * 7))] for v in vals)
    return f"{label + ':' if label else ''} {spark}".strip()


def render_table(data: dict) -> str:
    headers = data.get("headers", data.get("columns", []))
    rows = data.get("rows", [])
    if not headers:
        return "(empty table)"
    col_w = max(10, 40 // max(len(headers), 1))
    header_line = " | ".join(f"{h:<{col_w}}" for h in headers)
    sep = "-+-".join("-" * col_w for _ in headers)
    lines = [f"[bold]{header_line}[/bold]", sep]
    for row in rows:
        cells = []
        for cell in row:
            s = str(cell)
            color = _STATUS_COLORS.get(s)
            cells.append(
                f"[{color}]{s:<{col_w}}[/{color}]" if color else f"{s:<{col_w}}"
            )
        lines.append(" | ".join(cells))
    return "\n".join(lines)


def render_metric(data: dict) -> str:
    val = data.get("value", 0)
    unit = data.get("unit", "")
    label = data.get("label", "")
    delta = str(data.get("delta", ""))
    # + delta is bad for latency/errors; - is good
    d_color = "red" if delta.startswith("+") else "green"
    lines = [f"[bold yellow]{val}[/bold yellow][dim]{unit}[/dim]"]
    if delta:
        lines.append(f"[{d_color}]{delta}[/{d_color}]")
    if label:
        lines.append(f"[dim]{label}[/dim]")
    return "\n".join(lines)


def render_bar(data: dict) -> str:
    labels = data.get("labels", [])
    values = data.get("values", [])
    if not labels:
        return "(no data)"
    mx = max(values) if values else 1
    bar_w = 20
    lines = []
    for label, val in zip(labels, values):
        filled = round(val / mx * bar_w) if mx else 0
        color = "green" if val == 0 else ("yellow" if val < mx * 0.5 else "red")
        bar = f"[{color}]{'█' * filled}{'░' * (bar_w - filled)}[/{color}]"
        lines.append(f"{label:<10} {bar} [bold]{val}[/bold]")
    return "\n".join(lines)


PANEL_RENDERERS = {
    "gauge": render_gauge,
    "sparkline": render_sparkline,
    "table": render_table,
    "metric": render_metric,
    "bar": render_bar,
}


def render_panel(spec: dict) -> str:
    renderer = PANEL_RENDERERS.get(spec.get("type", ""))
    if renderer is None:
        return f"[red]Unknown panel type: {spec.get('type')}[/red]"
    try:
        return renderer(spec.get("data", {}))
    except Exception as exc:
        return f"[red]Error: {exc}[/red]"


# ---------------------------------------------------------------------------
# Layout helper
# ---------------------------------------------------------------------------

def build_layout(panels: list) -> list:
    """Group panels into rows.
    Respects panel["row"] for manual placement; otherwise auto-grid.
    <=4 panels -> 2 columns. >4 panels -> 3 columns.
    """
    if any("row" in p for p in panels):
        from collections import defaultdict
        rows_map: dict = defaultdict(list)
        auto_row = max((p.get("row", 0) for p in panels), default=0) + 1
        for p in panels:
            if "row" in p:
                rows_map[p["row"]].append(p)
            else:
                rows_map[auto_row].append(p)
                auto_row += 1
        return [rows_map[k] for k in sorted(rows_map)]
    cols = 2 if len(panels) <= 4 else 3
    return [panels[i: i + cols] for i in range(0, len(panels), cols)]


# ---------------------------------------------------------------------------
# Static output (Rich Columns -- pipe-safe, no Textual required)
# ---------------------------------------------------------------------------

def render_static(config: dict) -> None:
    from rich.console import Console
    from rich.columns import Columns
    from rich.panel import Panel as RichPanel
    from rich.rule import Rule
    from rich import box as richbox

    c = Console()
    title = config.get("title", "")
    if title:
        c.print(Rule(f"[bold]{title}[/bold]"))

    for row in build_layout(config.get("panels", [])):
        rich_panels = [
            RichPanel(render_panel(spec), title=spec.get("title", ""),
                      box=richbox.ROUNDED, expand=True)
            for spec in row
        ]
        c.print(Columns(rich_panels, equal=True, expand=True))


# ---------------------------------------------------------------------------
# Textual TUI
# ---------------------------------------------------------------------------

def run_tui(config: dict) -> None:
    from textual.app import App, ComposeResult
    from textual.widgets import Static, Header, Footer
    from textual.containers import Horizontal, ScrollableContainer

    title = config.get("title", "Dashboard")
    rows = build_layout(config.get("panels", []))
    refresh_interval = config.get("refresh_interval", None)

    class PanelWidget(Static):
        def __init__(self, spec: dict, **kwargs: Any) -> None:
            super().__init__(**kwargs)
            self._spec = spec

        def on_mount(self) -> None:
            self.update(render_panel(self._spec))

        def refresh_content(self) -> None:
            self.update(render_panel(self._spec))

    class DashboardApp(App):  # type: ignore[type-arg]
        CSS = """
        .row  { height: auto; margin-bottom: 1; }
        .panel { border: solid $accent; padding: 0 1; min-height: 6; width: 1fr; }
        """
        BINDINGS = [("q", "quit", "Quit"), ("r", "refresh", "Refresh")]
        TITLE = title

        def compose(self) -> ComposeResult:
            yield Header()
            with ScrollableContainer():
                for row_panels in rows:
                    with Horizontal(classes="row"):
                        for spec in row_panels:
                            yield PanelWidget(
                                spec, classes="panel",
                                id=f"panel-{spec.get('id', str(id(spec)))}"
                            )
            yield Footer()

        def action_refresh(self) -> None:
            for w in self.query(PanelWidget):
                w.refresh_content()

        def on_mount(self) -> None:
            if refresh_interval:
                self.set_interval(float(refresh_interval), self.action_refresh)

    DashboardApp().run()


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------

def main() -> None:
    parser = argparse.ArgumentParser(
        description="cli-charts dashboard: Textual TUI or Rich static output",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Panel types: gauge | sparkline | table | metric | bar

JSON config format:
  {"title": "My Dashboard", "panels": [
    {"id": "cpu", "type": "gauge", "title": "CPU",
     "data": {"value": 73, "total": 100, "label": "CPU"}},
    {"id": "rps", "type": "sparkline", "title": "Requests",
     "data": {"values": [1, 3, 5, 2, 8], "label": "rps"}}
  ]}

Examples:
  python dashboard.py --demo
  python dashboard.py --demo --no-interactive
  python dashboard.py --file metrics.json
  cat metrics.json | python dashboard.py --no-interactive
""",
    )
    src = parser.add_mutually_exclusive_group()
    src.add_argument("--json", dest="data", metavar="JSON",
                     help="Dashboard config as JSON string")
    src.add_argument("--file", metavar="PATH", help="Read config from JSON file")
    src.add_argument("--demo", action="store_true",
                     help="Built-in 6-panel system monitor demo")
    parser.add_argument("--no-interactive", action="store_true",
                        help="Rich static output (pipe-safe, no Textual required)")
    parser.add_argument("--check-deps", action="store_true",
                        help="Check required dependencies and exit")
    args = parser.parse_args()

    if args.check_deps:
        pkgs = [("rich", "rich"), ("textual", "textual")]
        all_ok = True
        for name, pip_name in pkgs:
            try:
                __import__(name)
                print(f"OK: {name}")
            except ImportError:
                print(f"MISSING: {pip_name} -> pip install {pip_name}")
                all_ok = False
        sys.exit(0 if all_ok else 2)

    if args.demo:
        config = DEMO_CONFIG
    elif args.file:
        with open(args.file) as f:
            config = json.load(f)
    elif args.data:
        try:
            config = json.loads(args.data)
        except json.JSONDecodeError as exc:
            print(f"ERROR:json: {exc}", file=sys.stderr)
            sys.exit(1)
    else:
        raw = sys.stdin.read().strip()
        if not raw:
            parser.print_help()
            sys.exit(1)
        try:
            config = json.loads(raw)
        except json.JSONDecodeError as exc:
            print(f"ERROR:json: {exc}", file=sys.stderr)
            sys.exit(1)

    if args.no_interactive or not sys.stdout.isatty():
        render_static(config)
    else:
        try:
            run_tui(config)
        except ImportError:
            print("textual not installed -- falling back to static output. "
                  "pip install textual", file=sys.stderr)
            render_static(config)


if __name__ == "__main__":
    main()
