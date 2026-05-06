"""glyph-arts: terminal-visible chart toolkit for Claude Code."""
import sys as _sys

# Normalize stdout/stderr to UTF-8 on Windows legacy consoles (cp1252).
# Rich + plotext emit braille / box-drawing chars that crash on cp1252.
# `errors='replace'` is a safety valve so an exotic glyph never aborts a render.
for _stream in (_sys.stdout, _sys.stderr):
    if hasattr(_stream, 'reconfigure') and getattr(_stream, 'encoding', '').lower() != 'utf-8':
        try:
            _stream.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, OSError):
            pass
del _sys

try:
    from importlib.metadata import version as _pkg_version
    __version__ = _pkg_version("glyph-arts")
except Exception:
    try:
        from pathlib import Path
        __version__ = (Path(__file__).parent.parent / "VERSION").read_text().strip()
    except Exception:
        __version__ = "unknown"
