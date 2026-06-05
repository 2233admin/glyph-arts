"""rank_table chart -- extracted from cli_charts.cmd._helpers (Phase 3a)."""


def rank_table(d, title, w, h, theme, **kw):
    """Sorted ranking table with Rich.

    JSON: {"items":[{"label":"Python","value":89},{"label":"Rust","value":95}]}
    or {"values":{"Python":89,"Rust":95}} (items auto-generated from values keys)
    """
    from rich.console import Console
    from rich.table import Table

    no_color = kw.get('no_color', False)
    c = Console(no_color=no_color)
    t = Table(title=title)

    if d.get('items'):
        # Format 1: items with label/value pairs
        t.add_column("Rank", justify="center")
        t.add_column("Item")
        t.add_column("Value", justify="right")
        sorted_items = sorted(d.get('items', []), key=lambda x: x.get('value', 0), reverse=True)
        for idx, item in enumerate(sorted_items, 1):
            t.add_row(str(idx), str(item.get('label', item)), f"{item.get('value', 0):.1f}")
    else:
        # Format 2: values dict {"Name": score}
        values = d.get('values', {})
        t.add_column("Rank", justify="center")
        t.add_column("Item")
        t.add_column("Score", justify="right")
        sorted_items = sorted(values.items(), key=lambda x: x[1], reverse=True)
        for idx, (name, score) in enumerate(sorted_items, 1):
            t.add_row(str(idx), str(name), f"{score:.1f}")

    c.print(t)
