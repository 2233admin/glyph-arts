"""glyph-arts: terminal-visible chart toolkit for Claude Code."""
import sys as _sys

# Normalize stdio to UTF-8 on Windows legacy consoles (cp1252/cp936).
# Rich + plotext emit braille / box-drawing chars, and PowerShell pipes UTF-8
# payloads that should not be decoded through the active ANSI code page.
for _stream in (_sys.stdin, _sys.stdout, _sys.stderr):
    if hasattr(_stream, 'reconfigure') and getattr(_stream, 'encoding', '').lower() != 'utf-8':
        try:
            _stream.reconfigure(encoding='utf-8', errors='replace')
        except (AttributeError, OSError):
            pass
del _sys

def _load_version() -> str:
    try:
        from pathlib import Path

        return (Path(__file__).parent.parent / "VERSION").read_text(encoding="utf-8").strip()
    except Exception:
        try:
            from importlib.metadata import version as _pkg_version

            return _pkg_version("glyph-arts")
        except Exception:
            return "unknown"


def __getattr__(name: str):
    if name == "__version__":
        version = _load_version()
        globals()["__version__"] = version
        return version
    raise AttributeError(f"module {__name__!r} has no attribute {name!r}")
