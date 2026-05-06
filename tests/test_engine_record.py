"""Phase 5 tests for asciinema recording wrapper."""

import inspect
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "export_test_outputs"


def _run(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=10,
        cwd=ROOT,
        env=env,
    )


def _output(name: str) -> Path:
    OUT_DIR.mkdir(exist_ok=True)
    path = OUT_DIR / name
    if path.exists():
        path.unlink()
    return path


def test_record_signature() -> None:
    from cli_charts.render.record_engine import record, record_replay

    assert callable(record)
    assert callable(record_replay)
    assert list(inspect.signature(record).parameters) == ["cast_path", "cmd", "duration"]
    assert list(inspect.signature(record_replay).parameters) == ["cast_path", "output"]


def test_record_dep_missing_returns_2() -> None:
    result = _run(
        ["record", "demo.cast", "--cmd", "echo hi", "--duration", "1"],
        env={"PATH": ""},
    )

    assert result.returncode == 2
    assert "ERROR:dep: asciinema not in PATH" in result.stderr


def test_record_replay_unknown_format_returns_1() -> None:
    cast = _output("record-demo.cast")
    cast.write_text('{"version": 2}\n', encoding="utf-8")
    result = _run(["record-replay", str(cast), "--output", str(_output("record-demo.xyz"))])

    assert result.returncode == 1
    assert "ERROR:schema:" in result.stderr


def test_record_help_no_crash() -> None:
    record_help = _run(["record", "--help"])
    replay_help = _run(["record-replay", "--help"])

    assert record_help.returncode == 0
    assert replay_help.returncode == 0
    assert "record" in record_help.stdout
    assert "record-replay" in replay_help.stdout


def test_record_replay_dispatches_correct_tool(monkeypatch) -> None:
    from cli_charts.render import record_engine

    cast = _output("record-dispatch.cast")
    cast.write_text('{"version": 2}\n', encoding="utf-8")
    calls: list[list[str]] = []

    monkeypatch.setattr(record_engine.shutil, "which", lambda name: f"/bin/{name}")

    def fake_run(cmd: list[str]) -> subprocess.CompletedProcess[str]:
        calls.append(cmd)
        return subprocess.CompletedProcess(cmd, 0)

    monkeypatch.setattr(record_engine.subprocess, "run", fake_run)

    assert record_engine.record_replay(cast, _output("record-dispatch.gif")) == 0
    assert record_engine.record_replay(cast, _output("record-dispatch.svg")) == 0
    assert calls[0][0] == "agg"
    assert calls[1][0] == "svg-term"


def test_dep_check_windows_install_hint(monkeypatch, capsys) -> None:
    from cli_charts.render import record_engine

    monkeypatch.setattr(record_engine.shutil, "which", lambda name: None)
    monkeypatch.setattr(record_engine.sys, "platform", "win32")

    assert record_engine.check_dep("asciinema") is False
    captured = capsys.readouterr()
    assert "scoop" in captured.err or "choco" in captured.err
