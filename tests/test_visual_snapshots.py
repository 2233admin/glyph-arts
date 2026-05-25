import json
import subprocess
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parent.parent
GOLDEN = ROOT / "tests" / "golden"


def _normalize(text: str) -> str:
    lines = text.replace("\r\n", "\n").splitlines()
    return "\n".join(line.rstrip() for line in lines).strip() + "\n"


def _golden(name: str) -> str:
    return _normalize((GOLDEN / name).read_text(encoding="utf-8"))


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


def test_portrait_ascii_snapshot(tmp_path):
    pytest.importorskip("PIL")
    from PIL import Image, ImageDraw

    image = Image.new("RGB", (48, 48), (4, 6, 12))
    draw = ImageDraw.Draw(image)
    draw.ellipse((16, 6, 31, 21), fill=(245, 190, 128))
    draw.rectangle((12, 20, 35, 42), fill=(216, 104, 48))
    draw.rectangle((18, 22, 29, 42), fill=(238, 232, 210))
    draw.ellipse((20, 12, 23, 15), fill=(24, 16, 16))
    draw.ellipse((26, 12, 29, 15), fill=(24, 16, 16))
    draw.arc((20, 13, 29, 20), 0, 180, fill=(120, 50, 40), width=1)

    path = tmp_path / "portrait.png"
    image.save(path)

    result = _run([
        "image",
        "--file",
        str(path),
        "--media-engine",
        "pillow",
        "--chat",
        "--image-style",
        "block",
        "--width",
        "32",
        "--height",
        "12",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert _normalize(result.stdout) == _golden("portrait_block.txt")


def test_sdr_spectrum_snapshot():
    data = {
        "freq": [99.0, 99.05, 99.1, 99.15, 99.2, 99.25, 99.3, 99.35, 99.4, 99.45, 99.5, 99.55, 99.6],
        "power": [-93, -92, -90, -84, -72, -55, -42, -56, -70, -84, -90, -92, -93],
        "center": 99.3,
        "bandwidth": 0.2,
    }
    result = _run([
        "spectrum",
        "--json",
        json.dumps(data),
        "--width",
        "64",
        "--height",
        "16",
        "--no-color",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert _normalize(result.stdout) == _golden("sdr_spectrum.txt")


def test_sdr_waterfall_snapshot():
    data = {
        "matrix": [
            [-94, -92, -84, -65, -48, -44, -55, -78, -91, -94],
            [-94, -88, -76, -58, -45, -42, -49, -69, -86, -94],
            [-94, -91, -82, -61, -43, -44, -58, -80, -90, -94],
            [-94, -93, -86, -70, -52, -45, -48, -64, -84, -93],
        ],
        "xlabels": ["99.0", "99.6"],
        "ylabels": ["t-3", "t-2", "t-1", "now"],
        "min": -94,
        "max": -42,
    }
    result = _run([
        "waterfall",
        "--json",
        json.dumps(data),
        "--width",
        "64",
        "--height",
        "12",
        "--no-color",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert _normalize(result.stdout) == _golden("sdr_waterfall.txt")
