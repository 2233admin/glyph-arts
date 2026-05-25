import subprocess
import sys
from pathlib import Path

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


def test_chat_graph_accepts_edge_list_text():
    result = _run([
        "chat",
        "graph",
        "--json",
        "A -> B\nB -> C",
        "--graph-charset",
        "ascii",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert "(A)" in result.stdout
    assert "(B)" in result.stdout
    assert "(C)" in result.stdout
    assert "\x1b[" not in result.stdout


def test_chat_graph_accepts_simple_dot_without_pydot():
    result = _run([
        "chat",
        "graph",
        "--graph-format",
        "dot",
        "--json",
        "digraph { A -> B; B -> C; }",
        "--graph-charset",
        "ascii",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert "(A)" in result.stdout
    assert "(C)" in result.stdout


def test_graph_can_write_output_file(tmp_path):
    output = tmp_path / "graph.txt"
    result = _run([
        "graph",
        "--json",
        "A -> B",
        "--graph-charset",
        "ascii",
        "--output",
        str(output),
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    assert "(A)" in output.read_text(encoding="utf-8")
