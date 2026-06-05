"""stackedbar chart -- extracted from cli_charts.cmd._helpers (Phase 2)."""

from cli_charts.charts._utils import _plt_finalize


def stackedbar(d, title, w, h, theme, **kw):
    """plotext stacked bar chart."""
    import plotext as plt
    xlabels = d['labels']
    values = [s['values'] for s in d['series']]
    slabels = [s.get('label', f'S{i}') for i, s in enumerate(d['series'])]
    plt.stacked_bar(xlabels, values, labels=slabels,
                    orientation=kw.get('orientation', 'vertical'))
    _plt_finalize(plt, title, w, h, theme, kw)
