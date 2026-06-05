"""step chart -- extracted from cli_charts.cmd._helpers (Phase 2)."""

from cli_charts.charts._utils import _plt_finalize


def step(d, title, w, h, theme, **kw):
    """plotext staircase step chart -- x-point duplication creates stairs.
    Same schema as line. Use for discrete state changes (e.g. bid price, stock level).
    """
    import plotext as plt
    series = d if isinstance(d, list) else [d]
    for s in series:
        x = s.get('x', list(range(len(s['y']))))
        y = s['y']
        sx, sy = [], []
        for i in range(len(x)):
            sx.append(x[i])
            sy.append(y[i])
            if i + 1 < len(x):
                sx.append(x[i + 1])
                sy.append(y[i])
        plt.plot(sx, sy, label=s.get('label', ''),
                 marker=s.get('marker'), color=s.get('color'))
    _plt_finalize(plt, title, w, h, theme, kw)
