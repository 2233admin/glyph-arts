from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "chat-drawing"
VERIFY = SKILL_ROOT / "scripts" / "verify_chat_art.py"


def test_chat_drawing_skill_has_closed_loop_contract() -> None:
    skill = (SKILL_ROOT / "SKILL.md").read_text(encoding="utf-8")
    metadata = (SKILL_ROOT / "agents" / "openai.yaml").read_text(encoding="utf-8")
    assert "name: chat-drawing" in skill
    assert "glyph-arts chat" in skill
    assert "Render first, verify second" in skill
    assert "scripts/verify_chat_art.py" in skill
    assert "references/routing.md" in skill
    assert "references/quality.md" in skill
    assert "references/decision-tree.md" in skill
    assert "references/agent-contract.md" in skill
    assert "Chat Drawing" in metadata
    assert "verify" in metadata


def test_chat_drawing_skill_references_cover_core_routes() -> None:
    routing = (SKILL_ROOT / "references" / "routing.md").read_text(encoding="utf-8")
    for route in [
        "chat image",
        "chat incplot",
        "chat plotext",
        "chat textplot",
        "chat turtle",
        "chat graph",
        "chat diagram flowchart",
        "chat diagram note",
        "chat effects",
        "chat sdr spectrum",
        "chat waterfall",
    ]:
        assert route in routing


def test_chat_drawing_cross_agent_contract_is_portable() -> None:
    contract = (SKILL_ROOT / "references" / "agent-contract.md").read_text(encoding="utf-8")
    decision_tree = (SKILL_ROOT / "references" / "decision-tree.md").read_text(encoding="utf-8")
    payload = json.loads((SKILL_ROOT / "agents" / "contract.json").read_text(encoding="utf-8"))

    for adapter in ["claude.md", "codex.md", "opencode.md"]:
        assert (SKILL_ROOT / "agents" / adapter).exists()

    assert "Codex, Claude, OpenCode" in contract
    assert "glyph-arts chat incplot" in contract
    assert "glyph-arts chat textplot" in contract
    assert "glyph-arts chat turtle" in contract
    assert "Unknown raw data shape" in decision_tree
    assert payload["loop"] == ["route", "render_stdout", "verify", "rerender_on_failure", "reply_with_stdout"]
    assert payload["routes"]["unknown_data"] == "glyph-arts chat incplot"


def test_verify_chat_art_accepts_good_box() -> None:
    art = "┌────┐\n│ OK │\n└────┘\n"
    result = subprocess.run(
        [sys.executable, str(VERIFY), "--max-width", "20", "--require-label", "OK", "--equal-box-width"],
        input=art,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
    assert payload["stats"]["max_width"] == 6


def test_verify_chat_art_rejects_bad_box_width() -> None:
    art = "┌────┐\n│ bad │\n└────┘\n"
    result = subprocess.run(
        [sys.executable, str(VERIFY), "--equal-box-width"],
        input=art,
        text=True,
        capture_output=True,
        check=False,
    )
    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert payload["ok"] is False
    assert "box or frame lines are not equal width" in payload["errors"]


def test_verify_chat_art_rejects_ansi_by_default() -> None:
    result = subprocess.run(
        [sys.executable, str(VERIFY)],
        input="\x1b[31mred\x1b[0m\n",
        text=True,
        capture_output=True,
        check=False,
    )
    payload = json.loads(result.stdout)
    assert result.returncode == 1
    assert "output contains ANSI escape codes" in payload["errors"]


def test_verify_chat_art_uses_display_width_for_chinese_box() -> None:
    art = "┌──────────┐\n│ 中文排版 │\n└──────────┘\n"
    result = subprocess.run(
        [sys.executable, str(VERIFY), "--equal-box-width"],
        input=art,
        text=True,
        capture_output=True,
        check=True,
    )
    payload = json.loads(result.stdout)
    assert payload["ok"] is True
