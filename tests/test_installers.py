from __future__ import annotations

import subprocess
import sys
import tarfile
import zipfile
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


def test_font_download_install_plan(monkeypatch) -> None:
    from cli_charts import installers

    monkeypatch.setattr(installers, "platform_key", lambda: "windows")

    plan = installers.render_install_plan("fonts", "download")

    assert "cli_charts.font_downloads install core" in plan
    assert "core OFL font pack" in plan
    assert "LICENSE and NOTICE" in plan


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


def test_font_downloader_extracts_fonts_and_writes_license(monkeypatch, tmp_path) -> None:
    from cli_charts import font_downloads

    archive = tmp_path / "JuliaMono-ttf.zip"
    with zipfile.ZipFile(archive, "w") as zf:
        zf.writestr("JuliaMono-Regular.ttf", b"font")
        zf.writestr("ignored.txt", b"ignore")

    def fake_latest_asset(spec):
        return archive.name, "https://example.test/font.zip"

    def fake_download(url, dest):
        if url.endswith(".zip"):
            dest.write_bytes(archive.read_bytes())
        else:
            dest.write_text("OFL", encoding="utf-8")

    monkeypatch.setattr(font_downloads, "_latest_asset", fake_latest_asset)
    monkeypatch.setattr(font_downloads, "_download", fake_download)

    rc = font_downloads.install_fonts(["juliamono"], tmp_path / "fonts")

    assert rc == 0
    assert (tmp_path / "fonts" / "juliamono" / "JuliaMono-Regular.ttf").read_bytes() == b"font"
    assert (tmp_path / "fonts" / "juliamono" / "LICENSE").read_text(encoding="utf-8") == "OFL"
    assert "Reserved Font Name: JuliaMono" in (
        tmp_path / "fonts" / "juliamono" / "NOTICE.txt"
    ).read_text(encoding="utf-8")


def test_font_downloader_extracts_tar_xz(tmp_path) -> None:
    from cli_charts import font_downloads

    source = tmp_path / "Hack-Regular.ttf"
    source.write_bytes(b"font")
    archive = tmp_path / "Hack.tar.xz"
    with tarfile.open(archive, "w:xz") as tf:
        tf.add(source, arcname="Hack/Hack-Regular.ttf")

    extracted = font_downloads._extract_fonts(archive, tmp_path / "out")

    assert [path.name for path in extracted] == ["Hack-Regular.ttf"]
    assert (tmp_path / "out" / "Hack-Regular.ttf").read_bytes() == b"font"


def test_font_groups_status_and_remove(tmp_path) -> None:
    from cli_charts import font_downloads

    selected = font_downloads._selected_specs(["core"])

    assert [spec.key for spec in selected] == [
        "iosevka",
        "juliamono",
        "jetbrainsmono-nerd",
        "symbols-nerd-font",
    ]

    font_root = tmp_path / "fonts"
    (font_root / "iosevka").mkdir(parents=True)
    (font_root / "iosevka" / "Iosevka-Regular.ttf").write_bytes(b"font")

    status = font_downloads.render_font_status(font_root)

    assert "iosevka" in status
    assert "OK" in status
    assert "juliamono" in status
    assert "MISSING" in status

    rc = font_downloads.remove_fonts(["iosevka"], font_root)

    assert rc == 0
    assert not (font_root / "iosevka").exists()


def test_fonts_cli_lists_downloadable_fonts() -> None:
    result = _run(["fonts", "list", "--no-splash"])

    assert result.returncode == 0, result.stderr
    assert "glyph-arts downloadable fonts" in result.stdout
    assert "jetbrainsmono-nerd" in result.stdout
    assert "symbols-nerd-font" in result.stdout


def test_doctor_cli_prints_backend_status() -> None:
    result = _run(["doctor", "--no-splash"])

    assert result.returncode == 0, result.stderr
    assert "glyph-arts backend doctor" in result.stdout
    assert "chafa" in result.stdout
    assert "graphviz" in result.stdout
    assert "diagon" in result.stdout
    assert "nerd-font" in result.stdout
    assert "symbols-font" in result.stdout
    assert "downloaded-fonts" in result.stdout
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
