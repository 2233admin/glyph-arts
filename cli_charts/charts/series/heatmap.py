"""heatmap chart -- extracted from cli_charts.cmd._helpers (Phase 2)."""

from cli_charts.charts._utils import _plt_finalize


def heatmap(d, title, w, h, theme, **kw):
    """plotext heatmap / correlation matrix.
    plotext.heatmap() requires a pandas DataFrame.
    """
    import pandas as pd
    import plotext as plt
    df = pd.DataFrame(
        d['matrix'],
        columns=d.get('xlabels'),
        index=d.get('ylabels'),
    )
    plt.heatmap(df)
    _plt_finalize(plt, title, w, h, theme, kw)
