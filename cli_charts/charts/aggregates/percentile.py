"""percentile chart -- extracted from cli_charts.cmd._helpers (Phase 3a)."""

from cli_charts.charts._utils import _textcharts_options
from cli_charts.registry import register


@register("percentile")

def percentile(d, title, w, h, theme, **kw):
    """textcharts percentile ladder -- show value distribution.

    JSON: {"data":[{"name":"Response Time","p50":50,"p90":90,"p95":95,"p99":99}]}
    or {"series":[{"name":"A","values":[...]}]} to auto-calculate.
    """
    import sys
    try:
        from textcharts import PercentileData, PercentileLadder

        if 'data' in d:
            # Direct percentile data
            data = [PercentileData(
                name=str(item['name']),
                p50=item.get('p50', 0),
                p90=item.get('p90', 0),
                p95=item.get('p95', 0),
                p99=item.get('p99', 0)
            ) for item in d.get('data', [])]
        elif 'series' in d:
            # Auto-calculate from values
            data = []
            for s in d.get('series', []):
                values = s.get('values', [])
                if values:
                    import numpy as np
                    arr = np.array(values)
                    data.append(PercentileData(
                        name=str(s.get('name', 'data')),
                        p50=np.percentile(arr, 50),
                        p90=np.percentile(arr, 90),
                        p95=np.percentile(arr, 95),
                        p99=np.percentile(arr, 99)
                    ))
        else:
            print("ERROR:schema: percentile requires 'data' or 'series'", file=sys.stderr)
            sys.exit(1)
            return

        chart = PercentileLadder(data=data, title=title, options=_textcharts_options(kw))
        print(chart.render())
    except ImportError:
        print("ERROR:dep: pip install textcharts", file=sys.stderr)
        sys.exit(2)
