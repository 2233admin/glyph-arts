"""rich_live chart -- extracted from cli_charts.cmd._helpers (Phase 3a)."""

from cli_charts.registry import register

@register("rich_live")

def rich_live(d, title, w, h, theme, **kw):
    """Compose multiple charts into a Rich Live/Layout panel grid.

    Schema:
        {"panels": [{"type":"bar","title":"Left","data":{...}}, ...],
         "layout": "row" | "column",
         "frames": 1}

    frames=1: static single-frame snapshot via Console.print(layout) -- pipe/TTY safe.
    frames>1: animated refresh via Rich Live (needs a TTY); falls back to static when piped.
    Each panel's child chart renders via the same CMDS dispatcher, with stdout captured
    and replayed inside a Rich Panel so ANSI colors from plotext/hires/etc. survive.
    """
    from io import StringIO
    import sys

    from rich import box as richbox
    from rich.console import Console
    from rich.layout import Layout
    from rich.panel import Panel
    from rich.text import Text

    from cli_charts.registry import CMDS

    panels_spec = d.get('panels') or []
    if not panels_spec:
        print('ERROR:schema: rich_live requires non-empty "panels" list', file=sys.stderr)
        sys.exit(1)

    orientation = d.get('layout', 'row')
    if orientation not in ('row', 'column'):
        print(f'ERROR:schema: layout must be "row" or "column", got {orientation!r}', file=sys.stderr)
        sys.exit(1)

    frames = max(1, int(d.get('frames', 1)))
    no_color = kw.get('no_color', False)
    panel_failures = []

    def _render_panel_content(panel_spec):
        """Dispatch sub-chart and capture its stdout as a Rich-renderable Text."""
        name = panel_spec.get('title') or panel_spec.get('name') or panel_spec.get('id') or panel_spec.get('type')
        ptype = panel_spec.get('type')
        if ptype not in CMDS:
            panel_failures.append((name, -1))
            return Text(f'[unknown panel type: {ptype!r}]', style='red')
        if ptype in ('dashboard', 'rich_live'):
            panel_failures.append((name, -1))
            return Text(f'[cannot nest {ptype!r} inside rich_live]', style='red')
        pdata = panel_spec.get('data', {})
        ptitle = panel_spec.get('title', '')
        pw = panel_spec.get('width', max(20, w // max(1, len(panels_spec)) if orientation == 'row' else w))
        ph = panel_spec.get('height', max(8, h // max(1, len(panels_spec)) if orientation == 'column' else h))
        buf = StringIO()
        saved_stdout = sys.stdout
        sys.stdout = buf
        try:
            try:
                CMDS[ptype](pdata, ptitle, pw, ph, theme, no_color=no_color)
            except (SystemExit, KeyboardInterrupt):
                raise
            except Exception as e:
                panel_failures.append((name, -1))
                return Text(f'[panel render failed: {type(e).__name__}: {e}]', style='red')
        finally:
            sys.stdout = saved_stdout
        captured = buf.getvalue().rstrip('\n')
        return Text.from_ansi(captured) if captured else Text('(empty)', style='dim')

    def _build_layout():
        lay = Layout()
        sub_layouts = []
        for idx, spec in enumerate(panels_spec):
            child = Layout(name=f'p{idx}')
            child.update(Panel(
                _render_panel_content(spec),
                title=spec.get('title') or None,
                box=richbox.ROUNDED,
            ))
            sub_layouts.append(child)
        if orientation == 'row':
            lay.split_row(*sub_layouts)
        else:
            lay.split_column(*sub_layouts)
        return lay

    console = Console(no_color=no_color, width=w if w else None)
    layout = _build_layout()

    if frames == 1 or not sys.stdout.isatty():
        if title:
            console.rule(title)
        console.print(layout)
        if panel_failures:
            print(f'ERROR:render: {len(panel_failures)} panel(s) failed: {panel_failures}',
                  file=sys.stderr)
            sys.exit(4)
        return

    import time

    from rich.live import Live
    refresh = float(d.get('refresh_per_second', 4))
    frame_delay = 1.0 / max(1.0, refresh)
    with Live(layout, refresh_per_second=refresh, console=console, transient=False):
        for _ in range(frames):
            layout = _build_layout()
            time.sleep(frame_delay)
    if panel_failures:
        print(f'ERROR:render: {len(panel_failures)} panel(s) failed: {panel_failures}',
              file=sys.stderr)
        sys.exit(4)
