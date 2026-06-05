"""boxplot_comparison chart -- extracted from cli_charts.cmd._helpers (Phase 3a)."""

from cli_charts.charts._utils import _textcharts_options


def boxplot_comparison(d, title, w, h, theme, **kw):
    """textcharts box plot -- statistical distribution comparison.

    JSON: {"series":[{"name":"A","values":[10,20,30,40,50]}]}
    """
    import sys
    try:
        from textcharts import BoxPlot, BoxPlotSeries

        series = []
        for s in d.get('series', []):
            values = s.get('values', [])
            if values:
                series.append(BoxPlotSeries(name=str(s.get('name', 'data')), values=values))
            else:
                series.append(BoxPlotSeries(name=str(s.get('name', 'data')), values=[0]))

        if series:
            chart = BoxPlot(series=series, title=title, options=_textcharts_options(kw))
            print(chart.render())
        else:
            print("(no data)", file=sys.stderr)
    except ImportError:
        print("ERROR:dep: pip install textcharts", file=sys.stderr)
        sys.exit(2)
