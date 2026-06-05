"""line chart -- extracted from cli_charts.cmd._helpers (Phase 2)."""

from cli_charts.charts._utils import _plt_finalize, _series_color
from cli_charts.osc8 import link as _osc8_link


def line(d, title, w, h, theme, **kw):
    """plotext multi-series line chart."""
    import plotext as plt
    plt.clear_figure()
    series = d if isinstance(d, list) else [d]
    for i, s in enumerate(series):
        x = s.get('x', list(range(len(s['y']))))
        label = s.get('label', '')
        if kw.get('link_data'):
            label = _osc8_link(label or f'S{i}', kw['link_data'])
        plt.plot(x, s['y'], label=label,
                 marker=s.get('marker'), color=_series_color(theme, i, s.get('color')))
    _plt_finalize(plt, title, w, h, theme, kw)
