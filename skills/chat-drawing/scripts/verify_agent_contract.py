#!/usr/bin/env python3
"""Verify that chat-drawing agent adapters cannot skip the render loop."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


REQUIRED_LOOP = [
    "route",
    "render_stdout",
    "verify",
    "rerender_on_failure",
    "reply_with_stdout",
]

REQUIRED_ROUTES = {
    "unknown_data": "glyph-arts chat incplot",
    "plot_overlays": "glyph-arts chat plotext",
    "function_curve": "glyph-arts chat textplot",
    "drawille_path": "glyph-arts chat turtle",
    "mermaid": "glyph-arts chat mermaid",
    "diagram": "glyph-arts chat diagram",
    "graph": "glyph-arts chat graph",
    "image": "glyph-arts chat image",
    "sdr_spectrum": "glyph-arts chat sdr spectrum",
    "sdr_waterfall": "glyph-arts chat waterfall",
}

REQUIRED_ADAPTER_TERMS = {
    "glyph-arts chat": "route through glyph-arts chat",
    "stdout": "render or capture stdout",
    "verify_chat_art.py": "run the verifier",
    "rerender": "rerender on failure",
}

FORBIDDEN_PHRASES = [
    "verification is optional",
    "skip verification",
    "save only",
    "artifact only",
    "reply without verification",
]


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as exc:
        raise ValueError(f"missing file: {path}") from exc
    except json.JSONDecodeError as exc:
        raise ValueError(f"invalid JSON: {path}: {exc}") from exc
    if not isinstance(data, dict):
        raise ValueError(f"{path}: top-level JSON must be an object")
    return data


def _load_protocol_validator(repo_root: Path) -> Any | None:
    sys.path.insert(0, str(repo_root))
    try:
        from cli_charts.render_target import validate_protocol
    except Exception:
        return None
    return validate_protocol


def _check_contract(skill_root: Path, errors: list[str]) -> dict[str, Any]:
    contract_path = skill_root / "agents" / "contract.json"
    contract = _read_json(contract_path)

    if contract.get("entry") != "glyph-arts chat":
        errors.append("contract.entry must be glyph-arts chat")
    if contract.get("loop") != REQUIRED_LOOP:
        errors.append(f"contract.loop must be {REQUIRED_LOOP}")

    anti_lazy = contract.get("anti_lazy")
    if not isinstance(anti_lazy, dict):
        errors.append("contract.anti_lazy must exist")
    else:
        gate = anti_lazy.get("gate", "")
        if "verify_agent_contract.py" not in gate:
            errors.append("contract.anti_lazy.gate must reference verify_agent_contract.py")
        must = anti_lazy.get("must")
        forbidden = anti_lazy.get("forbidden")
        if not isinstance(must, list) or len(must) < 5:
            errors.append("contract.anti_lazy.must must list the closed-loop duties")
        if not isinstance(forbidden, list) or len(forbidden) < 5:
            errors.append("contract.anti_lazy.forbidden must list lazy failure modes")

    verify_command = contract.get("verify", "")
    if "verify_chat_art.py" not in verify_command or "--max-width" not in verify_command:
        errors.append("contract.verify must call verify_chat_art.py with --max-width")

    routes = contract.get("routes")
    if not isinstance(routes, dict):
        errors.append("contract.routes must be an object")
    else:
        for key, command in REQUIRED_ROUTES.items():
            actual = routes.get(key)
            if actual != command:
                errors.append(f"contract.routes.{key} must be {command!r}, got {actual!r}")

    refs = contract.get("routing_refs")
    if not isinstance(refs, list):
        errors.append("contract.routing_refs must be a list")
    else:
        for ref in refs:
            if not isinstance(ref, str) or not (skill_root / ref).exists():
                errors.append(f"missing routing reference: {ref!r}")

    return contract


def _check_agent_adapters(skill_root: Path, contract: dict[str, Any], errors: list[str]) -> None:
    adapters = contract.get("agent_adapters")
    if not isinstance(adapters, list) or not adapters:
        errors.append("contract.agent_adapters must list adapter files")
        return

    for adapter in adapters:
        if not isinstance(adapter, str):
            errors.append(f"adapter entry must be a string: {adapter!r}")
            continue
        path = skill_root / "agents" / adapter
        if not path.exists():
            errors.append(f"missing agent adapter: {adapter}")
            continue
        text = path.read_text(encoding="utf-8").lower()
        for needle, duty in REQUIRED_ADAPTER_TERMS.items():
            if needle.lower() not in text:
                errors.append(f"{adapter}: missing {duty} ({needle})")
        for phrase in FORBIDDEN_PHRASES:
            if phrase in text:
                errors.append(f"{adapter}: forbidden lazy phrase: {phrase}")


def _check_openai_adapter(skill_root: Path, errors: list[str]) -> None:
    path = skill_root / "agents" / "openai.yaml"
    if not path.exists():
        errors.append("missing OpenAI adapter metadata: agents/openai.yaml")
        return
    text = path.read_text(encoding="utf-8").lower()
    for needle in ["glyph-arts chat", "stdout", "verify_chat_art.py", "rerender", "verified"]:
        if needle not in text:
            errors.append(f"openai.yaml: missing {needle}")


def _check_skill_docs(skill_root: Path, errors: list[str]) -> None:
    skill = (skill_root / "SKILL.md").read_text(encoding="utf-8")
    required = [
        "Render first, verify second",
        "verify_agent_contract.py",
        "verify_chat_art.py",
        "rerender",
        "reply",
    ]
    for needle in required:
        if needle not in skill:
            errors.append(f"SKILL.md missing {needle}")


def _check_capability_manifest(repo_root: Path, errors: list[str]) -> None:
    manifest_path = repo_root / "docs" / "chat_drawing_capabilities.json"
    manifest = _read_json(manifest_path)
    if manifest.get("default_entry") != "glyph-arts chat":
        errors.append("capability manifest default_entry must be glyph-arts chat")
    if manifest.get("closed_loop") != REQUIRED_LOOP:
        errors.append(f"capability manifest closed_loop must be {REQUIRED_LOOP}")

    validate_protocol = _load_protocol_validator(repo_root)
    capabilities = manifest.get("capabilities")
    if not isinstance(capabilities, dict) or not capabilities:
        errors.append("capability manifest must contain capabilities")
        return

    for name, capability in capabilities.items():
        if not isinstance(capability, dict):
            errors.append(f"{name}: capability must be an object")
            continue
        protocol = capability.get("protocol")
        if not isinstance(protocol, dict):
            errors.append(f"{name}: missing protocol")
        elif validate_protocol is not None:
            try:
                validate_protocol(protocol, name=name)
            except ValueError as exc:
                errors.append(str(exc))

        command = capability.get("command", "")
        if capability.get("chat") is True and not str(command).startswith("glyph-arts chat"):
            errors.append(f"{name}: chat capability command must start with glyph-arts chat")


def verify(repo_root: Path) -> list[str]:
    skill_root = repo_root / "skills" / "chat-drawing"
    errors: list[str] = []
    contract = _check_contract(skill_root, errors)
    _check_agent_adapters(skill_root, contract, errors)
    _check_openai_adapter(skill_root, errors)
    _check_skill_docs(skill_root, errors)
    _check_capability_manifest(repo_root, errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description="Verify the chat-drawing cross-agent contract.")
    parser.add_argument(
        "--repo-root",
        default=str(Path(__file__).resolve().parents[3]),
        help="Repository root containing skills/chat-drawing and docs/chat_drawing_capabilities.json",
    )
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    errors = verify(repo_root)
    payload = {
        "ok": not errors,
        "repo_root": str(repo_root),
        "checked": [
            "skills/chat-drawing/agents/contract.json",
            "skills/chat-drawing/agents/*.md",
            "skills/chat-drawing/agents/openai.yaml",
            "skills/chat-drawing/SKILL.md",
            "docs/chat_drawing_capabilities.json",
        ],
        "errors": errors,
    }
    print(json.dumps(payload, ensure_ascii=False, indent=2))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
