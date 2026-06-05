"""summary chart -- extracted from cli_charts.cmd._helpers (Phase 3a)."""

from cli_charts.charts._utils import _textcharts_options
from cli_charts.registry import register


@register("summary")

def summary(d, title, w, h, theme, **kw):
    """textcharts summary box -- key statistics at a glance."""
    import sys
    try:
        from textcharts import SummaryBox, SummaryStats
        stats = SummaryStats()
        for key, value in d.get('stats', {}).items():
            setattr(stats, key, value)
        chart = SummaryBox(stats=stats, subject=title, options=_textcharts_options(kw))
        print(chart.render())
    except ImportError:
        print("ERROR:dep: pip install textcharts", file=sys.stderr)
        sys.exit(2)
