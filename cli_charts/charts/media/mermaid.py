"""mermaid chart -- extracted from cli_charts.cmd._helpers (Phase 3b)."""

from cli_charts.registry import register

@register("mermaid")

def mermaid(d, title, w, h, theme, **kw):
    """beautiful-mermaid-inspired Mermaid renderer for chat-safe diagrams."""
    del h, theme
    from cli_charts.render.mermaid_engine import render_mermaid

    source = d.get('source') or d.get('text') or d.get('data') if isinstance(d, dict) else str(d)
    print(render_mermaid(
        source,
        width=w,
        use_ascii=bool(kw.get('mermaid_ascii')),
        padding_x=int(kw.get('mermaid_padding_x') or 5),
        padding_y=int(kw.get('mermaid_padding_y') or 1),
        box_padding=int(kw.get('mermaid_box_padding') or 1),
        theme=kw.get('mermaid_theme') or 'zinc-dark',
    ), end="")
