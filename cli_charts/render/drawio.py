"""draw.io XML generation and validation helpers."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path
from xml.etree import ElementTree as ET
from xml.sax.saxutils import escape


class DrawioValidationError(ValueError):
    """Raised when draw.io XML cannot be normalized safely."""


@dataclass(frozen=True)
class DrawioDocument:
    xml: str
    graph_model: str
    cells: str


_ARROW_RE = re.compile(r"\s*(<->|-->|->|=>|--)\s*")
_BARE_AMP_RE = re.compile(r"&(?!(?:lt|gt|amp|quot|apos|#[0-9]+|#x[0-9a-fA-F]+);)")


def render_drawio(
    source: str,
    *,
    output: str | None = None,
    fragment: bool = False,
    graph_model: bool = False,
    validate_only: bool = False,
) -> int:
    """Render text/XML input as draw.io XML and optionally write it to disk."""
    doc = drawio_document(source)
    rendered = doc.cells if fragment else doc.graph_model if graph_model else doc.xml
    if validate_only:
        rendered = "drawio: valid\n"
    if output:
        Path(output).write_text(rendered.rstrip("\n") + "\n", encoding="utf-8")
    else:
        print(rendered.rstrip("\n"))
    return 0


def drawio_document(source: str) -> DrawioDocument:
    text = _auto_fix_xml_text(source.strip())
    if not text:
        raise DrawioValidationError("draw.io input must not be empty")
    if _looks_like_drawio_xml(text):
        doc = _normalize_xml_document(text)
    else:
        doc = _document_from_text(text)
    validate_drawio_xml(doc.xml)
    return doc


def extract_mxgraph_model(source: str) -> str:
    """Return mxGraphModel XML for MCP servers that reject mxfile wrappers."""
    return drawio_document(source).graph_model


def validate_drawio_xml(xml: str, *, fragment: bool = False) -> None:
    """Validate common draw.io XML invariants.

    The checks mirror the practical constraints from Next AI Draw.io's MCP tool:
    unique mxCell IDs, sibling cells, valid XML syntax, and known source/target
    references for full documents.
    """
    text = xml.strip()
    if not text:
        raise DrawioValidationError("draw.io XML is empty")
    try:
        root = ET.fromstring(f"<wrapper>{text}</wrapper>" if fragment else text)
    except ET.ParseError as exc:
        raise DrawioValidationError(f"invalid XML: {exc}") from exc

    cells = [element for element in root.iter() if _tag(element) == "mxCell"]
    if not cells:
        raise DrawioValidationError("draw.io XML must contain at least one mxCell")

    ids: list[str] = []
    for cell in cells:
        cell_id = (cell.attrib.get("id") or "").strip()
        if not cell_id:
            raise DrawioValidationError("mxCell elements must have non-empty id attributes")
        ids.append(cell_id)
        for child in cell:
            if _tag(child) == "mxCell":
                raise DrawioValidationError("mxCell elements must be siblings, not nested")
    duplicates = sorted({cell_id for cell_id in ids if ids.count(cell_id) > 1})
    if duplicates:
        raise DrawioValidationError(f"duplicate mxCell id(s): {', '.join(duplicates[:5])}")

    id_set = set(ids)
    if not fragment:
        if _find_first(root, "mxGraphModel") is None:
            raise DrawioValidationError("full draw.io XML needs an mxGraphModel")
        if _find_first(root, "root") is None:
            raise DrawioValidationError("full draw.io XML needs a root element")
        if "0" not in id_set or "1" not in id_set:
            raise DrawioValidationError('full draw.io XML needs root cells id="0" and id="1"')

    allowed_external_parents = {"1"} if fragment else set()
    for cell in cells:
        for attr in ("parent", "source", "target"):
            ref = cell.attrib.get(attr)
            if ref and ref not in id_set and ref not in allowed_external_parents:
                raise DrawioValidationError(f'mxCell id="{cell.attrib.get("id")}" references missing {attr}="{ref}"')


def _document_from_text(source: str) -> DrawioDocument:
    nodes, edges = _parse_text_graph(source)
    cells = _cells_from_graph(nodes, edges)
    return _wrap_cells(cells)


def _normalize_xml_document(source: str) -> DrawioDocument:
    if source.lstrip().startswith("<mxfile"):
        root = ET.fromstring(source)
        model = _find_first(root, "mxGraphModel")
        if model is None:
            raise DrawioValidationError("mxfile does not contain mxGraphModel")
        graph_model = _serialize(model)
        root_el = _find_first(model, "root")
        if root_el is None:
            raise DrawioValidationError("mxGraphModel does not contain root")
        cells = "\n".join(_serialize(cell) for cell in root_el if _tag(cell) == "mxCell" and cell.attrib.get("id") not in {"0", "1"})
        return DrawioDocument(_mxfile(graph_model), graph_model, cells)

    if source.lstrip().startswith("<mxGraphModel"):
        model = ET.fromstring(source)
        if _tag(model) != "mxGraphModel":
            raise DrawioValidationError("expected mxGraphModel root")
        graph_model = _serialize(model)
        root_el = _find_first(model, "root")
        if root_el is None:
            raise DrawioValidationError("mxGraphModel does not contain root")
        cells = "\n".join(_serialize(cell) for cell in root_el if _tag(cell) == "mxCell" and cell.attrib.get("id") not in {"0", "1"})
        return DrawioDocument(_mxfile(graph_model), graph_model, cells)

    if "<mxCell" in source:
        validate_drawio_xml(source, fragment=True)
        return _wrap_cells(source)

    raise DrawioValidationError("draw.io XML must start with mxfile, mxGraphModel, or mxCell")


def _parse_text_graph(source: str) -> tuple[list[str], list[tuple[str, str, str, str]]]:
    nodes: list[str] = []
    edges: list[tuple[str, str, str, str]] = []

    def add_node(label: str) -> str:
        clean = label.strip()
        if clean and clean not in nodes:
            nodes.append(clean)
        return clean

    for raw in source.replace("\\n", "\n").splitlines():
        line = raw.strip()
        if not line:
            continue
        parts = _ARROW_RE.split(line)
        if len(parts) < 3:
            add_node(line)
            continue
        labels = parts[::2]
        arrows = parts[1::2]
        edge_label = ""
        if ":" in labels[-1]:
            labels[-1], edge_label = [part.strip() for part in labels[-1].split(":", 1)]
        for index, arrow in enumerate(arrows):
            source_label = add_node(labels[index])
            target_label = add_node(labels[index + 1])
            if source_label and target_label:
                label = edge_label if index == len(arrows) - 1 else ""
                edges.append((source_label, target_label, arrow, label))

    if not nodes:
        nodes = ["Diagram"]
    return nodes, edges


def _cells_from_graph(nodes: list[str], edges: list[tuple[str, str, str, str]]) -> str:
    id_by_label = {label: f"n{index + 1}" for index, label in enumerate(nodes)}
    out: list[str] = []
    for index, label in enumerate(nodes):
        x = 40 + (index % 4) * 190
        y = 40 + (index // 4) * 120
        width = max(120, min(220, 34 + len(label) * 8))
        out.append(_vertex_cell(id_by_label[label], label, x, y, width, 60))
    for index, (source, target, arrow, label) in enumerate(edges):
        out.append(_edge_cell(f"e{index + 1}", id_by_label[source], id_by_label[target], arrow, label))
    return "\n".join(out)


def _vertex_cell(cell_id: str, label: str, x: int, y: int, width: int, height: int) -> str:
    return (
        f'<mxCell id="{cell_id}" value="{_attr(label)}" '
        'style="rounded=1;whiteSpace=wrap;html=1;fillColor=#f8fafc;strokeColor=#475569;fontColor=#0f172a;" '
        'vertex="1" parent="1">\n'
        f'  <mxGeometry x="{x}" y="{y}" width="{width}" height="{height}" as="geometry"/>\n'
        "</mxCell>"
    )


def _edge_cell(cell_id: str, source: str, target: str, arrow: str, label: str) -> str:
    if arrow == "--":
        arrow_style = "endArrow=none;"
    elif arrow == "<->":
        arrow_style = "startArrow=classic;endArrow=classic;"
    else:
        arrow_style = "endArrow=classic;"
    return (
        f'<mxCell id="{cell_id}" value="{_attr(label)}" '
        f'style="edgeStyle=orthogonalEdgeStyle;rounded=0;orthogonalLoop=1;jettySize=auto;html=1;{arrow_style}strokeColor=#64748b;" '
        f'edge="1" parent="1" source="{_attr(source)}" target="{_attr(target)}">\n'
        '  <mxGeometry relative="1" as="geometry"/>\n'
        "</mxCell>"
    )


def _wrap_cells(cells: str) -> DrawioDocument:
    cell_text = cells.strip()
    graph_model = (
        '<mxGraphModel dx="1200" dy="800" grid="1" gridSize="10" guides="1" tooltips="1" '
        'connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="850" pageHeight="1100" '
        'math="0" shadow="0">\n'
        "  <root>\n"
        '    <mxCell id="0"/>\n'
        '    <mxCell id="1" parent="0"/>\n'
        f"{_indent(cell_text, 4)}\n"
        "  </root>\n"
        "</mxGraphModel>"
    )
    return DrawioDocument(_mxfile(graph_model), graph_model, cell_text)


def _mxfile(graph_model: str) -> str:
    return (
        '<mxfile host="glyph-arts" agent="glyph-arts" version="24.0.0">\n'
        '  <diagram id="glyph-arts-diagram" name="Page-1">\n'
        f"{_indent(graph_model, 4)}\n"
        "  </diagram>\n"
        "</mxfile>"
    )


def _auto_fix_xml_text(source: str) -> str:
    text = source.strip()
    if text.startswith("<![CDATA[") and text.endswith("]]>"):
        text = text[len("<![CDATA["):-len("]]>")].strip()
    if r"\"" in text:
        text = text.replace(r"\"", '"').replace(r"\n", "\n")
    if "<Cell" in text or "</Cell" in text:
        text = re.sub(r"<Cell(\s|>)", r"<mxCell\1", text)
        text = text.replace("</Cell>", "</mxCell>")
    if _looks_like_drawio_xml(text):
        text = _BARE_AMP_RE.sub("&amp;", text)
    return text


def _looks_like_drawio_xml(source: str) -> bool:
    stripped = source.lstrip()
    return stripped.startswith("<mxfile") or stripped.startswith("<mxGraphModel") or "<mxCell" in stripped


def _serialize(element: ET.Element) -> str:
    ET.indent(element, space="  ")
    return ET.tostring(element, encoding="unicode", short_empty_elements=True)


def _find_first(root: ET.Element, name: str) -> ET.Element | None:
    for element in root.iter():
        if _tag(element) == name:
            return element
    return None


def _tag(element: ET.Element) -> str:
    return element.tag.rsplit("}", 1)[-1]


def _attr(value: str) -> str:
    return escape(str(value), {'"': "&quot;"})


def _indent(text: str, spaces: int) -> str:
    prefix = " " * spaces
    return "\n".join(prefix + line if line else line for line in text.splitlines())
