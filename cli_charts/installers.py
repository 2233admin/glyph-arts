"""Dependency doctor and installer planning for terminal rendering backends."""

from __future__ import annotations

import os
import shutil
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path


@dataclass(frozen=True)
class BackendStatus:
    name: str
    ok: bool
    detail: str


@dataclass(frozen=True)
class InstallStep:
    label: str
    command: list[str]
    note: str = ""
    safe_to_run: bool = True


FONT_MARKERS = (
    "Nerd Font",
    "NerdFont",
    "JetBrainsMonoNF",
    "JetBrains Mono NL",
    "CaskaydiaCove",
    "Caskaydia Cove",
)

SYMBOLS_FONT_MARKERS = (
    "SymbolsNerdFont",
    "Symbols Nerd Font",
    "SymbolsOnly",
    "NerdFontsSymbolsOnly",
)

VALID_TARGETS = {"all", "chat", "media", "fonts", "diagrams", "petiglyph"}


def platform_key() -> str:
    try:
        from cli_charts.terminal_profiles import detect_terminal_runtime

        if detect_terminal_runtime().key == "wsl":
            return "linux"
    except Exception:
        pass
    if sys.platform.startswith("win"):
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


def detect_package_manager() -> str:
    key = platform_key()
    if key == "windows":
        for manager in ("scoop", "choco", "winget"):
            if shutil.which(manager):
                return manager
        if shutil.which("x"):
            return "x-cmd"
        return ""
    if key == "macos":
        if shutil.which("brew"):
            return "brew"
        return "x-cmd" if shutil.which("x") else ""
    for manager in ("brew", "apt-get", "dnf", "pacman", "snap"):
        if shutil.which(manager):
            return manager
    if shutil.which("x"):
        return "x-cmd"
    return ""


def detect_chafa() -> BackendStatus:
    return _tool_status("chafa", "high-fidelity raster terminal renderer")


def detect_ffmpeg() -> BackendStatus:
    return _tool_status("ffmpeg", "video/GIF frame extractor")


def detect_petiglyph() -> BackendStatus:
    binary = os.environ.get("GLYPH_ARTS_PETIGLYPH") or shutil.which("petiglyph") or shutil.which("petiglyph.exe")
    return BackendStatus(
        "petiglyph",
        bool(binary),
        binary or "missing (optional custom font glyph backend; pip install petiglyph)",
    )


def detect_graphviz() -> BackendStatus:
    return _tool_status("graphviz", "Graphviz dot layout/export backend", executable="dot")


def detect_diagon() -> BackendStatus:
    binary = os.environ.get("GLYPH_ARTS_DIAGON") or shutil.which("diagon") or shutil.which("diagon.exe")
    return BackendStatus("diagon", bool(binary), binary or "missing (math/sequence/tree/flowchart diagrams)")


def detect_nerd_font() -> BackendStatus:
    hits = _find_fonts(FONT_MARKERS, exclude_markers=SYMBOLS_FONT_MARKERS)
    if hits:
        names = ", ".join(path.name for path in hits[:3])
        suffix = "" if len(hits) <= 3 else f" (+{len(hits) - 3} more)"
        return BackendStatus("nerd-font", True, names + suffix)
    return BackendStatus("nerd-font", False, "No Nerd Font files found in common font directories")


def detect_symbols_font() -> BackendStatus:
    hits = _find_fonts(SYMBOLS_FONT_MARKERS)
    if hits:
        names = ", ".join(path.name for path in hits[:3])
        suffix = "" if len(hits) <= 3 else f" (+{len(hits) - 3} more)"
        return BackendStatus("symbols-font", True, names + suffix)
    return BackendStatus("symbols-font", False, "No Symbols Nerd Font files found in common font directories")


def detect_downloaded_fonts() -> BackendStatus:
    try:
        from cli_charts.font_downloads import downloaded_font_status

        ok, detail = downloaded_font_status()
    except Exception as exc:  # pragma: no cover - defensive doctor output
        return BackendStatus("downloaded-fonts", False, f"probe failed: {exc}")
    return BackendStatus("downloaded-fonts", ok, detail)


def detect_terminal_probe() -> BackendStatus:
    try:
        from cli_charts.font_tier import detect_font_tier
        from cli_charts.render.media_engine import _detect_chafa_format
        from cli_charts.terminal_profiles import detect_terminal_profile, detect_terminal_runtime

        profile = detect_terminal_profile()
        runtime = detect_terminal_runtime()
        chafa_format = _detect_chafa_format("auto", chat=False, output=None)
        font_tier = detect_font_tier()
    except Exception as exc:  # pragma: no cover - defensive doctor output
        return BackendStatus("terminal", False, f"probe failed: {exc}")

    tty = "yes" if os.isatty(1) else "no"
    term = os.environ.get("TERM", "") or "-"
    term_program = os.environ.get("TERM_PROGRAM", "") or "-"
    detail = (
        f"profile={profile.key}, format={chafa_format}, tty={tty}, "
        f"runtime={runtime.key}, shell={runtime.shell}, "
        f"truecolor={_yesno(profile.truecolor)}, sixel={_yesno(profile.sixel)}, "
        f"kitty={_yesno(profile.kitty)}, osc8={_yesno(profile.osc8)}, "
        f"font-tier={font_tier}, TERM={term}, TERM_PROGRAM={term_program}"
    )
    return BackendStatus("terminal", True, detail)


def backend_statuses() -> list[BackendStatus]:
    return [
        detect_chafa(),
        detect_graphviz(),
        detect_diagon(),
        detect_ffmpeg(),
        detect_petiglyph(),
        detect_nerd_font(),
        detect_symbols_font(),
        detect_downloaded_fonts(),
        detect_terminal_probe(),
    ]


def build_install_plan(target: str = "all", manager: str = "") -> list[InstallStep]:
    target = (target or "all").lower()
    if target not in VALID_TARGETS:
        raise ValueError(f"unknown install target: {target!r}")
    manager = manager or detect_package_manager()
    key = _platform_key_for_manager(manager) or platform_key()
    steps: list[InstallStep] = []
    if target in {"all", "media"}:
        steps.extend(_media_steps(key, manager))
    if target in {"all", "petiglyph"}:
        steps.extend(_petiglyph_steps(key, manager))
    if target == "chat":
        steps.extend(_chat_media_steps(key, manager))
    if target in {"all", "chat", "diagrams"}:
        steps.extend(_diagram_steps(key, manager))
    if target in {"all", "fonts"}:
        steps.extend(_font_steps(key, manager))
    if target == "chat":
        steps.extend(_font_steps(key, manager))
    if not steps:
        steps.append(InstallStep(
            "manual",
            [],
            "No supported package manager found. Install chafa, Graphviz, Diagon, "
            "JetBrainsMono Nerd Font, and Symbols Nerd Font manually.",
            safe_to_run=False,
        ))
    return _dedupe_steps(steps)


def render_doctor(*, fix_chat: bool = False) -> str:
    lines = ["glyph-arts backend doctor", ""]
    for status in backend_statuses():
        mark = "OK" if status.ok else "MISSING"
        lines.append(f"{status.name:<13} {mark:<7} {status.detail}")
    lines.extend(["", "Install plan (chat):", render_install_plan("chat")])
    if fix_chat:
        from cli_charts.chat_health import render_fix_chat_plan

        lines.extend(["", render_fix_chat_plan()])
    return "\n".join(lines).rstrip() + "\n"


def render_install_plan(target: str = "all", manager: str = "") -> str:
    lines = []
    for step in build_install_plan(target, manager):
        if step.command:
            lines.append(f"{step.label}: {_quote_command(step.command)}")
        else:
            lines.append(f"{step.label}: {step.note}")
        if step.note and step.command:
            lines.append(f"  # {step.note}")
    return "\n".join(lines).rstrip() + "\n"


def run_install_plan(target: str = "all", manager: str = "", *, yes: bool = False) -> int:
    steps = build_install_plan(target, manager)
    blocked = [step for step in steps if not step.safe_to_run]
    if blocked:
        for step in blocked:
            print(f"ERROR:install: {step.label}: {step.note}", file=sys.stderr)
        return 2
    if not yes:
        print("ERROR:install: pass --yes to execute package-manager commands", file=sys.stderr)
        print(render_install_plan(target, manager), end="")
        return 1
    for step in steps:
        if not step.command:
            print(f"[glyph-arts] {step.label}: {step.note}")
            continue
        if not _runner_exists(step.command):
            print(f"ERROR:install: {step.command[0]} not found for {step.label}", file=sys.stderr)
            return 2
        print(f"[glyph-arts] {step.label}: {_quote_command(step.command)}")
        result = subprocess.run(step.command)
        if result.returncode != 0:
            return result.returncode or 4
    return 0


def _media_steps(key: str, manager: str) -> list[InstallStep]:
    if manager == "x-cmd":
        return [InstallStep("media", ["x", "install", "chafa", "ffmpeg"])]
    if key == "windows":
        if manager == "scoop":
            return [InstallStep("media", ["scoop", "install", "chafa", "ffmpeg"])]
        if manager == "choco":
            return [InstallStep("media", ["choco", "install", "chafa", "ffmpeg", "-y"])]
        if manager == "winget":
            return [InstallStep("media", [], "Install chafa and ffmpeg with Scoop or Chocolatey for now.", False)]
    if key == "macos" and manager == "brew":
        return [InstallStep("media", ["brew", "install", "chafa", "ffmpeg"])]
    if key == "linux":
        if manager == "brew":
            return [InstallStep("media", ["brew", "install", "chafa", "ffmpeg"])]
        if manager == "apt-get":
            return [
                InstallStep("media-index", ["sudo", "apt-get", "update"]),
                InstallStep("media", ["sudo", "apt-get", "install", "-y", "chafa", "ffmpeg"]),
            ]
        if manager == "dnf":
            return [InstallStep("media", ["sudo", "dnf", "install", "-y", "chafa", "ffmpeg"])]
        if manager == "pacman":
            return [InstallStep("media", ["sudo", "pacman", "-S", "--needed", "chafa", "ffmpeg"])]
    return []


def _petiglyph_steps(key: str, manager: str) -> list[InstallStep]:
    del key, manager
    return [InstallStep(
        "petiglyph",
        [sys.executable, "-m", "pip", "install", "petiglyph"],
        "Optional Petiglyph CLI backend. Upstream also supports npm install -g petiglyph.",
    )]


def _platform_key_for_manager(manager: str) -> str:
    if manager in {"scoop", "choco", "winget"}:
        return "windows"
    return ""


def _chat_media_steps(key: str, manager: str) -> list[InstallStep]:
    if manager == "x-cmd":
        return [InstallStep("chat-media", ["x", "install", "chafa"])]
    if key == "windows":
        if manager == "scoop":
            return [InstallStep("chat-media", ["scoop", "install", "chafa"])]
        if manager == "choco":
            return [InstallStep("chat-media", ["choco", "install", "chafa", "-y"])]
        if manager == "winget":
            return [InstallStep(
                "chat-media",
                [],
                "Install chafa with Scoop or Chocolatey; winget does not expose a stable chafa package.",
            )]
    if key == "macos" and manager == "brew":
        return [InstallStep("chat-media", ["brew", "install", "chafa"])]
    if key == "linux":
        if manager == "brew":
            return [InstallStep("chat-media", ["brew", "install", "chafa"])]
        if manager == "apt-get":
            return [
                InstallStep("chat-media-index", ["sudo", "apt-get", "update"]),
                InstallStep("chat-media", ["sudo", "apt-get", "install", "-y", "chafa"]),
            ]
        if manager == "dnf":
            return [InstallStep("chat-media", ["sudo", "dnf", "install", "-y", "chafa"])]
        if manager == "pacman":
            return [InstallStep("chat-media", ["sudo", "pacman", "-S", "--needed", "chafa"])]
    return []


def _diagram_steps(key: str, manager: str) -> list[InstallStep]:
    steps: list[InstallStep] = []
    if manager == "x-cmd":
        steps.append(InstallStep("graphviz", ["x", "install", "graphviz"]))
        steps.extend(_diagon_steps(key, manager))
        return steps
    if key == "windows":
        if manager == "scoop":
            steps.append(InstallStep("graphviz", ["scoop", "install", "graphviz"]))
        elif manager == "choco":
            steps.append(InstallStep("graphviz", ["choco", "install", "graphviz", "-y"]))
        elif manager == "winget":
            steps.append(InstallStep("graphviz", ["winget", "install", "--id", "Graphviz.Graphviz"]))
    elif key == "macos" and manager == "brew":
        steps.append(InstallStep("graphviz", ["brew", "install", "graphviz"]))
    elif key == "linux":
        if manager == "brew":
            steps.append(InstallStep("graphviz", ["brew", "install", "graphviz"]))
        elif manager == "apt-get":
            steps.extend([
                InstallStep("graphviz-index", ["sudo", "apt-get", "update"]),
                InstallStep("graphviz", ["sudo", "apt-get", "install", "-y", "graphviz"]),
            ])
        elif manager == "dnf":
            steps.append(InstallStep("graphviz", ["sudo", "dnf", "install", "-y", "graphviz"]))
        elif manager == "pacman":
            steps.append(InstallStep("graphviz", ["sudo", "pacman", "-S", "--needed", "graphviz"]))

    steps.extend(_diagon_steps(key, manager))
    return steps


def _diagon_steps(key: str, manager: str) -> list[InstallStep]:
    if key == "linux" and manager == "snap":
        return [InstallStep("diagon", ["sudo", "snap", "install", "diagon"])]
    if manager == "x-cmd":
        return [InstallStep("diagon", ["x", "install", "diagon"])]
    return [InstallStep(
        "diagon",
        [],
        "Optional: install Diagon from upstream releases, snap, Nix, or source; "
        "builtin fallback remains active when it is missing.",
    )]


def _font_steps(key: str, manager: str) -> list[InstallStep]:
    if manager == "download":
        return [_font_download_step()]
    if manager == "x-cmd":
        return [InstallStep(
            "font",
            [],
            "Install JetBrainsMono Nerd Font plus Symbols Nerd Font in the terminal profile font list.",
        )]
    if key == "windows":
        if manager == "scoop":
            return [
                InstallStep("font-bucket", ["scoop", "bucket", "add", "nerd-fonts"]),
                InstallStep("font", ["scoop", "install", "JetBrainsMono-NF"]),
                InstallStep("symbols-font", ["scoop", "install", "NerdFontsSymbolsOnly"]),
            ]
        if manager == "choco":
            return [InstallStep(
                "font",
                [],
                "Install JetBrainsMono Nerd Font and NerdFontsSymbolsOnly with Scoop or manually.",
            )]
    if key == "macos" and manager == "brew":
        return [
            InstallStep("font", ["brew", "install", "--cask", "font-jetbrains-mono-nerd-font"]),
            InstallStep("symbols-font", ["brew", "install", "--cask", "font-symbols-only-nerd-font"]),
        ]
    if key == "linux":
        if manager == "pacman":
            return [
                InstallStep("font", ["sudo", "pacman", "-S", "--needed", "ttf-jetbrains-mono-nerd"]),
                InstallStep("symbols-font", ["sudo", "pacman", "-S", "--needed", "ttf-nerd-fonts-symbols"]),
            ]
        return [InstallStep(
            "font",
            [],
            "Install JetBrainsMono Nerd Font and Symbols Nerd Font into ~/.local/share/fonts, "
            "then run fc-cache -fv.",
        )]
    return []


def _font_download_step() -> InstallStep:
    from cli_charts.font_downloads import default_font_dir

    return InstallStep(
        "font-downloads",
        [
            sys.executable,
            "-m",
            "cli_charts.font_downloads",
            "install",
            "max",
        ],
        "Downloads the max open font pack, including Google Noto fallbacks, to "
        f"{default_font_dir()} with LICENSE and NOTICE files; select the font in your terminal.",
    )


def _tool_status(name: str, purpose: str, *, executable: str | None = None) -> BackendStatus:
    binary = executable or name
    path = shutil.which(binary)
    return BackendStatus(name, bool(path), path or f"missing ({purpose})")


def _find_fonts(markers: tuple[str, ...], *, exclude_markers: tuple[str, ...] = ()) -> list[Path]:
    roots = _font_roots()
    hits: list[Path] = []
    for root in roots:
        if not root.exists():
            continue
        try:
            for path in root.rglob("*"):
                if path.suffix.lower() not in {".ttf", ".otf", ".ttc"}:
                    continue
                name = path.name.replace("-", " ")
                lower_name = name.lower()
                if exclude_markers and any(marker.lower() in lower_name for marker in exclude_markers):
                    continue
                if any(marker.lower() in lower_name for marker in markers):
                    hits.append(path)
        except OSError:
            continue
    return hits


def _font_roots() -> list[Path]:
    key = platform_key()
    home = Path.home()
    if key == "windows":
        roots = [
            Path(os.environ.get("LOCALAPPDATA", "")) / "Microsoft" / "Windows" / "Fonts",
            Path(os.environ.get("WINDIR", "C:/Windows")) / "Fonts",
        ]
        scoop = home / "scoop" / "apps"
        if scoop.exists():
            roots.append(scoop)
        return roots
    if key == "macos":
        return [home / "Library" / "Fonts", Path("/Library/Fonts"), Path("/System/Library/Fonts")]
    return [home / ".local" / "share" / "fonts", Path("/usr/local/share/fonts"), Path("/usr/share/fonts")]


def _quote_command(command: list[str]) -> str:
    return " ".join(_quote_part(part) for part in command)


def _yesno(value: bool) -> str:
    return "yes" if value else "no"


def _dedupe_steps(steps: list[InstallStep]) -> list[InstallStep]:
    seen: set[tuple[str, ...]] = set()
    result: list[InstallStep] = []
    for step in steps:
        key = tuple(step.command) if step.command else (step.label, step.note)
        if key in seen:
            continue
        seen.add(key)
        result.append(step)
    return result


def _runner_exists(command: list[str]) -> bool:
    if not command:
        return True
    runner = command[1] if command[0] == "sudo" and len(command) > 1 else command[0]
    return bool(shutil.which(runner))


def _quote_part(part: str) -> str:
    if not part or any(ch.isspace() for ch in part):
        return '"' + part.replace('"', '\\"') + '"'
    return part
