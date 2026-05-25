def test_symbols_module_imports() -> None:
    import cli_charts.symbols  # noqa: F401


def test_geometric_has_50_plus_entries() -> None:
    from cli_charts.symbols import GEOMETRIC

    assert len(GEOMETRIC) >= 50


def test_block_has_32_plus_entries() -> None:
    from cli_charts.symbols import BLOCK

    assert len(BLOCK) >= 32


def test_braille_dots_helper_returns_correct_chars() -> None:
    from cli_charts.symbols import braille_dots

    assert braille_dots(0) == "⠀"
    assert braille_dots(255) == "⣿"


def test_box_styles_has_9_styles() -> None:
    from cli_charts.symbols import BOX_STYLES

    assert len(BOX_STYLES) == 9


def test_enclosed_circled_digits_starts_with_1() -> None:
    from cli_charts.symbols import ENCLOSED

    assert ENCLOSED["circled_digits"][0] == "①"


def test_get_symbol_returns_tier_appropriate_char() -> None:
    from cli_charts.symbols import get_symbol

    assert get_symbol("circle", tier="ascii").isascii()
    assert get_symbol("circle", tier="unicode") == "●"


def test_font_tier_auto_detect_warp_returns_unicode_extended(monkeypatch) -> None:
    from cli_charts.font_tier import detect_font_tier

    monkeypatch.delenv("GLYPH_ARTS_FONT_TIER", raising=False)
    monkeypatch.delenv("NERD_FONT", raising=False)
    monkeypatch.delenv("GLYPH_ARTS_TERMINAL_PROFILE", raising=False)
    monkeypatch.setenv("TERM_PROGRAM", "WarpTerminal")

    assert detect_font_tier() == "unicode-extended"


def test_font_tier_uses_terminal_profile_override(monkeypatch) -> None:
    from cli_charts.font_tier import detect_font_tier

    monkeypatch.delenv("GLYPH_ARTS_FONT_TIER", raising=False)
    monkeypatch.delenv("NERD_FONT", raising=False)
    monkeypatch.setenv("GLYPH_ARTS_TERMINAL_PROFILE", "warp")

    assert detect_font_tier() == "unicode-extended"
