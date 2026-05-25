"""Terminal host capability profiles."""

from __future__ import annotations

import os
import re
import sys
from collections.abc import Mapping
from dataclasses import dataclass


@dataclass(frozen=True)
class TerminalProfile:
    key: str
    name: str
    ansi: bool
    truecolor: bool
    osc8: bool
    sixel: bool
    kitty: bool
    iterm: bool
    chafa_format: str
    chafa_symbols: str
    chafa_colors: str
    font_tier: str
    image_strategy: str
    note: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "name": self.name,
            "ansi": self.ansi,
            "truecolor": self.truecolor,
            "osc8": self.osc8,
            "sixel": self.sixel,
            "kitty": self.kitty,
            "iterm": self.iterm,
            "chafa_format": self.chafa_format,
            "chafa_symbols": self.chafa_symbols,
            "chafa_colors": self.chafa_colors,
            "font_tier": self.font_tier,
            "image_strategy": self.image_strategy,
            "note": self.note,
        }


@dataclass(frozen=True)
class TerminalRuntime:
    key: str
    name: str
    shell: str
    distro: str
    package_scope: str
    note: str = ""

    def as_dict(self) -> dict[str, object]:
        return {
            "key": self.key,
            "name": self.name,
            "shell": self.shell,
            "distro": self.distro or "-",
            "package_scope": self.package_scope,
            "note": self.note,
        }


PROFILES: dict[str, TerminalProfile] = {
    "chat-pane": TerminalProfile(
        "chat-pane", "AI Chat Pane", True, False, False, False, False, False,
        "symbols", "ascii", "none", "unicode", "plain-text",
        "Portable chat transcript target; no terminal graphics protocols.",
    ),
    "windows-terminal": TerminalProfile(
        "windows-terminal", "Windows Terminal", True, True, True, False, False, False,
        "symbols", "vhalf", "full", "unicode", "chafa-symbols",
        "Default conservative profile; use windows-terminal-preview/canary for sixel.",
    ),
    "windows-terminal-preview": TerminalProfile(
        "windows-terminal-preview", "Windows Terminal Preview", True, True, True, True, False, False,
        "sixels", "vhalf", "full", "unicode", "chafa-sixels",
        "Windows Terminal Preview 1.22+ supports Sixel graphics.",
    ),
    "windows-terminal-canary": TerminalProfile(
        "windows-terminal-canary", "Windows Terminal Canary", True, True, True, True, False, False,
        "sixels", "vhalf", "full", "unicode", "chafa-sixels",
        "Bleeding-edge Windows Terminal profile; prefer sixels for images.",
    ),
    "warp": TerminalProfile(
        "warp", "Warp", True, True, False, False, False, False,
        "symbols", "vhalf", "full", "unicode-extended", "chafa-symbols",
        "Warp supports truecolor but not Sixel; use symbols/blocks.",
    ),
    "waveterm": TerminalProfile(
        "waveterm", "WaveTerm", True, True, False, False, False, False,
        "symbols", "vhalf", "full", "unicode-extended", "host-adapter",
        "Use glyph-arts wave for rich preview blocks.",
    ),
    "wezterm": TerminalProfile(
        "wezterm", "WezTerm", True, True, True, True, False, False,
        "sixels", "vhalf", "full", "unicode-extended", "chafa-sixels",
    ),
    "iterm": TerminalProfile(
        "iterm", "iTerm2", True, True, True, True, False, True,
        "iterm", "vhalf", "full", "unicode-extended", "iterm-inline-image",
    ),
    "kitty": TerminalProfile(
        "kitty", "Kitty", True, True, True, False, True, False,
        "kitty", "vhalf", "full", "unicode-extended", "kitty-graphics",
    ),
    "vscode": TerminalProfile(
        "vscode", "VS Code Terminal", True, True, True, False, False, False,
        "symbols", "vhalf", "full", "unicode", "chafa-symbols",
    ),
    "generic": TerminalProfile(
        "generic", "Generic Terminal", True, True, False, False, False, False,
        "symbols", "vhalf", "full", "unicode", "chafa-symbols",
    ),
}

ALIASES = {
    "wt": "windows-terminal",
    "windows-terminal-dev": "windows-terminal-preview",
    "windows-terminal-insiders": "windows-terminal-preview",
    "windows-terminal-preview": "windows-terminal-preview",
    "windows-terminal-canary": "windows-terminal-canary",
    "warpterminal": "warp",
    "wave": "waveterm",
}


def detect_terminal_profile(env: Mapping[str, str] | None = None) -> TerminalProfile:
    values = env or os.environ
    override = _normalize_key(values.get("GLYPH_ARTS_TERMINAL_PROFILE", ""))
    if override:
        return PROFILES.get(ALIASES.get(override, override), PROFILES["generic"])

    term_program = values.get("TERM_PROGRAM", "").lower()
    term = values.get("TERM", "").lower()
    if term_program == "warpterminal":
        return PROFILES["warp"]
    if term_program in {"waveterm", "wave"} or values.get("WAVETERM"):
        return PROFILES["waveterm"]
    if values.get("WT_SESSION"):
        if _truthy(values.get("WT_CANARY")):
            return PROFILES["windows-terminal-canary"]
        if _truthy(values.get("WT_PREVIEW")) or _version_at_least(values.get("WT_VERSION", ""), (1, 22)):
            return PROFILES["windows-terminal-preview"]
        return PROFILES["windows-terminal"]
    if "kitty" in term or values.get("KITTY_WINDOW_ID"):
        return PROFILES["kitty"]
    if term_program == "iterm.app":
        return PROFILES["iterm"]
    if term_program == "wezterm" or values.get("WEZTERM_EXECUTABLE"):
        return PROFILES["wezterm"]
    if term_program == "vscode":
        return PROFILES["vscode"]
    return PROFILES["generic"]


def detect_terminal_runtime(env: Mapping[str, str] | None = None) -> TerminalRuntime:
    values = env or os.environ
    shell = _shell_name(values)
    override = _normalize_key(values.get("GLYPH_ARTS_RUNTIME", ""))
    if override == "wsl":
        return _wsl_runtime(values, shell)
    if override == "windows":
        return TerminalRuntime("windows", "Windows", shell, "", "windows")
    if override == "macos":
        return TerminalRuntime("macos", "macOS", shell, "", "macos")
    if override == "linux":
        return TerminalRuntime("linux", "Linux", shell, "", "linux")
    if (
        not sys.platform.startswith("win")
        and (values.get("WSL_DISTRO_NAME") or values.get("WSL_INTEROP") or values.get("WSLENV"))
    ):
        return _wsl_runtime(values, shell)
    if sys.platform.startswith("win"):
        return TerminalRuntime("windows", "Windows", shell, "", "windows")
    if sys.platform == "darwin":
        return TerminalRuntime("macos", "macOS", shell, "", "macos")
    return TerminalRuntime("linux", "Linux", shell, "", "linux")


def _wsl_runtime(values: Mapping[str, str], shell: str) -> TerminalRuntime:
    distro = values.get("WSL_DISTRO_NAME", "")
    return TerminalRuntime(
        "wsl",
        "Windows Subsystem for Linux",
        shell,
        distro,
        "linux-in-wsl",
        "Install CLI backends inside WSL; configure fonts in the terminal host.",
    )


def render_terminal_profile(profile: TerminalProfile | None = None) -> str:
    selected = profile or detect_terminal_profile()
    runtime = detect_terminal_runtime()
    lines = ["glyph-arts terminal profile", ""]
    for key, value in selected.as_dict().items():
        lines.append(f"{key:<15} {_format_value(value)}")
    lines.extend(["", "runtime"])
    for key, value in runtime.as_dict().items():
        lines.append(f"{key:<15} {_format_value(value)}")
    return "\n".join(lines).rstrip() + "\n"


def _normalize_key(value: str) -> str:
    return value.strip().lower().replace("_", "-").replace(" ", "-")


def _truthy(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


def _version_at_least(value: str, target: tuple[int, int]) -> bool:
    match = re.search(r"(\d+)\.(\d+)", value or "")
    if not match:
        return False
    current = (int(match.group(1)), int(match.group(2)))
    return current >= target


def _format_value(value: object) -> str:
    if isinstance(value, bool):
        return "yes" if value else "no"
    return str(value)


def _shell_name(values: Mapping[str, str]) -> str:
    shell = values.get("SHELL") or values.get("COMSPEC") or values.get("ComSpec") or ""
    if not shell:
        return "-"
    normalized = shell.replace("\\", "/").rstrip("/")
    name = normalized.rsplit("/", 1)[-1]
    return name[:-4] if name.lower().endswith(".exe") else name
