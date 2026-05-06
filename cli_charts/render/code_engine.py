"""Rich syntax highlighting command."""

from __future__ import annotations

import sys
from pathlib import Path

from pygments.lexers import get_lexer_by_name
from pygments.util import ClassNotFound
from rich.console import Console
from rich.syntax import Syntax


def render_code(
    file_path: str,
    lang: str,
    *,
    theme: str = "monokai",
    line_numbers: bool = False,
    no_color: bool = False,
) -> int:
    path = Path(file_path)
    if not path.exists() or not path.is_file():
        print(f"ERROR:schema: file not found: {file_path}", file=sys.stderr)
        return 1

    try:
        code = path.read_text(encoding="utf-8")
    except UnicodeDecodeError:
        print(f"ERROR:schema: file is not utf-8 text: {file_path}", file=sys.stderr)
        return 1

    try:
        get_lexer_by_name(lang)
    except ClassNotFound:
        print(f"ERROR:schema: unsupported language: {lang}", file=sys.stderr)
        return 1

    syntax = Syntax(
        code,
        lang,
        theme=theme,
        line_numbers=line_numbers,
        word_wrap=False,
    )
    Console(
        no_color=no_color,
        force_terminal=not no_color,
        color_system="standard",
        legacy_windows=False,
    ).print(syntax)
    return 0
