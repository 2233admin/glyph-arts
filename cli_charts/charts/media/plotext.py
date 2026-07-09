"""plotext chart -- extracted from cli_charts.cmd._helpers (Phase 3b)."""

from cli_charts.registry import register

@register("plotext")

def plotext(d, title, w, h, theme, **kw):
    """plotext overlay renderer: error bars, date plots, text, lines, shapes."""
    from cli_charts.render.plotextx_engine import render_plotextx

    return render_plotextx(
        d,
        title=title,
        width=w,
        height=h,
        theme=theme,
        xlabel=kw.get('xlabel', ''),
        ylabel=kw.get('ylabel', ''),
        xlim=kw.get('xlim'),
        ylim=kw.get('ylim'),
        xscale=kw.get('xscale', 'linear'),
        yscale=kw.get('yscale', 'linear'),
        orientation=kw.get('orientation', 'vertical'),
        no_color=kw.get('no_color', False),
    )
