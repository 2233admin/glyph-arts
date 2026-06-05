"""box chart -- extracted from cli_charts.cmd._helpers (Phase 2)."""

from cli_charts.charts._utils import _plt_finalize


def box(d, title, w, h, theme, **kw):
    """plotext box plot (median/quartile/whisker).
    x-labels passed as first positional arg; data matrix as second.
    """
    import plotext as plt
    if 'quintuples' in d:
        # Pre-computed quantiles: list of 5-element lists
        plt.box(d.get('labels', []), d['quintuples'], quintuples=True)
    else:
        xlabels = d.get('labels', list(range(len(d['data']))))
        plt.box(xlabels, d['data'])
    _plt_finalize(plt, title, w, h, theme, kw)
