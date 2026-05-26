import subprocess
import sys
from pathlib import Path


def run_cli(*args, input_text=None):
    return subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", *args],
        input=input_text,
        text=True,
        encoding="utf-8",
        errors="replace",
        capture_output=True,
        timeout=10,
    )


def test_auto_cli_stdin_smoke():
    result = run_cli("auto", "--no-splash", "--no-color", input_text="[1,2,3]")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip()


def test_auto_cli_file_smoke():
    sample = Path(".pytest-tmp-auto-sample.csv")
    sample.write_text("name,value\nA,3\nB,7\n", encoding="utf-8")
    try:
        result = run_cli("auto", "--file", str(sample), "--no-splash", "--no-color")
        assert result.returncode == 0, result.stderr
        assert "A" in result.stdout
    finally:
        sample.unlink(missing_ok=True)


def test_live_random_cli_smoke():
    result = run_cli("live", "random", "--duration", "0.2", "--interval", "0.05", "--no-color", "--no-splash")
    assert result.returncode == 0, result.stderr
    assert result.stdout.strip()
