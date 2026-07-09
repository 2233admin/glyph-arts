"""turtle chart -- extracted from cli_charts.cmd._helpers (Phase 3b)."""

from cli_charts.registry import register

@register("turtle")

def turtle(d, title, w, h, theme, **kw):
    """drawille-style Turtle/Canvas renderer backed by Braille cells."""
    del theme, kw
    from cli_charts.render.braille_engine import render_turtle

    print(render_turtle(d, title=title, width=w, height=h), end="")
