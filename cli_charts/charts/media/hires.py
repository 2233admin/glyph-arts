"""hires chart -- extracted from cli_charts.cmd._helpers (Phase 3b)."""

from cli_charts.charts._utils import _HIRES_PALETTE, _HiresCanvas, _catmull_pixels
from cli_charts.registry import register

@register("hires")

def hires(d, title, w, h, theme, **kw):
    """24-bit colored braille renderer.  Catmull-Rom smooth curves + glow halos.
    Same multi-series schema as 'line'.  Each series accepts optional "color":[r,g,b]
    and "glow":false to disable the halo.
    """
    no_color = kw.get('no_color', False)
    series = d if isinstance(d, list) else [d]

    pw = w * 2 - 4
    ph = h * 4 - 4
    cx0, cy0 = 2, 0

    all_y = [v for s in series for v in s['y']]
    if not all_y:
        return
    y_range = max(all_y) - min(all_y)
    y_min = min(all_y) - y_range * 0.05
    y_max = max(all_y) + y_range * 0.05

    canvas = _HiresCanvas(w, h)

    for idx, s in enumerate(series):
        rgb = tuple(s['color']) if 'color' in s else _HIRES_PALETTE[idx % len(_HIRES_PALETTE)]
        dim = tuple(max(0, c // 5) for c in rgb)
        do_glow = s.get('glow', True) and not no_color
        ys = s['y']
        xs = s.get('x', list(range(len(ys))))
        pts = _catmull_pixels(ys, xs, cx0, cy0, pw, ph, y_min, y_max)
        if do_glow:
            for ox in (-1, 0, 1):
                for oy in (-1, 0, 1):
                    if ox == 0 and oy == 0:
                        continue
                    for px, py in pts:
                        canvas.dot(px + ox, py + oy, dim)
        for px, py in pts:
            canvas.dot(px, py, rgb)

    if title:
        print(title)
    for row in canvas.render(no_color):
        print(row)
