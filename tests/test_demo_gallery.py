import subprocess
import sys
import time


def test_demo_dispatch_wires():
    result = subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", "demo", "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert result.returncode == 0
    assert "30s" in result.stdout
    assert "--speed" in result.stdout


def test_gallery_dispatch_wires():
    result = subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", "gallery", "--help"],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        check=False,
    )
    assert result.returncode == 0
    assert "--output" in result.stdout
    assert "--chart" in result.stdout


def test_demo_speed_budget(monkeypatch):
    from cli_charts import demo_engine

    monkeypatch.setattr(demo_engine, "render_section", lambda *args: "")
    monkeypatch.setattr(demo_engine.time, "sleep", lambda _seconds: None)
    started = time.monotonic()
    assert demo_engine.run_demo(speed="fast", clear=False) == 0
    assert time.monotonic() - started < 2


def test_gallery_html_output(tmp_path, monkeypatch):
    from cli_charts import gallery_engine

    monkeypatch.setattr(gallery_engine, "render_preview", lambda *args, **kwargs: "<div>stub</div>")
    output = tmp_path / "g.html"
    assert gallery_engine.run_gallery(output=str(output), chart="bar") == 0
    content = output.read_text(encoding="utf-8").lower()
    assert "<html" in content
    assert "bar" in content
    assert 100 < output.stat().st_size < 2 * 1024 * 1024


def test_demo_keyboard_interrupt_clean(capsys, monkeypatch):
    from cli_charts import demo_engine

    def raise_interrupt(*args, **kwargs):
        raise KeyboardInterrupt

    monkeypatch.setattr(demo_engine, "_run_segments", raise_interrupt)
    assert demo_engine.run_demo(speed="fast", clear=False) == 0
    assert "cancelled" in capsys.readouterr().out
