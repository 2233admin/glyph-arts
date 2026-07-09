"""incplot chart -- extracted from cli_charts.cmd._helpers (Phase 3b)."""

from cli_charts.registry import CMDS, register

@register("incplot")

def incplot(d, title, w, h, theme, **kw):
    """incplot-style auto renderer for JSON, JSONL, CSV, and TSV."""
    from cli_charts.render.incplot_engine import detect_incplot

    detected = detect_incplot(d, kw.get('prefer', ''))
    nested_kw = dict(kw)
    nested_kw.pop('prefer', None)
    return CMDS[detected.chart_type](detected.data, title, w, h, theme, **nested_kw)
