"""indicator chart -- extracted from cli_charts.cmd._helpers (Phase 2)."""

from cli_charts.charts._utils import _plt_finalize, _render_statusline


def indicator(d, title, w, h, theme, **kw):
    """plotext big-number KPI display."""
    if kw.get('statusline'):
        _render_statusline('indicator', d, title)
        return
    import plotext as plt
    plt.indicator(d['value'], d.get('label', title or ''))
    _plt_finalize(plt, None, w, h, theme, kw)  # title already baked into label
