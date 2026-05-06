"""asciinema recording and replay wrappers."""

from __future__ import annotations

import html
import shutil
import subprocess
import sys
from pathlib import Path

DEP_INSTALL = {
    "asciinema": {
        "macos": "brew install asciinema",
        "linux": "apt install asciinema | dnf install asciinema",
        "windows": "scoop install asciinema | choco install asciinema | pip install asciinema",
    },
    "agg": {
        "macos": "brew install agg",
        "linux": "cargo install --git https://github.com/asciinema/agg",
        "windows": "scoop install agg | cargo install --git https://github.com/asciinema/agg",
    },
    "svg-term": {
        "macos": "npm install -g svg-term-cli",
        "linux": "npm install -g svg-term-cli",
        "windows": "npm install -g svg-term-cli",
    },
}


def _platform_key() -> str:
    if sys.platform == "win32":
        return "windows"
    if sys.platform == "darwin":
        return "macos"
    return "linux"


def check_dep(name: str) -> bool:
    if shutil.which(name) is None:
        install_cmd = DEP_INSTALL[name][_platform_key()]
        print(
            f"ERROR:dep: {name} not in PATH (install: {install_cmd})",
            file=sys.stderr,
        )
        return False
    return True


def _check_cast(path: Path) -> bool:
    if not path.exists():
        print(f"ERROR:schema: cast file not found: {path}", file=sys.stderr)
        return False
    if not path.is_file():
        print(f"ERROR:schema: cast path is not a file: {path}", file=sys.stderr)
        return False
    return True


def _write_html(cast_path: Path, output: Path) -> int:
    cast_ref = html.escape(cast_path.as_posix(), quote=True)
    title = html.escape(cast_path.name)
    output.write_text(
        "\n".join(
            [
                '<link rel="stylesheet" href="https://cdn.jsdelivr.net/npm/asciinema-player@3.8.0/dist/bundle/asciinema-player.css">',
                f'<div id="glyph-arts-cast" data-cast="{cast_ref}"></div>',
                '<script src="https://cdn.jsdelivr.net/npm/asciinema-player@3.8.0/dist/bundle/asciinema-player.min.js"></script>',
                "<script>",
                f'AsciinemaPlayer.create("{cast_ref}", document.getElementById("glyph-arts-cast"), {{title: "{title}"}});',
                "</script>",
                "",
            ]
        ),
        encoding="utf-8",
    )
    return 0


def record(cast_path: str | Path, cmd: str, duration: float) -> int:
    if not cmd:
        print("ERROR:schema: record requires --cmd", file=sys.stderr)
        return 1
    if duration <= 0:
        print("ERROR:schema: record requires --duration > 0", file=sys.stderr)
        return 1
    if not check_dep("asciinema"):
        return 2

    result = subprocess.run(
        [
            "asciinema",
            "rec",
            "--command",
            cmd,
            "--idle-time-limit",
            "0.5",
            str(cast_path),
        ]
    )
    return result.returncode


def record_replay(cast_path: str | Path, output: str | Path) -> int:
    cast = Path(cast_path)
    out = Path(output)
    if not output:
        print("ERROR:schema: record-replay requires --output", file=sys.stderr)
        return 1

    suffix = out.suffix.lower()
    if suffix not in {".gif", ".svg", ".html", ".cast"}:
        print(
            "ERROR:schema: record-replay output must end with .gif, .svg, .html, or .cast",
            file=sys.stderr,
        )
        return 1
    if not _check_cast(cast):
        return 1

    if suffix == ".gif":
        if not check_dep("agg"):
            return 2
        return subprocess.run(["agg", str(cast), str(out)]).returncode
    if suffix == ".svg":
        if not check_dep("svg-term"):
            return 2
        return subprocess.run(["svg-term", "--in", str(cast), "--out", str(out)]).returncode
    if suffix == ".html":
        return _write_html(cast, out)

    if cast.resolve() != out.resolve():
        shutil.copyfile(cast, out)
    return 0
