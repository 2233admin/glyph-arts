from __future__ import annotations


def test_detects_warp_profile_from_term_program() -> None:
    from cli_charts.terminal_profiles import detect_terminal_profile

    profile = detect_terminal_profile({"TERM_PROGRAM": "WarpTerminal"})

    assert profile.key == "warp"
    assert profile.truecolor is True
    assert profile.sixel is False
    assert profile.chafa_format == "symbols"
    assert profile.font_tier == "unicode-extended"


def test_detects_wsl_bash_runtime_under_warp() -> None:
    from cli_charts.terminal_profiles import detect_terminal_profile, detect_terminal_runtime

    env = {
        "GLYPH_ARTS_RUNTIME": "wsl",
        "TERM_PROGRAM": "WarpTerminal",
        "WSL_DISTRO_NAME": "Ubuntu",
        "SHELL": "/bin/bash",
    }

    profile = detect_terminal_profile(env)
    runtime = detect_terminal_runtime(env)

    assert profile.key == "warp"
    assert runtime.key == "wsl"
    assert runtime.shell == "bash"
    assert runtime.distro == "Ubuntu"
    assert runtime.package_scope == "linux-in-wsl"


def test_detects_windows_terminal_conservative_profile() -> None:
    from cli_charts.terminal_profiles import detect_terminal_profile

    profile = detect_terminal_profile({"WT_SESSION": "abc"})

    assert profile.key == "windows-terminal"
    assert profile.truecolor is True
    assert profile.sixel is False
    assert profile.chafa_format == "symbols"


def test_detects_windows_terminal_preview_profile_from_marker() -> None:
    from cli_charts.terminal_profiles import detect_terminal_profile

    profile = detect_terminal_profile({"WT_SESSION": "abc", "WT_PREVIEW": "1"})

    assert profile.key == "windows-terminal-preview"
    assert profile.sixel is True
    assert profile.chafa_format == "sixels"


def test_detects_windows_terminal_preview_profile_from_version() -> None:
    from cli_charts.terminal_profiles import detect_terminal_profile

    profile = detect_terminal_profile({"WT_SESSION": "abc", "WT_VERSION": "1.22.0"})

    assert profile.key == "windows-terminal-preview"
    assert profile.sixel is True


def test_terminal_profile_override_supports_canary_alias() -> None:
    from cli_charts.terminal_profiles import detect_terminal_profile

    profile = detect_terminal_profile({"GLYPH_ARTS_TERMINAL_PROFILE": "windows-terminal-canary"})

    assert profile.key == "windows-terminal-canary"
    assert profile.image_strategy == "chafa-sixels"


def test_render_terminal_profile_is_agent_readable() -> None:
    from cli_charts.terminal_profiles import PROFILES, render_terminal_profile

    text = render_terminal_profile(PROFILES["warp"])

    assert "glyph-arts terminal profile" in text
    assert "key             warp" in text
    assert "sixel           no" in text
    assert "runtime" in text
