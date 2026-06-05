"""Streaming stdin animation support for the legacy CLI dispatcher."""

import sys

ANIMATE_TYPES = {'line', 'scatter', 'sparkline'}


def animate_stdin(chart_type, title, w, h, theme, refresh, window, duration, kw):
    """Stream values from stdin and re-render chart after each point.

    Input format: one numeric value per line. Whitespace-separated fields are
    accepted; only the last field is used as the Y value.
    """
    import collections
    import time

    import plotext as plt
    from rich.console import Console
    from rich.live import Live
    from rich.text import Text

    from cli_charts.themes import get_palette

    if chart_type not in ANIMATE_TYPES:
        print(f'ERROR:schema: --animate supports: {", ".join(sorted(ANIMATE_TYPES))}',
              file=sys.stderr)
        sys.exit(1)

    buf = collections.deque(maxlen=window if window > 0 else None)
    t_start = time.monotonic()
    console = Console()

    def make_frame():
        ys = list(buf)
        xs = list(range(len(ys)))
        label = (title + ' ' if title else '') + f'[n={len(ys)}]'
        if chart_type == 'sparkline':
            try:
                from sparklines import sparklines as _sparklines

                lines = _sparklines(ys)
                return '\n'.join(lines) + f'\n{label}'
            except ImportError:
                return label + '\n' + ' '.join(f'{v:.1f}' for v in ys[-20:])
        plt.clf()
        plt_fn = {'line': 'plot', 'scatter': 'scatter'}.get(chart_type, chart_type)
        getattr(plt, plt_fn)(xs, ys)
        plt.title(label)
        plt.plotsize(w - 2, h)
        palette = get_palette(theme)
        if palette:
            if palette.get('plt_base'):
                plt.theme(palette['plt_base'])
            plt.canvas_color(palette['canvas'])
            plt.axes_color(palette['axes'])
            plt.ticks_color(palette['ticks'])
        else:
            plt.theme(theme)
        return plt.build()

    try:
        with Live(console=console, refresh_per_second=refresh, screen=False) as live:
            for raw_line in sys.stdin:
                raw_line = raw_line.strip()
                if not raw_line:
                    continue
                try:
                    val = float(raw_line.split()[-1])
                except ValueError:
                    continue
                buf.append(val)
                if len(buf) >= 2:
                    live.update(Text.from_ansi(make_frame()))
                if duration > 0 and time.monotonic() - t_start >= duration:
                    break
    except KeyboardInterrupt:
        pass
