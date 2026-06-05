"""graph chart -- extracted from cli_charts.cmd._helpers (Phase 3a)."""


def graph(d, title, w, h, theme, **kw):
    """PHART ASCII network graph."""
    del title, w, h, theme
    from cli_charts.render.graph_engine import render_graph

    style = kw.get('graph_style') or (d.get('node_style') if isinstance(d, dict) else None) or 'round'
    node_spacing = (d.get('node_spacing') if isinstance(d, dict) else None) or kw.get('graph_node_spacing') or 4
    layer_spacing = (d.get('layer_spacing') if isinstance(d, dict) else None) or kw.get('graph_layer_spacing') or 2
    rc = render_graph(
        d,
        output=kw.get('output') or None,
        graph_format=kw.get('graph_format') or (d.get('format') if isinstance(d, dict) else 'auto'),
        node_style=style,
        node_spacing=node_spacing,
        layer_spacing=layer_spacing,
        charset=kw.get('graph_charset') or 'unicode',
    )
    if rc:
        import sys
        sys.exit(rc)
