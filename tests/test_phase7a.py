import json
import os
import subprocess
import sys
import uuid
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
TEST_OUT = ROOT / "export_test_outputs" / "phase7a"


def _run(args: list[str], env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        [sys.executable, "-m", "cli_charts.chart", *args],
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=10,
        cwd=ROOT,
        env=merged,
    )


def test_osc8_link_data() -> None:
    from cli_charts.osc8 import link

    assert link("pt", "https://example.test/pt", force=True) == (
        "\x1b]8;;https://example.test/pt\x1b\\pt\x1b]8;;\x1b\\"
    )


def test_osc8_fallback_no_terminal_support() -> None:
    from cli_charts.osc8 import link

    assert link("pt", "https://example.test/pt", force=False) == "pt (https://example.test/pt)"


def test_osc8_link_title_in_chart() -> None:
    result = _run(
        [
            "line",
            "--title",
            "Revenue",
            "--link-title",
            "https://example.test/revenue",
            "--json",
            '[{"label":"X","x":[1,2,3],"y":[10,20,15]}]',
        ],
        env={"GLYPH_ARTS_OSC8": "1"},
    )

    assert result.returncode == 0, result.stderr
    assert "\x1b]8;;https://example.test/revenue\x1b\\Revenue\x1b]8;;\x1b\\" in result.stdout


def _case_dir() -> Path:
    path = TEST_OUT / uuid.uuid4().hex
    path.mkdir(parents=True, exist_ok=True)
    return path


def test_claude_ansi_theme_load_from_file(monkeypatch) -> None:
    home = _case_dir()
    themes = home / ".claude" / "themes"
    themes.mkdir(parents=True)
    (themes / "dark-ansi.json").write_text(
        json.dumps(
            {
                "colors": {
                    "background": "#010203",
                    "foreground": "#a0a1a2",
                    "ansi": ["#111111", "#222222", "#333333", "#444444"],
                }
            }
        ),
        encoding="utf-8",
    )
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("HOME", str(home))

    from cli_charts.themes.claude_ansi import get_claude_ansi_palette

    palette = get_claude_ansi_palette("dark")
    assert palette["canvas"] == (1, 2, 3)
    assert palette["ticks"] == (160, 161, 162)
    assert palette["series"][:2] == [(17, 17, 17), (34, 34, 34)]


def test_claude_ansi_fallback_no_file(monkeypatch) -> None:
    home = _case_dir()
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("HOME", str(home))

    from cli_charts.themes.claude_ansi import get_claude_ansi_palette

    palette = get_claude_ansi_palette("dark")
    assert palette["plt_base"] == "dark"
    assert len(palette["series"]) == 16


def test_claude_light_ansi_palette(monkeypatch) -> None:
    home = _case_dir()
    monkeypatch.setenv("USERPROFILE", str(home))
    monkeypatch.setenv("HOME", str(home))

    from cli_charts.themes.claude_ansi import get_claude_ansi_palette

    palette = get_claude_ansi_palette("light")
    assert palette["plt_base"] == "clear"
    assert palette["canvas"] == (255, 255, 255)


def test_statusline_single_line() -> None:
    result = _run(["sparkline", "--json", "[1,2,3,4,5,6,7,8,9,10]", "--statusline"])

    assert result.returncode == 0, result.stderr
    assert result.stdout.endswith("\n")
    assert "\n" not in result.stdout.rstrip("\n")
    assert len(result.stdout.rstrip("\n")) <= 80


def test_statusline_no_alt_screen_escape() -> None:
    result = _run(["gauge", "--json", '[{"label":"CPU","value":72,"max":100}]', "--statusline"])

    assert result.returncode == 0, result.stderr
    assert "\x1b[?1049" not in result.stdout
    assert "\n" not in result.stdout.rstrip("\n")


def test_subagent_rainbow_8_colors() -> None:
    from cli_charts.themes.subagent_rainbow import NAMED_COLORS, PALETTE

    assert list(NAMED_COLORS) == ["red", "blue", "green", "yellow", "purple", "orange", "pink", "cyan"]
    assert len(PALETTE["series"]) == 8


def test_multi_series_uses_subagent_palette() -> None:
    from cli_charts.themes import get_palette

    palette = get_palette("subagent-rainbow")
    assert palette is not None
    assert palette["series"][0] != palette["series"][1]
    assert len(palette["series"]) == 8


def test_markdown_table_gfm_output() -> None:
    from cli_charts.render.markdown_export import table_to_markdown

    rendered = table_to_markdown({"columns": ["A", "B"], "rows": [["x", "1"]]})
    assert rendered == "| A   | B   |\n|-----|-----|\n| x   | 1   |\n"


def test_markdown_table_via_output_md_suffix() -> None:
    output = _case_dir() / "out.md"
    result = _run(
        ["table", "--output", str(output), "--json", '{"columns":["A","B"],"rows":[["x","1"]]}']
    )

    assert result.returncode == 0, result.stderr
    assert output.read_text(encoding="utf-8") == "| A   | B   |\n|-----|-----|\n| x   | 1   |\n"
