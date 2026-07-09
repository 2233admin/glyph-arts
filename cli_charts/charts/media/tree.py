"""tree chart -- extracted from cli_charts.cmd._helpers (Phase 3b)."""

from cli_charts.registry import register

@register("tree")

def tree(d, title, w, h, theme, **kw):
    """rich Tree -- hierarchical / nested data."""
    from rich.console import Console
    from rich.tree import Tree as RichTree
    no_color = kw.get('no_color', False)
    c = Console(no_color=no_color)

    def _build(node, parent):
        label = node.get('label') or node.get('name') or str(node)
        style = node.get('style', '')
        branch = parent.add(f'[{style}]{label}[/{style}]' if style else label)
        for child in node.get('children', []):
            _build(child, branch)

    root_label = d.get('label') or d.get('name') or title or 'root'
    t = RichTree(root_label)
    for child in d.get('children', []):
        _build(child, t)
    c.print(t)
