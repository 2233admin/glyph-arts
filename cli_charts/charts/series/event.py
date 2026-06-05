"""event chart -- extracted from cli_charts.cmd._helpers (Phase 2)."""

from cli_charts.charts._utils import _plt_finalize


def event(d, title, w, h, theme, **kw):
    """plotext event / timeline plot.
    Orientation comes from --orientation CLI flag (kw) not JSON data.
    """
    import plotext as plt
    plt.event_plot(d['data'],
                   orientation=kw.get('orientation', 'vertical'))
    _plt_finalize(plt, title, w, h, theme, kw)
