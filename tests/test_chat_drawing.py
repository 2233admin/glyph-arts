import json
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip("PIL")

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


def _make_image(path: Path) -> None:
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (24, 18), (4, 6, 12))
    draw = ImageDraw.Draw(image)
    draw.ellipse((8, 3, 15, 10), fill=(245, 190, 128))
    draw.rectangle((6, 10, 17, 16), fill=(216, 104, 48))
    image.save(path)


def test_chat_image_alias_is_plain_text(tmp_path):
    image = tmp_path / "subject.png"
    _make_image(image)

    result = _run([
        "chat",
        "image",
        "--file",
        str(image),
        "--image-style",
        "block",
        "--width",
        "24",
        "--height",
        "8",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip()
    assert "\x1b[" not in result.stdout


def test_chat_infers_image_path(tmp_path):
    image = tmp_path / "subject.png"
    _make_image(image)

    result = _run([
        "chat",
        str(image),
        "--image-style",
        "block",
        "--width",
        "24",
        "--height",
        "8",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip()
    assert "\x1b[" not in result.stdout


def test_chat_sdr_spectrum_alias_is_chat_safe():
    data = {
        "freq": [99.0, 99.15, 99.3, 99.45, 99.6],
        "power": [-93, -80, -42, -82, -93],
        "center": 99.3,
        "bandwidth": 0.2,
    }

    result = _run([
        "chat",
        "sdr",
        "spectrum",
        "--json",
        json.dumps(data),
        "--width",
        "60",
        "--height",
        "14",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert "RF-Spectrum" in result.stdout
    assert "center=99.3" in result.stdout
    assert "\x1b[" not in result.stdout
