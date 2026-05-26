from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from cli_charts.render.incplot_engine import detect_incplot

ROOT = Path(__file__).resolve().parents[1]


def _run(*args: str, input_text: str = "") -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", *args],
        input=input_text,
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
    )


def test_incplot_numeric_csv_defaults_to_scatter() -> None:
    detected = detect_incplot("x,y\n1,2\n2,5\n3,3\n")

    assert detected.chart_type == "scatter"
    assert detected.data == {"label": "y", "x": [1.0, 2.0, 3.0], "y": [2.0, 5.0, 3.0]}


def test_incplot_jsonl_category_multi_value_to_multibar() -> None:
    raw = '{"name":"A","left":3,"right":5}\n{"name":"B","left":4,"right":6}\n'
    detected = detect_incplot(raw)

    assert detected.chart_type == "multibar"
    assert detected.data["labels"] == ["A", "B"]
    assert [series["label"] for series in detected.data["series"]] == ["left", "right"]


def test_incplot_prefer_hist_for_numeric_json() -> None:
    detected = detect_incplot("[1,1,2,3,5]", "hist")

    assert detected.chart_type == "hist"
    assert detected.data == {"values": [1.0, 1.0, 2.0, 3.0, 5.0]}


def test_incplot_prefer_stackedbar_for_multi_value_csv() -> None:
    detected = detect_incplot("name,left,right\nA,3,5\nB,4,6\n", "stackedbar")

    assert detected.chart_type == "stackedbar"
    assert detected.data["labels"] == ["A", "B"]
    assert [series["label"] for series in detected.data["series"]] == ["left", "right"]


def test_incplot_temporal_csv_normalizes_iso_dates() -> None:
    detected = detect_incplot("date,value\n2026-01-01,3\n2026-01-02,7\n")

    assert detected.chart_type == "line"
    assert detected.data == [{"label": "value", "x": ["01/01/2026", "02/01/2026"], "y": [3.0, 7.0]}]


def test_chat_incplot_renders_raw_csv() -> None:
    result = _run(
        "chat",
        "incplot",
        "--width",
        "60",
        "--height",
        "12",
        "--no-splash",
        input_text="x,y\n1,2\n2,5\n3,3\n",
    )

    assert result.returncode == 0, result.stderr
    assert "y" in result.stdout
    assert "┌" in result.stdout


def test_chat_incplot_renders_temporal_csv() -> None:
    result = _run(
        "chat",
        "incplot",
        "--width",
        "64",
        "--height",
        "10",
        "--no-splash",
        input_text="date,value\n2026-01-01,3\n2026-01-02,7\n2026-01-03,5\n",
    )

    assert result.returncode == 0, result.stderr
    assert "ERROR" not in result.stderr
    assert "value" in result.stdout


def test_chat_textplot_renders_function_braille() -> None:
    result = _run(
        "chat",
        "textplot",
        "--json",
        json.dumps({"expr": "sin(x)", "xmin": -6.28, "xmax": 6.28}),
        "--width",
        "50",
        "--height",
        "12",
        "--no-splash",
    )

    assert result.returncode == 0, result.stderr
    assert "y = sin(x)" in result.stdout
    assert any("\u2800" <= char <= "\u28ff" and char != "\u2800" for char in result.stdout)


def test_chat_turtle_renders_drawille_style_path() -> None:
    result = _run(
        "chat",
        "turtle",
        "--json",
        json.dumps({"commands": [["forward", 24], ["right", 90], ["forward", 16], ["right", 90], ["forward", 24]]}),
        "--width",
        "36",
        "--height",
        "10",
        "--no-splash",
    )

    assert result.returncode == 0, result.stderr
    assert any("\u2800" <= char <= "\u28ff" and char != "\u2800" for char in result.stdout)
