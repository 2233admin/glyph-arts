"""banner chart -- extracted from cli_charts.cmd._helpers (Phase 3b)."""

from cli_charts.registry import register

@register("banner")

def banner(d, title, w, h, theme, **kw):
    """pyfiglet large ASCII art text banner."""
    import pyfiglet
    text = d.get('text', title or 'BANNER')
    font = d.get('font', 'big')
    result = pyfiglet.figlet_format(text, font=font, width=d.get('width', w))
    color = d.get('color')
    if color and not kw.get('no_color'):
        from rich.console import Console
        Console().print(f'[{color}]{result}[/{color}]', end='')
    else:
        print(result, end='')
