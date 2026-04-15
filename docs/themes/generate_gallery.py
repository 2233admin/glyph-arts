#!/usr/bin/env python3
"""Theme gallery generator -- renders all 4 brand palettes to the terminal.

Usage:
    python docs/themes/generate_gallery.py              # all themes, bar+line
    python docs/themes/generate_gallery.py --theme claude
    python docs/themes/generate_gallery.py --chart line
    python docs/themes/generate_gallery.py --no-color   # plain text, no ANSI
"""
import argparse
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).parent.parent.parent
CHART = REPO / 'scripts' / 'chart.py'

THEMES = ['claude', 'linear', 'tesla', 'vercel']

BAR_DATA = '{"labels":["Jan","Feb","Mar","Apr","May","Jun"],"values":[42,58,35,71,63,50]}'
LINE_DATA = '[{"label":"Series A","x":[1,2,3,4,5,6,7,8],"y":[10,18,14,22,20,28,25,32]},{"label":"Series B","x":[1,2,3,4,5,6,7,8],"y":[20,15,25,18,30,22,35,28]}]'

CHARTS = {
    'bar':  ('bar',  BAR_DATA,  'Monthly Activity'),
    'line': ('line', LINE_DATA, 'Multi-Series Trend'),
}


def render(theme: str, chart_key: str, no_color: bool) -> None:
    chart_type, data, title = CHARTS[chart_key]
    cmd = [
        sys.executable, str(CHART),
        chart_type,
        '--json', data,
        '--title', f'{title} [{theme}]',
        '--theme', theme,
        '--height', '12',
        '--width', '72',
    ]
    if no_color:
        cmd.append('--no-color')
    subprocess.run(cmd)


def main() -> None:
    p = argparse.ArgumentParser(description='glyph-arts theme gallery')
    p.add_argument('--theme',    choices=THEMES, default=None,
                   help='Render only this theme (default: all)')
    p.add_argument('--chart',    choices=list(CHARTS), default=None,
                   help='Render only this chart type (default: bar + line)')
    p.add_argument('--no-color', action='store_true')
    args = p.parse_args()

    themes = [args.theme] if args.theme else THEMES
    charts = [args.chart] if args.chart else list(CHARTS)

    for theme in themes:
        sep = '=' * 72
        print(f'\n{sep}')
        print(f'  THEME: {theme.upper()}')
        print(f'{sep}')
        for chart in charts:
            render(theme, chart, args.no_color)


if __name__ == '__main__':
    main()
