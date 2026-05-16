"""Phase 2 tests for the composable art command."""

import inspect
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(args):
    return subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        cwd=ROOT,
    )


def test_render_art_signature():
    from cli_charts.render.art_engine import ART_FONTS, ART_FRAMES, ART_GRADIENTS, render_art

    assert ART_FONTS
    assert "sunset" in ART_GRADIENTS
    assert "double" in ART_FRAMES
    sig = inspect.signature(render_art)
    assert list(sig.parameters) == [
        "text",
        "font",
        "decor",
        "frame",
        "gradient",
        "theme",
        "w",
        "h",
        "no_color",
        "output",
        "justify",
        "anim",
    ]


def test_art_basic_text_exit0():
    result = _run(["art", "HI", "--font", "slant"])
    assert result.returncode == 0
    assert len(result.stdout.strip().splitlines()) > 1


def test_art_empty_text_returns_1():
    result = _run(["art", "", "--font", "slant"])
    assert result.returncode == 1
    assert "ERROR:schema:" in result.stderr


def test_art_unknown_font_returns_1():
    result = _run(["art", "HI", "--font", "bogus_font"])
    assert result.returncode == 1
    assert "unknown font bogus_font" in result.stderr


def test_art_dep_missing_returns_2(monkeypatch):
    import cli_charts.render.art_engine as art_engine

    monkeypatch.setattr(art_engine, "_HAS_ART", False)
    # Use an art library decor (heart1 is in art.DECORATION_NAMES)
    rc = art_engine.render_art("HI", "slant", "heart1", None, None, "pro", 80, 20, False, "", None, False)
    assert rc == 2


def test_art_frame_double_in_output():
    result = _run(["art", "X", "--font", "slant", "--frame", "double"])
    assert result.returncode == 0
    assert "╔" in result.stdout or "═" in result.stdout


def test_art_no_color_no_ansi():
    result = _run(["art", "X", "--font", "slant", "--gradient", "sunset", "--no-color"])
    assert result.returncode == 0
    assert not re.search(r"\x1b\[[0-9;]*m", result.stdout)


def test_art_gradient_with_color_has_ansi():
    result = _run(["art", "X", "--font", "slant", "--gradient", "sunset"])
    assert result.returncode == 0
    assert re.search(r"\x1b\[[0-9;]*m", result.stdout)


def test_art_output_file_written():
    output = ROOT / "art_output_test.txt"
    if output.exists():
        output.unlink()
    result = _run(["art", "X", "--font", "slant", "--output", str(output)])
    assert result.returncode == 0
    assert output.exists()
    assert output.read_text(encoding="utf-8").strip()
    output.unlink()


def test_art_in_engine_choices():
    result = _run(["art", "--help"])
    assert result.returncode == 0
    assert "--font" in result.stdout
