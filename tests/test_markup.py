from __future__ import annotations

import inspect
import subprocess
import sys

from cli_charts import markup


def test_table_visible_width_handles_cjk_emoji_and_ansi() -> None:
    rendered = markup.render_table(
        {
            "columns": ["Name", "状态"],
            "rows": [
                ["服务A", "\x1b[1;31mFAIL\x1b[0m"],
                ["emoji", "👨‍👩‍👧‍👦🇨🇳1️⃣"],
                ["nerd", "\ue0b0"],
            ],
        },
        format="rounded_grid",
    )
    widths = {markup.visible_width(line) for line in rendered.splitlines()}
    assert len(widths) == 1
    assert markup.visible_width("\x1b[38;2;255;0;0mred\x1b[0m") == 3


def test_grapheme_wrap_does_not_split_zwj_or_keycap() -> None:
    wrapped = markup.wrap_visible("👨‍👩‍👧‍👦1️⃣AB", 2)
    assert "👨‍👩‍👧‍👦" in wrapped.splitlines()
    assert "1️⃣" in wrapped.splitlines()


def test_render_table_formats_and_wrapping() -> None:
    data = {
        "columns": ["A", "B"],
        "rows": [["alpha", "汉字English"], ["beta", "plain"]],
        "maxcolwidths": [None, 6],
    }
    assert markup.render_table(data, format="github").startswith("| A")
    assert "\\|" in markup.render_table({"columns": ["A|B"], "rows": [["x\ny"]]}, format="github")
    assert "<br>" in markup.render_table({"columns": ["A"], "rows": [["x\ny"]]}, format="github")
    assert "+-" in markup.render_table(data, format="grid")
    rounded = markup.render_table(data, format="rounded_grid", maxcolwidths=data["maxcolwidths"])
    assert "汉字" in rounded
    assert "English" not in rounded.splitlines()[3]


def test_mermaid_builder_emits_themed_flowchart() -> None:
    rendered = markup.build_mermaid_flowchart(
        {
            "nodes": [{"id": "alert", "label": "Alert", "shape": "round"}, {"id": "triage", "label": "Triage"}],
            "edges": [{"from": "alert", "to": "triage", "label": "page"}],
        },
        theme="incident",
    )
    assert rendered.startswith("%%{init:")
    assert '"theme":"base"' in rendered
    assert "flowchart TD" in rendered
    assert 'alert("Alert")' in rendered
    assert "alert -->|page| triage" in rendered


def test_svg_card_and_markdown_panel_sources() -> None:
    svg = markup.render_svg_card({"title": "Deploy", "subtitle": "green", "body": ["api ok"]})
    assert "<svg" in svg
    assert "Deploy" in svg
    quote = markup.render_markdown_panel({"title": "Status", "body": ["ok", "done"]})
    assert quote == "> **Status**\n> ok\n> done\n"
    details = markup.render_markdown_panel({"kind": "details", "title": "Trace", "body": "line"})
    assert details.startswith("<details>")
    assert "<summary>Trace</summary>" in details


def test_svg_fallback_uses_text_symbols_when_chafa_is_available() -> None:
    svg = markup.render_svg_card({"title": "Fallback", "body": ["terminal preview"]})
    fallback = markup.render_svg_fallback(svg, width=40, no_color=True)
    if fallback != svg:
        assert "\x1b" not in fallback
        assert "<svg" not in fallback


def test_textual_image_raster_fallback(tmp_path) -> None:
    from PIL import Image, ImageDraw

    path = tmp_path / "card.png"
    image = Image.new("RGB", (32, 16), "#111827")
    draw = ImageDraw.Draw(image)
    draw.rectangle((0, 0, 6, 16), fill="#22c55e")
    draw.rectangle((10, 5, 26, 9), fill="#f9fafb")
    image.save(path)

    rendered = markup.render_raster_textual(path, width=24)
    assert rendered.strip()
    assert "\x1b" not in rendered


def test_chat_cli_textual_image(tmp_path) -> None:
    from PIL import Image

    path = tmp_path / "card.png"
    Image.new("RGB", (12, 8), "#f9fafb").save(path)
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli_charts.chart",
            "chat",
            "image",
            "--file",
            str(path),
            "--media-engine",
            "pillow",
            "--width",
            "16",
            "--height",
            "8",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert result.stdout.strip()


def test_chat_cli_table_and_raw_mermaid() -> None:
    table = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli_charts.chart",
            "table",
            "--json",
            '{"columns":["A","B"],"rows":[["服务","ok"]]}',
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert "服务" in table.stdout
    assert "ok" in table.stdout
    raw = subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", "chat", "mermaid", "--json", "flowchart LR\nA-->B"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )
    assert "A" in raw.stdout
    assert "B" in raw.stdout


def test_formula_panel_renders_source_as_unicode_math() -> None:
    rendered = markup.render_formula_panel({
        "title": "Formula",
        "items": [
            r"E = mc^2",
            r"\int exp(-x^2) dx = \sqrt{\pi}",
            r"\sum_{n=1}^{\infty} x^n/n",
        ],
    })

    assert "Formula" in rendered
    assert "mc²" in rendered
    assert "∫ exp(-x²) dx = √(π)" in rendered
    assert "∑ₙ₌₁^{∞}" in rendered


def test_chat_cli_formula_accepts_raw_text() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", "chat", "formula"],
        input=r"E = mc^2",
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert result.stdout == "E = mc²\n"


def test_formula_pretty_uses_sympy_multiline_layout() -> None:
    rendered = markup.render_formula_pretty({
        "title": "Pretty",
        "items": ["(a+b)/(c+d)", "Integral(exp(-x^2), x)"],
    })

    assert "Pretty" in rendered
    assert "a + b" in rendered
    assert "─────" in rendered
    assert "⌠" in rendered


def test_chat_cli_formula_pretty_accepts_raw_text() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", "chat", "formula-pretty"],
        input="(a+b)/(c+d)",
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert "a + b" in result.stdout
    assert "─────" in result.stdout


def test_chat_calibration_renders_ascii_and_braille_widths() -> None:
    rendered = markup.render_chat_calibration({"widths": [12]})

    assert "12:\n123456789012\n" in rendered
    assert "⣿" * 12 in rendered


def test_chat_calibration_range_glyph_and_recommendation() -> None:
    rendered = markup.render_chat_calibration({
        "from": 8,
        "to": 12,
        "step": 4,
        "glyph": "mixed",
        "recommend": True,
    })

    assert "inline = floor(W * 0.85)" in rendered
    assert "8:\n⠿⣶⣿⣤⠿⣶⣿⣤" in rendered
    assert "12:\n⠿⣶⣿⣤⠿⣶⣿⣤⠿⣶⣿⣤" in rendered
    assert "12345678" not in rendered


def test_chat_calibration_terminal_mode_reports_safe_width() -> None:
    rendered = markup.render_chat_calibration({
        "terminal": True,
        "terminal_cols": 40,
        "glyph": "digits",
    })

    assert "terminal columns = 40" in rendered
    assert "safe inline width = 38" in rendered
    assert "8:\n12345678" in rendered
    assert "40:\n1234567890123456789012345678901234567890" in rendered


def test_chat_calibration_terminal_mode_accepts_columns_env(monkeypatch) -> None:
    monkeypatch.setenv("GLYPH_ARTS_COLS", "180")
    rendered = markup.render_chat_calibration({
        "terminal": True,
        "glyph": "digits",
    })

    assert "terminal columns = 180" in rendered
    assert "safe inline width = 178" in rendered


def test_chat_cli_calibrate_needs_no_json() -> None:
    result = subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", "chat", "calibrate"],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert "96:" in result.stdout
    assert "⣿" * 96 in result.stdout


def test_chat_cli_calibrate_accepts_range_flags() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli_charts.chart",
            "chat",
            "calibrate",
            "--calibrate-from",
            "10",
            "--calibrate-to",
            "14",
            "--calibrate-step",
            "4",
            "--calibrate-glyph",
            "digits",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert "10:\n1234567890" in result.stdout
    assert "14:\n12345678901234" in result.stdout
    assert "⣿" not in result.stdout


def test_chat_cli_calibrate_terminal_mode() -> None:
    result = subprocess.run(
        [
            sys.executable,
            "-m",
            "cli_charts.chart",
            "chat",
            "calibrate",
            "--terminal",
            "--calibrate-glyph",
            "digits",
        ],
        check=True,
        capture_output=True,
        text=True,
        encoding="utf-8",
    )

    assert "terminal columns =" in result.stdout
    assert "safe inline width =" in result.stdout


def test_visible_width_helpers_do_not_use_len_for_width() -> None:
    for name in ("visible_width", "wrap_visible"):
        source = inspect.getsource(getattr(markup, name))
        assert "len(" not in source
