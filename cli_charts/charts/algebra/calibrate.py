"""calibrate chart -- extracted from cli_charts.cmd._helpers (Phase 3a)."""


def calibrate(d, title, w, h, theme, **kw):
    """Print chat/terminal width calibration rulers."""
    from cli_charts.markup import render_chat_calibration

    spec = d if isinstance(d, dict) else {}
    spec.setdefault("from", kw.get("calibrate_from", 96))
    spec.setdefault("to", kw.get("calibrate_to", 160))
    spec.setdefault("step", kw.get("calibrate_step", 8))
    spec.setdefault("glyph", kw.get("calibrate_glyph", "all"))
    spec.setdefault("terminal", kw.get("terminal", False))
    spec.setdefault("recommend", kw.get("recommend", False))
    print(render_chat_calibration(spec), end="")
