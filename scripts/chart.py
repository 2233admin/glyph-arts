#!/usr/bin/env python3
"""cli-charts: terminal-visible chart toolkit for Claude Code.

Usage: python chart.py <type> [options]
Types (22):
  plotext : kline line scatter bar multibar stackedbar hist heatmap box indicator event confusion
  rich    : table tree panel gauge pie
  drawille: curve
  uniplot : uniplot
  misc    : graph sparkline banner
"""
import sys
import os
import json
import argparse


# -- helpers -----------------------------------------------------------------

def _canvas_line(canvas, x0, y0, x1, y1):
    """Bresenham's line algorithm -- drawille Canvas has no built-in line()."""
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    while True:
        canvas.set(x0, y0)
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy


def _plt_finalize(plt, title, w, h, theme, kw):
    """Apply common plotext settings and render."""
    if title:
        plt.title(title)
    plt.plotsize(w, h)
    plt.theme(theme)
    if kw.get('xlabel'):
        plt.xlabel(kw['xlabel'])
    if kw.get('ylabel'):
        plt.ylabel(kw['ylabel'])
    if kw.get('xlim'):
        plt.xlim(*kw['xlim'])
    if kw.get('ylim'):
        plt.ylim(*kw['ylim'])
    if kw.get('xscale') == 'log':
        plt.xscale('log')
    if kw.get('yscale') == 'log':
        plt.yscale('log')
    if kw.get('output'):
        plt.save_fig(kw['output'], keep_colors=False)
    else:
        plt.show()


# -- renderers ---------------------------------------------------------------

def kline(d, title, w, h, theme, **kw):
    """plotext candlestick K-line. dates MUST be DD/MM/YYYY."""
    import plotext as plt
    plt.candlestick(d['dates'], {
        'Open': d['open'], 'High': d['high'],
        'Low': d['low'],   'Close': d['close'],
    })
    _plt_finalize(plt, title, w, h, theme, kw)


def line(d, title, w, h, theme, **kw):
    """plotext multi-series line chart."""
    import plotext as plt
    series = d if isinstance(d, list) else [d]
    for s in series:
        x = s.get('x', list(range(len(s['y']))))
        plt.plot(x, s['y'], label=s.get('label', ''),
                 marker=s.get('marker'), color=s.get('color'))
    _plt_finalize(plt, title, w, h, theme, kw)


def scatter(d, title, w, h, theme, **kw):
    """plotext scatter plot. Same schema as line."""
    import plotext as plt
    series = d if isinstance(d, list) else [d]
    for s in series:
        x = s.get('x', list(range(len(s['y']))))
        plt.scatter(x, s['y'], label=s.get('label', ''),
                    marker=s.get('marker'), color=s.get('color'))
    _plt_finalize(plt, title, w, h, theme, kw)


def bar(d, title, w, h, theme, **kw):
    """plotext vertical/horizontal bar chart."""
    import plotext as plt
    plt.bar(d['labels'], d['values'],
            orientation=kw.get('orientation', 'vertical'))
    _plt_finalize(plt, title, w, h, theme, kw)


def pie(d, title, w, h, theme, **kw):
    """Rich percentage-bar pie breakdown. labels + values arrays of equal length."""
    from rich.console import Console
    from rich.table import Table
    from rich import box as rich_box
    total = sum(d['values']) or 1
    bar_w = 36
    colors = ['red', 'green', 'blue', 'yellow', 'magenta', 'cyan',
              'bright_red', 'bright_green', 'bright_blue']
    tbl = Table(title=title or None, box=rich_box.ROUNDED, show_lines=False)
    tbl.add_column('Label', style='bold')
    tbl.add_column('Pct', justify='right')
    tbl.add_column('Distribution', min_width=bar_w)
    tbl.add_column('Value', justify='right')
    for i, (label, val) in enumerate(zip(d['labels'], d['values'])):
        pct = val / total * 100
        filled = round(pct / 100 * bar_w)
        color = colors[i % len(colors)]
        bar = f'[{color}]{"█" * filled}[/{color}]{"░" * (bar_w - filled)}'
        tbl.add_row(str(label), f'{pct:.1f}%', bar, str(val))
    Console().print(tbl)


def multibar(d, title, w, h, theme, **kw):
    """plotext grouped multi-series bar chart."""
    import plotext as plt
    xlabels = d['labels']
    values = [s['values'] for s in d['series']]
    slabels = [s.get('label', f'S{i}') for i, s in enumerate(d['series'])]
    plt.multiple_bar(xlabels, values, labels=slabels,
                     orientation=kw.get('orientation', 'vertical'))
    _plt_finalize(plt, title, w, h, theme, kw)


def stackedbar(d, title, w, h, theme, **kw):
    """plotext stacked bar chart."""
    import plotext as plt
    xlabels = d['labels']
    values = [s['values'] for s in d['series']]
    slabels = [s.get('label', f'S{i}') for i, s in enumerate(d['series'])]
    plt.stacked_bar(xlabels, values, labels=slabels,
                    orientation=kw.get('orientation', 'vertical'))
    _plt_finalize(plt, title, w, h, theme, kw)


def hist(d, title, w, h, theme, **kw):
    """plotext histogram -- single or multi-series."""
    import plotext as plt
    series = d if isinstance(d, list) else [d]
    for s in series:
        plt.hist(s['values'], bins=s.get('bins', 20),
                 label=s.get('label', ''), color=s.get('color'))
    _plt_finalize(plt, title, w, h, theme, kw)


def heatmap(d, title, w, h, theme, **kw):
    """plotext heatmap / correlation matrix.
    plotext.heatmap() requires a pandas DataFrame.
    """
    import plotext as plt
    import pandas as pd
    df = pd.DataFrame(
        d['matrix'],
        columns=d.get('xlabels'),
        index=d.get('ylabels'),
    )
    plt.heatmap(df)
    _plt_finalize(plt, title, w, h, theme, kw)


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


def indicator(d, title, w, h, theme, **kw):
    """plotext big-number KPI display."""
    import plotext as plt
    plt.indicator(d['value'], d.get('label', title or ''))
    _plt_finalize(plt, None, w, h, theme, kw)  # title already baked into label


def event(d, title, w, h, theme, **kw):
    """plotext event / timeline plot.
    Orientation comes from --orientation CLI flag (kw) not JSON data.
    """
    import plotext as plt
    plt.event_plot(d['data'],
                   orientation=kw.get('orientation', 'vertical'))
    _plt_finalize(plt, title, w, h, theme, kw)


def sparkline(d, title, w, h, theme, **kw):
    """sparklines unicode block chart -- single line."""
    import sparklines as sl
    if title:
        print(title)
    for ln in sl.sparklines(d['values']):
        print(ln)


def table(d, title, w, h, theme, **kw):
    """rich double-edge formatted table."""
    from rich.console import Console
    from rich.table import Table
    from rich import box as richbox
    no_color = kw.get('no_color', False)
    c = Console(no_color=no_color)
    box_style = getattr(richbox, d.get('box', 'DOUBLE_EDGE'), richbox.DOUBLE_EDGE)
    t = Table(title=title, box=box_style,
              caption=d.get('caption'),
              row_styles=d.get('row_styles'))
    for col in d['columns']:
        if isinstance(col, dict):
            t.add_column(col['name'], style=col.get('style', 'white'),
                         footer=str(col.get('footer', '')))
        else:
            t.add_column(str(col))
    for row in d['rows']:
        t.add_row(*[str(v) for v in row])
    c.print(t)


def tree(d, title, w, h, theme, **kw):
    """rich Tree -- hierarchical / nested data."""
    from rich.console import Console
    from rich.tree import Tree as RichTree
    no_color = kw.get('no_color', False)
    c = Console(no_color=no_color)

    def _build(node, parent):
        label = node.get('label', str(node))
        style = node.get('style', '')
        branch = parent.add(f'[{style}]{label}[/{style}]' if style else label)
        for child in node.get('children', []):
            _build(child, branch)

    root_label = d.get('label', title or 'root')
    t = RichTree(root_label)
    for child in d.get('children', []):
        _build(child, t)
    c.print(t)


def panel(d, title, w, h, theme, **kw):
    """rich Panel -- bordered text / callout box."""
    from rich.console import Console
    from rich.panel import Panel as RichPanel
    from rich import box as richbox
    no_color = kw.get('no_color', False)
    c = Console(no_color=no_color)
    box_style = getattr(richbox, d.get('box', 'ROUNDED'), richbox.ROUNDED)
    p = RichPanel(d['content'],
                  title=d.get('title', title or None),
                  subtitle=d.get('subtitle'),
                  box=box_style)
    c.print(p)


def graph(d, title, w, h, theme, **kw):
    """PHART ASCII network graph."""
    from phart import ASCIIRenderer, LayoutOptions, NodeStyle
    import networkx as nx
    G = nx.DiGraph() if d.get('directed', True) else nx.Graph()
    for node in d.get('nodes', []):
        G.add_node(node['id'] if isinstance(node, dict) else node)
    G.add_edges_from(d['edges'])
    style_name = d.get('node_style', 'ROUND').upper()
    style = getattr(NodeStyle, style_name, NodeStyle.ROUND)
    opts = LayoutOptions(
        node_style=style,
        node_spacing=d.get('node_spacing', 4),
        layer_spacing=d.get('layer_spacing', 2),
    )
    print(ASCIIRenderer(G, options=opts).render())


def curve(d, title, w, h, theme, **kw):
    """drawille braille pixel canvas -- connected high-res curves.
    Points are auto-scaled to fit --width x --height.
    Uses Bresenham's line between consecutive points for smooth output.
    """
    import drawille
    points = d['points']
    if not points:
        print('(no points)', file=sys.stderr)
        return
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    # drawille: 2 pixels wide x 4 pixels tall per terminal cell
    canvas_w = max(1, w * 2 - 1)
    canvas_h = max(1, h * 4 - 1)

    def scale(v, lo, hi, size):
        return size // 2 if hi == lo else round((v - lo) / (hi - lo) * size)

    if title:
        print(title)
    c = drawille.Canvas()
    if len(points) == 1:
        c.set(scale(points[0][0], min_x, max_x, canvas_w),
              canvas_h - scale(points[0][1], min_y, max_y, canvas_h))
    else:
        for i in range(len(points) - 1):
            x1 = scale(points[i][0],     min_x, max_x, canvas_w)
            y1 = canvas_h - scale(points[i][1],     min_y, max_y, canvas_h)
            x2 = scale(points[i + 1][0], min_x, max_x, canvas_w)
            y2 = canvas_h - scale(points[i + 1][1], min_y, max_y, canvas_h)
            _canvas_line(c, x1, y1, x2, y2)
    print(c.frame())


def gauge(d, title, w, h, theme, **kw):
    """rich multi-metric progress bars (static gauge).
    Auto-colors: green <70%, yellow <90%, red >=90%.
    """
    from rich.console import Console
    from rich.table import Table
    from rich import box as richbox
    no_color = kw.get('no_color', False)
    c = Console(no_color=no_color)
    metrics = d if isinstance(d, list) else d.get('metrics', [d])
    t = Table(title=title, box=richbox.SIMPLE, show_header=False, padding=(0, 1))
    t.add_column('Label', style='bold', min_width=12)
    t.add_column('Bar', min_width=32)
    t.add_column('Value', justify='right', min_width=10)
    for m in metrics:
        val = float(m['value'])
        mx  = float(m.get('max', 100))
        pct = max(0.0, min(1.0, val / mx)) if mx != 0 else 0.0
        bar_w = 30
        filled = round(pct * bar_w)
        auto_color = 'green' if pct < 0.7 else ('yellow' if pct < 0.9 else 'red')
        color = m.get('color', auto_color)
        bar = f'[{color}]{"█" * filled}{"░" * (bar_w - filled)}[/{color}]'
        t.add_row(m.get('label', ''), bar, f'{val:.1f} / {mx:.0f}')
    c.print(t)


def confusion(d, title, w, h, theme, **kw):
    """plotext ML confusion matrix.
    actual/predicted must be lists of class labels (int or str).
    """
    import plotext as plt
    plt.confusion_matrix(d['actual'], d['predicted'],
                         labels=d.get('labels'))
    _plt_finalize(plt, title, w, h, theme, kw)


def banner(d, title, w, h, theme, **kw):
    """pyfiglet large ASCII art text banner."""
    import pyfiglet
    text = d.get('text', title or 'BANNER')
    font = d.get('font', 'big')
    result = pyfiglet.figlet_format(text, font=font, width=d.get('width', w))
    color = d.get('color')
    if color and not kw.get('no_color'):
        from rich.console import Console
        Console().print(f'[{color}]{result}[/{color}]', end='')
    else:
        print(result, end='')


def uniplot(d, title, w, h, theme, **kw):
    """uniplot scientific line/scatter with labeled axes.
    Same multi-series schema as 'line'. Set "lines":false per series for scatter.
    Respects --xlim, --ylim, --width, --height.
    """
    from uniplot import plot as uplot
    series = d if isinstance(d, list) else [d]
    ys = [s['y'] for s in series]
    xs = [s.get('x', list(range(len(s['y'])))) for s in series]
    labels = [s.get('label', f'S{i}') for i, s in enumerate(series)]
    lines = all(s.get('lines', True) for s in series)
    plot_kw = dict(
        title=title or '',
        legend_labels=labels,
        lines=lines,
        width=w,
        height=h,
    )
    if kw.get('xlim'):
        plot_kw['x_min'], plot_kw['x_max'] = kw['xlim']
    if kw.get('ylim'):
        plot_kw['y_min'], plot_kw['y_max'] = kw['ylim']
    if len(series) == 1:
        uplot(ys=ys[0], xs=xs[0], **plot_kw)
    else:
        uplot(ys=ys, xs=xs, **plot_kw)


# -- DuckDB loader -----------------------------------------------------------

def load_duckdb(sql, db_path, chart_type):
    import duckdb
    df = duckdb.connect(db_path).execute(sql).df()
    if chart_type == 'kline':
        col0 = df.columns[0]
        dates = [d.strftime('%d/%m/%Y') for d in df[col0]]
        return {
            'dates': dates,
            'open':  df['open'].tolist(),
            'high':  df['high'].tolist(),
            'low':   df['low'].tolist(),
            'close': df['close'].tolist(),
        }
    if chart_type in ('line', 'scatter'):
        col0 = df.columns[0]
        return [{'label': c, 'x': df[col0].tolist(), 'y': df[c].tolist()}
                for c in df.columns[1:]]
    if chart_type in ('bar', 'pie'):
        cols = list(df.columns)
        return {'labels': df[cols[0]].astype(str).tolist(),
                'values': df[cols[1]].tolist()}
    if chart_type == 'table':
        return {'columns': list(df.columns),
                'rows': df.values.tolist()}
    if chart_type == 'hist':
        return [{'label': c, 'values': df[c].tolist()} for c in df.columns]
    if chart_type == 'heatmap':
        return {'matrix': df.values.tolist(),
                'xlabels': list(df.columns),
                'ylabels': list(df.index.astype(str))}
    if chart_type == 'curve':
        cols = list(df.columns)
        return {'points': list(zip(df[cols[0]].tolist(), df[cols[1]].tolist()))}
    if chart_type == 'sparkline':
        return {'values': df.iloc[:, 0].tolist()}
    if chart_type == 'confusion':
        cols = list(df.columns)
        return {'actual': df[cols[0]].tolist(), 'predicted': df[cols[1]].tolist()}
    if chart_type == 'uniplot':
        col0 = df.columns[0]
        return [{'label': c, 'x': df[col0].tolist(), 'y': df[c].tolist()}
                for c in df.columns[1:]]
    # graph: 2-col edge list; others: generic dict
    if chart_type == 'graph':
        cols = list(df.columns)
        return {'edges': list(zip(df[cols[0]].astype(str),
                                  df[cols[1]].astype(str)))}
    return df.to_dict(orient='list')


# -- registry ----------------------------------------------------------------

CMDS = {
    'kline':      kline,
    'line':       line,
    'scatter':    scatter,
    'bar':        bar,
    'pie':        pie,
    'multibar':   multibar,
    'stackedbar': stackedbar,
    'hist':       hist,
    'heatmap':    heatmap,
    'box':        box,
    'indicator':  indicator,
    'event':      event,
    'confusion':  confusion,
    'sparkline':  sparkline,
    'table':      table,
    'tree':       tree,
    'panel':      panel,
    'gauge':      gauge,
    'graph':      graph,
    'curve':      curve,
    'uniplot':    uniplot,
    'banner':     banner,
}

EXPECTED_SCHEMAS = {
    'kline':      '{"dates":["DD/MM/YYYY",...], "open":[...], "high":[...], "low":[...], "close":[...]}',
    'line':       '[{"label":"A","x":[...],"y":[...]}] or {"label":"A","y":[...]}',
    'scatter':    '[{"label":"A","x":[...],"y":[...]}] or {"label":"A","y":[...]}',
    'bar':        '{"labels":[...], "values":[...]}',
    'pie':        '{"labels":["A","B","C"], "values":[30,50,20]}',
    'multibar':   '{"labels":[...], "series":[{"label":"A","values":[...]}, ...]}',
    'stackedbar': '{"labels":[...], "series":[{"label":"A","values":[...]}, ...]}',
    'hist':       '{"values":[...], "bins":20} or [{"label":"A","values":[...]}, ...]',
    'heatmap':    '{"matrix":[[...]], "xlabels":[...], "ylabels":[...]}',
    'box':        '{"data":[[s1_vals],[s2_vals],...], "labels":["A","B",...]}',
    'indicator':  '{"value":23.4, "label":"Total Return %"}',
    'event':      '{"data":[x1,x2,...]}',
    'confusion':  '{"actual":[0,1,2,0], "predicted":[0,2,1,0], "labels":["Cat","Dog","Bird"]}',
    'sparkline':  '{"values":[1,3,5,2,8,4,6]}',
    'table':      '{"columns":[...], "rows":[[...], ...]}',
    'tree':       '{"label":"root","children":[{"label":"A","children":[...]}]}',
    'panel':      '{"content":"text here", "title":"optional", "box":"ROUNDED"}',
    'gauge':      '[{"label":"CPU","value":75,"max":100,"color":"red"}, ...] or {"metrics":[...]}',
    'graph':      '{"edges":[["A","B"],...], "directed":true, "node_style":"ROUND"}',
    'curve':      '{"points":[[x,y],...]}',
    'uniplot':    '[{"label":"A","x":[...],"y":[...]}] or {"label":"A","y":[...]}',
    'banner':     '{"text":"PROFIT","font":"big","color":"green"}',
}

# Types where --width/--height/--theme have no effect
_NO_SIZE_THEME = {'table', 'tree', 'panel', 'graph', 'sparkline', 'gauge', 'banner', 'pie'}


# -- main --------------------------------------------------------------------

def main():
    p = argparse.ArgumentParser(
        description='CLI Charts -- terminal-visible charts for Claude Code',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Chart types (22):
  plotext : kline line scatter bar multibar stackedbar hist heatmap box indicator event confusion
  rich    : table tree panel gauge pie
  drawille: curve
  uniplot : uniplot
  misc    : graph sparkline banner

Examples:
  python chart.py kline --json '{"dates":["07/04/2026"],"open":[100],"high":[102],"low":[99],"close":[101]}'
  python chart.py scatter --json '[{"label":"A","x":[1,2,3],"y":[4,2,5]}]'
  python chart.py hist --json '{"values":[1,2,2,3,3,3,4,4,5],"bins":5}'
  python chart.py heatmap --json '{"matrix":[[1,2],[3,4]],"xlabels":["A","B"],"ylabels":["X","Y"]}'
  python chart.py box --json '{"data":[[1,2,3,4,5],[2,3,4,5,6]],"labels":["A","B"]}'
  python chart.py sparkline --json '{"values":[1,3,5,2,8,4,6]}'
  python chart.py indicator --json '{"value":23.4,"label":"Total Return %"}'
  python chart.py confusion --json '{"actual":[0,1,2,0,1,2],"predicted":[0,2,2,0,0,1],"labels":["Cat","Dog","Bird"]}'
  python chart.py gauge --json '[{"label":"CPU","value":72,"max":100},{"label":"RAM","value":14,"max":32}]'
  python chart.py banner --json '{"text":"PROFIT","font":"big","color":"green"}'
  python chart.py uniplot --json '[{"label":"A","x":[1,2,3,4],"y":[2,4,3,6]},{"label":"B","y":[1,3,2,5]}]'
  python chart.py tree --json '{"label":"root","children":[{"label":"A"},{"label":"B","children":[{"label":"C"}]}]}'
  python chart.py panel --json '{"content":"Hello world","title":"Info","box":"ROUNDED"}'
  python chart.py multibar --json '{"labels":["Q1","Q2"],"series":[{"label":"Rev","values":[10,12]},{"label":"Cost","values":[8,9]}]}'
  python chart.py event --json '{"data":[1,3,5,8,13]}'
  python chart.py line --duckdb "SELECT trade_date, close FROM stock_daily LIMIT 60" --db /path/to/data.duckdb
  cat data.json | python chart.py line
""")
    p.add_argument('type', choices=list(CMDS), metavar='TYPE',
                   help='Chart type: ' + ' | '.join(CMDS))
    p.add_argument('--json',        dest='data', help='JSON data string')
    p.add_argument('--duckdb',      metavar='SQL',
                   help='SQL query against a DuckDB database')
    p.add_argument('--db',          default=None,
                   help='DuckDB file path (required with --duckdb)')
    p.add_argument('--title',       default='')
    p.add_argument('--width',       type=int, default=70,
                   help='Chart width in terminal columns (ignored for table/tree/panel/graph/sparkline)')
    p.add_argument('--height',      type=int, default=20,
                   help='Chart height in terminal rows (ignored for table/tree/panel/graph/sparkline)')
    p.add_argument('--theme',       default='pro',
                   help='plotext theme: pro dark clear matrix (ignored for rich/graph/sparkline)')
    p.add_argument('--xlabel',      default='', help='X-axis label (plotext charts)')
    p.add_argument('--ylabel',      default='', help='Y-axis label (plotext charts)')
    p.add_argument('--xlim',        nargs=2, type=float, metavar=('MIN', 'MAX'),
                   help='X-axis limits')
    p.add_argument('--ylim',        nargs=2, type=float, metavar=('MIN', 'MAX'),
                   help='Y-axis limits')
    p.add_argument('--xscale',      choices=['linear', 'log'], default='linear')
    p.add_argument('--yscale',      choices=['linear', 'log'], default='linear')
    p.add_argument('--orientation', choices=['vertical', 'horizontal'],
                   default='vertical', help='Bar orientation (bar/multibar/stackedbar)')
    p.add_argument('--output',      default='',
                   help='Save chart to file instead of displaying (plotext only)')
    p.add_argument('--no-color',    action='store_true',
                   help='Disable ANSI colors (respects NO_COLOR env var)')
    p.add_argument('--version',     action='version', version='cli-charts 2.2.0')
    args = p.parse_args()

    # Warn when size/theme options are silently ignored
    if args.type in _NO_SIZE_THEME:
        ignored = []
        if args.width != 70:    ignored.append('--width')
        if args.height != 20:   ignored.append('--height')
        if args.theme != 'pro': ignored.append('--theme')
        if ignored:
            print(f"warning: {', '.join(ignored)} ignored for {args.type} charts",
                  file=sys.stderr)

    # Respect NO_COLOR env var (https://no-color.org)
    no_color = args.no_color or bool(os.environ.get('NO_COLOR'))

    if args.duckdb:
        if not args.db:
            p.error('--db is required when using --duckdb '
                    '(e.g. --db /path/to/data.duckdb)')
        data = load_duckdb(args.duckdb, args.db, args.type)
    else:
        raw = args.data or sys.stdin.read().strip()
        if not raw:
            p.error('Provide --json, --duckdb, or pipe JSON to stdin')
        try:
            data = json.loads(raw)
        except json.JSONDecodeError as exc:
            p.error(f'Invalid JSON: {exc}')

    kw = dict(
        xlabel=args.xlabel,
        ylabel=args.ylabel,
        xlim=args.xlim,
        ylim=args.ylim,
        xscale=args.xscale,
        yscale=args.yscale,
        orientation=args.orientation,
        output=args.output,
        no_color=no_color,
    )

    try:
        CMDS[args.type](data, args.title, args.width, args.height, args.theme, **kw)
    except (KeyError, IndexError, TypeError, ValueError) as exc:
        p.error(
            f'Invalid {args.type} data schema: {exc}\n'
            f'Expected: {EXPECTED_SCHEMAS[args.type]}'
        )


if __name__ == '__main__':
    main()
