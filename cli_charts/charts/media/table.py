"""table chart -- extracted from cli_charts.cmd._helpers (Phase 3b)."""

from cli_charts.registry import register

@register("table")

def table(d, title, w, h, theme, **kw):
    """rich double-edge formatted table."""
    output = kw.get('output')
    if output and str(output).lower().endswith('.md'):
        from cli_charts.render.markdown_export import export_table
        export_table(d, output)
        return
    from rich import box as richbox
    from rich.console import Console
    from rich.table import Table
    no_color = kw.get('no_color', False)
    c = Console(no_color=no_color)
    box_style = getattr(richbox, d.get('box', 'DOUBLE_EDGE'), richbox.DOUBLE_EDGE)
    t = Table(title=title, box=box_style,
              caption=d.get('caption'),
              row_styles=d.get('row_styles'))
    for col in d.get('columns') or d.get('headers', []):
        if isinstance(col, dict):
            t.add_column(col['name'], style=col.get('style', 'white'),
                         footer=str(col.get('footer', '')))
        else:
            t.add_column(str(col))
    for row in d['rows']:
        t.add_row(*[str(v) for v in row])
    c.print(t)
