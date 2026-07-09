#!/usr/bin/env python3
"""glyph-arts: terminal-visible chart toolkit for Claude Code.

Usage: python chart.py <type> [options]
See CHART_TYPES_BY_ENGINE for the authoritative chart type list.

Animation (--animate):
  Stream values from stdin line-by-line; chart re-renders after each point.
  Supported types: line, scatter, sparkline
  Flags: --refresh FPS (default 10), --window N (default 50), --duration SEC
"""
import contextlib
import datetime
import importlib
import io
import json
import os
import random
import shutil
import subprocess
import sys
import tempfile

from cli_charts.charts._utils import (
    _BRAILLE_DOTS, _CHAT_EFFECT_ALIASES, _CHAT_GROUP_ALIASES, _CHAT_HEALTH_ALIASES,
    _DIAGRAM_KIND_ALIASES, _HIRES_PALETTE, _IMAGE_EXTENSIONS, _MEDIA_TYPES,
    _bar_symbols, _canvas_line, _capture_stdout, _catmull_pixels, _has_flag,
    _HiresCanvas, _lttb, _normalize_kline_dates, _plt_finalize, _render_statusline,
    _rewrite_chat_argv, _rewrite_diagram_argv, _sample_data, _sample_indices,
    _series_color, _statusline_values, _style_to_bar_symbols, _style_to_gauge,
    _symbol_tier, _textcharts_options, load_duckdb,
)
from cli_charts.charts.aggregates.boxplot_comparison import boxplot_comparison
from cli_charts.charts.aggregates.cdf_chart import cdf_chart
from cli_charts.charts.aggregates.comparison import comparison
from cli_charts.charts.aggregates.diverging import diverging
from cli_charts.charts.aggregates.graph import graph
from cli_charts.charts.aggregates.percentile import percentile
from cli_charts.charts.aggregates.rank_table import rank_table
from cli_charts.charts.aggregates.sparkline_table import sparkline_table
from cli_charts.charts.aggregates.stacked_bar_text import stacked_bar_text
from cli_charts.charts.aggregates.summary import summary
from cli_charts.charts.algebra.calibrate import calibrate
from cli_charts.charts.algebra.formula import formula
from cli_charts.charts.algebra.formula_pretty import formula_pretty
from cli_charts.charts.algebra.splash_command import splash_command
from cli_charts.charts.algebra.status_command import status_command
from cli_charts.charts.algebra.wave_command import wave_command
from cli_charts.charts.composite.dashboard import dashboard
from cli_charts.charts.composite.panel import panel
from cli_charts.charts.composite.rich_live import rich_live
from cli_charts.charts.series.bar import bar, hbar
from cli_charts.charts.series.box import box
from cli_charts.charts.series.curve import curve
from cli_charts.charts.series.event import event
from cli_charts.charts.series.heatmap import heatmap
from cli_charts.charts.series.hist import hist
from cli_charts.charts.series.indicator import indicator
from cli_charts.charts.series.kline import kline
from cli_charts.charts.series.line import line
from cli_charts.charts.series.multibar import multibar
from cli_charts.charts.series.scatter import scatter
from cli_charts.charts.series.sparkline import sparkline
from cli_charts.charts.series.spectrum import spectrum
from cli_charts.charts.series.stackedbar import stackedbar
from cli_charts.charts.series.step import step
from cli_charts.charts.media.art_command import art_command
from cli_charts.charts.media.banner import banner
from cli_charts.charts.media.bar import bar
from cli_charts.charts.media.confusion import confusion
from cli_charts.charts.media.diagram import diagram
from cli_charts.charts.media.effect import effect
from cli_charts.charts.media.gauge import gauge
from cli_charts.charts.media.hbar import hbar
from cli_charts.charts.media.hires import hires
from cli_charts.charts.media.incplot import incplot
from cli_charts.charts.media.mermaid import mermaid
from cli_charts.charts.media.pie import pie
from cli_charts.charts.media.plotille_chart import plotille_chart
from cli_charts.charts.media.plotext import plotext
from cli_charts.charts.media.radar import radar
from cli_charts.charts.media.table import table
from cli_charts.charts.media.textplot import textplot
from cli_charts.charts.media.tree import tree
from cli_charts.charts.media.turtle import turtle
from cli_charts.charts.media.uniplot import uniplot
from cli_charts.charts.series.waterfall import waterfall
from cli_charts.cmd.animate_stream import ANIMATE_TYPES
from cli_charts.cmd.direct_commands import dispatch_direct_command
from cli_charts.cmd.media_dispatch import dispatch_media
from cli_charts.cmd.motion_commands import dispatch_motion_command
from cli_charts.cmd.parser import build_parser
from cli_charts.cmd.text_input_commands import dispatch_text_input_command
from cli_charts.cmd.tool_commands import dispatch_tool_command
from cli_charts.font_tier import detect_font_tier
from cli_charts.osc8 import link as _osc8_link
from cli_charts.registry import DEFAULT_STYLE, STYLE_ROUTES, resolve_engine
from cli_charts.registry import STYLES as _STYLES
from cli_charts.symbols import BLOCK, BRAILLE_ALL, get_symbol
from cli_charts.themes import get_palette as _get_palette

# Re-exported by cli_charts.chart for compatibility with older imports.
_ANIMATE_TYPES = ANIMATE_TYPES

# -- helpers -----------------------------------------------------------------

_MARKER_SYMBOLS = {
    'circle': 'circle',
    'triangle': 'triangle_up',
    'diamond': 'diamond',
    'star': 'star',
    'square': 'square',
}

def animate_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("animate is dispatched by main()")


def record_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("record is dispatched by main()")


def record_replay_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("record-replay is dispatched by main()")


def to_hyperframes_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("to-hyperframes is dispatched by main()")


def to_ascii_motion_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("to-ascii-motion is dispatched by main()")


def code_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("code is dispatched by main()")


def demo_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("demo is dispatched by main()")


def gallery_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("gallery is dispatched by main()")


def auto_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("auto is dispatched by main()")


def live_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("live is dispatched by main()")


def doctor_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("doctor is dispatched by main()")


def install_backends_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("install-backends is dispatched by main()")


def fonts_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("fonts is dispatched by main()")


def chat_health_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("chat-health is dispatched by main()")


def serve_command(d, title, w, h, theme, **kw):
    """Placeholder registry entry; dispatched specially by main()."""
    raise RuntimeError("serve is dispatched by main()")


CMDS = {
    'kline':      kline,
    'line':       line,
    'scatter':    scatter,
    'step':       step,
    'bar':        bar,
    'hbar':       hbar,
    'pie':        pie,
    'multibar':   multibar,
    'stackedbar': stackedbar,
    'hist':       hist,
    'heatmap':    heatmap,
    'spectrum':   spectrum,
    'waterfall':  waterfall,
    'box':        box,
    'indicator':  indicator,
    'event':      event,
    'confusion':  confusion,
    'sparkline':  sparkline,
    'table':      table,
    'tree':       tree,
    'panel':      panel,
    'gauge':      gauge,
    'dashboard':  dashboard,
    'incplot':    incplot,
    'graph':      graph,
    'diagram':    diagram,
    'formula':    formula,
    'formula-pretty': formula_pretty,
    'math':       formula,
    'math-pretty': formula_pretty,
    'calibrate':  calibrate,
    'mermaid':    mermaid,
    'plotext':    plotext,
    'textplot':   textplot,
    'turtle':     turtle,
    'effect':     effect,
    'curve':      curve,
    'uniplot':    uniplot,
    'banner':      banner,
    'art':         art_command,
    'candlestick': kline,
    'hires':       hires,
    'radar':       radar,
    'plotille':    plotille_chart,
    'rich_live':   rich_live,
    # textcharts types
    'comparison':      comparison,
    'diverging':       diverging,
    'summary':         summary,
    'sparkline-table': sparkline_table,
    'cdf':             cdf_chart,
    'rank':            rank_table,
    'percentile':       percentile,
    'boxplot':         boxplot_comparison,
    'stacked-text':    stacked_bar_text,
    'animate':     animate_command,
    'record':      record_command,
    'record-replay': record_replay_command,
    'to-hyperframes': to_hyperframes_command,
    'to-ascii-motion': to_ascii_motion_command,
    'code':        code_command,
    'status':      status_command,
    'splash':      splash_command,
    'demo':        demo_command,
    'gallery':     gallery_command,
    'auto':        auto_command,
    'live':        live_command,
    'doctor':      doctor_command,
    'install-backends': install_backends_command,
    'fonts':       fonts_command,
    'chat-health': chat_health_command,
    'wave':        wave_command,
    'serve':       serve_command,
}

# Single source of truth for chart-type docs. Order is intentional.
CHART_TYPES_BY_ENGINE: dict[str, list[str]] = {
    'incplot': ['incplot'],
    'plotext': [
        'kline', 'candlestick', 'line', 'scatter', 'step', 'bar', 'hbar', 'multibar',
        'stackedbar', 'hist', 'heatmap', 'box', 'indicator', 'event',
        'confusion', 'plotext',
    ],
    'sdr': ['spectrum', 'waterfall'],
    'rich': ['table', 'tree', 'panel', 'gauge', 'pie', 'dashboard', 'rich_live'],
    'diagram': ['diagram', 'formula', 'formula-pretty', 'math', 'math-pretty', 'mermaid'],
    'drawille': ['curve', 'hires', 'radar', 'textplot', 'turtle'],
    'plotille': ['plotille'],
    'uniplot': ['uniplot'],
    'textcharts': ['comparison', 'diverging', 'summary', 'sparkline-table', 'cdf', 'rank', 'percentile', 'boxplot', 'stacked-text'],
    'misc': ['graph', 'effect', 'sparkline', 'banner', 'art', 'animate', 'record', 'record-replay', 'to-hyperframes', 'to-ascii-motion', 'code', 'status', 'splash', 'demo', 'gallery', 'auto', 'live', 'doctor', 'install-backends', 'fonts', 'chat-health', 'wave', 'calibrate', 'serve'],
    'media': ['image', 'video'],
}

_CHART_TYPE_KEYS = {t for ts in CHART_TYPES_BY_ENGINE.values() for t in ts}
assert _CHART_TYPE_KEYS == set(CMDS) | _MEDIA_TYPES, \
    "CHART_TYPES_BY_ENGINE drift vs CMDS/media types"

CHART_TYPE_COUNT: int = len(_CHART_TYPE_KEYS)

EXPECTED_SCHEMAS = {
    'kline':      '{"dates":["DD/MM/YYYY",...], "open":[...], "high":[...], "low":[...], "close":[...]}',
    'line':       '[{"label":"A","x":[...],"y":[...]}] or {"label":"A","y":[...]}',
    'scatter':    '[{"label":"A","x":[...],"y":[...]}] or {"label":"A","y":[...]}',
    'step':       '[{"label":"A","x":[...],"y":[...]}] or {"label":"A","y":[...]}',
    'bar':        '{"labels":[...], "values":[...]}',
    'pie':        '{"labels":["A","B","C"], "values":[30,50,20]}',
    'multibar':   '{"labels":[...], "series":[{"label":"A","values":[...]}, ...]}',
    'stackedbar': '{"labels":[...], "series":[{"label":"A","values":[...]}, ...]}',
    'hist':       '{"values":[...], "bins":20} or [{"label":"A","values":[...]}, ...]',
    'heatmap':    '{"matrix":[[...]], "xlabels":[...], "ylabels":[...]}',
    'spectrum':   '{"freq":[99.0,...], "power":[-93,...], "center":99.3, "bandwidth":0.2}',
    'waterfall':  '{"matrix":[[...]], "xlabels":["99.0","99.6"], "ylabels":["t-1","now"], "min":-94, "max":-42}',
    'box':        '{"data":[[s1_vals],[s2_vals],...], "labels":["A","B",...]}',
    'indicator':  '{"value":23.4, "label":"Total Return %"}',
    'event':      '{"data":[x1,x2,...]}',
    'confusion':  '{"actual":[0,1,2,0], "predicted":[0,2,1,0], "labels":["Cat","Dog","Bird"]}',
    'sparkline':  '{"values":[1,3,5,2,8,4,6]}',
    'table':      '{"columns":[...], "rows":[[...], ...]}',
    'tree':       '{"label":"root","children":[{"label":"A","children":[...]}]}',
    'panel':      '{"content":"text here", "title":"optional", "box":"ROUNDED"}',
    'gauge':      '[{"label":"CPU","value":75,"max":100,"color":"red"}, ...] or {"metrics":[...]}',
    'dashboard':  '{"panels":[{"type":"gauge","data":{"label":"CPU","value":72,"max":100},"title":"CPU"},{"type":"sparkline","data":{"values":[1,3,5,2,8]},"title":"Load"}]}',
    'incplot':    'Raw JSON/JSONL/CSV/TSV auto plot. Supports prefer=bar|multibar|stackedbar|line|scatter|hist|table|kline via --prefer.',
    'graph':      '{"edges":[["A","B"],...], "directed":true, "node_style":"ROUND"}',
    'diagram':    'glyph-arts diagram sequence --json "Alice->Bob: Hello" or {"kind":"flowchart","text":"A -> B"}',
    'formula':    'Raw formula text or {"items":["E = mc^2", "\\\\int exp(-x^2) dx"]}; emits compact Unicode math',
    'formula-pretty': 'Raw formula text or {"items":["(a+b)/(c+d)", "Integral(exp(-x^2), x)"]}; emits SymPy multi-line math',
    'calibrate':  'glyph-arts chat calibrate --terminal --calibrate-glyph braille',
    'mermaid':    'Mermaid source text: graph/flowchart, sequenceDiagram, stateDiagram-v2, classDiagram, erDiagram, xychart-beta',
    'plotext':    '{"series":[{"type":"line|scatter|error|bar|hist|candlestick","x":[...],"y":[...]}],"texts":[...],"vlines":[...],"hlines":[...],"shapes":[...]}',
    'effect':     'glyph-arts effect gallery|pipeline|metrics|system-map|signal-panel|timeline|matrix|comparison|swimlane|kanban|quadrant|mindmap',
    'curve':      '{"points":[[x,y],...]}',
    'uniplot':    '[{"label":"A","x":[...],"y":[...]}] or {"label":"A","y":[...]}',
    'banner':      '{"text":"PROFIT","font":"big","color":"green"}',
    'art':         'glyph-arts art TEXT --font slant --decor barcode --frame double --gradient sunset',
    'candlestick': '{"dates":["DD/MM/YYYY",...], "open":[...], "high":[...], "low":[...], "close":[...]}',
    'hires':       '[{"label":"Q5","y":[3.5,9.2,9.4],"color":[0,245,212]},{"label":"Q1","y":[3.1,5.1,4.5],"color":[255,107,107]}]',
    'radar':       '{"labels":["ATK","DEF","SPD","MGC","LCK"],"series":[{"label":"Hero","values":[80,60,90,70,50],"color":[0,245,212]}],"max":100}',
    'textplot':    '{"expr":"sin(x) / x","xmin":-20,"xmax":20} or trailing expression text',
    'turtle':      '{"commands":[["forward",30],["right",90],["forward",30]]}',
    'plotille':    '[{"label":"A","x":[1,2,3,4],"y":[2,4,3,6],"color":"bright_cyan"}]',
    'rich_live':   '{"panels":[{"type":"bar","title":"Left","data":{"labels":["A","B"],"values":[1,2]}},{"type":"sparkline","title":"Right","data":{"values":[1,3,5,2,8]}}],"layout":"row","frames":1}',
    'animate':     'glyph-arts animate line --duration 5 --frames 30 --json \'[{"label":"DAU","x":[...],"y":[...]}]\'',
    'record':      "glyph-arts record demo.cast --cmd 'echo hi' --duration 1",
    'record-replay': 'glyph-arts record-replay demo.cast --output demo.gif',
    'to-hyperframes': "glyph-arts to-hyperframes --json '[{\"label\":\"x\",\"x\":[1,2],\"y\":[3,4]}]' --frames 30 --duration 5 --output-dir ./hf",
    'to-ascii-motion': "glyph-arts to-ascii-motion --json '[{\"label\":\"x\",\"x\":[1,2],\"y\":[3,4]}]' --formats html,mp4,svg --output-dir ./out",
    'code':        'glyph-arts code --file foo.py --lang python',
    'status':      'glyph-arts status --kind ok --message "All tests green"',
    'splash':      'glyph-arts splash',
    'demo':        'glyph-arts demo --speed fast',
    'gallery':     'glyph-arts gallery --output gallery.html',
    'auto':        "glyph-arts auto --json '[1,2,3]'",
    'live':        'glyph-arts live random --duration 10 --interval 0.2',
    'doctor':      'glyph-arts doctor',
    'install-backends': 'glyph-arts install-backends --target all [--run --yes]',
    'fonts':       'glyph-arts fonts install core',
    'chat-health': 'glyph-arts chat probe',
    'wave':        'glyph-arts wave render bar --json \'{"labels":["A"],"values":[3]}\'',
}

# Types where --width/--height/--theme have no effect
_NO_SIZE_THEME = {'table', 'tree', 'panel', 'graph', 'sparkline', 'gauge', 'banner', 'pie', 'dashboard', 'rich_live'}

PIXEL_SUPPORTED = frozenset({'bar', 'line', 'scatter'})
INTERACTIVE_SUPPORTED = frozenset({'line'})
_GLYPH_VISUAL_STYLES = {
    'auto',
    'ascii',
    'unicode',
    'braille',
    'block',
    'shade',
    'bar',
    'half-circle',
    'full-circle',
}
_DEPENDENCY_CORE = [
    'plotext',
    'rich',
    'uniplot',
    'pyfiglet',
    'sparklines',
    'duckdb',
    'pandas',
    'networkx',
    'phart',
]
_DEPENDENCY_MEDIA = (
    ('chafa', 'image/video high-fidelity render'),
    ('ffmpeg', 'video frame extract'),
    ('diagon', 'math/sequence/tree/flowchart diagrams'),
)
_DEPENDENCY_OPTIONAL = (
    ('PIL', 'image text fallback', 'Pillow'),
    ('drawille', 'curve chart', 'glyph-arts[braille]'),
    ('lttb', 'LTTB sampling', 'glyph-arts[lttb]'),
    ('textual', 'dashboard TUI', 'glyph-arts[tui]'),
)


def _build_cli_epilog():
    epilog_lines = [f'Chart types ({CHART_TYPE_COUNT}):']
    for engine, types in CHART_TYPES_BY_ENGINE.items():
        epilog_lines.append(f'  {engine:9}: {" ".join(types)}')
    epilog_lines.append("""
Examples:
  python chart.py kline --json '{"dates":["07/04/2026"],"open":[100],"high":[102],"low":[99],"close":[101]}'
  python chart.py scatter --json '[{"label":"A","x":[1,2,3],"y":[4,2,5]}]'
  python chart.py hist --json '{"values":[1,2,2,3,3,3,4,4,5],"bins":5}'
  python chart.py heatmap --json '{"matrix":[[1,2],[3,4]],"xlabels":["A","B"],"ylabels":["X","Y"]}'
  python chart.py spectrum --json '{"freq":[99.0,99.3,99.6],"power":[-93,-42,-93],"center":99.3,"bandwidth":0.2}'
  python chart.py waterfall --json '{"matrix":[[0,3,8,3,0],[0,2,9,4,0]],"xlabels":["99.0","99.6"],"ylabels":["t-1","now"]}'
  python chart.py diagram sequence --json 'Alice->Bob: Hello'
  python chart.py chat mermaid --json 'graph LR\nA[Start] --> B[Done]'
  python chart.py chat effects
  python chart.py effect signal-panel
  python chart.py chat image --file photo.jpg --width 80 --height 30
  python chart.py chat sequence --json 'Alice->Bob: Hello'
  python chart.py chat sdr spectrum --json '{"freq":[99.0,99.3,99.6],"power":[-93,-42,-93]}'
  python chart.py box --json '{"data":[[1,2,3,4,5],[2,3,4,5,6]],"labels":["A","B"]}'
  python chart.py sparkline --json '{"values":[1,3,5,2,8,4,6]}'
  python chart.py indicator --json '{"value":23.4,"label":"Total Return %"}'
  python chart.py confusion --json '{"actual":[0,1,2,0,1,2],"predicted":[0,2,2,0,0,1],"labels":["Cat","Dog","Bird"]}'
  python chart.py gauge --json '[{"label":"CPU","value":72,"max":100},{"label":"RAM","value":14,"max":32}]'
  python chart.py banner --json '{"text":"PROFIT","font":"big","color":"green"}'
  python chart.py uniplot --json '[{"label":"A","x":[1,2,3,4],"y":[2,4,3,6]},{"label":"B","y":[1,3,2,5]}]'
  python chart.py tree --json '{"label":"root","children":[{"label":"A"},{"label":"B","children":[{"label":"C"}]}]}'
  python chart.py panel --json '{"content":"Hello world","title":"Info","box":"ROUNDED"}'
  python chart.py multibar --json '{"labels":["Q1","Q2"],"series":[{"label":"Rev","values":[10,12]},{"label":"Cost","values":[8,9]}]}'
  python chart.py event --json '{"data":[1,3,5,8,13]}'
  python chart.py line --duckdb "SELECT trade_date, close FROM stock_daily LIMIT 60" --db /path/to/data.duckdb
  cat data.json | python chart.py line
""")
    return '\n'.join(epilog_lines)


def _print_dependency_status(include_optional=False):
    print('[core]')
    for pkg in _DEPENDENCY_CORE:
        try:
            __import__(pkg)
            status = 'OK'
        except ImportError:
            status = 'MISSING'
        print(f'  {pkg:<13} {status}')
    print('[media]')
    for tool, purpose in _DEPENDENCY_MEDIA:
        status = 'OK' if shutil.which(tool) else 'MISSING'
        print(f'  {tool:<13} {status}  ({purpose})')
    if include_optional:
        print('[optional]')
        for pkg, purpose, install in _DEPENDENCY_OPTIONAL:
            try:
                __import__(pkg)
                status = 'OK'
                hint = ''
            except ImportError:
                status = 'MISSING'
                hint = f'  -> pip install {install}'
            print(f'  {pkg:<13} {status}  ({purpose}){hint}')


def _print_style_list():
    print('Available styles per chart type:\n')
    for ctype in sorted(STYLE_ROUTES):
        engines = STYLE_ROUTES[ctype]
        parts = [f'{s} ({eng})' for s, eng in engines.items()]
        print(f'  {ctype:<12} {", ".join(parts)}')
    print(f'\nDefault style: {DEFAULT_STYLE}')
    print('Override: --style <name> or GLYPH_ARTS_STYLE=<name>')


def _handle_pre_parse_flags(raw_argv):
    if '--check-deps' in raw_argv:
        _print_dependency_status(include_optional='--all' in raw_argv)
        return True
    if '--list-styles' in raw_argv:
        _print_style_list()
        return True
    return False


def _apply_font_and_style_defaults(args):
    if args.font_tier is None:
        args.font_tier = detect_font_tier()
    if args.chat_profile != 'auto':
        from cli_charts.chat_health import chat_profile_tier

        args.font_tier = chat_profile_tier(args.chat_profile, args.font_tier)
        if args.chat_profile == 'ascii':
            args.no_color = True

    if args.style is None:
        env_style = os.environ.get('GLYPH_ARTS_STYLE', '').strip().lower()
        if env_style and env_style in _STYLES:
            args.style = env_style


def _load_ascii_motion_adapter():
    try:
        adapter = importlib.import_module("cli_charts.adapters.ascii_motion")
        client = importlib.import_module("cli_charts.mcp_clients.ascii_motion")
    except ImportError:
        print("error: --polish ascii-motion requires 'pip install glyph-arts[ai-motion]'", file=sys.stderr)
        sys.exit(2)
    if getattr(client, "ClientSession", None) is None:
        print("error: --polish ascii-motion requires 'pip install glyph-arts[ai-motion]'", file=sys.stderr)
        sys.exit(2)
    return adapter


def _require_ascii_motion_npx():
    npx = shutil.which("npx") or shutil.which("npx.cmd") or "npx"
    try:
        result = subprocess.run(
            [npx, "ascii-motion-mcp", "--version"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
    except FileNotFoundError:
        print("error: ascii-motion-mcp not found; install via 'npm i -g ascii-motion-mcp'", file=sys.stderr)
        sys.exit(3)
    if result.returncode != 0:
        print("error: ascii-motion-mcp not found; install via 'npm i -g ascii-motion-mcp'", file=sys.stderr)
        sys.exit(3)


def _render_ascii_motion_frames(chart_type, data, args, adapter, no_color=False):
    if chart_type not in CMDS or chart_type in {
        'animate', 'record', 'record-replay', 'to-hyperframes', 'to-ascii-motion',
    'code', 'status', 'splash', 'demo', 'gallery', 'auto', 'live', 'doctor', 'install-backends', 'fonts', 'chat-health', 'wave',
    }:
        print('ERROR:schema: to-ascii-motion needs a renderable chart type argument', file=sys.stderr)
        sys.exit(1)
    kw = dict(
        xlabel=args.xlabel,
        ylabel=args.ylabel,
        xlim=args.xlim,
        ylim=args.ylim,
        xscale=args.xscale,
        yscale=args.yscale,
        orientation=args.orientation,
        output='',
        no_color=no_color,
        font_tier=args.font_tier,
        marker=args.marker if chart_type == 'scatter' else None,
        symbol_set=args.symbols if chart_type == 'bar' else None,
        candle_style=args.candle_style if chart_type == 'kline' else 'default',
        gauge_style=args.gauge_style if chart_type == 'gauge' else 'bar',
    )
    text = _capture_stdout(lambda: CMDS[chart_type](data, args.title, args.width, args.height, args.theme, **kw))
    return [adapter.text_to_cells(text)]


def _build_arg_parser():
    return build_parser(
        commands=CMDS,
        media_types=_MEDIA_TYPES,
        marker_symbols=_MARKER_SYMBOLS,
        registry_styles=_STYLES,
        glyph_visual_styles=_GLYPH_VISUAL_STYLES,
        epilog=_build_cli_epilog(),
    )


def main(argv=None):
    raw_argv = list(sys.argv[1:] if argv is None else argv)
    raw_argv = _rewrite_chat_argv(raw_argv, CMDS)
    raw_argv = _rewrite_diagram_argv(raw_argv)
    p = _build_arg_parser()
    if _handle_pre_parse_flags(raw_argv):
        sys.exit(0)

    args = p.parse_args(raw_argv)
    if args.type == 'serve':
        if not args.stdio:
            print('ERROR:schema: serve currently requires --stdio', file=sys.stderr)
            sys.exit(1)
        from cli_charts.serve_stdio import run_stdio_server

        sys.exit(run_stdio_server(main))

    _apply_font_and_style_defaults(args)

    tool_rc = dispatch_tool_command(args, raw_argv)
    if tool_rc is not None:
        sys.exit(tool_rc)

    from cli_charts.splash import maybe_play_first_run
    maybe_play_first_run(no_splash=args.no_splash)

    direct_rc = dispatch_direct_command(args, calibrate_func=calibrate)
    if direct_rc is not None:
        sys.exit(direct_rc)

    # Media types (image/video) bypass JSON loading -- they take a filesystem path.
    if args.type in _MEDIA_TYPES:
        sys.exit(dispatch_media(args))
        return

    text_rc = dispatch_text_input_command(
        args,
        commands=CMDS,
        diagram_func=diagram,
        mermaid_func=mermaid,
        effect_func=effect,
    )
    if text_rc is not None:
        sys.exit(text_rc)

    motion_rc = dispatch_motion_command(
        args,
        load_ascii_motion_adapter=_load_ascii_motion_adapter,
        require_ascii_motion_npx=_require_ascii_motion_npx,
        render_ascii_motion_frames=_render_ascii_motion_frames,
    )
    if motion_rc is not None:
        sys.exit(motion_rc)

    if args.animate:
        from cli_charts.cmd.animate_stream import animate_stdin

        no_color = args.no_color or bool(os.environ.get('NO_COLOR'))
        kw = dict(xlabel=args.xlabel, ylabel=args.ylabel, xlim=args.xlim,
                  ylim=args.ylim, xscale=args.xscale, yscale=args.yscale,
                  orientation=args.orientation, output=args.output,
                  no_color=no_color, visual_style=args.style)
        animate_stdin(args.type, args.title, args.width, args.height,
                      args.theme, args.refresh, args.window, args.duration, kw)
        return

    # Warn when size/theme options are silently ignored
    _default_width = shutil.get_terminal_size((70, 20)).columns
    if args.type in _NO_SIZE_THEME:
        ignored = []
        if args.width != _default_width:
            ignored.append('--width')
        if args.height != 20:
            ignored.append('--height')
        if args.theme != 'pro':
            ignored.append('--theme')
        if ignored:
            print(f"warning: {', '.join(ignored)} ignored for {args.type} charts",
                  file=sys.stderr)

    # Respect NO_COLOR env var (https://no-color.org)
    no_color = args.no_color or bool(os.environ.get('NO_COLOR'))

    try:
        if args.type == 'auto':
            if args.file:
                with open(args.file, encoding='utf-8') as _f:
                    raw = _f.read().strip()
            elif args.data:
                raw = args.data
            else:
                raw = sys.stdin.read().strip()
            if not raw:
                print('ERROR:schema: Provide --json, --file, or pipe JSON/CSV/TSV to stdin',
                      file=sys.stderr)
                sys.exit(1)
            from cli_charts.auto_detect import detect_auto
            detected = detect_auto(raw, args.prefer)
            args.type = detected.chart_type
            data = detected.data
        elif args.duckdb:
            if not args.db:
                print('ERROR:schema: --db is required when using --duckdb '
                      '(e.g. --db /path/to/data.duckdb)', file=sys.stderr)
                sys.exit(1)
            import duckdb as _duckdb_mod  # noqa: F401
            data = load_duckdb(args.duckdb, args.db, args.type)
        else:
            if args.file:
                with open(args.file, encoding='utf-8') as _f:
                    raw = _f.read().strip()
            elif args.data:
                raw = args.data
            else:
                raw = sys.stdin.read().strip()
            if not raw:
                print('ERROR:schema: Provide --json, --file, --duckdb, or pipe JSON to stdin',
                      file=sys.stderr)
                sys.exit(1)
            try:
                data = json.loads(raw)
            except json.JSONDecodeError as exc:
                if args.type == 'graph':
                    data = raw
                else:
                    print(f'ERROR:json: {exc}', file=sys.stderr)
                    sys.exit(1)

        if args.sample > 0:
            data = _sample_data(data, args.sample, chart_type=args.type)

        kw = dict(
            xlabel=args.xlabel,
            ylabel=args.ylabel,
            xlim=args.xlim,
            ylim=args.ylim,
            xscale=args.xscale,
            yscale=args.yscale,
            orientation=args.orientation,
            output=args.output,
            format=args.format,
            no_color=no_color,
            link_data=args.link_data,
            link_title=args.link_title,
            statusline=args.statusline,
            rich_progress=args.rich_progress,
            prefer=args.prefer,
            font_tier=args.font_tier,
            marker=args.marker if args.type == 'scatter' else None,
            symbol_set=args.symbols if args.type == 'bar' else None,
            visual_style=args.style,
            candle_style=args.candle_style if args.type == 'kline' else 'default',
            gauge_style=(
                args.style
                if args.type == 'gauge' and args.style in _GLYPH_VISUAL_STYLES
                else args.gauge_style if args.type == 'gauge' else 'bar'
            ),
            graph_format=args.graph_format,
            graph_style=args.graph_style,
            graph_charset=args.graph_charset,
            graph_node_spacing=args.graph_node_spacing,
            graph_layer_spacing=args.graph_layer_spacing,
            mermaid_theme=args.mermaid_theme,
            mermaid_ascii=args.mermaid_ascii,
            mermaid_padding_x=args.mermaid_padding_x,
            mermaid_padding_y=args.mermaid_padding_y,
            mermaid_box_padding=args.mermaid_box_padding,
            effect_kind=args.effect_kind,
        )

        # Style routing: redirect to alternate engine if --style is set
        _resolved_engine = resolve_engine(args.type, args.style) if args.style in _STYLES else None
        if _resolved_engine and args.engine == 'ascii':
            from cli_charts.render.style_router import render_styled
            rc = render_styled(
                args.type, _resolved_engine, args.style,
                data, args.title, args.width, args.height, args.theme, **kw
            )
            if rc is not None:
                sys.exit(rc)
            # rc=None means engine not yet implemented, fall through to default

        try:
            if args.engine == 'pixel':
                if args.type not in PIXEL_SUPPORTED:
                    print(f'WARNING: --engine pixel does not yet support {args.type!r} '
                          f'(Phase A: {sorted(PIXEL_SUPPORTED)}); falling back to ascii',
                          file=sys.stderr)
                else:
                    from cli_charts.render.matplotlib_engine import render_pixel
                    rc = render_pixel(
                        args.type, data, args.width, args.height,
                        title=args.title, theme=args.theme,
                        output=args.output, no_color=no_color, art=args.art,
                    )
                    sys.exit(rc)
            if args.engine == 'interactive':
                from cli_charts.render.interactive_engine import render_interactive
                rc = render_interactive(
                    args.type, data, args.width, args.height,
                    title=args.title, theme=args.theme, no_color=no_color,
                )
                sys.exit(rc)

            if args.polish == 'ascii-motion':
                adapter = _load_ascii_motion_adapter()
                _require_ascii_motion_npx()
                output = _capture_stdout(lambda: CMDS[args.type](data, args.title, args.width, args.height, args.theme, **kw))
                cells = adapter.text_to_cells(output)
                project_dir = tempfile.mkdtemp(prefix='glyph-arts-ascii-motion-')
                import asyncio

                asyncio.run(adapter.polish_frames(project_dir, [cells], style=args.polish_style))
                if args.output:
                    formats = [args.output.rsplit('.', 1)[-1].lower()] if '.' in args.output else ['html']
                    asyncio.run(adapter.to_ascii_motion(project_dir, [cells], formats, os.path.dirname(args.output) or '.'))
                return

            if args.output and args.type == 'table' and args.output.lower().endswith('.md'):
                CMDS[args.type](data, args.title, args.width, args.height, args.theme, **kw)
            elif args.output:
                from cli_charts.render.export_engine import export_to_path

                kw["output"] = ""
                buf = io.StringIO()
                with contextlib.redirect_stdout(buf):
                    CMDS[args.type](
                        data, args.title, args.width, args.height, args.theme, **kw
                    )
                export_to_path(buf.getvalue(), args.output, no_color)
            else:
                CMDS[args.type](data, args.title, args.width, args.height, args.theme, **kw)
        except (KeyError, IndexError, TypeError, ValueError) as exc:
            print(f'ERROR:schema: Invalid {args.type} data schema: {exc}\n'
                  f'Expected: {EXPECTED_SCHEMAS.get(args.type, "?")}',
                  file=sys.stderr)
            sys.exit(1)

        if os.environ.get('CLI_CHARTS_LOG') == '1':
            try:
                entry = json.dumps({
                    'ts': datetime.datetime.now().isoformat(),
                    'type': args.type,
                    'title': args.title,
                })
                with open('.chart_history.jsonl', 'a', encoding='utf-8') as _lf:
                    _lf.write(entry + '\n')
            except Exception:
                pass

    except ImportError as exc:
        pkg = str(exc).split("'")[1] if "'" in str(exc) else str(exc)
        print(f'ERROR:dep: pip install {pkg}', file=sys.stderr)
        sys.exit(2)
    except SystemExit:
        raise
    except Exception:
        import traceback
        last = traceback.format_exc().strip().splitlines()[-1]
        print(f'ERROR:render: {last}', file=sys.stderr)
        sys.exit(4)


if __name__ == '__main__':
    main()
