"""stacked_bar_text chart -- extracted from cli_charts.cmd._helpers (Phase 3a)."""

from cli_charts.charts._utils import _textcharts_options
from cli_charts.registry import register


@register("stacked_bar_text")

def stacked_bar_text(d, title, w, h, theme, **kw):
    """textcharts stacked bar chart -- composition over categories.

    JSON: {"data":[{"label":"Project A","segments":[{"label":"Backend","value":30},{"label":"Frontend","value":20}]}]}
    """
    import sys
    try:
        from textcharts import StackedBar, StackedBarData, StackedBarSegment

        data = []
        for item in d.get('data', []):
            segments = [
                StackedBarSegment(phase_name=str(seg.get('label', 'Segment')), value=seg.get('value', 0))
                for seg in item.get('segments', [])
            ]
            data.append(StackedBarData(label=str(item.get('label', '')), segments=segments))

        if data:
            chart = StackedBar(data=data, title=title, options=_textcharts_options(kw))
            print(chart.render())
        else:
            print("(no data)", file=sys.stderr)
    except ImportError:
        print("ERROR:dep: pip install textcharts", file=sys.stderr)
        sys.exit(2)
