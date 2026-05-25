import pytest


def test_render_protocol_serializes_chat_contract() -> None:
    from cli_charts.render_target import RenderProtocol, RenderTarget, UnicodeTier

    protocol = RenderProtocol(
        targets=(RenderTarget.CHAT, RenderTarget.TERMINAL, RenderTarget.ARTIFACT),
        chat_safe=True,
        uses_ansi=False,
        unicode_tier=UnicodeTier.UNICODE,
        fallback="ascii",
    )

    assert protocol.as_json() == {
        "targets": ["chat", "terminal", "artifact"],
        "chat_safe": True,
        "uses_ansi": False,
        "unicode_tier": "unicode",
        "fallback": "ascii",
        "requires_host": "none",
    }


def test_validate_protocol_rejects_ansi_chat() -> None:
    from cli_charts.render_target import validate_protocol

    with pytest.raises(ValueError, match="chat target requires"):
        validate_protocol({
            "targets": ["chat"],
            "chat_safe": True,
            "uses_ansi": True,
            "unicode_tier": "unicode",
            "fallback": "ascii",
            "requires_host": "none",
        })


def test_validate_protocol_rejects_host_without_host_name() -> None:
    from cli_charts.render_target import validate_protocol

    with pytest.raises(ValueError, match="host target requires"):
        validate_protocol({
            "targets": ["host"],
            "chat_safe": False,
            "uses_ansi": False,
            "unicode_tier": "unicode",
            "fallback": "artifact",
            "requires_host": "none",
        })
