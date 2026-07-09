"""art_command chart -- extracted from cli_charts.cmd._helpers (Phase 3b)."""

import sys

from cli_charts.registry import register

@register("art_command")

def art_command(d, title, w, h, theme, **kw):
    """Composable text art command (argparse dispatch only)."""
    del d, title
    from cli_charts.render.art_engine import list_decors, list_fonts, render_art
    if kw.get('list_fonts'):
        list_fonts()
        sys.exit(0)
    if kw.get('list_decors'):
        list_decors()
        sys.exit(0)
    rc = render_art(
        kw.get('text', ''),
        kw.get('font', 'slant'),
        kw.get('decor'),
        kw.get('frame'),
        kw.get('gradient'),
        theme,
        w,
        h,
        kw.get('no_color', False),
        kw.get('output', ''),
        kw.get('justify'),
        kw.get('anim', False),
    )
    sys.exit(rc)
