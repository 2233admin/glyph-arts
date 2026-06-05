"""diverging chart -- extracted from cli_charts.cmd._helpers (Phase 3a)."""

from cli_charts.charts._utils import _textcharts_options


def diverging(d, title, w, h, theme, **kw):
    """textcharts diverging bar chart -- positive/negative comparison.

    JSON: {"data":[{"label":"Product A","pct_change":25},{"label":"Product B","pct_change":-15}]}
    """
    import sys
    try:
        from textcharts import DivergingBar, DivergingBarData
        data = [
            DivergingBarData(label=str(item['label']), pct_change=item.get('pct_change', item.get('value', 0)))
            for item in d.get('data', [])
        ]
        chart = DivergingBar(data=data, title=title, options=_textcharts_options(kw))
        print(chart.render())
    except ImportError:
        print("ERROR:dep: pip install textcharts", file=sys.stderr)
        sys.exit(2)
