"""bar chart -- extracted from cli_charts.cmd._helpers (Phase 2)."""

import sys

from cli_charts.charts._utils import _bar_symbols, _capture_stdout, _plt_finalize, _style_to_bar_symbols, _symbol_tier
from cli_charts.symbols import BLOCK


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


def hbar(d, title, w, h, theme, **kw):
    """Horizontal bar chart using textgraph/ascii-graph.

    Uses textgraph.horizontal() for enhanced horizontal bars with labels.
    Falls back to ascii-graph or plotext.
    """
    labels = d.get('labels', [f'[{i}]' for i in range(len(d['values']))])
    values = d['values']

    if title:
        print(title)

    # Try textgraph.horizontal() first
    try:
        from textgraph import horizontal as textgraph_hbar
        data = list(zip(labels, values, strict=False))
        print(textgraph_hbar(data))
        return
    except ImportError:
        pass

    # Try ascii-graph
    try:
        from ascii_graph import Pyasciigraph
        g = Pyasciigraph()
        data = list(zip(labels, values, strict=False))
        for line in g.graph(title or 'bar', data):
            print(line)
        return
    except ImportError:
        pass

    # Fallback to plotext
    import plotext as plt
    plt.clear_figure()
    plt.bar(labels, values, orientation='horizontal')
    _plt_finalize(plt, '', w, h, theme, kw)
