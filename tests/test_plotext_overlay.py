from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(payload: dict, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [
            sys.executable,
            "-m",
            "cli_charts.chart",
            "chat",
            "plotext",
            "--json",
            json.dumps(payload),
            "--width",
            "72",
            "--height",
            "16",
            "--no-splash",
            *extra,
        ],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
    )


def test_chat_plotext_supports_error_bars_text_lines_and_shapes() -> None:
    result = _run(
        {
            "series": [
                {"type": "line", "x": [1, 2, 3, 4], "y": [2, 5, 3, 6], "label": "signal"},
                {
                    "type": "error",
                    "x": [1, 2, 3, 4],
                    "y": [2, 5, 3, 6],
                    "yerr": [0.4, 0.8, 0.3, 0.6],
                    "label": "err",
                },
            ],
            "texts": [{"text": "peak", "x": 3.2, "y": 6}],
            "vlines": [{"value": 2, "color": "red"}],
            "hlines": [4],
            "shapes": [
                {
                    "type": "rectangle",
                    "x": [1.5, 3.5],
                    "y": [2.2, 5.8],
                    "lines": True,
                    "fill": False,
                    "color": "cyan",
                }
            ],
        }
    )

    assert result.returncode == 0, result.stderr
    assert "signal" in result.stdout
    assert "peak" in result.stdout
    assert "┌" in result.stdout
    assert "\x1b[" not in result.stdout


def test_chat_plotext_colorize_respects_no_color() -> None:
    result = _run({"colorize": "OK", "color": "green", "style": "bold"})

    assert result.returncode == 0, result.stderr
    assert result.stdout.strip() == "OK"
    assert "\x1b[" not in result.stdout
