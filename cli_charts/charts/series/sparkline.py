"""sparkline chart -- extracted from cli_charts.cmd._helpers (Phase 2)."""

from cli_charts.charts._utils import _render_statusline


def sparkline(d, title, w, h, theme, **kw):
    """sparklines unicode block chart -- single line.

    Uses textgraph.spark() for enhanced sparklines with multiple styles.
    Falls back to sparklines library if textgraph is unavailable.
    """
    if kw.get('statusline'):
        _render_statusline('sparkline', d, title)
        return
    if title:
        print(title)
    values = d['values']

    # Try textgraph.spark() first (better sparklines)
    try:
        from textgraph import spark as textgraph_spark
        print(textgraph_spark(values))
        return
    except ImportError:
        pass

    # Fallback to sparklines library
    import sparklines as sl
    for ln in sl.sparklines(values):
        print(ln)
