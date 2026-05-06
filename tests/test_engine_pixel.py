"""Phase A spike tests for --engine pixel."""

import inspect
import shutil
import subprocess
import sys
from pathlib import Path

import pytest

pytest.importorskip(
    'matplotlib',
    reason='matplotlib not installed',
)

pytestmark = pytest.mark.skipif(shutil.which('chafa') is None, reason='chafa not in PATH')

ROOT = Path(__file__).resolve().parent.parent


def _run(args):
    return subprocess.run(
        [sys.executable, '-m', 'cli_charts.chart', *args],
        capture_output=True,
        text=True,
        timeout=30,
        cwd=str(ROOT),
    )


def test_render_pixel_signature():
    from cli_charts.render.matplotlib_engine import PIXEL_SUPPORTED, render_pixel

    assert PIXEL_SUPPORTED == frozenset({'bar', 'line', 'scatter'})
    assert callable(render_pixel)
    sig = inspect.signature(render_pixel)
    params = list(sig.parameters)
    assert params[:4] == ['chart_type', 'data', 'w', 'h']


def test_bar_pixel_exit0():
    result = _run([
        'bar', '--engine', 'pixel',
        '--json', '{"labels":["A","B","C"],"values":[3,7,5]}',
        '--width', '40', '--height', '12',
    ])

    assert result.returncode == 0, f'stderr={result.stderr}'
    assert len(result.stdout) > 100


def test_line_pixel_exit0():
    result = _run([
        'line', '--engine', 'pixel',
        '--json', '[{"label":"x","x":[1,2,3,4,5],"y":[10,20,15,30,25]}]',
        '--width', '40', '--height', '12',
    ])

    assert result.returncode == 0, f'stderr={result.stderr}'
    assert len(result.stdout) > 100


def test_scatter_pixel_exit0():
    result = _run([
        'scatter', '--engine', 'pixel',
        '--json', '[{"label":"x","x":[1,2,3,4,5,6,7],"y":[2,4,3,8,6,9,5]}]',
        '--width', '40', '--height', '12',
    ])

    assert result.returncode == 0, f'stderr={result.stderr}'
    assert len(result.stdout) > 100


def test_heatmap_unsupported_fallback():
    result = _run([
        'heatmap', '--engine', 'pixel',
        '--json', '{"matrix":[[1,2],[3,4]]}',
        '--width', '40', '--height', '8',
    ])

    assert result.returncode == 0, f'stderr={result.stderr}'
    assert 'fallback' in result.stderr.lower() or 'ascii' in result.stderr.lower()


def test_output_file_png(tmp_path):
    output = tmp_path / 'out.png'
    result = _run([
        'bar', '--engine', 'pixel',
        '--json', '{"labels":["A","B"],"values":[1,2]}',
        '--width', '40', '--height', '10',
        '--output', str(output),
    ])

    assert result.returncode == 0, f'stderr={result.stderr}'
    assert output.exists()
    assert output.stat().st_size > 0


def test_no_color_no_truecolor():
    result = _run([
        'bar', '--engine', 'pixel', '--no-color',
        '--json', '{"labels":["A","B"],"values":[1,2]}',
        '--width', '40', '--height', '10',
    ])

    assert result.returncode == 0, f'stderr={result.stderr}'
    assert '\x1b[38;2;' not in result.stdout
    assert '\x1b[38;2;' not in result.stderr
