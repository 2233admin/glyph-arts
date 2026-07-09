"""radar chart -- extracted from cli_charts.cmd._helpers (Phase 3b)."""

import math
import sys

from cli_charts.charts._utils import _HIRES_PALETTE, _HiresCanvas
from cli_charts.registry import register

@register("radar")

def radar(d, title, w, h, theme, **kw):
    """Polar radar/spider chart on a 24-bit braille canvas.
    {"labels":["ATK","DEF","SPD","MGC","LCK"],
     "series":[{"label":"Hero","values":[80,60,90,70,50],"color":[0,245,212]}],
     "max":100}
    'max' defaults to the largest value across all series.
    """
    no_color = kw.get('no_color', False)
    labels = d['labels']
    series_list = d.get('series', [d])
    n_axes = len(labels)
    if n_axes < 3:
        print('ERROR:schema: radar requires at least 3 labels', file=sys.stderr)
        sys.exit(1)

    pw = w * 2
    ph = h * 4
    canvas = _HiresCanvas(w, h)
    cx = pw // 2
    cy = ph // 2
    r_max = min(cx, cy) - 8

    v_max = d.get('max', max(v for s in series_list for v in s['values']))
    GRID  = (32, 34, 55)
    AXIS  = (50, 52, 80)

    # Concentric rings
    for ring_pct in (0.25, 0.50, 0.75, 1.0):
        r = int(r_max * ring_pct)
        for i in range(n_axes):
            a1 = math.pi / 2 - 2 * math.pi * i / n_axes
            a2 = math.pi / 2 - 2 * math.pi * (i + 1) / n_axes
            x1 = cx + int(r * math.cos(a1))
            y1 = cy - int(r * math.sin(a1))
            x2 = cx + int(r * math.cos(a2))
            y2 = cy - int(r * math.sin(a2))
            canvas.line(x1, y1, x2, y2, GRID)

    # Axis spokes
    spoke_ends = []
    for i in range(n_axes):
        angle = math.pi / 2 - 2 * math.pi * i / n_axes
        ex = cx + int(r_max * math.cos(angle))
        ey = cy - int(r_max * math.sin(angle))
        spoke_ends.append((ex, ey, angle))
        canvas.line(cx, cy, ex, ey, AXIS)

    # Data polygons
    for idx, s in enumerate(series_list):
        vals = s['values']
        rgb = tuple(s['color']) if 'color' in s else _HIRES_PALETTE[idx % len(_HIRES_PALETTE)]
        dim = tuple(max(0, c // 5) for c in rgb)
        pts = []
        for i, v in enumerate(vals):
            pct = min(v / v_max, 1.0)
            angle = math.pi / 2 - 2 * math.pi * i / n_axes
            px = cx + int(r_max * pct * math.cos(angle))
            py = cy - int(r_max * pct * math.sin(angle))
            pts.append((px, py))
        pts.append(pts[0])
        # glow
        if not no_color:
            for j in range(len(pts) - 1):
                for ox in (-1, 0, 1):
                    for oy in (-1, 0, 1):
                        if ox == 0 and oy == 0:
                            continue
                        canvas.line(pts[j][0] + ox, pts[j][1] + oy,
                                    pts[j + 1][0] + ox, pts[j + 1][1] + oy, dim)
        for j in range(len(pts) - 1):
            canvas.line(pts[j][0], pts[j][1], pts[j + 1][0], pts[j + 1][1], rgb)

    if title:
        print(title)
    rows = canvas.render(no_color)
    for row in rows:
        print(row)

    # Print axis labels below chart
    label_line = "  ".join(
        f"\033[38;2;{_HIRES_PALETTE[0][0]};{_HIRES_PALETTE[0][1]};{_HIRES_PALETTE[0][2]}m{lbl}\033[0m"
        if not no_color else lbl
        for lbl in labels
    )
    print(label_line)

    # Legend
    if len(series_list) > 1 or series_list[0].get('label'):
        for idx, s in enumerate(series_list):
            lbl = s.get('label', f'S{idx}')
            rgb = tuple(s['color']) if 'color' in s else _HIRES_PALETTE[idx % len(_HIRES_PALETTE)]
            if no_color:
                print(f"  [{lbl}]")
            else:
                print(f"  \033[38;2;{rgb[0]};{rgb[1]};{rgb[2]}m██ {lbl}\033[0m")
