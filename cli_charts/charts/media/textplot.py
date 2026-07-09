"""textplot chart -- extracted from cli_charts.cmd._helpers (Phase 3b)."""

from cli_charts.registry import register

@register("textplot")

def textplot(d, title, w, h, theme, **kw):
    """textplots-rs-style continuous function plot on a Braille canvas."""
    del theme, kw
    from cli_charts.render.braille_engine import render_textplot

    print(render_textplot(d, title=title, width=w, height=h), end="")
