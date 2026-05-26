from __future__ import annotations

from cli_charts.render.text_layout import center_text, display_width, fit_text, pad_right


def test_display_width_counts_chinese_as_double_width() -> None:
    assert display_width("中文") == 4
    assert display_width("A中B") == 4


def test_padding_uses_display_width_not_codepoint_count() -> None:
    padded = pad_right("中文", 6)
    assert display_width(padded) == 6
    assert padded.endswith("  ")


def test_center_and_fit_text_are_display_width_safe() -> None:
    centered = center_text("指标", 8)
    assert display_width(centered) == 8
    assert fit_text("中文排版", 5) == "中文…"
