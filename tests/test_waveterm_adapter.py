import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _run(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged_env = os.environ.copy()
    if env:
        merged_env.update(env)
    return subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=20,
        env=merged_env,
    )


def test_wave_detects_env_and_wsh(monkeypatch) -> None:
    from cli_charts.adapters import waveterm

    monkeypatch.setenv("WAVETERM_SESSIONID", "session-1")
    monkeypatch.setenv("WAVETERM_WORKSPACEID", "workspace-1")
    monkeypatch.setenv("WAVETERM_BLOCKID", "block-1")
    monkeypatch.setattr(waveterm.shutil, "which", lambda name: "C:/Wave/wsh.exe" if name == "wsh" else "")

    status = waveterm.detect_wave()

    assert status.in_wave is True
    assert status.ok is True
    assert status.wsh_path == "C:/Wave/wsh.exe"
    assert status.session == "session-1"


def test_wave_view_dry_run_prints_wsh_command(tmp_path) -> None:
    preview = tmp_path / "preview.html"
    preview.write_text("<pre>ok</pre>", encoding="utf-8")

    result = _run(["wave", "view", "--file", str(preview), "--dry-run", "--no-splash"])

    assert result.returncode == 0, result.stderr
    assert "wsh view" in result.stdout
    assert str(preview) in result.stdout


def test_wave_render_dry_run_plans_chart_export_and_view() -> None:
    result = _run([
        "wave",
        "render",
        "bar",
        "--json",
        '{"labels":["A"],"values":[3]}',
        "--dry-run",
        "--no-splash",
    ])

    assert result.returncode == 0, result.stderr
    assert "chart:" in result.stdout
    assert "-m cli_charts.chart bar" in result.stdout
    assert "--file" in result.stdout
    assert "payload.txt" in result.stdout
    assert "--output" in result.stdout
    assert "view:" in result.stdout
    assert "wsh view" in result.stdout


def test_wave_doctor_cli_prints_adapter_status() -> None:
    result = _run(["wave", "doctor", "--no-splash"])

    assert result.returncode == 0, result.stderr
    assert "glyph-arts WaveTerm adapter" in result.stdout
    assert "inside-wave" in result.stdout
    assert "wsh" in result.stdout
