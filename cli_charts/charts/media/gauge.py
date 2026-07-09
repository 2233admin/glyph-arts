"""gauge chart -- extracted from cli_charts.cmd._helpers (Phase 3b)."""

from cli_charts.charts._utils import _render_statusline, _style_to_gauge, _symbol_tier
from cli_charts.registry import register
from cli_charts.symbols import BLOCK, BRAILLE_ALL, get_symbol

@register("gauge")

def gauge(d, title, w, h, theme, **kw):
    """rich multi-metric progress bars (static gauge).
    Auto-colors: green <70%, yellow <90%, red >=90%.
    """
    if kw.get('statusline'):
        _render_statusline('gauge', d, title)
        return
    if kw.get('rich_progress'):
        from rich.console import Console
        from rich.progress import (
            BarColumn,
            MofNCompleteColumn,
            Progress,
            TaskProgressColumn,
            TextColumn,
            TimeRemainingColumn,
        )
        no_color = kw.get('no_color', False)
        console = Console(no_color=no_color, force_terminal=not no_color, legacy_windows=False)
        metrics = d if isinstance(d, list) else d.get('metrics', [d])
        progress = Progress(
            TextColumn("[bold]{task.description}"),
            BarColumn(),
            TaskProgressColumn(),
            MofNCompleteColumn(),
            TimeRemainingColumn(),
            console=console,
        )
        with progress:
            for m in metrics:
                val = float(m['value'])
                mx = float(m.get('max', 100))
                progress.add_task(str(m.get('label', '')), total=mx, completed=val)
        return
    from rich import box as richbox
    from rich.console import Console
    from rich.table import Table
    no_color = kw.get('no_color', False)
    c = Console(no_color=no_color)
    metrics = d if isinstance(d, list) else d.get('metrics', [d])
    t = Table(title=title, box=richbox.SIMPLE, show_header=False, padding=(0, 1))
    t.add_column('Label', style='bold', min_width=12)
    t.add_column('Bar', min_width=32)
    t.add_column('Value', justify='right', min_width=10)
    style = _style_to_gauge(kw.get('gauge_style') or kw.get('visual_style') or 'bar')
    if style == 'bar':
        full, empty = BLOCK['eighth_low_8'], BLOCK['shade_light']
    elif style == 'ascii':
        full, empty = '#', '-'
    elif style == 'block':
        full, empty = BLOCK['eighth_low_8'], ' '
    elif style == 'shade':
        full, empty = BLOCK['eighth_low_8'], BLOCK['shade_light']
    elif style == 'half-circle':
        tier = _symbol_tier(kw)
        full = get_symbol('half_circle_left', tier=tier)
        empty = get_symbol('half_circle_right', tier=tier)
    elif style == 'full-circle':
        full, empty = get_symbol('circle', tier=_symbol_tier(kw)), ' '
    elif style == 'braille':
        full, empty = BRAILLE_ALL[255], BRAILLE_ALL[0]
    else:
        raise ValueError(f"unknown gauge style: {style!r}")
    for m in metrics:
        val = float(m['value'])
        mx  = float(m.get('max', 100))
        pct = max(0.0, min(1.0, val / mx)) if mx != 0 else 0.0
        bar_w = 30
        filled = round(pct * bar_w)
        auto_color = 'green' if pct < 0.7 else ('yellow' if pct < 0.9 else 'red')
        color = m.get('color', auto_color)
        bar = f'[{color}]{full * filled}{empty * (bar_w - filled)}[/{color}]'
        t.add_row(m.get('label', ''), bar, f'{val:.1f} / {mx:.0f}')
    c.print(t)
