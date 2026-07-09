"""effect chart -- extracted from cli_charts.cmd._helpers (Phase 3b)."""

from cli_charts.registry import register

@register("effect")

def effect(d, title, w, h, theme, **kw):
    """Chat-first visual effect presets composed from the renderer toolbox."""
    del h, theme
    from cli_charts.render.effect_engine import render_effect

    if isinstance(d, dict):
        data = d
        kind = kw.get('effect_kind') or d.get('kind') or d.get('effect') or ''
    else:
        data = {'text': str(d)}
        kind = kw.get('effect_kind') or ''
    print(render_effect(str(kind), data, title=title, width=w), end="")
