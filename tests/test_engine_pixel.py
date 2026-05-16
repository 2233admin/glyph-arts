"""Phase A spike tests for --engine pixel."""

import inspect
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

if shutil.which('chafa') is None:
    pytest.skip('chafa not in PATH', allow_module_level=True)

pytest.importorskip(
    'matplotlib',
    reason='matplotlib not installed',
)

ROOT = Path(__file__).resolve().parent.parent


def _run(args):
    """Run chart.py CLI. stdout is binary because chafa kitty graphics
    protocol output is not utf-8 decodable; stderr stays text for greps."""
    return subprocess.run(
        [sys.executable, '-m', 'cli_charts.chart', *args],
        capture_output=True,
        timeout=30,
        cwd=str(ROOT),
    )


def _stderr_text(result):
    return (result.stderr or b'').decode('utf-8', errors='replace')


def test_render_pixel_signature():
    from cli_charts.render.matplotlib_engine import PIXEL_SUPPORTED, render_pixel

    assert PIXEL_SUPPORTED == frozenset({'bar', 'line', 'scatter'})
    assert callable(render_pixel)
    sig = inspect.signature(render_pixel)
    params = list(sig.parameters)
    assert params[:4] == ['chart_type', 'data', 'w', 'h']


def test_art_tier_low_uses_block_symbols():
    from cli_charts.render.matplotlib_engine import _build_chafa_cmd

    cmd = _build_chafa_cmd(40, 10, 'symbols', False, art='low')

    assert cmd[cmd.index('--symbols') + 1] == 'block'


def test_art_tier_default_uses_vhalf_symbols():
    from cli_charts.render.matplotlib_engine import _build_chafa_cmd

    cmd = _build_chafa_cmd(40, 10, 'symbols', False)

    assert cmd[cmd.index('--symbols') + 1] == 'vhalf'


def test_art_tier_high_uses_sextant_symbols():
    from cli_charts.render.matplotlib_engine import _build_chafa_cmd

    cmd = _build_chafa_cmd(40, 10, 'symbols', False, art='high')

    assert cmd[cmd.index('--symbols') + 1] == 'sextant'


def test_art_tier_includes_truecolor_flag():
    from cli_charts.render.matplotlib_engine import _build_chafa_cmd

    for art in ('low', 'default', 'high'):
        cmd = _build_chafa_cmd(40, 10, 'symbols', False, art=art)
        assert cmd[cmd.index('-c') + 1] == 'full'


def test_art_flag_argparse_choices():
    result = _run(['bar', '--engine', 'pixel', '--art', 'low', '--help'])

    assert result.returncode == 0
    assert b'--art' in result.stdout


def test_art_flag_default_is_default():
    from cli_charts.render.matplotlib_engine import render_pixel

    sig = inspect.signature(render_pixel)

    assert sig.parameters['art'].default == 'default'


def test_pixel_render_with_art_flag():
    result = _run([
        'bar', '--engine', 'pixel', '--art', 'low',
        '--json', '{"labels":["A","B"],"values":[1,2]}',
        '--width', '40', '--height', '10',
    ])

    assert result.returncode == 0, f'stderr={_stderr_text(result)}'
    assert len(result.stdout) > 100


def test_bar_pixel_exit0():
    result = _run([
        'bar', '--engine', 'pixel',
        '--json', '{"labels":["A","B","C"],"values":[3,7,5]}',
        '--width', '40', '--height', '12',
    ])

    assert result.returncode == 0, f'stderr={_stderr_text(result)}'
    assert len(result.stdout) > 100


def test_line_pixel_exit0():
    result = _run([
        'line', '--engine', 'pixel',
        '--json', '[{"label":"x","x":[1,2,3,4,5],"y":[10,20,15,30,25]}]',
        '--width', '40', '--height', '12',
    ])

    assert result.returncode == 0, f'stderr={_stderr_text(result)}'
    assert len(result.stdout) > 100


def test_scatter_pixel_exit0():
    result = _run([
        'scatter', '--engine', 'pixel',
        '--json', '[{"label":"x","x":[1,2,3,4,5,6,7],"y":[2,4,3,8,6,9,5]}]',
        '--width', '40', '--height', '12',
    ])

    assert result.returncode == 0, f'stderr={_stderr_text(result)}'
    assert len(result.stdout) > 100


def test_heatmap_unsupported_fallback():
    result = _run([
        'heatmap', '--engine', 'pixel',
        '--json', '{"matrix":[[1,2],[3,4]]}',
        '--width', '40', '--height', '8',
    ])

    assert result.returncode == 0, f'stderr={_stderr_text(result)}'
    err = _stderr_text(result).lower()
    assert 'fallback' in err or 'ascii' in err


def test_output_file_png(tmp_path):
    output = tmp_path / 'out.png'
    result = _run([
        'bar', '--engine', 'pixel',
        '--json', '{"labels":["A","B"],"values":[1,2]}',
        '--width', '40', '--height', '10',
        '--output', str(output),
    ])

    assert result.returncode == 0, f'stderr={_stderr_text(result)}'
    assert output.exists()
    assert output.stat().st_size > 0


def test_no_color_no_truecolor():
    result = _run([
        'bar', '--engine', 'pixel', '--no-color',
        '--json', '{"labels":["A","B"],"values":[1,2]}',
        '--width', '40', '--height', '10',
    ])

    assert result.returncode == 0, f'stderr={_stderr_text(result)}'
    # chafa --colors none -> no truecolor escape (\x1b[38;2; = SGR truecolor fg)
    assert b'\x1b[38;2;' not in result.stdout
    assert b'\x1b[38;2;' not in (result.stderr or b'')
