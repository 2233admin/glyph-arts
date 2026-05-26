"""Chat glyph probing and profile recommendations."""

from __future__ import annotations

from dataclasses import dataclass

from wcwidth import wcswidth

from cli_charts.font_downloads import downloaded_font_status
from cli_charts.font_tier import detect_font_tier
from cli_charts.terminal_profiles import detect_terminal_profile, detect_terminal_runtime

TIER_RANK = {
    "ascii": 0,
    "unicode": 1,
    "unicode-extended": 2,
    "nerd": 3,
}

PROFILE_TO_TIER = {
    "ascii": "ascii",
    "safe": "unicode",
    "rich": "unicode-extended",
    "max": "nerd",
}


@dataclass(frozen=True)
class ProbeCase:
    key: str
    label: str
    sample: str
    required_tier: str
    note: str


PROBE_CASES = (
    ProbeCase("ascii", "ASCII", "+-|/\\_[]{}", "ascii", "plain transcript fallback"),
    ProbeCase("box", "Box drawing", "┌─┬─┐│└─┴─┘", "unicode", "tables, panels, diagrams"),
    ProbeCase("block", "Block elements", "▁▂▃▄▅▆▇█ ░▒▓", "unicode", "bars and dense fills"),
    ProbeCase("braille", "Braille", "⠁⠃⠇⡇⣿", "unicode-extended", "plots and image approximations"),
    ProbeCase("sextant", "Sextant", "🬀🬁🬂🬃🬄🬅", "unicode-extended", "high-density pixel glyphs"),
    ProbeCase("arrows", "Arrows/math", "←↑→↓ ⇄ ∑ ∫ √ ≈ ≤ ≥", "unicode", "formula and flow labels"),
    ProbeCase("emoji", "Emoji", "✅ ⚠️ 🔥 📈", "unicode-extended", "status and chat labels"),
    ProbeCase("cjk", "CJK width", "开始 -> 完成", "unicode", "Chinese labels and mixed-width layout"),
    ProbeCase("nerd", "Nerd Font PUA", "\ue0b0 \uf013 \uf0e7 \uf121", "nerd", "private-use icons"),
)


def chat_profile_tier(profile: str, detected_tier: str | None = None) -> str:
    profile = (profile or "auto").strip().lower()
    detected = detected_tier or detect_font_tier()
    if profile == "auto":
        return detected
    return PROFILE_TO_TIER.get(profile, detected)


def recommend_chat_profile(font_tier: str | None = None) -> str:
    tier = font_tier or detect_font_tier()
    rank = TIER_RANK.get(tier, 1)
    if rank <= 0:
        return "ascii"
    if rank == 1:
        return "safe"
    if rank == 2:
        return "rich"
    return "max"


def probe_rows(font_tier: str | None = None) -> list[dict[str, object]]:
    tier = font_tier or detect_font_tier()
    rank = TIER_RANK.get(tier, 1)
    rows: list[dict[str, object]] = []
    for case in PROBE_CASES:
        sample_width = wcswidth(case.sample)
        width_ok = sample_width >= 0
        tier_ok = rank >= TIER_RANK[case.required_tier]
        rows.append({
            "key": case.key,
            "label": case.label,
            "sample": case.sample,
            "required_tier": case.required_tier,
            "ok": bool(width_ok and tier_ok),
            "width": sample_width,
            "note": case.note,
        })
    return rows


def render_chat_probe(font_tier: str | None = None) -> str:
    tier = font_tier or detect_font_tier()
    profile = recommend_chat_profile(tier)
    lines = [
        "glyph-arts chat glyph probe",
        "",
        f"font-tier: {tier}",
        f"recommended chat profile: {profile}",
        "",
    ]
    for row in probe_rows(tier):
        mark = "OK" if row["ok"] else "FALLBACK"
        lines.append(
            f"{str(row['label']):<14} {mark:<8} "
            f"tier={row['required_tier']:<16} width={row['width']:<3} {row['sample']}"
        )
        lines.append(f"{'':<14} {'':<8} {row['note']}")
    return "\n".join(lines).rstrip() + "\n"


def render_chat_profile(font_tier: str | None = None) -> str:
    tier = font_tier or detect_font_tier()
    selected = recommend_chat_profile(tier)
    lines = [
        "glyph-arts chat profiles",
        "",
        f"detected font-tier: {tier}",
        f"recommended: {selected}",
        "",
        "ascii  plain ASCII only; maximum portability",
        "safe   Unicode boxes, arrows, blocks; no exotic glyph dependency",
        "rich   Braille/sextant/emoji-friendly chat rendering",
        "max    Nerd Font PUA plus broad symbol fallback",
    ]
    return "\n".join(lines).rstrip() + "\n"


def render_fix_chat_plan(font_tier: str | None = None) -> str:
    terminal = detect_terminal_profile()
    runtime = detect_terminal_runtime()
    tier = font_tier or detect_font_tier()
    recommendation = recommend_chat_profile(tier)
    fonts_ok, fonts_detail = downloaded_font_status()
    missing = []
    if not fonts_ok:
        missing.append("downloaded max font pack")
    if recommendation != "max":
        missing.append("max glyph profile not currently safe")

    lines = [
        "glyph-arts chat fix plan",
        "",
        f"terminal: {terminal.name} ({terminal.key})",
        f"runtime: {runtime.name} ({runtime.key}, shell={runtime.shell})",
        f"font-tier: {tier}",
        f"recommended chat profile: {recommendation}",
        f"downloaded-fonts: {'OK' if fonts_ok else 'MISSING'} {fonts_detail}",
        "",
        "Recommended font fallback chain:",
        "1. Iosevka or JuliaMono",
        "2. Symbols Nerd Font",
        "3. Noto Sans Symbols 2",
        "4. Noto Color Emoji",
        "5. GNU Unifont",
        "",
        "Commands:",
        "glyph-arts fonts install max",
        "glyph-arts chat probe",
        "glyph-arts doctor --fix-chat",
        "",
        "Terminal notes:",
        "Windows Terminal / VS Code / Warp: select the main font in the profile settings, then add fallback fonts when the host supports fallback lists.",
        "WSL: install CLI backends inside WSL, but configure fonts in the Windows terminal host.",
    ]
    if missing:
        lines.extend(["", "Missing:", *[f"- {item}" for item in missing]])
    return "\n".join(lines).rstrip() + "\n"


def run_chat_health_command(args) -> int:
    action = args.art_text[0] if args.art_text else "probe"
    tier = chat_profile_tier(getattr(args, "chat_profile", "auto"), getattr(args, "font_tier", None))
    if action in {"probe", "glyphs"}:
        print(render_chat_probe(tier), end="")
        return 0
    if action in {"profile", "profiles"}:
        print(render_chat_profile(tier), end="")
        return 0
    if action in {"fix", "fix-chat", "doctor"}:
        print(render_fix_chat_plan(tier), end="")
        return 0
    print("ERROR:chat-health: expected probe, profile, or fix", flush=True)
    return 2
