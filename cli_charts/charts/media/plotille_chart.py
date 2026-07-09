"""plotille_chart chart -- extracted from cli_charts.cmd._helpers (Phase 3b)."""

import sys

from cli_charts.registry import register

@register("plotille_chart")

def plotille_chart(d, title, w, h, theme, **kw):
    """plotille Figure: composable braille chart with proper axis labels.
    Same multi-series schema as 'line'.  Each series supports "color":"bright_cyan" etc.
    plotille color names: bright_cyan bright_red bright_yellow bright_green white grey
    """
    try:
        import plotille
    except ImportError:
        print('ERROR:dep: pip install plotille', file=sys.stderr)
        sys.exit(2)

    series = d if isinstance(d, list) else [d]
    fig = plotille.Figure()
    fig.width = w
    fig.height = h
    if kw.get('xlabel'):
        fig.x_label = kw['xlabel']
    if kw.get('ylabel'):
        fig.y_label = kw['ylabel']
    if kw.get('xlim'):
        fig.set_x_limits(*kw['xlim'])
    if kw.get('ylim'):
        fig.set_y_limits(*kw['ylim'])

    colors = ['bright_cyan', 'bright_red', 'bright_yellow', 'bright_green',
              'bright_blue', 'bright_magenta']
    for idx, s in enumerate(series):
        ys = s['y']
        xs = s.get('x', list(range(len(ys))))
        color = s.get('color', colors[idx % len(colors)])
        label = s.get('label', f'S{idx}')
        fig.plot(xs, ys, lc=color, label=label)

    if title:
        print(title)
    print(fig.show(legend=True))
