"""hist chart -- extracted from cli_charts.cmd._helpers (Phase 2)."""

from cli_charts.charts._utils import _plt_finalize


def hist(d, title, w, h, theme, **kw):
    """plotext histogram -- single or multi-series."""
    import plotext as plt
    series = d if isinstance(d, list) else [d]
    for s in series:
        plt.hist(s['values'], bins=s.get('bins', 20),
                 label=s.get('label', ''), color=s.get('color'))
    _plt_finalize(plt, title, w, h, theme, kw)
