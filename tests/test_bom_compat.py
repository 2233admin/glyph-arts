"""BOM-safe file input tests.

Verifies that --file inputs containing a UTF-8 BOM (\\xef\\xbb\\xbf) are
parsed correctly. Reproduces the bug fixed by the utf-8-sig change in
cli_charts/cmd/_helpers.py and cli_charts/dashboard.py.

The issue: on Windows, PowerShell's `Out-File -Encoding utf8` writes
a UTF-8 BOM by default. Python's `json.load` treats the BOM as
invalid content, raising `json.JSONDecodeError: Expecting value: line 1
column 1 (char 0)`. Switching to `encoding="utf-8-sig"` strips the BOM
automatically and is backward-compatible with non-BOM files.
"""
import json
import os
import subprocess
import sys
import tempfile

import pytest


def _write_bom_json(path: str, payload) -> None:
    """Write a JSON file with a UTF-8 BOM prefix (mimic PowerShell Out-File)."""
    with open(path, "wb") as f:
        f.write(b"\xef\xbb\xbf")  # UTF-8 BOM
        f.write(json.dumps(payload).encode("utf-8"))


def _run(chart_type: str, json_path: str) -> tuple[int, str, str]:
    """Invoke `python -m cli_charts.chart <type> --file <path>` and capture output."""
    repo_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    env = {**os.environ, "PYTHONPATH": repo_root, "NO_COLOR": "1",
           "PYTHONIOENCODING": "utf-8", "PYTHONUTF8": "1"}
    proc = subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", chart_type,
         "--file", json_path, "--title", "BOM test"],
        capture_output=True, env=env, timeout=20,
    )
    # Decode with utf-8; if a chart's own renderer writes non-utf8 to stdout
    # we only care about the ERROR:json signal in stderr.
    out = proc.stdout.decode("utf-8", errors="replace")
    err = proc.stderr.decode("utf-8", errors="replace")
    return proc.returncode, out, err


@pytest.mark.parametrize("chart_type,payload", [
    ("bar",       {"labels": ["Q1", "Q2"], "values": [10, 14]}),
    ("sparkline", {"values": [1, 3, 5, 2, 8]}),
    ("line",     [{"label": "a", "x": [1, 2], "y": [3, 4]}]),
    ("pie",      {"labels": ["x", "y"], "values": [3, 7]}),
    ("gauge",    {"label": "ok", "value": 1, "max": 3}),
])
def test_chart_loads_bom_file(chart_type, payload):
    """The json loader step must not raise on a BOM-prefixed input file."""
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "bom.json")
        _write_bom_json(path, payload)
        rc, out, err = _run(chart_type, path)
        assert "ERROR:json" not in err, (
            f"BOM file failed JSON load for {chart_type}\\nstderr: {err}"
        )


def test_non_bom_file_still_works():
    """Sanity check: fix is backward-compatible with normal no-BOM files."""
    payload = {"labels": ["x"], "values": [5]}
    with tempfile.TemporaryDirectory() as td:
        path = os.path.join(td, "plain.json")
        with open(path, "w", encoding="utf-8") as f:
            json.dump(payload, f)
        rc, out, err = _run("bar", path)
        assert "ERROR:json" not in err, err


def test_raw_open_with_utf8sig_strips_bom(tmp_path):
    """Direct unit check: open(args.file, encoding='utf-8-sig') strips BOM."""
    p = tmp_path / "bom.json"
    p.write_bytes(b"\xef\xbb\xbf" + b'{"a":1}')
    with open(p, encoding="utf-8-sig") as f:
        data = json.load(f)
    assert data == {"a": 1}


def test_raw_open_with_utf8_fails_on_bom(tmp_path):
    """Demonstrate the original bug for completeness."""
    p = tmp_path / "bom.json"
    p.write_bytes(b"\xef\xbb\xbf" + b'{"a":1}')
    with pytest.raises(json.JSONDecodeError):
        with open(p, encoding="utf-8") as f:
            json.load(f)
