"""kline chart -- extracted from cli_charts.cmd._helpers (Phase 2)."""

from cli_charts.charts._utils import _normalize_kline_dates, _plt_finalize, _symbol_tier
from cli_charts.symbols import get_symbol


def kline(d, title, w, h, theme, **kw):
    """plotext candlestick K-line. Accepts DD/MM/YYYY or YYYY-MM-DD dates."""
    candle_style = kw.get('candle_style')
    if candle_style and candle_style != 'default':
        tier = _symbol_tier(kw)
        up = get_symbol('triangle_up', tier=tier)
        down = get_symbol('triangle_down', tier=tier)
        for date, open_, close in zip(d['dates'], d['open'], d['close'], strict=False):
            marker = up if close >= open_ else down
            print(f"{date} {marker} {open_} -> {close}")
        return
    import plotext as plt
    plt.clear_figure()
    plt.candlestick(_normalize_kline_dates(d['dates']), {
        'Open': d['open'], 'High': d['high'],
        'Low': d['low'],   'Close': d['close'],
    })
    _plt_finalize(plt, title, w, h, theme, kw)
