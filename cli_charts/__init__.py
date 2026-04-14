"""cli-charts: terminal-visible chart toolkit for Claude Code."""
try:
    from importlib.metadata import version as _pkg_version
    __version__ = _pkg_version("cli-charts")
except Exception:
    try:
        from pathlib import Path
        __version__ = (Path(__file__).parent.parent / "VERSION").read_text().strip()
    except Exception:
        __version__ = "3.0.0"
