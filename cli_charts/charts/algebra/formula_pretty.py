"""formula_pretty chart -- extracted from cli_charts.cmd._helpers (Phase 3a)."""


def formula_pretty(d, title, w, h, theme, **kw):
    """Formula source -> SymPy terminal pretty-printer."""
    from cli_charts.markup import render_formula_pretty

    spec = d if isinstance(d, (dict, list, str)) else str(d)
    if title and isinstance(spec, dict) and not spec.get("title"):
        spec = {**spec, "title": title}
    elif title and not isinstance(spec, dict):
        spec = {"title": title, "items": spec if isinstance(spec, list) else [spec]}
    print(render_formula_pretty(spec), end="")
