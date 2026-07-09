"""pie chart -- extracted from cli_charts.cmd._helpers (Phase 3b)."""

from cli_charts.registry import register

@register("pie")

def pie(d, title, w, h, theme, **kw):
    """Rich percentage-bar pie breakdown. labels + values arrays of equal length."""
    from rich import box as rich_box
    from rich.console import Console
    from rich.table import Table
    total = sum(d['values']) or 1
    bar_w = 36
    colors = ['red', 'green', 'blue', 'yellow', 'magenta', 'cyan',
              'bright_red', 'bright_green', 'bright_blue']
    tbl = Table(title=title or None, box=rich_box.ROUNDED, show_lines=False)
    tbl.add_column('Label', style='bold')
    tbl.add_column('Pct', justify='right')
    tbl.add_column('Distribution', min_width=bar_w)
    tbl.add_column('Value', justify='right')
    for i, (label, val) in enumerate(zip(d['labels'], d['values'], strict=False)):
        pct = val / total * 100
        filled = round(pct / 100 * bar_w)
        color = colors[i % len(colors)]
        bar = f'[{color}]{"█" * filled}[/{color}]{"░" * (bar_w - filled)}'
        tbl.add_row(str(label), f'{pct:.1f}%', bar, str(val))
    Console().print(tbl)
