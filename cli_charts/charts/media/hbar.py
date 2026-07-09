"""hbar chart -- extracted from cli_charts.cmd._helpers (Phase 3b)."""

from cli_charts.charts._utils import _plt_finalize
from cli_charts.registry import register

@register("hbar")

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
