"""cdf_chart chart -- extracted from cli_charts.cmd._helpers (Phase 3a)."""

from cli_charts.charts._utils import _textcharts_options


def cdf_chart(d, title, w, h, theme, **kw):
    """textcharts CDF chart -- cumulative distribution function.

    JSON: {"series":[{"name":"A","values":[1,2,3,4,5]}]}
    """
    import sys
    try:
        from textcharts import CDFChart, CDFSeriesData

        series = []
        for s in d.get('series', [{'name': 'data', 'values': d.get('values', [])}]):
            if isinstance(s, dict):
                series.append(CDFSeriesData(name=str(s.get('name', 'data')), values=s.get('values', [])))
            else:
                series.append(CDFSeriesData(name='data', values=s))

        if series:
            chart = CDFChart(data=series, title=title, options=_textcharts_options(kw))
            print(chart.render())
        else:
            print("(no data)", file=sys.stderr)
    except ImportError:
        print("ERROR:dep: pip install textcharts", file=sys.stderr)
        sys.exit(2)
