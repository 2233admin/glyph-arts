"""PHART-backed graph rendering helpers."""

from __future__ import annotations

import sys
import tempfile
from pathlib import Path
from typing import Any


def render_graph(
    data: Any,
    *,
    output: str | None = None,
    graph_format: str = "auto",
    node_style: str = "round",
    node_spacing: int = 4,
    layer_spacing: int = 2,
    charset: str = "unicode",
) -> int:
    """Render graph data with PHART from JSON, edge-list text, DOT, or GraphML."""
    try:
        from phart import NodeStyle
    except ImportError:
        print("ERROR:dep: pip install phart", file=sys.stderr)
        return 2

    style = getattr(NodeStyle, node_style.upper(), NodeStyle.ROUND)
    use_ascii = charset == "ascii"
    fmt = (graph_format or "auto").lower()

    try:
        renderer = _build_renderer(
            data,
            graph_format=fmt,
            node_style=style,
            node_spacing=node_spacing,
            layer_spacing=layer_spacing,
            use_ascii=use_ascii,
        )
    except Exception as exc:
        print(f"ERROR:schema: Invalid graph data: {exc}", file=sys.stderr)
        return 1

    text = renderer.render().rstrip("\n") + "\n"
    if output:
        Path(output).write_text(text, encoding="utf-8")
    else:
        print(text, end="")
    return 0


def _build_renderer(
    data: Any,
    *,
    graph_format: str,
    node_style,
    node_spacing: int,
    layer_spacing: int,
    use_ascii: bool,
):
    import networkx as nx
    from phart import ASCIIRenderer, LayoutOptions

    options = LayoutOptions(
        node_style=node_style,
        node_spacing=node_spacing,
        layer_spacing=layer_spacing,
        use_ascii=use_ascii,
    )
    if graph_format == "graphml":
        text = str(data)
        if _looks_like_graphml(text):
            with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".graphml", delete=False) as handle:
                handle.write(text)
                path = handle.name
        else:
            path = text
        return ASCIIRenderer.from_graphml(path, options=options)

    if graph_format == "dot":
        dot_text = str(data)
        try:
            return ASCIIRenderer.from_dot(dot_text, options=options)
        except Exception:
            data = _parse_edge_text(_dot_to_edge_text(dot_text))

    if isinstance(data, str):
        text = data.replace("\\n", "\n").strip()
        if graph_format == "auto":
            if _looks_like_dot(text):
                try:
                    return ASCIIRenderer.from_dot(text, options=options)
                except Exception:
                    data = _parse_edge_text(_dot_to_edge_text(text))
            if _looks_like_graphml(text):
                with tempfile.NamedTemporaryFile("w", encoding="utf-8", suffix=".graphml", delete=False) as handle:
                    handle.write(text)
                    graphml_path = handle.name
                return ASCIIRenderer.from_graphml(graphml_path, options=options)
        data = _parse_edge_text(text)

    if not isinstance(data, dict):
        raise ValueError("graph expects a JSON object or edge-list text")

    graph = nx.DiGraph() if data.get("directed", True) else nx.Graph()
    for node in data.get("nodes", []):
        graph.add_node(node["id"] if isinstance(node, dict) else node)
    edges = data.get("edges")
    if edges is None:
        text = data.get("text") or data.get("source") or data.get("dot") or data.get("graphml")
        if text:
            return _build_renderer(
                str(text),
                graph_format=data.get("format", graph_format),
                node_style=node_style,
                node_spacing=node_spacing,
                layer_spacing=layer_spacing,
                use_ascii=use_ascii,
            )
        raise ValueError("graph needs edges[], text/source, dot, or graphml")
    graph.add_edges_from(edges)
    return ASCIIRenderer(graph, options=options)


def _looks_like_dot(text: str) -> bool:
    stripped = text.lstrip().lower()
    return stripped.startswith("digraph ") or stripped.startswith("graph ") or (
        "{" in stripped and "}" in stripped and ("->" in stripped or "--" in stripped)
    )


def _looks_like_graphml(text: str) -> bool:
    stripped = text.lstrip().lower()
    return stripped.startswith("<?xml") or stripped.startswith("<graphml")


def _parse_edge_text(text: str) -> dict[str, Any]:
    edges = []
    nodes = []
    directed = True
    for raw_line in text.splitlines():
        line = raw_line.strip().strip(";")
        if not line or line.startswith("#"):
            continue
        if "->" in line:
            parts = [part.strip().strip('"') for part in line.split("->") if part.strip()]
            edges.extend(zip(parts, parts[1:], strict=False))
        elif "--" in line:
            directed = False
            parts = [part.strip().strip('"') for part in line.split("--") if part.strip()]
            edges.extend(zip(parts, parts[1:], strict=False))
        elif "," in line:
            left, right = [part.strip().strip('"') for part in line.split(",", 1)]
            edges.append((left, right))
        else:
            bits = [part.strip().strip('"') for part in line.split() if part.strip()]
            if len(bits) >= 2:
                edges.append((bits[0], bits[1]))
            elif bits:
                nodes.append(bits[0])
    return {"nodes": nodes, "edges": edges, "directed": directed}


def _dot_to_edge_text(text: str) -> str:
    cleaned = (
        text.replace("{", "\n")
        .replace("}", "\n")
        .replace(";", "\n")
        .replace("digraph", "\n")
        .replace("graph", "\n")
    )
    lines = []
    for line in cleaned.splitlines():
        stripped = line.strip()
        if stripped and not stripped.startswith("//"):
            lines.append(stripped)
    return "\n".join(lines)
