import subprocess
import sys
from pathlib import Path

import pytest

from cli_charts.render.drawio import DrawioValidationError, drawio_document, extract_mxgraph_model, validate_drawio_xml

ROOT = Path(__file__).resolve().parent.parent


def _run(args):
    return subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
    )


def test_diagram_drawio_generates_full_drawio_xml():
    result = _run(["diagram", "drawio", "--json", "Client -> API -> DB: query", "--no-splash"])

    assert result.returncode == 0, result.stderr
    assert "<mxfile" in result.stdout
    assert "<mxGraphModel" in result.stdout
    assert "Client" in result.stdout
    assert "API" in result.stdout
    assert "query" in result.stdout
    validate_drawio_xml(result.stdout)


def test_diagram_drawio_can_write_output(tmp_path):
    output = tmp_path / "architecture.drawio"

    result = _run(["diagram", "drawio", "--json", "A -> B", "--output", str(output), "--no-splash"])

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    text = output.read_text(encoding="utf-8")
    assert text.startswith("<mxfile")
    validate_drawio_xml(text)


def test_diagram_drawio_fragment_outputs_mcp_cells_only():
    result = _run(["diagram", "drawio", "--drawio-fragment", "--json", "A -> B", "--no-splash"])

    assert result.returncode == 0, result.stderr
    assert "<mxCell" in result.stdout
    assert "<mxfile" not in result.stdout
    assert 'id="0"' not in result.stdout
    validate_drawio_xml(result.stdout, fragment=True)


def test_diagram_drawio_graph_model_output_for_mcp_create():
    result = _run(["diagram", "drawio", "--drawio-graph-model", "--json", "A -> B", "--no-splash"])

    assert result.returncode == 0, result.stderr
    assert result.stdout.lstrip().startswith("<mxGraphModel")
    assert "<mxfile" not in result.stdout
    validate_drawio_xml(result.stdout)


def test_drawio_document_wraps_existing_mxcell_fragment():
    fragment = '<mxCell id="2" value="A & B" vertex="1" parent="1"><mxGeometry as="geometry"/></mxCell>'

    doc = drawio_document(fragment)

    assert "A &amp; B" in doc.xml
    assert doc.graph_model.startswith("<mxGraphModel")
    validate_drawio_xml(doc.xml)


def test_extract_mxgraph_model_removes_mxfile_wrapper():
    model = extract_mxgraph_model("A -> B")

    assert model.startswith("<mxGraphModel")
    assert "<mxfile" not in model


def test_drawio_validator_rejects_duplicate_ids():
    duplicate = """
<mxGraphModel>
  <root>
    <mxCell id="0"/>
    <mxCell id="1" parent="0"/>
    <mxCell id="2" value="A" vertex="1" parent="1"/>
    <mxCell id="2" value="B" vertex="1" parent="1"/>
  </root>
</mxGraphModel>
"""

    with pytest.raises(DrawioValidationError, match="duplicate"):
        validate_drawio_xml(duplicate)
