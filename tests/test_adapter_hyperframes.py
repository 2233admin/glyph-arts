import inspect
import json
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SERIES_JSON = '[{"label":"x","x":[1,2,3,4,5],"y":[10,20,15,30,25]}]'


def _tmp_dir():
    path = ROOT / "_temp" / f"hyperframes-{uuid.uuid4().hex}"
    path.mkdir(parents=True)
    return path


def _run(args):
    return subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", *args],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(ROOT),
    )


def test_to_hyperframes_signature():
    from cli_charts.adapters.hyperframes import to_hyperframes
    from cli_charts.chart import CMDS

    assert callable(to_hyperframes)
    params = list(inspect.signature(to_hyperframes).parameters)
    assert params[:4] == ["series_json", "frames", "duration_s", "output_dir"]
    assert "to-hyperframes" in CMDS


def test_to_hyperframes_creates_frame_pngs():
    tmp_path = _tmp_dir()
    result = _run([
        "to-hyperframes",
        "--json",
        SERIES_JSON,
        "--frames",
        "5",
        "--duration",
        "2",
        "--output-dir",
        str(tmp_path),
    ])

    assert result.returncode == 0, result.stderr
    frames = sorted(tmp_path.glob("frame_*.png"))
    assert [frame.name for frame in frames] == [f"frame_{i:03d}.png" for i in range(1, 6)]
    assert all(frame.stat().st_size > 0 for frame in frames)


def test_to_hyperframes_creates_manifest_json():
    tmp_path = _tmp_dir()
    result = _run([
        "to-hyperframes",
        "--json",
        SERIES_JSON,
        "--frames",
        "5",
        "--duration",
        "2",
        "--output-dir",
        str(tmp_path),
    ])

    assert result.returncode == 0, result.stderr
    manifest = json.loads((tmp_path / "manifest.json").read_text())
    assert manifest == {
        "version": "1.0",
        "frames": 5,
        "duration_ms": 2000,
        "fps": 2,
        "tracks": [
            {
                "type": "image-sequence",
                "files": [f"frame_{i:03d}.png" for i in range(1, 6)],
            }
        ],
    }


def test_to_hyperframes_creates_composition_html():
    tmp_path = _tmp_dir()
    result = _run([
        "to-hyperframes",
        "--json",
        SERIES_JSON,
        "--frames",
        "5",
        "--duration",
        "2",
        "--output-dir",
        str(tmp_path),
    ])

    assert result.returncode == 0, result.stderr
    html = (tmp_path / "composition.html").read_text()
    assert "data-hyperframes-composition" in html
    assert "data-track='image-sequence'" in html
    assert "data-frames='5'" in html
    assert "data-duration='2000'" in html
    assert html.count("<img ") == 5
    assert "src='frame_001.png' data-time='0'" in html
    assert "src='frame_005.png' data-time='1600'" in html


def test_to_hyperframes_invalid_data_returns_1():
    tmp_path = _tmp_dir()
    result = _run([
        "to-hyperframes",
        "--json",
        '{"label":"bad","y":["nope"]}',
        "--frames",
        "3",
        "--duration",
        "1",
        "--output-dir",
        str(tmp_path),
    ])

    assert result.returncode == 1
    assert "ERROR:schema:" in result.stderr


def test_to_hyperframes_help_no_crash():
    result = _run(["to-hyperframes", "--help"])

    assert result.returncode == 0
    assert "--output-dir" in result.stdout
