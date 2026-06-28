"""Petiglyph compatibility layer.

Petiglyph stays optional: glyph-arts owns routing, artifact inspection,
chat-safe previews, and safety guards while v1 delegates font generation to the
upstream Petiglyph CLI.
"""

from __future__ import annotations

import json
import os
import shlex
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

PETIGLYPH_INSTALL_HINT = "Install Petiglyph with `pip install petiglyph` or `npm install -g petiglyph`."


@dataclass(frozen=True)
class PetiglyphGlyph:
    name: str
    source: str
    codepoint: str
    character: str
    preview: str = ""


@dataclass(frozen=True)
class PetiglyphAnimation:
    name: str
    fps: int | None = None
    frames: tuple[str, ...] = ()
    rows: int | None = None
    cols: int | None = None


@dataclass(frozen=True)
class PetiglyphArtifacts:
    ttf: tuple[Path, ...] = ()
    bdf: tuple[Path, ...] = ()
    glyph_map: Path | None = None
    sample: Path | None = None
    previews: tuple[Path, ...] = ()
    glyphs: tuple[PetiglyphGlyph, ...] = ()


@dataclass(frozen=True)
class PetiglyphProject:
    name: str
    root: Path
    manifest: Path
    input_dir: Path
    build_dir: Path
    font_name: str
    glyph_size: int | None = None
    codepoint_start: str = ""
    animations: tuple[PetiglyphAnimation, ...] = ()
    artifacts: PetiglyphArtifacts = field(default_factory=PetiglyphArtifacts)


class PetiglyphBackend:
    key = "base"

    def available(self) -> bool:
        raise NotImplementedError

    def command(self, args: list[str]) -> list[str]:
        raise NotImplementedError

    def run(self, args: list[str], *, dry_run: bool = False) -> int:
        raise NotImplementedError


class CliPetiglyphBackend(PetiglyphBackend):
    key = "cli"

    def __init__(self, binary: str | None = None) -> None:
        override = binary or os.environ.get("GLYPH_ARTS_PETIGLYPH", "")
        resolved = shutil.which("petiglyph") or shutil.which("petiglyph.exe")
        self.binary = override or resolved or "petiglyph"
        self._resolved = override or resolved

    def available(self) -> bool:
        return bool(self._resolved or shutil.which(self.binary))

    def command(self, args: list[str]) -> list[str]:
        return [self.binary, *args]

    def run(self, args: list[str], *, dry_run: bool = False) -> int:
        cmd = self.command(args)
        if dry_run:
            print("[glyph-arts] petiglyph dry-run: " + _quote_command(cmd))
            return 0
        if not self.available():
            print("ERROR:petiglyph: backend CLI not found", file=sys.stderr)
            print(PETIGLYPH_INSTALL_HINT, file=sys.stderr)
            return 127
        result = subprocess.run(cmd)
        return result.returncode


class NativePetiglyphBackend(PetiglyphBackend):
    key = "native"

    def available(self) -> bool:
        return False

    def command(self, args: list[str]) -> list[str]:
        del args
        return []

    def run(self, args: list[str], *, dry_run: bool = False) -> int:
        del args, dry_run
        print("ERROR:petiglyph: native backend is reserved but not implemented", file=sys.stderr)
        return 2


def run_petiglyph_command(args: Any, raw_argv: list[str] | None = None) -> int:
    raw_argv = raw_argv or []
    tokens = list(getattr(args, "art_text", []) or [])
    if not tokens or tokens[0] in {"-h", "--help", "help"}:
        print(render_petiglyph_help(), end="")
        return 0

    action = tokens[0]
    if action == "preview":
        if len(tokens) < 2:
            print("ERROR:petiglyph: preview needs a project path or name", file=sys.stderr)
            return 2
        return render_project_preview_command(args, tokens[1])

    if action == "doctor":
        print(render_petiglyph_doctor(), end="")
        backend = _select_backend(args)
        if backend.available() and _has_token(raw_argv, "--upstream"):
            return backend.run(["doctor"], dry_run=getattr(args, "dry_run", False))
        return 0

    if action == "use-project" and _is_enhanced_show_sample(tokens, args):
        if len(tokens) < 2:
            print("ERROR:petiglyph: use-project needs a project path or name", file=sys.stderr)
            return 2
        return render_project_preview_command(args, tokens[1], sample_only=True)

    if action in {"delete-project", "uninstall-font", "uninstall-all-fonts"}:
        return _run_destructive(args, tokens)

    backend = _select_backend(args)
    cli_args = _build_cli_args(args, tokens, raw_argv)
    return backend.run(cli_args, dry_run=getattr(args, "dry_run", False))


def render_project_preview_command(args: Any, project_ref: str, *, sample_only: bool = False) -> int:
    try:
        project = read_petiglyph_project(project_ref)
    except FileNotFoundError as exc:
        print(f"ERROR:petiglyph: {exc}", file=sys.stderr)
        print("Pass a project directory containing petiglyph.toml for chat/json previews.", file=sys.stderr)
        return 2

    glyph = getattr(args, "glyph", "") or ""
    animation = getattr(args, "animation", "") or ""
    if getattr(args, "petiglyph_json_output", False):
        print(json.dumps(project_to_dict(project, glyph=glyph, animation=animation), ensure_ascii=False, indent=2))
        return 0

    print(render_petiglyph_project_summary(project, glyph=glyph, animation=animation), end="")
    if sample_only and not getattr(args, "chat", False):
        return 0
    if getattr(args, "chat", False):
        return render_petiglyph_chat_previews(
            project,
            glyph=glyph,
            animation=animation,
            width=min(int(getattr(args, "width", 80) or 80), 80),
            height=min(int(getattr(args, "height", 24) or 24), 32),
            limit=int(getattr(args, "preview_limit", 6) or 6),
            no_color=bool(getattr(args, "no_color", False)),
        )
    return 0


def render_petiglyph_help() -> str:
    return """glyph-arts petiglyph

Usage:
  glyph-arts petiglyph tui
  glyph-arts petiglyph new-project <name>
  glyph-arts petiglyph list projects
  glyph-arts petiglyph list installed-fonts
  glyph-arts petiglyph use-project <project> create glyph --input <file>...
  glyph-arts petiglyph use-project <project> create grid-glyph --input <file> --rows N --cols N
  glyph-arts petiglyph use-project <project> create animated-glyph --input <file> --fps N
  glyph-arts petiglyph use-project <project> create animated-grid-glyph --input <file> --fps N --rows N --cols N
  glyph-arts petiglyph use-project <project> build [--force-remap]
  glyph-arts petiglyph use-project <project> install-font
  glyph-arts petiglyph use-project <project> show-sample [--chat] [--json]
  glyph-arts petiglyph preview <project-dir> [--chat] [--json]
  glyph-arts petiglyph delete-project <project>... [--yes]
  glyph-arts petiglyph uninstall-font <family>... [--yes]
  glyph-arts petiglyph uninstall-all-fonts [--yes]

Notes:
  Petiglyph is optional. Install it with `pip install petiglyph` or
  `npm install -g petiglyph`.
  Destructive commands are dry-run by default; pass --yes to execute.
"""


def render_petiglyph_doctor() -> str:
    backend = CliPetiglyphBackend()
    ffmpeg = shutil.which("ffmpeg") or shutil.which("ffmpeg.exe")
    try:
        from cli_charts.terminal_profiles import detect_terminal_profile, detect_terminal_runtime

        terminal = detect_terminal_profile()
        runtime = detect_terminal_runtime()
        terminal_detail = f"{terminal.name} ({terminal.key}), runtime={runtime.key}, shell={runtime.shell}"
    except Exception as exc:
        terminal_detail = f"probe failed: {exc}"

    lines = ["glyph-arts petiglyph doctor", ""]
    lines.append(f"{'petiglyph':<13} {'OK' if backend.available() else 'MISSING':<7} {backend.binary if backend.available() else PETIGLYPH_INSTALL_HINT}")
    lines.append(f"{'ffmpeg':<13} {'OK' if ffmpeg else 'MISSING':<7} {ffmpeg or 'needed for GIF/video animation imports'}")
    lines.append(f"{'terminal':<13} OK      {terminal_detail}")
    lines.extend([
        "",
        "Install options:",
        f"  {sys.executable} -m pip install petiglyph",
        "  npm install -g petiglyph",
        "",
        "Safety:",
        "  delete-project, uninstall-font, and uninstall-all-fonts require --yes.",
    ])
    return "\n".join(lines).rstrip() + "\n"


def read_petiglyph_project(project_ref: str) -> PetiglyphProject:
    root = _resolve_project_root(project_ref)
    manifest = root / "petiglyph.toml"
    if not manifest.exists():
        raise FileNotFoundError(f"{root} does not contain petiglyph.toml")

    data = _read_toml(manifest)
    input_dir = root / str(data.get("input_dir") or "images")
    build_dir = root / str(data.get("out_dir") or "build")
    font_name = str(data.get("font_name") or root.name)
    return PetiglyphProject(
        name=root.name,
        root=root,
        manifest=manifest,
        input_dir=input_dir,
        build_dir=build_dir,
        font_name=font_name,
        glyph_size=_int_or_none(data.get("glyph_size")),
        codepoint_start=str(data.get("codepoint_start") or ""),
        animations=tuple(_read_animations(data)),
        artifacts=read_petiglyph_artifacts(build_dir),
    )


def read_petiglyph_artifacts(build_dir: Path) -> PetiglyphArtifacts:
    glyph_map = build_dir / "glyph-map.json"
    sample = build_dir / "glyph-sample.txt"
    previews_dir = build_dir / "previews"
    previews = tuple(sorted(previews_dir.glob("*.png"))) if previews_dir.exists() else ()
    glyphs = tuple(_read_glyph_map(glyph_map, previews)) if glyph_map.exists() else ()
    return PetiglyphArtifacts(
        ttf=tuple(sorted(build_dir.glob("*.ttf"))) if build_dir.exists() else (),
        bdf=tuple(sorted(build_dir.glob("*.bdf"))) if build_dir.exists() else (),
        glyph_map=glyph_map if glyph_map.exists() else None,
        sample=sample if sample.exists() else None,
        previews=previews,
        glyphs=glyphs,
    )


def render_petiglyph_project_summary(project: PetiglyphProject, *, glyph: str = "", animation: str = "") -> str:
    artifacts = project.artifacts
    sample_text = artifacts.sample.read_text(encoding="utf-8", errors="replace").strip() if artifacts.sample else ""
    glyphs = _filter_glyphs(artifacts.glyphs, glyph)
    previews = _filter_paths(artifacts.previews, glyph or animation)
    lines = [
        "glyph-arts petiglyph project",
        "",
        f"project: {project.name}",
        f"root: {project.root}",
        f"font: {project.font_name}",
        f"build: {project.build_dir}",
        f"glyph-size: {project.glyph_size or '-'}",
        f"codepoint-start: {project.codepoint_start or '-'}",
        "",
        f"ttf: {len(artifacts.ttf)}",
        f"bdf: {len(artifacts.bdf)}",
        f"glyph-map: {artifacts.glyph_map or '-'}",
        f"sample: {artifacts.sample or '-'}",
        f"previews: {len(previews)}",
    ]
    if sample_text:
        lines.extend(["", "sample:", sample_text])
    if glyphs:
        lines.extend(["", "glyphs:"])
        for item in glyphs[:20]:
            label = item.name or item.source or "-"
            lines.append(f"  {item.codepoint or '-':<10} {item.character} {label}")
        if len(glyphs) > 20:
            lines.append(f"  ... {len(glyphs) - 20} more")
    return "\n".join(lines).rstrip() + "\n"


def render_petiglyph_chat_previews(
    project: PetiglyphProject,
    *,
    glyph: str = "",
    animation: str = "",
    width: int = 80,
    height: int = 24,
    limit: int = 6,
    no_color: bool = False,
) -> int:
    previews = _filter_paths(project.artifacts.previews, glyph or animation)[: max(0, limit)]
    if not previews:
        print("\npreview fallback: no build/previews/*.png files found")
        return 0
    try:
        from cli_charts.render.media_engine import render_image
    except Exception as exc:
        print(f"\npreview fallback unavailable: {exc}", file=sys.stderr)
        return 1

    rc = 0
    with tempfile.TemporaryDirectory(prefix="glyph-arts-petiglyph-preview-") as tmpdir:
        for preview in previews:
            print(f"\npreview: {preview.name}")
            render_path = _alpha_composite_preview(preview, Path(tmpdir))
            current = render_image(
                str(render_path),
                width,
                height,
                symbols="ascii",
                no_color=no_color,
                engine="pillow",
                chat=True,
                mode="auto",
                trim=True,
                image_style="classic",
                color_mode="original",
                background="dark",
                dither="atkinson",
                dither_strength=0.8,
                chafa_format="symbols",
                chafa_colors="none" if no_color else "auto",
                chafa_symbols="ascii",
            )
            rc = rc or current
    return rc


def project_to_dict(project: PetiglyphProject, *, glyph: str = "", animation: str = "") -> dict[str, Any]:
    artifacts = project.artifacts
    sample_text = artifacts.sample.read_text(encoding="utf-8", errors="replace") if artifacts.sample else ""
    return {
        "name": project.name,
        "root": str(project.root),
        "manifest": str(project.manifest),
        "input_dir": str(project.input_dir),
        "build_dir": str(project.build_dir),
        "font_name": project.font_name,
        "glyph_size": project.glyph_size,
        "codepoint_start": project.codepoint_start,
        "animations": [
            {
                "name": item.name,
                "fps": item.fps,
                "frames": list(item.frames),
                "rows": item.rows,
                "cols": item.cols,
            }
            for item in project.animations
        ],
        "artifacts": {
            "ttf": [str(path) for path in artifacts.ttf],
            "bdf": [str(path) for path in artifacts.bdf],
            "glyph_map": str(artifacts.glyph_map) if artifacts.glyph_map else "",
            "sample": str(artifacts.sample) if artifacts.sample else "",
            "sample_text": sample_text,
            "previews": [str(path) for path in _filter_paths(artifacts.previews, glyph or animation)],
            "glyphs": [
                {
                    "name": item.name,
                    "source": item.source,
                    "codepoint": item.codepoint,
                    "character": item.character,
                    "preview": item.preview,
                }
                for item in _filter_glyphs(artifacts.glyphs, glyph)
            ],
        },
    }


def _run_destructive(args: Any, tokens: list[str]) -> int:
    backend = _select_backend(args)
    cli_args = _build_cli_args(args, tokens, [])
    if not getattr(args, "yes", False):
        print("[glyph-arts] petiglyph destructive dry-run: " + _quote_command(backend.command(cli_args)))
        print("Pass --yes to execute this destructive Petiglyph command.")
        return 0
    return backend.run(cli_args, dry_run=getattr(args, "dry_run", False))


def _alpha_composite_preview(path: Path, tmpdir: Path) -> Path:
    """Composite transparent Petiglyph masks onto white for ASCII fallback."""
    try:
        from PIL import Image

        image = Image.open(path).convert("RGBA")
        if image.getchannel("A").getextrema() == (255, 255):
            return path
        base = Image.new("RGBA", image.size, (255, 255, 255, 255))
        base.alpha_composite(image)
        out = tmpdir / path.name
        base.convert("RGB").save(out)
        return out
    except Exception:
        return path


def _build_cli_args(args: Any, tokens: list[str], raw_argv: list[str]) -> list[str]:
    cli_args = list(tokens)
    inputs = [item for group in (getattr(args, "petiglyph_input", None) or []) for item in group]
    if inputs:
        cli_args.extend(["--input", *inputs])
    if getattr(args, "rows", None) is not None:
        cli_args.extend(["--rows", str(args.rows)])
    if getattr(args, "cols", None) is not None:
        cli_args.extend(["--cols", str(args.cols)])
    if getattr(args, "bleed", ""):
        cli_args.extend(["--bleed", str(args.bleed)])
    if getattr(args, "threshold", None) is not None:
        cli_args.extend(["--threshold", str(args.threshold)])
    if getattr(args, "clear_threshold", False):
        cli_args.append("--clear-threshold")
    if getattr(args, "force_remap", False):
        cli_args.append("--force-remap")
    if getattr(args, "build", False):
        cli_args.append("--build")
    if getattr(args, "install", False):
        cli_args.append("--install")
    if _has_token(raw_argv, "--fps"):
        cli_args.extend(["--fps", str(getattr(args, "fps", 12))])
    if _has_token(raw_argv, "--invert") and "--invert" not in cli_args:
        cli_args.append("--invert")
    for extra in getattr(args, "petiglyph_arg", None) or []:
        cli_args.extend(shlex.split(extra))
    return cli_args


def _select_backend(args: Any) -> PetiglyphBackend:
    backend = (getattr(args, "petiglyph_backend", "auto") or "auto").strip().lower()
    if backend == "native":
        return NativePetiglyphBackend()
    return CliPetiglyphBackend()


def _is_enhanced_show_sample(tokens: list[str], args: Any) -> bool:
    return (
        len(tokens) >= 3
        and tokens[0] == "use-project"
        and tokens[2] == "show-sample"
        and (getattr(args, "chat", False) or getattr(args, "petiglyph_json_output", False))
    )


def _resolve_project_root(project_ref: str) -> Path:
    raw = Path(project_ref).expanduser()
    candidates = [raw]
    if not raw.is_absolute():
        candidates.append(Path.cwd() / raw)
    for candidate in candidates:
        if candidate.exists():
            return candidate.resolve()
    return raw.resolve()


def _read_toml(path: Path) -> dict[str, Any]:
    try:
        import tomllib

        with path.open("rb") as handle:
            data = tomllib.load(handle)
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def _read_animations(data: dict[str, Any]) -> list[PetiglyphAnimation]:
    raw = data.get("animations") or []
    animations: list[PetiglyphAnimation] = []
    if not isinstance(raw, list):
        return animations
    for item in raw:
        if not isinstance(item, dict):
            continue
        frames = item.get("frames") or []
        if not isinstance(frames, list):
            frames = []
        animations.append(PetiglyphAnimation(
            name=str(item.get("name") or item.get("source") or ""),
            fps=_int_or_none(item.get("fps")),
            frames=tuple(str(frame) for frame in frames),
            rows=_int_or_none(item.get("rows")),
            cols=_int_or_none(item.get("cols")),
        ))
    return animations


def _read_glyph_map(path: Path, previews: tuple[Path, ...]) -> list[PetiglyphGlyph]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return []
    preview_by_stem = {preview.stem.lower(): preview for preview in previews}
    glyphs: list[PetiglyphGlyph] = []
    for item in _iter_mapping_items(data):
        name = str(item.get("name") or item.get("glyph") or item.get("id") or "")
        source = str(item.get("source") or item.get("path") or item.get("file") or "")
        codepoint = _format_codepoint(item.get("codepoint") or item.get("unicode") or item.get("char"))
        char = _codepoint_to_char(codepoint)
        key = (name or Path(source).stem).lower()
        preview = str(preview_by_stem.get(key, "")) if key else ""
        glyphs.append(PetiglyphGlyph(name=name, source=source, codepoint=codepoint, character=char, preview=preview))
    return glyphs


def _iter_mapping_items(value: Any) -> list[dict[str, Any]]:
    found: list[dict[str, Any]] = []
    if isinstance(value, list):
        for item in value:
            found.extend(_iter_mapping_items(item))
    elif isinstance(value, dict):
        keys = set(value)
        if keys & {"codepoint", "unicode", "char"} and keys & {"name", "glyph", "id", "source", "path", "file"}:
            found.append(value)
        else:
            for key, item in value.items():
                if isinstance(item, (str, int)) and _looks_like_codepoint(item):
                    found.append({"name": str(key), "codepoint": item})
                else:
                    found.extend(_iter_mapping_items(item))
    return found


def _looks_like_codepoint(value: Any) -> bool:
    if isinstance(value, int):
        return True
    text = str(value).strip()
    return len(text) == 1 or text.upper().startswith("U+") or text.lower().startswith("0x")


def _format_codepoint(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, int):
        return f"U+{value:04X}"
    text = str(value).strip()
    if len(text) == 1:
        return f"U+{ord(text):04X}"
    if text.lower().startswith("0x"):
        try:
            return f"U+{int(text, 16):04X}"
        except ValueError:
            return text
    if text.upper().startswith("U+"):
        return "U+" + text[2:].upper()
    return text


def _codepoint_to_char(codepoint: str) -> str:
    if not codepoint.upper().startswith("U+"):
        return ""
    try:
        value = int(codepoint[2:], 16)
        if 0 <= value <= 0x10FFFF:
            return chr(value)
    except ValueError:
        return ""
    return ""


def _filter_glyphs(glyphs: tuple[PetiglyphGlyph, ...], needle: str) -> list[PetiglyphGlyph]:
    needle = (needle or "").strip().lower()
    if not needle:
        return list(glyphs)
    return [
        item for item in glyphs
        if needle in item.name.lower() or needle in item.source.lower() or needle in item.codepoint.lower()
    ]


def _filter_paths(paths: tuple[Path, ...], needle: str) -> list[Path]:
    needle = (needle or "").strip().lower()
    if not needle:
        return list(paths)
    return [path for path in paths if needle in path.name.lower() or needle in path.stem.lower()]


def _int_or_none(value: Any) -> int | None:
    try:
        return int(value)
    except (TypeError, ValueError):
        return None


def _has_token(raw_argv: list[str], token: str) -> bool:
    return token in raw_argv or any(item.startswith(token + "=") for item in raw_argv)


def _quote_command(command: list[str]) -> str:
    return " ".join(_quote_part(part) for part in command)


def _quote_part(part: str) -> str:
    if not part or any(ch.isspace() for ch in part):
        return '"' + part.replace('"', '\\"') + '"'
    return part
