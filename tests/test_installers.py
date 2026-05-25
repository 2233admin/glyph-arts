from __future__ import annotations

import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def _run(args: list[str]) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", *args],
        cwd=ROOT,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=15,
    )


def test_windows_scoop_install_plan(monkeypatch) -> None:
    from cli_charts import installers

    monkeypatch.setattr(installers, "platform_key", lambda: "windows")

    plan = installers.render_install_plan("all", "scoop")

    assert "scoop install chafa ffmpeg" in plan
    assert "scoop install graphviz" in plan
    assert "scoop bucket add nerd-fonts" in plan
    assert "scoop install JetBrainsMono-NF" in plan
    assert "scoop install NerdFontsSymbolsOnly" in plan
    assert "Diagon from upstream" in plan


def test_platform_key_treats_wsl_as_linux(monkeypatch) -> None:
    from cli_charts import installers

    monkeypatch.setenv("GLYPH_ARTS_RUNTIME", "wsl")
    monkeypatch.setenv("WSL_DISTRO_NAME", "Ubuntu")

    assert installers.platform_key() == "linux"


def test_macos_brew_install_plan(monkeypatch) -> None:
    from cli_charts import installers

    monkeypatch.setattr(installers, "platform_key", lambda: "macos")

    plan = installers.render_install_plan("all", "brew")

    assert "brew install chafa ffmpeg" in plan
    assert "brew install graphviz" in plan
    assert "brew install --cask font-jetbrains-mono-nerd-font" in plan
    assert "brew install --cask font-symbols-only-nerd-font" in plan


def test_chat_install_plan_omits_video_backend(monkeypatch) -> None:
    from cli_charts import installers

    monkeypatch.setattr(installers, "platform_key", lambda: "windows")

    plan = installers.render_install_plan("chat", "scoop")

    assert "scoop install chafa" in plan
    assert "ffmpeg" not in plan
    assert "scoop install graphviz" in plan
    assert "scoop install NerdFontsSymbolsOnly" in plan


def test_diagrams_install_plan_has_graphviz_and_diagon_note(monkeypatch) -> None:
    from cli_charts import installers

    monkeypatch.setattr(installers, "platform_key", lambda: "windows")

    plan = installers.render_install_plan("diagrams", "scoop")

    assert "scoop install graphviz" in plan
    assert "diagon: Optional:" in plan


def test_run_install_plan_requires_yes(monkeypatch, capsys) -> None:
    from cli_charts import installers

    monkeypatch.setattr(installers, "platform_key", lambda: "windows")

    rc = installers.run_install_plan("media", "scoop", yes=False)

    assert rc == 1
    captured = capsys.readouterr()
    assert "--yes" in captured.err
    assert "scoop install chafa ffmpeg" in captured.out


def test_run_install_plan_skips_optional_notes(monkeypatch, capsys) -> None:
    from cli_charts import installers

    commands: list[list[str]] = []

    class Result:
        returncode = 0

    def fake_run(command):
        commands.append(command)
        return Result()

    monkeypatch.setattr(installers, "platform_key", lambda: "windows")
    monkeypatch.setattr(installers, "_runner_exists", lambda command: True)
    monkeypatch.setattr(installers.subprocess, "run", fake_run)

    rc = installers.run_install_plan("diagrams", "scoop", yes=True)

    assert rc == 0
    assert commands == [["scoop", "install", "graphviz"]]
    assert "Diagon from upstream" in capsys.readouterr().out


def test_doctor_cli_prints_backend_status() -> None:
    result = _run(["doctor", "--no-splash"])

    assert result.returncode == 0, result.stderr
    assert "glyph-arts backend doctor" in result.stdout
    assert "chafa" in result.stdout
    assert "graphviz" in result.stdout
    assert "diagon" in result.stdout
    assert "nerd-font" in result.stdout
    assert "symbols-font" in result.stdout
    assert "terminal" in result.stdout
    assert "profile=" in result.stdout
    assert "runtime=" in result.stdout
    assert "shell=" in result.stdout


def test_terminal_probe_reports_windows_terminal_preview(monkeypatch) -> None:
    from cli_charts import installers
    from cli_charts.render import media_engine

    monkeypatch.setenv("GLYPH_ARTS_TERMINAL_PROFILE", "windows-terminal-preview")
    monkeypatch.delenv("GLYPH_ARTS_CHAFA_FORMAT", raising=False)
    monkeypatch.delenv("GLYPH_ARTS_FORMAT", raising=False)
    monkeypatch.setattr(media_engine.os, "isatty", lambda fd: fd == 1)
    monkeypatch.setattr(installers.os, "isatty", lambda fd: fd == 1)

    status = installers.detect_terminal_probe()

    assert status.ok is True
    assert "profile=windows-terminal-preview" in status.detail
    assert "format=sixels" in status.detail
    assert "sixel=yes" in status.detail


def test_terminal_probe_reports_warp_wsl_bash(monkeypatch) -> None:
    from cli_charts import installers
    from cli_charts.render import media_engine

    monkeypatch.delenv("GLYPH_ARTS_TERMINAL_PROFILE", raising=False)
    monkeypatch.delenv("GLYPH_ARTS_CHAFA_FORMAT", raising=False)
    monkeypatch.delenv("GLYPH_ARTS_FORMAT", raising=False)
    monkeypatch.setenv("GLYPH_ARTS_RUNTIME", "wsl")
    monkeypatch.setenv("TERM_PROGRAM", "WarpTerminal")
    monkeypatch.setenv("WSL_DISTRO_NAME", "Ubuntu")
    monkeypatch.setenv("SHELL", "/bin/bash")
    monkeypatch.setattr(media_engine.os, "isatty", lambda fd: fd == 1)
    monkeypatch.setattr(installers.os, "isatty", lambda fd: fd == 1)

    status = installers.detect_terminal_probe()

    assert status.ok is True
    assert "profile=warp" in status.detail
    assert "runtime=wsl" in status.detail
    assert "shell=bash" in status.detail
    assert "format=symbols" in status.detail


def test_install_backends_cli_prints_plan() -> None:
    result = _run(["install-backends", "--target", "chat", "--manager", "scoop", "--no-splash"])

    assert result.returncode == 0, result.stderr
    assert "scoop install chafa" in result.stdout
    assert "scoop install graphviz" in result.stdout
