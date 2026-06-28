"""Argument parser construction for the glyph-arts command line."""

import argparse
import shutil

from cli_charts.cmd.media_args import add_media_arguments

_VERSION: str | None = None


def _load_version() -> str:
    global _VERSION
    if _VERSION is not None:
        return _VERSION
    try:
        from pathlib import Path as _Path

        _VERSION = (_Path(__file__).parent.parent / "VERSION").read_text(encoding="utf-8").strip()
    except Exception:
        try:
            from importlib.metadata import version as _pkg_version

            _VERSION = _pkg_version("glyph-arts")
        except Exception:
            _VERSION = "unknown"
    return _VERSION


class _LazyVersionAction(argparse.Action):
    def __init__(self, option_strings, dest=argparse.SUPPRESS, default=argparse.SUPPRESS, **kwargs):
        super().__init__(option_strings=option_strings, dest=dest, nargs=0, default=default, **kwargs)

    def __call__(self, parser, namespace, values, option_string=None):
        parser.exit(message=f"glyph-arts {_load_version()}\n")


def build_parser(
    *,
    commands,
    media_types,
    marker_symbols,
    registry_styles,
    glyph_visual_styles,
    epilog,
):
    command_names = list(commands)
    p = argparse.ArgumentParser(
        description='glyph-arts -- terminal-visible charts and chat drawing',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=epilog)
    p.add_argument('type', choices=command_names + sorted(media_types), metavar='TYPE',
                   help='Chart type, or use `chat TYPE ...` for chat-safe drawing: ' + ' | '.join(command_names) +
                        ' | image | video (media via Pillow/chafa/ffmpeg)')
    p.add_argument('art_text', nargs='*',
                   help='Text for TYPE=art (example: glyph-arts art SHIP IT)')
    p.add_argument('--json',        dest='data', help='JSON data string')
    p.add_argument('--file',        metavar='PATH',
                   help='Read JSON from a file path')
    p.add_argument('--duckdb',      metavar='SQL',
                   help='SQL query against a DuckDB database')
    p.add_argument('--db',          default=None,
                   help='DuckDB file path (required with --duckdb)')
    p.add_argument('--title',       default='')
    p.add_argument('--width',       type=int,
                   default=shutil.get_terminal_size((70, 20)).columns,
                   help='Chart width in terminal columns (ignored for table/tree/panel/graph/sparkline)')
    p.add_argument('--height',      type=int, default=20,
                   help='Chart height in terminal rows (ignored for table/tree/panel/graph/sparkline)')
    p.add_argument('--theme',       default='pro',
                   help='plotext theme: pro dark clear matrix retro elegant + brand palettes: claude linear tesla vercel (ignored for rich/graph/sparkline)')
    p.add_argument('--font-tier',   choices=['ascii', 'unicode', 'unicode-extended', 'nerd'],
                   default=None, help='Terminal font capability tier (default: auto-detect)')
    p.add_argument('--chat-profile', choices=['auto', 'ascii', 'safe', 'rich', 'max'],
                   default='auto', help='Chat glyph profile: auto, ascii, safe, rich, or max')
    p.add_argument('--font',        default='slant',
                   help='TYPE=art figlet font (default: slant). Use --list-fonts to see all.')
    p.add_argument('--decor',       default=None,
                   help='TYPE=art optional decoration (barcode/snake/dna/wave + 200+ from art lib). Use --list-decors to see all.')
    p.add_argument('--frame',       choices=['single', 'double', 'rounded', 'ascii', 'heavy', 'none'],
                   default=None, help='TYPE=art optional Rich frame')
    p.add_argument('--gradient',    choices=['sunset', 'viridis', 'ocean', 'rainbow', 'none'],
                   default=None, help='TYPE=art optional text gradient')
    p.add_argument('--justify',     choices=['left', 'center', 'right'],
                   default=None, help='TYPE=art figlet text alignment')
    p.add_argument('--anim',        action='store_true',
                   help='TYPE=art animation mode (requires art library; pip install glyph-arts[art])')
    p.add_argument('--list-fonts',  action='store_true',
                   help='TYPE=art: list all available figlet fonts')
    p.add_argument('--list-decors', action='store_true',
                   help='TYPE=art: list all available decorations')
    p.add_argument('--engine',      choices=['ascii', 'pixel', 'interactive'], default='ascii',
                   help='Render backend. ascii (default) = plotext/rich/drawille text art. '
                        'pixel = matplotlib + chafa true-color pixel chart (requires '
                        '`pip install glyph-arts[pixel]` + chafa system binary). '
                        'Phase A pixel support: bar/line/scatter only. '
                        'interactive = Textual keyboard-first TUI for line charts '
                        '(requires `pip install glyph-arts[interactive]`).')
    add_media_arguments(p)
    p.add_argument('--art', choices=['low', 'default', 'high'], default='default',
                   help='Visual fidelity tier (only with --engine pixel). low=block(compat). default=vhalf(btop-style). high=sextant(max resolution).')
    p.add_argument('--xlabel',      default='', help='X-axis label (plotext charts)')
    p.add_argument('--ylabel',      default='', help='Y-axis label (plotext charts)')
    p.add_argument('--xlim',        nargs=2, type=float, metavar=('MIN', 'MAX'),
                   help='X-axis limits')
    p.add_argument('--ylim',        nargs=2, type=float, metavar=('MIN', 'MAX'),
                   help='Y-axis limits')
    p.add_argument('--xscale',      choices=['linear', 'log'], default='linear')
    p.add_argument('--yscale',      choices=['linear', 'log'], default='linear')
    p.add_argument('--orientation', choices=['vertical', 'horizontal'],
                   default='vertical', help='Bar orientation (bar/multibar/stackedbar)')
    p.add_argument('--output',      default='',
                   help='Save chart to file (.png with pixel engine; .txt/.ansi/.html with ascii engine; .md for table)')
    p.add_argument('--format',      default=None,
                   help="Output format (reserved for future use)")
    p.add_argument('--output-dir',  default='',
                   help='TYPE=to-hyperframes/to-ascii-motion output directory')
    p.add_argument('--out-dir',     dest='output_dir',
                   help='Alias for --output-dir')
    p.add_argument('--formats',     default='html',
                   help='TYPE=to-ascii-motion comma-separated exports (html,mp4,gif,react,svg)')
    p.add_argument('--polish',      choices=['ascii-motion'], default='',
                   help='Route rendered chart through ASCII Motion polish')
    p.add_argument('--polish-style', default='retro',
                   help='ASCII Motion polish style (terminal, retro, matrix, minimalist, detailed, colorful)')
    p.add_argument('--cmd',         default='',
                   help='TYPE=record command to run inside asciinema')
    p.add_argument('--no-color',    action='store_true',
                   help='Disable ANSI colors (respects NO_COLOR env var)')
    p.add_argument('--marker',      choices=list(marker_symbols), default=None,
                   help='TYPE=scatter marker symbol set')
    p.add_argument('--symbols',     default=None, metavar='SET',
                   help='TYPE=bar symbol set (block, progress, braille, arrows); '
                        'image symbols (ascii, shade, block, half) or chafa --symbols value; '
                        'video chafa --symbols value')
    p.add_argument('--candle-style', choices=['default', 'geom'], default='default',
                   help='TYPE=kline candle glyph style')
    p.add_argument('--gauge-style', choices=['bar', 'half-circle', 'full-circle', 'braille'],
                   default='bar', help='TYPE=gauge glyph style')
    p.add_argument('--style',       choices=sorted(set(registry_styles) | glyph_visual_styles),
                   default=None, help='Rendering style. Supports global style routing plus legacy glyph styles.')
    p.add_argument('--list-styles', action='store_true',
                   help='Show available styles for each chart type and exit')
    p.add_argument('--prefer',      choices=['sparkline', 'bar', 'multibar', 'stackedbar', 'line', 'scatter', 'hist', 'table', 'kline', 'candlestick'], default='',
                   help='TYPE=auto/incplot chart preference override')
    p.add_argument('--calibrate-from', dest='calibrate_from', type=int, default=96,
                   help='TYPE=calibrate starting ruler width')
    p.add_argument('--calibrate-to', dest='calibrate_to', type=int, default=160,
                   help='TYPE=calibrate ending ruler width')
    p.add_argument('--calibrate-step', dest='calibrate_step', type=int, default=8,
                   help='TYPE=calibrate ruler width step')
    p.add_argument('--calibrate-glyph', choices=['all', 'ascii', 'digits', 'braille', 'solid', 'mixed'], default='all',
                   help='TYPE=calibrate glyph family to print')
    p.add_argument('--terminal', action='store_true',
                   help='TYPE=calibrate measure current terminal columns')
    p.add_argument('--recommend', action='store_true',
                   help='TYPE=calibrate print preset recommendation rules')
    p.add_argument('--diagram-kind', choices=['math', 'sequence', 'tree', 'table', 'frame', 'box', 'note', 'flowchart', 'graphdag', 'dag', 'graphplanar', 'planar'],
                   default='', help='TYPE=diagram generator override')
    p.add_argument('--diagram-engine', choices=['auto', 'diagon', 'builtin'], default='auto',
                   help='TYPE=diagram backend. auto uses Diagon when installed, else builtin fallback.')
    p.add_argument('--mermaid-theme', choices=[
        'zinc-light', 'zinc-dark', 'tokyo-night', 'tokyo-night-storm',
        'tokyo-night-light', 'catppuccin-mocha', 'catppuccin-latte', 'nord',
        'nord-light', 'dracula', 'github-light', 'github-dark',
        'solarized-light', 'solarized-dark', 'one-dark',
    ], default='zinc-dark', help='TYPE=mermaid beautiful-mermaid-compatible theme name')
    p.add_argument('--mermaid-ascii', action='store_true',
                   help='TYPE=mermaid use ASCII connectors instead of Unicode')
    p.add_argument('--mermaid-padding-x', type=int, default=5,
                   help='TYPE=mermaid horizontal spacing between nodes')
    p.add_argument('--mermaid-padding-y', type=int, default=1,
                   help='TYPE=mermaid vertical spacing between nodes')
    p.add_argument('--mermaid-box-padding', type=int, default=1,
                   help='TYPE=mermaid node inner padding')
    p.add_argument('--graph-format', choices=['auto', 'json', 'edges', 'dot', 'graphml'], default='auto',
                   help='TYPE=graph input format override')
    p.add_argument('--graph-style', choices=['minimal', 'square', 'round', 'diamond'], default='round',
                   help='TYPE=graph PHART node style')
    p.add_argument('--graph-charset', choices=['unicode', 'ascii'], default='unicode',
                   help='TYPE=graph PHART character set')
    p.add_argument('--graph-node-spacing', type=int, default=4,
                   help='TYPE=graph horizontal node spacing')
    p.add_argument('--graph-layer-spacing', type=int, default=2,
                   help='TYPE=graph vertical layer spacing')
    p.add_argument('--effect-kind', choices=['gallery', 'pipeline', 'metrics', 'system-status', 'system-map', 'signal-panel', 'timeline', 'matrix', 'comparison', 'swimlane', 'kanban', 'quadrant', 'mindmap'],
                   default='', help='TYPE=effect preset override')
    p.add_argument('--fps',         type=int, default=12, metavar='N',
                   help='Video playback frames/sec for type=video (default: 12)')
    p.add_argument('--input', dest='petiglyph_input', action='append', nargs='+',
                   default=[],
                   help='TYPE=petiglyph source file(s) for create glyph/grid/animation')
    p.add_argument('--rows', type=int, default=None,
                   help='TYPE=petiglyph grid row count')
    p.add_argument('--cols', type=int, default=None,
                   help='TYPE=petiglyph grid column count')
    p.add_argument('--bleed', choices=['off', 'weak', 'strong'], default='',
                   help='TYPE=petiglyph grid bleed setting')
    p.add_argument('--threshold', type=float, default=None,
                   help='TYPE=petiglyph threshold value')
    p.add_argument('--clear-threshold', action='store_true',
                   help='TYPE=petiglyph clear a configured threshold')
    p.add_argument('--force-remap', action='store_true',
                   help='TYPE=petiglyph build with fresh codepoint remapping')
    p.add_argument('--build', action='store_true',
                   help='TYPE=petiglyph build after create/configure when upstream supports it')
    p.add_argument('--install', action='store_true',
                   help='TYPE=petiglyph install font after create/configure when upstream supports it')
    p.add_argument('--glyph', default='',
                   help='TYPE=petiglyph preview/show-sample glyph filter')
    p.add_argument('--animation', default='',
                   help='TYPE=petiglyph preview/show-sample animation filter')
    p.add_argument('--preview-limit', type=int, default=6,
                   help='TYPE=petiglyph maximum preview PNGs to render in --chat mode')
    p.add_argument('--petiglyph-backend', choices=['auto', 'cli', 'native'], default='auto',
                   help='TYPE=petiglyph backend selector')
    p.add_argument('--petiglyph-arg', action='append', default=[],
                   help='TYPE=petiglyph raw upstream CLI argument(s); repeat as needed')
    p.add_argument('--petiglyph-json-output', action='store_true',
                   help=argparse.SUPPRESS)
    p.add_argument('--version',     action=_LazyVersionAction, help='Show glyph-arts version and exit')
    p.add_argument('--check-deps',  action='store_true',
                   help='Print dependency availability table and exit')
    p.add_argument('--all',         action='store_true',
                   help='With --check-deps: also show optional deps (braille/lttb/tui)')
    p.add_argument('--sample',      type=int, default=0, metavar='N',
                   help='Downsample any list longer than N in the input data')
    p.add_argument('--animate',    action='store_true',
                   help='Read stdin line-by-line and re-render chart after each value')
    p.add_argument('--refresh',    type=int, default=10, metavar='FPS',
                   help='Animation refresh rate in frames/sec (default: 10)')
    p.add_argument('--window',     type=int, default=50,  metavar='N',
                   help='Keep last N data points in view (0=unlimited, default: 50)')
    p.add_argument('--duration',   type=float, default=0, metavar='SEC',
                   help='Auto-stop after SEC seconds (0=until EOF/Ctrl-C)')
    p.add_argument('--interval',   type=float, default=0.2, metavar='SEC',
                   help='TYPE=live update interval in seconds (default: 0.2)')
    p.add_argument('--frames',     type=int, default=30, metavar='N',
                   help='TYPE=animate frame count (default: 30)')
    p.add_argument('--spinner',    default='',
                   help='TYPE=animate/status Rich spinner preset (dots, dots2, line, pong, ...)')
    p.add_argument('--rich-progress', action='store_true',
                   help='TYPE=gauge render with rich.progress Progress')
    p.add_argument('--lang',       default='',
                   help='TYPE=code syntax language (python, javascript, ...)')
    p.add_argument('--kind',       default='info',
                   help='TYPE=status kind: ok, warn, error, info, loading')
    p.add_argument('--message',    default='',
                   help='TYPE=status message text')
    p.add_argument('--link-data',  default='',
                   help='OSC 8 hyperlink URL for line/scatter data labels')
    p.add_argument('--link-title', default='',
                   help='OSC 8 hyperlink URL for the chart title')
    p.add_argument('--statusline', action='store_true',
                   help='Single-line ANSI-safe output for Claude Code statusLine.command')
    p.add_argument('--no-splash',  action='store_true',
                   help='Skip the first-run mascot splash')
    p.add_argument('--speed', choices=['fast', 'normal', 'slow'], default='normal',
                   help='TYPE=demo speed: fast=10s, normal=30s, slow=60s')
    p.add_argument('--no-clear', action='store_true',
                   help='TYPE=demo do not clear the terminal between sections')
    p.add_argument('--demo', action='store_true',
                   help='TYPE=dashboard use built-in dashboard demo')
    p.add_argument('--no-interactive', action='store_true',
                   help='TYPE=dashboard render static Rich dashboard instead of Textual TUI')
    p.add_argument('--chart', default='',
                   help='TYPE=gallery pre-select chart type')
    p.add_argument(
        '--target',
        choices=['all', 'chat', 'media', 'fonts', 'diagrams', 'petiglyph'],
        default='all',
        help='TYPE=install-backends install target',
    )
    p.add_argument(
        '--manager',
        choices=[
            'auto', 'download', 'scoop', 'choco', 'winget', 'brew', 'apt-get',
            'dnf', 'pacman', 'snap', 'x-cmd',
        ],
        default='auto',
        help='TYPE=install-backends package manager override',
    )
    p.add_argument('--run', action='store_true',
                   help='TYPE=install-backends execute the generated install commands')
    p.add_argument('--yes', action='store_true',
                   help='TYPE=install-backends confirm execution when used with --run')
    p.add_argument('--fix-chat', action='store_true',
                   help='TYPE=doctor print chat glyph/font remediation plan')
    p.add_argument('--font-dir', default='',
                   help='TYPE=fonts download/status directory (default: ~/.glyph-arts/fonts)')
    p.add_argument('--dry-run', action='store_true',
                   help='TYPE=wave print planned chart/wsh commands without running them')
    p.add_argument('--wave-format', choices=['html', 'txt', 'ansi'], default='html',
                   help='TYPE=wave render export format for wave render')
    p.add_argument('--wave-stdout', action='store_true',
                   help='TYPE=wave render also print the generated preview file')
    p.add_argument('--stdio', action='store_true',
                   help='TYPE=serve read newline-delimited JSON requests from stdin')
    return p
