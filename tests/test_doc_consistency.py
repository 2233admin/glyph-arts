"""Doc-drift regression tests for chart docs and canonical type metadata."""
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def test_canonical_count_matches_cli_choices():
    from cli_charts.chart import _MEDIA_TYPES, CHART_TYPE_COUNT, CHART_TYPES_BY_ENGINE, CMDS

    flat = {t for ts in CHART_TYPES_BY_ENGINE.values() for t in ts}
    expected = set(CMDS) | _MEDIA_TYPES
    assert flat == expected, (
        "CHART_TYPES_BY_ENGINE missing or extra vs CLI choices: "
        f"missing={expected - flat}, extra={flat - expected}"
    )
    assert CHART_TYPE_COUNT == len(flat) == len(expected)


def test_argparse_epilog_uses_dynamic_count():
    from cli_charts.chart import CHART_TYPE_COUNT

    src = (ROOT / 'cli_charts' / 'chart.py').read_text(encoding='utf-8')
    assert "Chart types ({CHART_TYPE_COUNT})" in src
    matches = re.findall(r'Chart types \((\d+)\)', src)
    for match in matches:
        assert int(match) == CHART_TYPE_COUNT, (
            f"chart.py has hard-coded 'Chart types ({match})' "
            f"but real count is {CHART_TYPE_COUNT}"
        )


def test_readme_chart_count_matches_code():
    from cli_charts.chart import CHART_TYPE_COUNT

    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    matches = re.findall(r'(\d+)\s*chart types', readme, re.IGNORECASE)
    matches += re.findall(r'Total:\s*\*\*(\d+)', readme)
    for match in matches:
        assert int(match) == CHART_TYPE_COUNT, (
            f"README claims '{match} chart types' but code has {CHART_TYPE_COUNT}"
        )


def test_readme_no_demo_placeholder():
    readme = (ROOT / 'README.md').read_text(encoding='utf-8')
    assert 'demo.gif  <-- record with' not in readme
    assert '![demo](demo/chartex-demo.gif)' in readme


def test_readme_lists_system_deps_for_media():
    readme = (ROOT / 'README.md').read_text(encoding='utf-8').lower()
    for tool in ('chafa', 'ffmpeg'):
        assert tool in readme, f'README does not mention {tool}'


def test_skill_md_engines_match_code():
    from cli_charts.chart import CHART_TYPES_BY_ENGINE

    skill_path = ROOT / 'SKILL.md'
    if not skill_path.exists():
        return
    skill = skill_path.read_text(encoding='utf-8').lower()
    for engine in CHART_TYPES_BY_ENGINE:
        if engine == 'misc':
            continue
        assert engine.lower() in skill, f"SKILL.md doesn't mention engine '{engine}'"
