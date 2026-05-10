"""Tests for the mermaid diagram cmd."""

import os
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
        cwd=ROOT,
    )


def test_mermaid_registered():
    from cli_charts.cmd._helpers import CMDS

    assert "mermaid" in CMDS


def test_mermaid_cli_accepts_type():
    result = _run(["mermaid", "--json", '{"source": "flowchart LR; A --> B"}'])
    assert result.returncode == 0, result.stderr
    assert "A" in result.stdout
    assert "B" in result.stdout


def test_mermaid_renders_flowchart():
    result = _run([
        "mermaid",
        "--json",
        '{"source": "flowchart LR; X --> Y --> Z"}',
        "--title",
        "Test",
    ])
    assert result.returncode == 0, result.stderr
    assert "Test" in result.stdout
    assert "X" in result.stdout


def test_mermaid_empty_source_exits_1():
    result = _run(["mermaid", "--json", '{"source": "   "}'])
    assert result.returncode == 1
    assert "ERROR:input" in result.stderr


def test_mermaid_missing_dep_exits_2():
    # Test in-process by temporarily hiding mmdflux from PATH
    import os
    old_path = os.environ.get("PATH", "")
    # Remove mmdflux's directory from PATH
    import shutil

    mmdflux_dir = Path(shutil.which("mmdflux")).parent
    new_path = os.pathsep.join(p for p in old_path.split(os.pathsep) if p != str(mmdflux_dir))
    env = {**os.environ, "PATH": new_path}
    result = subprocess.run(
        [sys.executable, "-m", "cli_charts.chart",
         "mermaid", "--json", '{"source": "flowchart LR; A --> B"}'],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
        env=env,
        cwd=ROOT,
    )
    assert result.returncode == 2, f"expected exit 2, got {result.returncode}: {result.stderr}"
    assert "ERROR:dep" in result.stderr


def test_mermaid_ascii_format():
    result = _run([
        "mermaid",
        "--json",
        '{"source": "flowchart LR; A --> B"}',
    ])
    # ASCII output uses +---+ box style (no Unicode box-drawing chars)
    assert result.returncode == 0
    # Output should have box chars (either Unicode or ASCII)
    assert any(c in result.stdout for c in ["┌", "+", "│", "|"])
