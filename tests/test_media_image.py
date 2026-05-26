import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("PIL")

ROOT = Path(__file__).resolve().parent.parent


def _make_image(path: Path) -> None:
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (12, 8), (12, 16, 32))
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 5, 3), fill=(240, 150, 60))
    draw.rectangle((6, 0, 11, 7), fill=(245, 245, 230))
    draw.line((0, 7, 11, 0), fill=(40, 180, 220), width=2)
    image.save(path)


def _make_center_subject(path: Path) -> None:
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (48, 36), (5, 7, 12))
    draw = ImageDraw.Draw(image)
    draw.ellipse((16, 10, 31, 23), fill=(245, 190, 120))
    draw.rectangle((13, 22, 34, 34), fill=(230, 120, 50))
    image.save(path)


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


def test_image_chat_ascii_is_plain_text(tmp_path):
    image = tmp_path / "sample.png"
    _make_image(image)

    result = _run([
        "image",
        "--file",
        str(image),
        "--media-engine",
        "pillow",
        "--chat",
        "--width",
        "18",
        "--height",
        "8",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert "\x1b[" not in result.stdout
    assert result.stdout.strip()
    lines = result.stdout.rstrip("\n").splitlines()
    assert 1 <= len(lines) <= 8
    assert max(len(line) for line in lines) <= 18
    assert any(ch in result.stdout for ch in "#%@")


def test_image_pillow_half_color_uses_truecolor_ansi(tmp_path):
    image = tmp_path / "sample.png"
    _make_image(image)

    result = _run([
        "image",
        "--file",
        str(image),
        "--media-engine",
        "pillow",
        "--symbols",
        "half",
        "--width",
        "12",
        "--height",
        "6",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert "\x1b[38;2;" in result.stdout
    assert "▀" in result.stdout


def test_image_chat_output_file(tmp_path):
    image = tmp_path / "sample.png"
    output = tmp_path / "sample.txt"
    _make_image(image)

    result = _run([
        "image",
        "--file",
        str(image),
        "--media-engine",
        "pillow",
        "--chat",
        "--width",
        "18",
        "--height",
        "8",
        "--output",
        str(output),
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert result.stdout == ""
    rendered = output.read_text(encoding="utf-8")
    assert rendered.strip()
    assert "\x1b[" not in rendered


def test_image_chat_trims_background_by_default(tmp_path):
    image = tmp_path / "subject.png"
    _make_center_subject(image)

    trimmed = _run([
        "image",
        "--file",
        str(image),
        "--media-engine",
        "pillow",
        "--chat",
        "--image-style",
        "block",
        "--width",
        "24",
        "--height",
        "10",
        "--no-splash",
    ])
    untrimmed = _run([
        "image",
        "--file",
        str(image),
        "--media-engine",
        "pillow",
        "--chat",
        "--image-style",
        "block",
        "--no-trim",
        "--width",
        "24",
        "--height",
        "10",
        "--no-splash",
    ])

    assert trimmed.returncode == 0, trimmed.stderr
    assert untrimmed.returncode == 0, untrimmed.stderr
    assert trimmed.stdout.splitlines()[0].strip()
    assert max(len(line) for line in trimmed.stdout.splitlines()) < max(len(line) for line in untrimmed.stdout.splitlines())


def test_image_ascii_art_skill_styles_render(tmp_path):
    image = tmp_path / "sample.png"
    _make_image(image)

    styles = [
        "classic",
        "braille",
        "block",
        "edge",
        "dot-cross",
        "halftone",
        "particles",
        "retro-art",
        "terminal",
    ]
    for style in styles:
        result = _run([
            "image",
            "--file",
            str(image),
            "--media-engine",
            "pillow",
            "--chat",
            "--image-style",
            style,
            "--width",
            "24",
            "--height",
            "10",
            "--no-splash",
        ])

        assert result.returncode == 0, f"{style}: {result.stderr}"
        assert result.stdout.strip(), style


def test_image_color_modes_can_emit_ansi(tmp_path):
    image = tmp_path / "sample.png"
    _make_image(image)

    result = _run([
        "image",
        "--file",
        str(image),
        "--media-engine",
        "pillow",
        "--image-style",
        "terminal",
        "--color-mode",
        "matrix",
        "--width",
        "18",
        "--height",
        "8",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert "\x1b[38;2;" in result.stdout


def test_image_dither_ratio_and_exports(tmp_path):
    image = tmp_path / "sample.png"
    _make_image(image)

    for suffix in ("txt", "md", "html", "svg", "png", "gif", "tsx"):
        output = tmp_path / f"out.{suffix}"
        result = _run([
            "image",
            "--file",
            str(image),
            "--media-engine",
            "pillow",
            "--image-style",
            "retro-art",
            "--ratio",
            "1:1",
            "--dither",
            "atkinson",
            "--width",
            "24",
            "--height",
            "10",
            "--output",
            str(output),
            "--no-splash",
        ])

        assert result.returncode == 0, f"{suffix}: {result.stderr}"
        assert output.exists(), suffix
        assert output.stat().st_size > 0, suffix


def test_chafa_command_exposes_format_symbols_and_colors() -> None:
    from cli_charts.render.media_engine import _build_chafa_cmd

    cmd = _build_chafa_cmd(
        80,
        24,
        symbols="sextant",
        chafa_format="symbols",
        chafa_colors="256",
        chafa_args=["--dither=ordered"],
    )

    assert cmd[cmd.index("--format") + 1] == "symbols"
    assert cmd[cmd.index("--symbols") + 1] == "sextant"
    assert cmd[cmd.index("--colors") + 1] == "256"
    assert "--dither=ordered" in cmd


def test_chafa_command_chat_forces_symbols() -> None:
    from cli_charts.render.media_engine import _build_chafa_cmd

    cmd = _build_chafa_cmd(80, 24, chafa_format="kitty", chat=True)

    assert cmd[cmd.index("--format") + 1] == "symbols"


def test_chafa_auto_uses_windows_terminal_preview_sixels(monkeypatch: pytest.MonkeyPatch) -> None:
    from cli_charts.render import media_engine

    monkeypatch.delenv("GLYPH_ARTS_CHAFA_FORMAT", raising=False)
    monkeypatch.delenv("GLYPH_ARTS_FORMAT", raising=False)
    monkeypatch.setenv("GLYPH_ARTS_TERMINAL_PROFILE", "windows-terminal-preview")
    monkeypatch.setattr(media_engine.os, "isatty", lambda fd: fd == 1)

    assert media_engine._detect_chafa_format("auto") == "sixels"


def test_chafa_auto_keeps_warp_on_symbols(monkeypatch: pytest.MonkeyPatch) -> None:
    from cli_charts.render import media_engine

    monkeypatch.delenv("GLYPH_ARTS_CHAFA_FORMAT", raising=False)
    monkeypatch.delenv("GLYPH_ARTS_FORMAT", raising=False)
    monkeypatch.delenv("GLYPH_ARTS_TERMINAL_PROFILE", raising=False)
    monkeypatch.setenv("TERM_PROGRAM", "WarpTerminal")
    monkeypatch.setattr(media_engine.os, "isatty", lambda fd: fd == 1)

    assert media_engine._detect_chafa_format("auto") == "symbols"


def test_chafa_image_output_writes_captured_bytes(tmp_path, monkeypatch: pytest.MonkeyPatch) -> None:
    from cli_charts.render import media_engine

    image = tmp_path / "sample.png"
    output = tmp_path / "sample.ansi"
    _make_image(image)
    calls = {}

    def fake_run(cmd, **kwargs):
        calls["cmd"] = cmd
        calls["kwargs"] = kwargs
        return subprocess.CompletedProcess(cmd, 0, stdout=b"ART\n", stderr=b"")

    monkeypatch.setattr(media_engine.shutil, "which", lambda name: "chafa" if name == "chafa" else None)
    monkeypatch.setattr(media_engine.subprocess, "run", fake_run)

    rc = media_engine.render_image_chafa(
        str(image),
        32,
        12,
        symbols="braille",
        output=str(output),
        chafa_format="symbols",
        chafa_colors="full",
        chafa_args=["--stretch"],
    )

    assert rc == 0
    assert output.read_bytes() == b"ART\n"
    assert calls["kwargs"]["capture_output"] is True
    assert calls["cmd"][calls["cmd"].index("--colors") + 1] == "full"
    assert "--stretch" in calls["cmd"]
