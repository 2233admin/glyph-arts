"""curve chart -- extracted from cli_charts.cmd._helpers (Phase 2)."""

import sys

from cli_charts.charts._utils import _canvas_line


def curve(d, title, w, h, theme, **kw):
    """drawille braille pixel canvas -- connected high-res curves.
    Points are auto-scaled to fit --width x --height.
    Uses Bresenham's line between consecutive points for smooth output.
    """
    import drawille
    points = d['points']
    if not points:
        print('(no points)', file=sys.stderr)
        return
    xs = [p[0] for p in points]
    ys = [p[1] for p in points]
    min_x, max_x = min(xs), max(xs)
    min_y, max_y = min(ys), max(ys)
    # drawille: 2 pixels wide x 4 pixels tall per terminal cell
    canvas_w = max(1, w * 2 - 1)
    canvas_h = max(1, h * 4 - 1)

    def scale(v, lo, hi, size):
        return size // 2 if hi == lo else round((v - lo) / (hi - lo) * size)

    if title:
        print(title)
    c = drawille.Canvas()
    if len(points) == 1:
        c.set(scale(points[0][0], min_x, max_x, canvas_w),
              canvas_h - scale(points[0][1], min_y, max_y, canvas_h))
    else:
        for i in range(len(points) - 1):
            x1 = scale(points[i][0],     min_x, max_x, canvas_w)
            y1 = canvas_h - scale(points[i][1],     min_y, max_y, canvas_h)
            x2 = scale(points[i + 1][0], min_x, max_x, canvas_w)
            y2 = canvas_h - scale(points[i + 1][1], min_y, max_y, canvas_h)
            _canvas_line(c, x1, y1, x2, y2)
    print(c.frame())
