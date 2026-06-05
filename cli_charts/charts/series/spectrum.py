"""spectrum chart -- extracted from cli_charts.cmd._helpers (Phase 2)."""

from cli_charts.charts._utils import _render_statusline


def spectrum(d, title, w, h, theme, **kw):
    """SDR-style RF spectrum with center/band/peak overlays."""
    if kw.get('statusline'):
        _render_statusline('spectrum', d, title)
        return
    from cli_charts.render.sdr_engine import render_spectrum

    print(render_spectrum(d, title=title, width=w, height=h), end="")
