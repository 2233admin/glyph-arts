"""Render target protocol metadata for glyph-arts."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class RenderTarget(str, Enum):
    CHAT = "chat"
    TERMINAL = "terminal"
    ARTIFACT = "artifact"
    HOST = "host"


class UnicodeTier(str, Enum):
    ASCII = "ascii"
    UNICODE = "unicode"
    UNICODE_EXTENDED = "unicode-extended"
    NERD = "nerd"


VALID_FALLBACKS = {"plain", "ascii", "unicode", "artifact", "host"}


@dataclass(frozen=True)
class RenderProtocol:
    targets: tuple[RenderTarget, ...]
    chat_safe: bool
    uses_ansi: bool = False
    unicode_tier: UnicodeTier = UnicodeTier.UNICODE
    fallback: str = "ascii"
    requires_host: str = "none"

    def as_json(self) -> dict[str, Any]:
        return {
            "targets": [target.value for target in self.targets],
            "chat_safe": self.chat_safe,
            "uses_ansi": self.uses_ansi,
            "unicode_tier": self.unicode_tier.value,
            "fallback": self.fallback,
            "requires_host": self.requires_host,
        }


def validate_protocol(value: dict[str, Any], *, name: str = "capability") -> None:
    targets = value.get("targets")
    if not isinstance(targets, list) or not targets:
        raise ValueError(f"{name}: protocol.targets must be a non-empty list")
    allowed_targets = {target.value for target in RenderTarget}
    unknown_targets = sorted(set(targets) - allowed_targets)
    if unknown_targets:
        raise ValueError(f"{name}: unknown render target(s): {', '.join(unknown_targets)}")

    if "chat_safe" not in value or not isinstance(value["chat_safe"], bool):
        raise ValueError(f"{name}: protocol.chat_safe must be boolean")
    if "uses_ansi" not in value or not isinstance(value["uses_ansi"], bool):
        raise ValueError(f"{name}: protocol.uses_ansi must be boolean")

    tier = value.get("unicode_tier")
    allowed_tiers = {tier.value for tier in UnicodeTier}
    if tier not in allowed_tiers:
        raise ValueError(f"{name}: protocol.unicode_tier must be one of {sorted(allowed_tiers)}")

    fallback = value.get("fallback")
    if fallback not in VALID_FALLBACKS:
        raise ValueError(f"{name}: protocol.fallback must be one of {sorted(VALID_FALLBACKS)}")

    requires_host = value.get("requires_host", "none")
    if not isinstance(requires_host, str) or not requires_host:
        raise ValueError(f"{name}: protocol.requires_host must be a non-empty string")

    is_chat = RenderTarget.CHAT.value in targets
    if is_chat and (not value["chat_safe"] or value["uses_ansi"]):
        raise ValueError(f"{name}: chat target requires chat_safe=true and uses_ansi=false")
    if value["chat_safe"] and not is_chat:
        raise ValueError(f"{name}: chat_safe=true requires the chat target")
    if RenderTarget.HOST.value in targets and requires_host == "none":
        raise ValueError(f"{name}: host target requires protocol.requires_host")
