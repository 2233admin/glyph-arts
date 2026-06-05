"""panel chart -- extracted from cli_charts.cmd._helpers (Phase 3a)."""


def panel(d, title, w, h, theme, **kw):
    """rich Panel -- bordered text / callout box."""
    from rich import box as richbox
    from rich.console import Console
    from rich.panel import Panel as RichPanel
    no_color = kw.get('no_color', False)
    c = Console(no_color=no_color)
    box_style = getattr(richbox, d.get('box', 'ROUNDED'), richbox.ROUNDED)
    p = RichPanel(d['content'],
                  title=d.get('title', title or None),
                  subtitle=d.get('subtitle'),
                  box=box_style)
    c.print(p)
