"""wave_command -- extracted from cli_charts.cmd._helpers (Phase 3a)."""

from cli_charts.registry import register

@register("wave_command")

def wave_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("wave is dispatched by main()")
