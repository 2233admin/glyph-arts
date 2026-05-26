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


def test_chat_probe_cli_reports_recommendation() -> None:
    result = _run(["chat", "probe", "--font-tier", "unicode-extended", "--no-splash"])

    assert result.returncode == 0, result.stderr
    assert "glyph-arts chat glyph probe" in result.stdout
    assert "recommended chat profile: rich" in result.stdout
    assert "Braille" in result.stdout
    assert "Nerd Font PUA" in result.stdout


def test_chat_profile_cli_reports_profiles() -> None:
    result = _run(["chat", "profile", "--font-tier", "ascii", "--no-splash"])

    assert result.returncode == 0, result.stderr
    assert "glyph-arts chat profiles" in result.stdout
    assert "recommended: ascii" in result.stdout
    assert "max" in result.stdout


def test_doctor_fix_chat_prints_plan() -> None:
    result = _run(["doctor", "--fix-chat", "--font-tier", "unicode", "--no-splash"])

    assert result.returncode == 0, result.stderr
    assert "glyph-arts backend doctor" in result.stdout
    assert "glyph-arts chat fix plan" in result.stdout
    assert "glyph-arts fonts install max" in result.stdout
    assert "Noto Sans Symbols 2" in result.stdout


def test_chat_profile_tier_mapping() -> None:
    from cli_charts.chat_health import chat_profile_tier, recommend_chat_profile

    assert chat_profile_tier("ascii", "nerd") == "ascii"
    assert chat_profile_tier("safe", "ascii") == "unicode"
    assert chat_profile_tier("rich", "unicode") == "unicode-extended"
    assert chat_profile_tier("max", "unicode") == "nerd"
    assert recommend_chat_profile("nerd") == "max"
