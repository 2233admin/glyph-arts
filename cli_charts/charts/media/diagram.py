"""diagram chart -- extracted from cli_charts.cmd._helpers (Phase 3b)."""

import sys

from cli_charts.charts._utils import _render_statusline
from cli_charts.registry import register

@register("diagram")

def diagram(d, title, w, h, theme, **kw):
    """Diagon-compatible structural diagram renderer."""
    del theme
    from cli_charts.render.diagram_engine import render_diagram

    if isinstance(d, dict):
        kind = kw.get('diagram_kind') or d.get('kind') or d.get('type')
        text = d.get('text') or d.get('source') or d.get('data') or ''
    else:
        kind = kw.get('diagram_kind')
        text = str(d)
    if not kind:
        raise ValueError('diagram needs a kind such as sequence/tree/table/flowchart/math')
    rc = render_diagram(
        kind,
        text,
        width=w,
        output=kw.get('output') or None,
        engine=kw.get('diagram_engine', 'auto'),
    )
    if rc:
        sys.exit(rc)
    if title and kw.get('statusline'):
        _render_statusline('diagram', {'label': title, 'value': 1}, title)
