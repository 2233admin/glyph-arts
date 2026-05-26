import json
import os
import subprocess
import sys
from pathlib import Path

SCRIPT = Path(__file__).parent.parent / "scripts" / "chart.py"


def _run(chart_type: str, payload: dict, *extra: str) -> subprocess.CompletedProcess:
    return subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            chart_type,
            "--json",
            json.dumps(payload),
            "--no-color",
            "--width",
            "60",
            "--height",
            "12",
            *extra,
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )


def test_spectrum_renders_fft_payload():
    payload = {
        "freq": [99.1, 99.2, 99.3, 99.4],
        "db": [-80, -45, -72, -60],
        "avg": [-82, -60, -70, -65],
        "max_hold": [-78, -42, -68, -58],
        "noise_floor": -79,
        "squelch": -62,
        "center": 99.2,
        "bandwidth": 0.2,
        "vfo": 99.3,
        "signals": [{"freq": 99.2, "label": "FM"}],
        "peaks": [99.2],
    }
    result = _run("spectrum", payload)
    assert result.returncode == 0, result.stderr
    assert "center=99.2" in result.stdout
    assert "vfo=99.3" in result.stdout
    assert "FM@99.2" in result.stdout
    assert "avg" in result.stdout
    assert "hold" in result.stdout
    assert "99.1" in result.stdout
    assert "99.4" in result.stdout


def test_waterfall_renders_spectrogram_payload():
    payload = {
        "matrix": [[-80, -70, -60], [-75, -45, -68], [-72, -55, -74]],
        "freq": ["99.1", "99.2", "99.3"],
        "time": ["t0", "t1", "t2"],
    }
    result = _run("waterfall", payload)
    assert result.returncode == 0, result.stderr
    assert "99.1" in result.stdout
    assert "t0" in result.stdout


def test_spectrum_schema_error():
    result = _run("spectrum", {"freq": [1, 2]})
    assert result.returncode == 1
    assert "ERROR:schema:" in result.stderr


def test_spectrum_single_bin_renders_point():
    result = _run("spectrum", {"freq": [99.1], "db": [-42]})
    assert result.returncode == 0, result.stderr
    assert "·" in result.stdout
    assert "99.1" in result.stdout


def test_spectrum_ascii_font_tier_uses_ascii_symbols():
    result = _run(
        "spectrum",
        {"freq": [99.1, 99.2], "db": [-80, -42], "center": 99.15, "peaks": [99.2]},
        "--font-tier",
        "ascii",
    )
    assert result.returncode == 0, result.stderr
    for glyph in ("┌", "─", "·", "▲", "│", "┃"):
        assert glyph not in result.stdout
    assert "+" in result.stdout
    assert "." in result.stdout


def test_spectrum_reads_csv_stdin():
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "spectrum",
            "--format",
            "csv",
            "--no-color",
            "--width",
            "60",
            "--height",
            "12",
        ],
        input="freq,db\n99.1,-80\n99.2,-42\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "99.1" in result.stdout
    assert "99.2" in result.stdout


def test_spectrum_renders_traces_only_payload():
    result = _run(
        "spectrum",
        {"traces": [{"freq": [99.1, 99.2, 99.3], "db": [-80, -42, -70], "label": "rx"}]},
    )
    assert result.returncode == 0, result.stderr
    assert "rx" in result.stdout
    assert "live" not in result.stdout
    assert "99.1" in result.stdout


def test_waterfall_reads_csv_stdin():
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "waterfall",
            "--format",
            "csv",
            "--no-color",
            "--width",
            "60",
            "--height",
            "12",
        ],
        input="time,99.1,99.2\nt0,-80,-70\nt1,-60,-45\n",
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "t0" in result.stdout
    assert "99.1" in result.stdout


def test_waterfall_renders_tuning_overlays():
    result = _run(
        "waterfall",
        {
            "matrix": [[-90, -80, -70], [-70, -60, -50]],
            "freq": [99.1, 99.2, 99.3],
            "center": 99.2,
            "bandwidth": 0.1,
            "vfos": [{"freq": 99.3, "label": "rx"}],
        },
    )
    assert result.returncode == 0, result.stderr
    assert "center=99.2" in result.stdout
    assert "rx=99.3" in result.stdout


def test_waterfall_uses_ansi_intensity_when_color_enabled():
    env = os.environ.copy()
    env.pop("NO_COLOR", None)
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "waterfall",
            "--json",
            json.dumps({"matrix": [[-90, -60, -30]], "freq": [1, 2, 3]}),
            "--width",
            "40",
            "--height",
            "8",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        env=env,
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "\x1b[" in result.stdout


def test_waterfall_respects_height_by_showing_recent_rows_only():
    payload = {
        "matrix": [[-90, -80], [-80, -70], [-70, -60], [-60, -50], [-50, -40]],
        "time": ["old0", "old1", "old2", "new3", "now"],
    }
    result = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
            "waterfall",
            "--json",
            json.dumps(payload),
            "--no-color",
            "--width",
            "40",
            "--height",
            "4",
        ],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert result.returncode == 0, result.stderr
    assert "now" in result.stdout
    assert "old0" not in result.stdout
