import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _run(args, env=None):
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=30,
        env=merged_env,
    )


def test_chat_diagram_sequence_builtin_is_plain_text():
    result = _run([
        "chat",
        "diagram",
        "sequence",
        "--diagram-engine",
        "builtin",
        "--json",
        "Alice->Bob: Hello",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert "Alice -> Bob : Hello" in result.stdout
    assert "Sequence Diagram" in result.stdout
    assert "►" in result.stdout
    assert "\x1b[" not in result.stdout


def test_chat_sequence_alias_routes_to_diagram_builtin():
    result = _run([
        "chat",
        "sequence",
        "--diagram-engine",
        "builtin",
        "--json",
        "Client->Server: GET /",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert "Client -> Server : GET /" in result.stdout


def test_diagram_frame_builtin_writes_output(tmp_path):
    output = tmp_path / "frame.txt"

    result = _run([
        "diagram",
        "frame",
        "--diagram-engine",
        "builtin",
        "--json",
        "chat drawing",
        "--output",
        str(output),
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    rendered = output.read_text(encoding="utf-8")
    assert "chat drawing" in rendered
    assert rendered.startswith("┌")
    assert "Frame" in rendered
    assert "1 │ chat drawing" in rendered


def test_diagram_flowchart_builtin_splits_arrow_chain():
    result = _run([
        "chat",
        "diagram",
        "flowchart",
        "--diagram-engine",
        "builtin",
        "--json",
        "Capture -> Render -> Reply",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert "Capture" in result.stdout
    assert "Render" in result.stdout
    assert "Reply" in result.stdout
    assert "Render -> Reply" not in result.stdout


def test_diagram_note_builtin_has_equal_width_box():
    result = _run([
        "chat",
        "diagram",
        "note",
        "--diagram-engine",
        "builtin",
        "--json",
        "NOTE\nCache is not invalidated during batch operations.\nRefresh before reading results.",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert "NOTE" in result.stdout
    assert "Cache is not invalidated" in result.stdout
    lines = [line for line in result.stdout.splitlines() if line]
    assert len({len(line) for line in lines}) == 1


def test_diagram_note_builtin_handles_chinese_display_width():
    from cli_charts.render.text_layout import display_width

    result = _run([
        "chat",
        "diagram",
        "note",
        "--diagram-engine",
        "builtin",
        "--json",
        "注意\n中文排版要对齐。\n数学符号 αᵢ² 也要稳。",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert "中文排版" in result.stdout
    lines = [line for line in result.stdout.splitlines() if line]
    assert len({display_width(line) for line in lines}) == 1


def test_diagram_table_builtin_handles_chinese_cells():
    from cli_charts.render.text_layout import display_width

    result = _run([
        "chat",
        "diagram",
        "table",
        "--diagram-engine",
        "builtin",
        "--json",
        "指标|数值\n中文|42\nalpha|β",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert "指标" in result.stdout
    assert "┌" in result.stdout
    lines = [line for line in result.stdout.splitlines() if line]
    assert len({display_width(line) for line in lines}) == 1


def test_diagram_math_builtin_renders_unicode_math_without_diagon():
    result = _run([
        "chat",
        "diagram",
        "math",
        "--diagram-engine",
        "builtin",
        "--json",
        "alpha_i^2 + sqrt(x) + 1/2",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert "Math" in result.stdout
    assert "αᵢ²" in result.stdout
    assert "√(x)" in result.stdout
    assert "─" in result.stdout


def test_diagram_math_builtin_handles_integrals_arrows_and_infinity():
    result = _run([
        "chat",
        "diagram",
        "math",
        "--diagram-engine",
        "builtin",
        "--json",
        "int_0^infty e^{-x^2} dx = sqrt(pi)/2\nalpha + beta -> gamma",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert "∫₀∞" in result.stdout
    assert "e⁻ˣ²" in result.stdout
    assert "√(π)" in result.stdout
    assert "α + β → γ" in result.stdout
    assert "∞ty" not in result.stdout


def test_diagram_math_builtin_renders_matrix():
    result = _run([
        "chat",
        "diagram",
        "math",
        "--diagram-engine",
        "builtin",
        "--json",
        "matrix(alpha, beta; gamma, delta)",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert "⎡ α  β ⎤" in result.stdout
    assert "⎣ γ  δ ⎦" in result.stdout


def test_diagram_tree_builtin_parses_indentation():
    result = _run([
        "chat",
        "diagram",
        "tree",
        "--diagram-engine",
        "builtin",
        "--json",
        "app\n  cli\n    chart.py\n  render\n    diagram_engine.py",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert "└── app" in result.stdout
    assert "├── cli" in result.stdout
    assert "diagram_engine.py" in result.stdout
    assert "  cli" not in result.stdout


def test_diagram_sequence_builtin_supports_return_arrow():
    result = _run([
        "chat",
        "diagram",
        "sequence",
        "--diagram-engine",
        "builtin",
        "--json",
        "Client->Server: GET\nServer-->>Client: 200 OK",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert "Client -> Server : GET" in result.stdout
    assert "Server -> Client : 200 OK" in result.stdout
    assert "┄" in result.stdout


def test_diagram_flowchart_builtin_renders_branch_list():
    result = _run([
        "chat",
        "diagram",
        "flowchart",
        "--diagram-engine",
        "builtin",
        "--json",
        "Check -> Pass: ok\nCheck -> Fail: error\nPass -> Ship\nFail -> Fix",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert "Flowchart" in result.stdout
    assert "[Check]" in result.stdout
    assert "ok" in result.stdout
    assert "error" in result.stdout
    assert "→ [Pass]" in result.stdout


def test_diagram_core_capabilities_list_diagon_generators():
    from cli_charts.render.diagram_engine import diagram_capabilities

    caps = diagram_capabilities()
    assert [cap["diagon"] for cap in caps] == [
        "Math",
        "Sequence",
        "Tree",
        "Table",
        "Frame",
        "Flowchart",
        "GraphDAG",
        "GraphPlanar",
    ]
    assert all(cap["builtin"] is True for cap in caps)


def test_diagram_graphplanar_builtin() -> None:
    result = _run([
        "chat",
        "diagram",
        "graphplanar",
        "--diagram-engine",
        "builtin",
        "--json",
        "A -- B\nB -- C\nC -- D\nD -- A",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert "GraphPlanar" in result.stdout
    assert "A -- B" in result.stdout


def test_diagram_graphdag_builtin_layers() -> None:
    result = _run([
        "chat",
        "diagram",
        "graphdag",
        "--diagram-engine",
        "builtin",
        "--json",
        "Plan -> Build\nPlan -> Test\nBuild -> Ship\nTest -> Ship",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert "GraphDAG" in result.stdout
    assert "Plan -> Build" in result.stdout
    assert "▼" in result.stdout


def test_diagram_can_call_external_diagon(tmp_path):
    fake = tmp_path / "diagon.cmd"
    fake.write_text("@echo off\r\necho external-%1\r\n", encoding="utf-8")

    result = _run([
        "diagram",
        "math",
        "--diagram-engine",
        "diagon",
        "--json",
        "1+1",
        "--no-splash",
    ], env={"GLYPH_ARTS_DIAGON": str(fake)})

    assert result.returncode == 0, result.stderr
    assert "external-Math" in result.stdout
