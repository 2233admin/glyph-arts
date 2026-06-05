"""comparison chart -- extracted from cli_charts.cmd._helpers (Phase 3a)."""

from cli_charts.charts._utils import _textcharts_options


def comparison(d, title, w, h, theme, **kw):
    """textcharts comparison bar chart -- side-by-side bars for A/B testing.

    JSON: {"data":[{"label":"Python","baseline":85,"comparison":89.5}, ...]}
    """
    import sys
    try:
        from textcharts import ComparisonBar, ComparisonBarData
        data = [
            ComparisonBarData(
                label=str(item['label']),
                baseline_value=item.get('baseline', 0),
                comparison_value=item.get('comparison', item.get('value', 0)),
                baseline_name=str(item.get('baseline_name', 'Baseline')),
                comparison_name=str(item.get('comparison_name', 'Comparison'))
            )
            for item in d.get('data', [])
        ]
        chart = ComparisonBar(data=data, title=title, options=_textcharts_options(kw))
        print(chart.render())
    except ImportError:
        print("ERROR:dep: pip install textcharts", file=sys.stderr)
        sys.exit(2)
