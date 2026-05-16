"""Phase 3 tests for multi-format --output export."""

import importlib.util
import inspect
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
DATA = '{"labels":["A","B"],"values":[1,2]}'
OUT_DIR = ROOT / "export_test_outputs"


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        cwd=ROOT,
    )


def _output(name: str) -> Path:
    OUT_DIR.mkdir(exist_ok=True)
    path = OUT_DIR / name
    if path.exists():
        path.unlink()
    return path


@pytest.mark.skipif(
    importlib.util.find_spec("matplotlib") is None or shutil.which("chafa") is None,
    reason="matplotlib or chafa not installed",
)
def test_output_png_unchanged() -> None:
    output = _output("out.png")
    result = _run([
        "bar",
        "--engine",
        "pixel",
        "--json",
        DATA,
        "--width",
        "40",
        "--height",
        "10",
        "--output",
        str(output),
    ])

    assert result.returncode == 0, result.stderr
    assert output.exists()
    assert output.stat().st_size > 0


def test_output_txt_strips_ansi() -> None:
    output = _output("out.txt")
    result = _run(["bar", "--json", DATA, "--output", str(output)])

    assert result.returncode == 0, result.stderr
    assert "\x1b" not in output.read_text(encoding="utf-8")


def test_output_ansi_keeps_escape() -> None:
    output = _output("out.ansi")
    result = _run(["bar", "--json", DATA, "--output", str(output)])

    assert result.returncode == 0, result.stderr
    assert "\x1b" in output.read_text(encoding="utf-8")


def test_output_html_wraps_pre() -> None:
    output = _output("wraps.html")
    result = _run(["bar", "--json", DATA, "--output", str(output)])
    rendered = output.read_text(encoding="utf-8")

    assert result.returncode == 0, result.stderr
    assert "<pre" in rendered
    assert '<span style="color:#' in rendered


def test_output_html_strips_ansi_codes() -> None:
    output = _output("strips.html")
    result = _run(["bar", "--json", DATA, "--output", str(output)])

    assert result.returncode == 0, result.stderr
    assert "\x1b" not in output.read_text(encoding="utf-8")


def test_unknown_extension_errors() -> None:
    output = _output("out.xyz")
    result = _run(["bar", "--json", DATA, "--output", str(output)])

    assert result.returncode != 0
    assert "ERROR:" in result.stderr


def test_no_color_html_uses_default_palette() -> None:
    output = _output("no-color.html")
    result = _run(["bar", "--json", DATA, "--no-color", "--output", str(output)])
    rendered = output.read_text(encoding="utf-8")

    assert result.returncode == 0, result.stderr
    assert '<span style="color:#' not in rendered


def test_export_to_path_signature() -> None:
    from cli_charts.render.export_engine import export_to_path

    assert callable(export_to_path)
    assert list(inspect.signature(export_to_path).parameters) == [
        "content",
        "path",
        "no_color",
    ]
