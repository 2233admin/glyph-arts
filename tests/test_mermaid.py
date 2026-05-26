from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", *args],
        cwd=ROOT,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        check=False,
    )


def test_chat_mermaid_flowchart_unicode() -> None:
    src = "graph LR\n  A[开始] -->|是| B{判断}\n  B --> C[结束]"
    result = _run(["chat", "mermaid", "--json", src, "--width", "90"])
    assert result.returncode == 0, result.stderr
    assert "开始" in result.stdout
    assert "判断" in result.stdout
    assert "────►" in result.stdout
    assert "\x1b[" not in result.stdout


def test_mermaid_sequence_ascii_mode() -> None:
    src = "sequenceDiagram\n  Alice->>Bob: Hello\n  Bob-->>Alice: Hi"
    result = _run(["mermaid", "--mermaid-ascii", "--json", src])
    assert result.returncode == 0, result.stderr
    assert "Mermaid Sequence" in result.stdout
    assert "Alice --> Bob : Hello" in result.stdout
    assert "Bob <-- Alice : Hi" in result.stdout
    assert "+" in result.stdout


def test_mermaid_state_class_er_and_xychart() -> None:
    samples = [
        ("stateDiagram-v2\n  Idle --> Processing: start", "State"),
        ("classDiagram\n  Animal <|-- Duck\n  Animal: +int age", "Mermaid Class"),
        ("erDiagram\n  CUSTOMER ||--o{ ORDER : places", "ER Diagram"),
        ('xychart-beta\n  title "Revenue"\n  x-axis [Jan, Feb]\n  bar [10, 20]', "Revenue"),
    ]
    for src, marker in samples:
        result = _run(["mermaid", "--json", src, "--width", "80"])
        assert result.returncode == 0, result.stderr
        assert marker in result.stdout


def test_mermaid_xychart_combined_has_rounded_bars_line_and_legend() -> None:
    src = 'xychart-beta\n  title "Sales"\n  x-axis [Jan, Feb, Mar]\n  bar [10, 20, 15]\n  line [8, 18, 22]'
    result = _run(["mermaid", "--json", src, "--width", "80"])
    assert result.returncode == 0, result.stderr
    assert "Sales" in result.stdout
    assert "╭" in result.stdout
    assert "legend" in result.stdout
    assert "█ bar" in result.stdout
    assert "╭ line" in result.stdout


def test_mermaid_xychart_horizontal() -> None:
    src = 'xychart-beta horizontal\n  title "语言热度"\n  x-axis [Python, JavaScript, Rust]\n  bar [30, 25, 18]\n  line [28, 26, 20]'
    result = _run(["chat", "mermaid", "--json", src, "--width", "88"])
    assert result.returncode == 0, result.stderr
    assert "语言热度" in result.stdout
    assert "Python" in result.stdout
    assert "●" in result.stdout
    assert "legend" in result.stdout


def test_mermaid_capability_is_documented() -> None:
    manifest = (ROOT / "docs" / "chat_drawing_capabilities.json").read_text(encoding="utf-8")
    assert "mermaid" in manifest
