"""bar chart -- extracted from cli_charts.cmd._helpers (Phase 3b)."""

import sys

from cli_charts.charts._utils import _bar_symbols, _capture_stdout, _plt_finalize, _style_to_bar_symbols, _symbol_tier
from cli_charts.registry import register
from cli_charts.symbols import BLOCK

@register("bar")

def bar(d, title, w, h, theme, **kw):
    """plotext vertical/horizontal bar chart."""
    # Use textgraph for horizontal bars when orientation is horizontal
    if kw.get('orientation') == 'horizontal':
        return hbar(d, title, w, h, theme, **kw)
    import plotext as plt
    plt.clear_figure()
    plt.bar(d['labels'], d['values'],
            orientation=kw.get('orientation', 'vertical'))
    symbol_set = kw.get('symbol_set') or _style_to_bar_symbols(kw.get('visual_style'))
    if symbol_set:
        full, empty = _bar_symbols(symbol_set, _symbol_tier(kw))
        default_full = BLOCK['eighth_low_8']
        output = _capture_stdout(lambda: _plt_finalize(plt, title, w, h, theme, kw))
        sys.stdout.write(output.replace(default_full, full).replace(' ', empty if symbol_set in {'braille', 'shade'} else ' '))
        return
    _plt_finalize(plt, title, w, h, theme, kw)
