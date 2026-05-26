"""On-demand downloads and status checks for optional OFL terminal fonts."""

from __future__ import annotations

import argparse
import json
import shutil
import tarfile
import urllib.request
import zipfile
from dataclasses import dataclass
from pathlib import Path

FONT_SUFFIXES = {".ttf", ".otf", ".ttc", ".woff", ".woff2"}


@dataclass(frozen=True)
class FontDownloadSpec:
    key: str
    name: str
    repo: str
    asset_prefixes: tuple[str, ...]
    asset_suffixes: tuple[str, ...]
    license_url: str
    family_hint: str
    reserved_font_name: str = ""
    note: str = ""


FONT_DOWNLOADS: dict[str, FontDownloadSpec] = {
    "iosevka": FontDownloadSpec(
        key="iosevka",
        name="Iosevka",
        repo="be5invis/Iosevka",
        asset_prefixes=("PkgTTF-Iosevka-", "PkgTTC-Iosevka-"),
        asset_suffixes=(".zip",),
        license_url="https://raw.githubusercontent.com/be5invis/Iosevka/main/LICENSE.md",
        family_hint="Iosevka",
        note="dense coding font; excellent for charts and tables",
    ),
    "juliamono": FontDownloadSpec(
        key="juliamono",
        name="JuliaMono",
        repo="cormullion/juliamono",
        asset_prefixes=("JuliaMono",),
        asset_suffixes=(".zip",),
        license_url="https://raw.githubusercontent.com/cormullion/juliamono/master/LICENSE",
        family_hint="JuliaMono",
        reserved_font_name="JuliaMono",
        note="wide Unicode math and technical glyph coverage",
    ),
    "jetbrainsmono-nerd": FontDownloadSpec(
        key="jetbrainsmono-nerd",
        name="JetBrainsMono Nerd Font",
        repo="ryanoasis/nerd-fonts",
        asset_prefixes=("JetBrainsMono",),
        asset_suffixes=(".zip", ".tar.xz"),
        license_url="https://raw.githubusercontent.com/ryanoasis/nerd-fonts/master/LICENSE",
        family_hint="JetBrainsMono Nerd Font",
        note="Nerd Font icons plus strong terminal readability",
    ),
    "symbols-nerd-font": FontDownloadSpec(
        key="symbols-nerd-font",
        name="Symbols Nerd Font",
        repo="ryanoasis/nerd-fonts",
        asset_prefixes=("NerdFontsSymbolsOnly", "SymbolsOnly"),
        asset_suffixes=(".zip", ".tar.xz"),
        license_url="https://raw.githubusercontent.com/ryanoasis/nerd-fonts/master/LICENSE",
        family_hint="Symbols Nerd Font",
        note="fallback private-use icon coverage",
    ),
    "firacode-nerd": FontDownloadSpec(
        key="firacode-nerd",
        name="FiraCode Nerd Font",
        repo="ryanoasis/nerd-fonts",
        asset_prefixes=("FiraCode",),
        asset_suffixes=(".zip", ".tar.xz"),
        license_url="https://raw.githubusercontent.com/ryanoasis/nerd-fonts/master/LICENSE",
        family_hint="FiraCode Nerd Font",
        note="ligature-friendly Nerd Font fallback",
    ),
    "hack-nerd": FontDownloadSpec(
        key="hack-nerd",
        name="Hack Nerd Font",
        repo="ryanoasis/nerd-fonts",
        asset_prefixes=("Hack",),
        asset_suffixes=(".zip", ".tar.xz"),
        license_url="https://raw.githubusercontent.com/ryanoasis/nerd-fonts/master/LICENSE",
        family_hint="Hack Nerd Font",
        note="compact cross-platform Nerd Font fallback",
    ),
    "cascadia-code": FontDownloadSpec(
        key="cascadia-code",
        name="Cascadia Code",
        repo="microsoft/cascadia-code",
        asset_prefixes=("CascadiaCode-",),
        asset_suffixes=(".zip",),
        license_url="https://raw.githubusercontent.com/microsoft/cascadia-code/main/LICENSE",
        family_hint="Cascadia Code",
        note="Windows Terminal native-friendly font",
    ),
    "monaspace": FontDownloadSpec(
        key="monaspace",
        name="Monaspace",
        repo="githubnext/monaspace",
        asset_prefixes=("monaspace-", "Monaspace"),
        asset_suffixes=(".zip",),
        license_url="https://raw.githubusercontent.com/githubnext/monaspace/main/LICENSE",
        family_hint="Monaspace",
        note="modern coding font family with texture variants",
    ),
}

FONT_GROUPS: dict[str, tuple[str, ...]] = {
    "core": ("iosevka", "juliamono", "jetbrainsmono-nerd", "symbols-nerd-font"),
    "nerd": ("jetbrainsmono-nerd", "symbols-nerd-font", "firacode-nerd", "hack-nerd"),
    "programming": ("iosevka", "juliamono", "cascadia-code", "monaspace"),
}
FONT_GROUPS["all"] = tuple(FONT_DOWNLOADS)


def default_font_dir() -> Path:
    return Path.home() / ".glyph-arts" / "fonts"


def install_fonts(fonts: list[str], dest: Path | None = None) -> int:
    dest = dest or default_font_dir()
    selected = _selected_specs(fonts)
    dest.mkdir(parents=True, exist_ok=True)
    for spec in selected:
        target = dest / spec.key
        target.mkdir(parents=True, exist_ok=True)
        asset_name, asset_url = _latest_asset(spec)
        archive = target / asset_name
        print(f"[glyph-arts] download {spec.name}: {asset_url}")
        _download(asset_url, archive)
        extracted = _extract_fonts(archive, target)
        _download(spec.license_url, target / "LICENSE")
        _write_notice(spec, target, asset_url, extracted)
        print(f"[glyph-arts] installed {spec.name}: {target}")
    print(_terminal_hint(selected, dest), end="")
    return 0


def render_font_list() -> str:
    lines = ["glyph-arts downloadable fonts", ""]
    for key, spec in FONT_DOWNLOADS.items():
        lines.append(f"{key:<20} {spec.name:<24} {spec.note}")
    lines.extend(["", "Groups:"])
    for group, names in FONT_GROUPS.items():
        lines.append(f"{group:<20} {', '.join(names)}")
    return "\n".join(lines).rstrip() + "\n"


def render_font_status(dest: Path | None = None) -> str:
    dest = dest or default_font_dir()
    lines = ["glyph-arts font downloads", f"root: {dest}", ""]
    for key, spec in FONT_DOWNLOADS.items():
        record = _font_record(spec, dest)
        mark = "OK" if record["installed"] else "MISSING"
        detail = record["detail"]
        lines.append(f"{key:<20} {mark:<7} {detail}")
    return "\n".join(lines).rstrip() + "\n"


def downloaded_font_status(dest: Path | None = None) -> tuple[bool, str]:
    dest = dest or default_font_dir()
    records = [_font_record(spec, dest) for spec in FONT_DOWNLOADS.values()]
    installed = [str(record["name"]) for record in records if record["installed"]]
    if installed:
        return True, f"{', '.join(installed)} in {dest}"
    return False, f"No downloaded fonts found in {dest}"


def remove_fonts(fonts: list[str], dest: Path | None = None) -> int:
    dest = dest or default_font_dir()
    for spec in _selected_specs(fonts):
        target = dest / spec.key
        if target.exists():
            shutil.rmtree(target)
            print(f"[glyph-arts] removed {spec.name}: {target}")
        else:
            print(f"[glyph-arts] missing {spec.name}: {target}")
    return 0


def run_fonts_command(args) -> int:
    action = args.art_text[0] if args.art_text else "status"
    names = args.art_text[1:]
    dest = Path(args.font_dir).expanduser() if getattr(args, "font_dir", "") else default_font_dir()
    if action in {"list", "ls"}:
        print(render_font_list(), end="")
        return 0
    if action in {"status", "doctor"}:
        print(render_font_status(dest), end="")
        return 0
    if action in {"install", "download"}:
        return install_fonts(names or ["core"], dest)
    if action in {"remove", "rm", "clean"}:
        return remove_fonts(names or ["core"], dest)
    print("ERROR:fonts: expected list, status, install, or remove", flush=True)
    return 2


def _selected_specs(fonts: list[str]) -> list[FontDownloadSpec]:
    names = fonts or ["core"]
    expanded: list[str] = []
    for name in names:
        expanded.extend(FONT_GROUPS.get(name, (name,)))
    unknown = [name for name in expanded if name not in FONT_DOWNLOADS]
    if unknown:
        valid = ", ".join([*FONT_GROUPS, *FONT_DOWNLOADS])
        raise SystemExit(f"unknown font download: {', '.join(unknown)}; valid: {valid}")
    result: list[FontDownloadSpec] = []
    seen: set[str] = set()
    for name in expanded:
        if name in seen:
            continue
        seen.add(name)
        result.append(FONT_DOWNLOADS[name])
    return result


def _font_record(spec: FontDownloadSpec, dest: Path) -> dict[str, object]:
    target = dest / spec.key
    files = sorted(path for path in target.glob("*") if path.suffix.lower() in FONT_SUFFIXES)
    if files:
        detail = f"{len(files)} font files; family={spec.family_hint}; path={target}"
        return {"installed": True, "name": spec.name, "detail": detail}
    return {"installed": False, "name": spec.name, "detail": spec.note or "not downloaded"}


def _latest_asset(spec: FontDownloadSpec) -> tuple[str, str]:
    api_url = f"https://api.github.com/repos/{spec.repo}/releases/latest"
    with urllib.request.urlopen(_request(api_url), timeout=30) as response:
        payload = json.loads(response.read().decode("utf-8"))
    assets = payload.get("assets", [])
    for asset in assets:
        name = str(asset.get("name", ""))
        url = str(asset.get("browser_download_url", ""))
        if name.startswith(spec.asset_prefixes) and name.endswith(spec.asset_suffixes) and url:
            return name, url
    raise RuntimeError(f"no matching {spec.name} font zip asset found in latest release")


def _download(url: str, dest: Path) -> None:
    with urllib.request.urlopen(_request(url), timeout=120) as response:
        dest.write_bytes(response.read())


def _extract_fonts(archive: Path, dest: Path) -> list[Path]:
    dest.mkdir(parents=True, exist_ok=True)
    if archive.name.endswith(".tar.xz"):
        return _extract_tar_fonts(archive, dest)
    return _extract_zip_fonts(archive, dest)


def _extract_zip_fonts(archive: Path, dest: Path) -> list[Path]:
    extracted: list[Path] = []
    with zipfile.ZipFile(archive) as zf:
        for info in zf.infolist():
            name = info.filename.replace("\\", "/")
            if name.endswith("/"):
                continue
            suffix = Path(name).suffix.lower()
            if suffix not in FONT_SUFFIXES:
                continue
            out = dest / Path(name).name
            out.write_bytes(zf.read(info))
            extracted.append(out)
    if not extracted:
        raise RuntimeError(f"no font files found in {archive.name}")
    return extracted


def _extract_tar_fonts(archive: Path, dest: Path) -> list[Path]:
    extracted: list[Path] = []
    with tarfile.open(archive, "r:xz") as tf:
        for member in tf.getmembers():
            if not member.isfile():
                continue
            name = member.name.replace("\\", "/")
            suffix = Path(name).suffix.lower()
            if suffix not in FONT_SUFFIXES:
                continue
            src = tf.extractfile(member)
            if src is None:
                continue
            out = dest / Path(name).name
            out.write_bytes(src.read())
            extracted.append(out)
    if not extracted:
        raise RuntimeError(f"no font files found in {archive.name}")
    return extracted


def _write_notice(spec: FontDownloadSpec, dest: Path, asset_url: str, fonts: list[Path]) -> None:
    reserved = f"\nReserved Font Name: {spec.reserved_font_name}" if spec.reserved_font_name else ""
    files = "\n".join(f"- {path.name}" for path in fonts)
    notice = (
        f"{spec.name}\n"
        f"Source: https://github.com/{spec.repo}\n"
        f"Downloaded asset: {asset_url}\n"
        "License: SIL Open Font License 1.1\n"
        f"Suggested terminal family: {spec.family_hint}"
        f"{reserved}\n\n"
        "Downloaded font files:\n"
        f"{files}\n"
    )
    (dest / "NOTICE.txt").write_text(notice, encoding="utf-8")


def _terminal_hint(specs: list[FontDownloadSpec], dest: Path) -> str:
    families = ", ".join(spec.family_hint for spec in specs)
    return (
        "[glyph-arts] next: install or select one of these terminal font families: "
        f"{families}\n"
        f"[glyph-arts] downloaded files live under: {dest}\n"
    )


def _request(url: str) -> urllib.request.Request:
    return urllib.request.Request(url, headers={"User-Agent": "glyph-arts-font-downloader"})


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Download optional glyph-arts OFL fonts")
    parser.add_argument("action", nargs="?", default="status", choices=["list", "status", "install", "remove"])
    parser.add_argument("fonts", nargs="*")
    parser.add_argument("--font", action="append", choices=[*FONT_GROUPS, *FONT_DOWNLOADS], default=[])
    parser.add_argument("--dest", type=Path, default=default_font_dir())
    args = parser.parse_args(argv)
    fonts = [*args.font, *args.fonts]
    if args.action == "list":
        print(render_font_list(), end="")
        return 0
    if args.action == "status":
        print(render_font_status(args.dest), end="")
        return 0
    if args.action == "remove":
        return remove_fonts(fonts or ["core"], args.dest)
    return install_fonts(fonts or ["core"], args.dest)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
