# glyph-arts -- Theme Reference

`--theme <name>` applies a colour palette to any plotext-based chart type
(bar, line, scatter, step, multibar, stackedbar, hist, heatmap, box, event,
indicator, confusion, kline).  Ignored for rich/graph/sparkline/image/video.

---

## Quick Start

```bash
python scripts/chart.py bar \
  --json '{"labels":["A","B","C"],"values":[10,20,15]}' \
  --theme claude --title "My Chart"
```

Run the gallery to see all themes side by side:

```bash
python docs/themes/generate_gallery.py          # all themes, bar+line
python docs/themes/generate_gallery.py --theme vercel --chart line
```

---

## Built-in plotext Themes

These pass straight through to `plt.theme()`:

| Name | Description |
|------|-------------|
| `pro` | Default -- dark background, colourful series |
| `dark` | Near-black background |
| `clear` | White background, minimal |
| `matrix` | Green-on-black hacker style |
| `retro` | Warm amber CRT look |
| `elegant` | Muted teal tones |

---

## Brand Palette Themes

Custom 24-bit RGB palettes modelled on real design systems.

### `--theme claude`

Anthropic / Claude -- warm terracotta against near-black.

| Role | Hex | RGB |
|------|-----|-----|
| Canvas (background) | `#0F0D0B` | (15, 13, 11) |
| Axes frame | `#28231E` | (40, 35, 30) |
| Tick labels / title | `#DCD2C3` | (220, 210, 195) |
| Series 1 -- coral | `#CC7860` | (204, 120, 92) |
| Series 2 -- amber | `#DEAA5A` | (222, 170, 90) |
| Series 3 -- sage | `#91B98C` | (145, 185, 140) |
| Series 4 -- sky | `#60A0C3` | (96, 160, 195) |

Base: plotext `dark`

---

### `--theme linear`

Linear -- void-black background, indigo accent.

| Role | Hex | RGB |
|------|-----|-----|
| Canvas (background) | `#0D0D13` | (13, 13, 19) |
| Axes frame | `#1E1E2D` | (30, 30, 45) |
| Tick labels / title | `#C2C5D7` | (194, 197, 215) |
| Series 1 -- indigo | `#5E6AD2` | (94, 106, 210) |
| Series 2 -- violet | `#8250DC` | (130, 80, 220) |
| Series 3 -- teal | `#32B9B9` | (50, 185, 185) |
| Series 4 -- sky | `#4BA0E6` | (75, 160, 230) |

Base: plotext `dark`

---

### `--theme tesla`

Tesla -- deep navy, signature red primary.

| Role | Hex | RGB |
|------|-----|-----|
| Canvas (background) | `#171A20` | (23, 26, 32) |
| Axes frame | `#2D323C` | (45, 50, 60) |
| Tick labels / title | `#D2D7DE` | (210, 215, 222) |
| Series 1 -- red | `#E82127` | (232, 33, 39) |
| Series 2 -- platinum | `#C8D2DC` | (200, 210, 220) |
| Series 3 -- blue | `#4191D7` | (65, 145, 215) |
| Series 4 -- green | `#32C382` | (50, 195, 130) |

Base: plotext `dark`

---

### `--theme vercel`

Vercel -- pure black canvas, electric blue accent, high contrast.

| Role | Hex | RGB |
|------|-----|-----|
| Canvas (background) | `#000000` | (0, 0, 0) |
| Axes frame | `#232323` | (35, 35, 35) |
| Tick labels / title | `#EAEAEA` | (234, 234, 234) |
| Series 1 -- blue | `#0070F3` | (0, 112, 243) |
| Series 2 -- white | `#FFFFFF` | (255, 255, 255) |
| Series 3 -- cyan | `#00DCDC` | (0, 220, 220) |
| Series 4 -- pink | `#F03C78` | (240, 60, 120) |

Base: plotext `clear` (overridden to black)

---

## Adding a Custom Theme

1. Create `cli_charts/themes/<name>.py` with a `PALETTE` dict:

```python
PALETTE = {
    "canvas":   (R, G, B),
    "axes":     (R, G, B),
    "ticks":    (R, G, B),
    "series":   [(R1,G1,B1), (R2,G2,B2), ...],  # at least 6
    "plt_base": "dark",   # or "clear", "pro", None
}
```

2. Register it in `cli_charts/themes/__init__.py`:

```python
from .<name> import PALETTE as _NAME
CUSTOM_THEMES["<name>"] = _NAME
```

3. Use it: `--theme <name>`
