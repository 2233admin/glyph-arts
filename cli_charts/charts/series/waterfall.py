"""waterfall chart -- extracted from cli_charts.cmd._helpers (Phase 2)."""

from cli_charts.charts._utils import _render_statusline


def waterfall(d, title, w, h, theme, **kw):
    """SDR-style waterfall intensity map."""
    if kw.get('statusline'):
        _render_statusline('waterfall', d, title)
        return
    from cli_charts.render.sdr_engine import render_waterfall

    print(render_waterfall(d, title=title, width=w, height=h), end="")
