"""scatter chart -- extracted from cli_charts.cmd._helpers (Phase 2)."""

from cli_charts.charts._utils import _plt_finalize, _series_color, _symbol_tier
from cli_charts.osc8 import link as _osc8_link
from cli_charts.symbols import get_symbol

_MARKER_SYMBOLS = {
    'circle': 'circle',
    'triangle': 'triangle_up',
    'diamond': 'diamond',
    'star': 'star',
    'square': 'square',
}


def scatter(d, title, w, h, theme, **kw):
    """plotext scatter plot. Same schema as line."""
    import plotext as plt
    plt.clear_figure()
    series = d if isinstance(d, list) else [d]
    marker_name = kw.get('marker')
    marker = get_symbol(_MARKER_SYMBOLS[marker_name], tier=_symbol_tier(kw)) if marker_name else None
    for i, s in enumerate(series):
        x = s.get('x', list(range(len(s['y']))))
        label = s.get('label', '')
        if kw.get('link_data'):
            label = _osc8_link(label or f'S{i}', kw['link_data'])
        plt.scatter(x, s['y'], label=label,
                    marker=marker or s.get('marker'), color=_series_color(theme, i, s.get('color')))
    _plt_finalize(plt, title, w, h, theme, kw)
