---
name: glyph-arts
description: glyph-arts -- terminal-visible chart toolkit. All chart types directly in the CLI -- no files, no GUI. plotext (kline/candlestick/line/scatter/step/bar/multibar/stackedbar/hist/heatmap/box/indicator/event/confusion), sdr (spectrum/waterfall), rich (table/tree/panel/gauge/pie/dashboard/rich_live), drawille (curve/hires/radar), plotille (composable braille Figure), uniplot scientific line, media image/video (via chafa+ffmpeg, 2x4 braille sub-pixel with 24-bit truecolor), ASCII network graph, sparkline, pyfiglet banner, composable art text, cursor-home animate for line/bar/scatter/sparkline, asciinema record/replay export via record and record-replay. LTTB-aware downsampling via --sample. Textual TUI dashboard via scripts/dashboard.py.
version: 3.0.1
---

# Glyph Arts Skill

## Vision

When AI lives in the terminal, visualization must live there too.
No browser. No generated files. No context switch.
glyph-arts gives the AI a native sense of sight inside the terminal.

## Invocation

```bash
SKILL=~/.claude/skills/glyph-arts
python $SKILL/scripts/chart.py <type> [--json '<data>'] [--file path.json] \
  [--duckdb 'SQL'] [--db PATH] \
  [--title 'T'] [--width N] [--height 20] [--theme pro] \
  [--sample N] [--xlabel X] [--ylabel Y] \
  [--xlim MIN MAX] [--ylim MIN MAX] \
  [--xscale linear|log] [--yscale linear|log] \
  [--orientation vertical|horizontal] [--output FILE] [--no-color] \
  [--link-data URL] [--link-title URL] [--statusline]

python $SKILL/scripts/chart.py animate <line|bar|scatter|sparkline> \
  --duration SEC --frames N --json '<data>'

python $SKILL/scripts/chart.py record demo.cast --cmd 'glyph-arts art DEMO' --duration 10
python $SKILL/scripts/chart.py record-replay demo.cast --output demo.gif

python $SKILL/scripts/chart.py to-hyperframes \
  --json '[{"label":"x","x":[1,2,3,4,5],"y":[10,20,15,30,25]}]' \
  --frames 30 --duration 5 --output-dir ./hf-demo
```

**stdin pipe (for large data):**
```bash
echo '<json>' | python $SKILL/scripts/chart.py <type>
cat data.json  | python $SKILL/scripts/chart.py line
```

**file input:**
```bash
python $SKILL/scripts/chart.py bar --file path/to/data.json
```

**check dependencies:**
```bash
python $SKILL/scripts/chart.py --check-deps
```

Width defaults to terminal width (`$COLUMNS`). Override with `--width 120`.

---

## Decision Tree -- Which Chart to Use

```
What is your data shape?
|
+-- Time series / sequence
|   +-- Trend over time              -> plotext line
|   +-- Volume/count per period      -> plotext bar
|   +-- OHLC financial data          -> plotext kline
|   +-- Sparse scientific signal     -> uniplot
|
+-- Distribution / proportion
|   +-- Parts of a whole (<12 slices) -> rich pie
|   +-- Frequency distribution        -> plotext hist
|   +-- Two variables correlated      -> plotext scatter
|
+-- Comparison across categories
|   +-- Side-by-side bars             -> plotext bar (grouped -> multibar)
|   +-- Ranked list with scores       -> rich table
|   +-- Performance gauge (0-100)     -> rich gauge
|
+-- Hierarchy / tree structure        -> rich tree
|
+-- Density / matrix
|   +-- 2D correlation matrix         -> plotext heatmap
|
+-- Continuous curve (hi-res)         -> drawille curve
|
+-- Multiple metrics at once          -> rich dashboard
|
+-- Inline sparkline (1 row)          -> sparkline
|   +-- Claude Code statusLine        -> sparkline --statusline
|
+-- Progressive reveal in terminal    -> animate line/bar/scatter/sparkline
|
+-- MP4/WebM/high-quality video       -> to-hyperframes, then npx hyperframes render
|
+-- Network / graph topology          -> graph
|
+-- Large ASCII label / banner        -> banner
|
+-- Styled text art / framed wordmark -> art
```

## Claude Code CLI Compatibility

Trigger keywords:

- `Claude Code statusline`, `statusLine.command`, `single-line metric` -> use `sparkline`, `indicator`, or `gauge` with `--statusline`.
- `OSC 8`, `terminal hyperlink`, `clickable title` -> add `--link-title URL`; for line/scatter series labels add `--link-data URL`.
- `Claude theme`, `dark-ansi`, `light-ansi`, `~/.claude/themes` -> use `--theme claude-dark-ansi` or `--theme claude-light-ansi`.
- `subagent colors`, `agent rainbow`, `red blue green yellow purple orange pink cyan` -> use `--theme subagent-rainbow` for multi-series charts.
- `markdown table`, `GFM`, `Claude markdown render` -> use `table --output table.md`.

Claude decision tree:

```
Need output inside Claude Code?
|
+-- Status line shell command         -> sparkline/indicator/gauge --statusline
+-- Clickable terminal reference      -> --link-title URL or --link-data URL
+-- Match current Claude ANSI theme   -> --theme claude-dark-ansi or claude-light-ansi
+-- Match subagent color names        -> --theme subagent-rainbow
+-- Render table as markdown          -> table --output result.md
+-- Fullscreen TUI requested          -> dashboard/rich_live only when the user accepts TUI behavior
```

---

## Chart Types Reference

### Engine: plotext
| Type | JSON keys | Notes |
|------|-----------|-------|
| `kline` | `dates[], open[], high[], low[], close[]` | dates must be DD/MM/YYYY |
| `candlestick` | same as kline | alias for kline |
| `line` | `[{"label":"A","x":[...],"y":[...]}]` | multi-series supported |
| `scatter` | `[{"label":"A","x":[...],"y":[...]}]` | |
| `step` | `[{"label":"A","x":[...],"y":[...]}]` | staircase; x-point duplication |
| `bar` | `{"labels":[], "values":[]}` | use --orientation horizontal |
| `multibar` | `{"labels":[], "series":[{"label":"A","values":[]}]}` | grouped bars |
| `stackedbar` | `{"labels":[], "series":[{"label":"A","values":[]}]}` | |
| `hist` | `{"values":[], "bins":20}` | |
| `heatmap` | `{"matrix":[[]], "xlabels":[], "ylabels":[]}` | needs pandas |
| `box` | `{"data":[[s1],[s2]], "labels":["A","B"]}` | |
| `indicator` | `{"value":23.4, "label":"Return %"}` | big KPI number |
| `event` | `{"data":[x1,x2,...]}` | timeline plot |
| `confusion` | `{"actual":[], "predicted":[], "labels":[]}` | ML confusion matrix |

### Engine: sdr
| Type | JSON keys | Notes |
|------|-----------|-------|
| `spectrum` | `{"freq":[...], "db":[...], "avg":[...], "max_hold":[...], "noise_floor":-88, "squelch":-60, "center":99.5, "bandwidth":0.2, "vfo":99.55, "signals":[...]}` | FFT spectrum with live/avg/hold traces, center/span, VFO/marker, threshold, and peak overlays; JSON/JSONL/CSV/TSV |
| `waterfall` | `{"matrix":[[...]], "freq":[...], "time":[...], "center":99.5, "vfos":[...]}` | spectrogram rows over time; maps dB to ANSI/ASCII intensity and overlays tuning cursors |

### Engine: rich (7 types)
| Type | JSON keys |
|------|-----------|
| `table` | `{"columns":[], "rows":[[]]}` |
| `tree` | `{"label":"root","children":[{"label":"A","children":[]}]}` |
| `panel` | `{"content":"text","title":"optional","box":"ROUNDED"}` |
| `gauge` | `[{"label":"CPU","value":72,"max":100,"color":"green"}]` |
| `pie` | `{"labels":["A","B","C"],"values":[30,50,20]}` |
| `dashboard` | `{"panels":[{"type":"gauge","data":{...},"title":"CPU"},...]}` — delegates to scripts/dashboard.py |
| `rich_live` | `{"panels":[{"type":"sparkline","data":{...},"title":"Left"},...],"layout":"row","frames":1}` — multi-panel Rich Layout, `layout:"row"` or `"column"`, `frames:1` for pipe-safe snapshot |

### Engine: drawille (1 type)
| Type | JSON keys |
|------|-----------|
| `curve` | `{"points":[[x,y],...]}` -- Braille Unicode, highest resolution |

### Engine: hires (1 type) — 24-bit Braille
| Type | JSON keys | Notes |
|------|-----------|-------|
| `hires` | `[{"label":"A","y":[...],"x":[...],"color":[r,g,b],"glow":true}]` | Catmull-Rom smooth curves, per-dot 24-bit RGB, glow halos |

### Engine: radar (1 type) — Polar Braille
| Type | JSON keys | Notes |
|------|-----------|-------|
| `radar` | `{"labels":[...],"series":[{"label":"A","values":[...],"color":[r,g,b]}],"max":100}` | Spider/radar chart, min 3 axes |

### Engine: plotille (1 type)
| Type | JSON keys | Notes |
|------|-----------|-------|
| `plotille` | `[{"label":"A","x":[...],"y":[...],"color":"bright_cyan"}]` | Composable braille Figure with axis labels |

### Engine: uniplot (1 type)
| Type | JSON keys |
|------|-----------|
| `uniplot` | `[{"label":"A","x":[...],"y":[...]}]` -- scientific axis formatting |

### Engine: textcharts (9 types)
Zero-dependency, 15 chart types with ANSI colors. Install: `pip install "glyph-arts[textcharts]"` or `pip install textcharts`.

| Type | JSON keys | Notes |
|------|-----------|-------|
| `comparison` | `{"data":[{"label":"A","baseline":85,"comparison":89.5}]}` | A/B comparison bars with % change |
| `diverging` | `{"data":[{"label":"A","pct_change":25}]}` | positive/negative diverging bars |
| `summary` | `{"stats":{"cpu":73.5,"memory":58.2}}` | key statistics summary box |
| `sparkline-table` | `{"columns":[],"values":{}}` | table with inline sparklines |
| `cdf` | `{"series":[{"name":"A","values":[...]}]}` | cumulative distribution function |
| `rank` | `{"items":[{"label":"A","value":89}]}` or `{"values":{"A":89}}` | sorted ranking table (Rich) |
| `percentile` | `{"data":[{"name":"A","p50":50,"p90":90}]}` | percentile ladder |
| `boxplot` | `{"series":[{"name":"A","values":[...]}]}` | statistical box plots |
| `stacked-text` | `{"data":[{"label":"A","segments":[{"label":"X","value":30}]}]}` | stacked composition bars |

### Engine: media (chafa + ffmpeg) -- 2 types
Charts use a native Python engine. Media (image/video) shells out to
`chafa` (pre-installed via `scoop install chafa` on Windows, distro
package elsewhere) for 24-bit truecolor braille rendering. Video also
needs `ffmpeg`. These types take a filesystem path via `--file`, not
JSON data.

| Type | Input | Notes |
|------|-------|-------|
| `image` | `--file path/to.png` | any format chafa accepts (PNG/JPEG/GIF/BMP/WebP/SVG). Size via `--width`/`--height`. `--symbols SET` picks chafa symbol set (default `braille`; also `block`, `ascii`, `half`, `all`). `--fit subject` trims background before rendering portraits/objects. `--filter anime` sharpens line art for dense chat output. `--filter ink` inverts white-page formulas/scans/documents so dark terminal backgrounds show ink instead of paper. `--preset terminal` fits the current terminal pane, and `--cols N` overrides the detected width. `--preset chat/chat-hd/chat-max/chat-4k` applies fixed pipelines at 72x36, 96x48, 120x60, or 132x66. `--no-color` forces monochrome |
| `video` | `--file path/to.mp4` | ffmpeg extracts frames to tempdir then chafa renders each. `--fps N` (default 12) paces playback. `--duration SEC` clips (else plays to EOF). Ctrl-C exits cleanly, cursor restored |

Use `glyph-arts chat calibrate` to print ASCII and braille rulers that measure
the active chat window width before selecting `chat-hd`, `chat-max`, or `chat-4k`.
Use `glyph-arts chat calibrate --terminal` when the output target is the current
terminal; it reads the terminal column count directly. On Windows Terminal,
ConPTY usually reports columns correctly when attached; if a runner reports 80,
use `--cols N` or set `GLYPH_ARTS_COLS=N`.
For 4K panes, run `glyph-arts chat calibrate --calibrate-from 160 --calibrate-to
240 --calibrate-step 8 --calibrate-glyph braille --recommend`.

#### Agent operating rules for terminal image previews

When the user asks to "draw", "show in chat", "preview this image", "render this
material", or similar, and the target surface is a terminal conversation such as
Warp, Windows Terminal, Claude Code, or Codex CLI:

1. Prefer the terminal-fit path, not fixed chat presets:
   `glyph-arts image --file IMAGE --preset terminal`.
2. If the command runs inside an agent runner and reports a fake 80-column
   terminal, ask for or infer the pane width, then use
   `glyph-arts image --file IMAGE --preset terminal --cols N`.
3. On Windows/PowerShell, the equivalent persistent override is
   `$env:GLYPH_ARTS_COLS="N"` followed by
   `glyph-arts image --file IMAGE --preset terminal`.
4. Use fixed presets only when the user explicitly wants a portable size:
   `chat` for narrow inline output, `chat-hd` for medium, `chat-max` for wide,
   `chat-4k` for known 4K panes.
5. Do not hand-assemble `--fit subject --filter anime --symbols braille
   --no-color`; `--preset terminal` already applies that tuned pipeline.
6. For white-page formulas, scans, screenshots, and documents, add
   `--filter ink` to the terminal preset:
   `glyph-arts image --file FORMULA.png --preset terminal --filter ink`.
7. If formula source text is available, do not rasterize it. Use
   `glyph-arts chat formula` and pipe LaTeX-ish/plain formula text; raster
   formula rendering is only a screenshot fallback.
   For fractions, integrals, matrices, and algebra that need real terminal
   layout, use `glyph-arts chat formula-pretty` (SymPy pretty printer).
8. To discover a terminal pane limit, run
   `glyph-arts chat calibrate --terminal --calibrate-glyph braille --recommend`;
   if captured output says 80 but the pane is visibly wider, use `--cols N` or
   `GLYPH_ARTS_COLS=N`.

Rationale for chart/media split: the native `curve` renderer connects
every consecutive point-pair via Bresenham, which fills silhouettes into
blobs when fed pixel data. chafa is purpose-built and superset of
timg/viu on Windows. HANDOFF 2026-04-14 records the full architectural
decision.

### Misc (4 types)
| Type | JSON keys |
|------|-----------|
| `graph` | `{"edges":[["A","B"]],"directed":true,"node_style":"ROUND"}` |
| `sparkline` | `{"values":[1,3,5,2,8]}` -- single-row inline |
| `banner` | `{"text":"PROFIT","font":"big","color":"green"}` |
| `art` | positional text: `art SHIP IT --font slant --decor barcode --frame double --gradient sunset` |
| `animate` | `animate line --duration 5 --frames 30 --json '[{"label":"A","x":[...],"y":[...]}]'` |
| `record` | `record demo.cast --cmd 'glyph-arts art DEMO' --duration 10` |
| `record-replay` | `record-replay demo.cast --output demo.gif` -- `.gif` via agg, `.svg` via svg-term, `.html` snippet, `.cast` passthrough |
| `to-hyperframes` | `to-hyperframes --json '[{"label":"A","x":[...],"y":[...]}]' --frames 30 --duration 5 --output-dir ./hf` -- writes PNG frame sequence, `manifest.json`, and `composition.html`; requires HyperFrames installed separately with `npx hyperframes init` |

Trigger keywords for `art`: wordmark, figlet, framed text, gradient text,
decorated ASCII, composable text art.

Trigger keywords for `animate`: animation, animated chart, progressive reveal,
terminal playback, cursor-home redraw.

Trigger keywords for `record`: record terminal, asciinema, cast file,
terminal recording, replay export, gif export, svg export.

Trigger keywords for `to-hyperframes`: 视频, video, mp4, webm, 动画, motion,
GSAP, launch, demo, hyperframes.

Video output decision tree:
- User wants GIF + short demo -> use `glyph-arts record` + `glyph-arts record-replay`
- User wants MP4 + high quality video -> use `glyph-arts to-hyperframes` + `npx hyperframes render`
- User wants embed README -> use `record-replay --output .gif` because GIF auto-plays in GitHub README
- User wants embed blog HTML -> use `record-replay --output .svg` for vector scaling

---

## Output Contract

**Success:** exit code `0`, chart rendered to stdout.

**Failure modes:**
| Condition | Exit code | Stderr format |
|-----------|-----------|---------------|
| Invalid JSON | `1` | `ERROR:json: <message>` |
| Missing required key | `1` | `ERROR:schema: <message>` |
| Unknown chart type | `1` | argparse error |
| Missing dependency | `2` | `ERROR:dep: pip install <package>` |
| Render failed | `4` | `ERROR:render: <traceback_last_line>` |

**AI parsing rule:** always check exit code first. If non-zero, read stderr for structured error tag.

---

## Size & Performance Limits

| Engine | Recommended max data points | Hard limit |
|--------|----------------------------|------------|
| plotext | 10,000 | 50,000 |
| rich table | 500 rows | 2,000 rows |
| drawille | 50,000 | 200,000 |
| uniplot | 100,000 | -- |

**Over limit?** Use `--file` + `--sample <n>` to auto-downsample.

---

## AI Usage Rules

### DO
- Use `sparkline` for a single inline metric in the middle of analysis
- Use `dashboard` when presenting 3+ related metrics simultaneously
- Use `--file` or stdin pipe when data exceeds 200 characters in JSON string form
- Use `drawille curve` when signal continuity matters (audio, sensor, physics)
- Use `rich table` when the user needs to read exact values
- Use `--sample N` to downsample large datasets before rendering

### DO NOT
- Do not pass more than 500 rows via `--json` inline -- use `--file` instead
- Do not use `plotext heatmap` for data with more than 20x20 cells
- Do not use `rich pie` with more than 12 slices -- switch to `bar`
- Do not call `banner` except for final result banners or section headers
- Do not generate a chart without a `--title` when presenting analysis results

---

## Examples

**Time series:**
```bash
python $SKILL/scripts/chart.py line \
  --json '[{"label":"DAU","x":[1,2,3,4,5],"y":[100,120,115,130,125]}]' \
  --title "Daily Active Users"
```

**Multi-series:**
```bash
python $SKILL/scripts/chart.py line \
  --json '[{"label":"Revenue","y":[100,120,90,140]},{"label":"Cost","y":[80,95,75,110]}]' \
  --title "P&L Trend"
```

**Pie chart:**
```bash
python $SKILL/scripts/chart.py pie \
  --json '{"labels":["Equity","Bond","Cash"],"values":[60,30,10]}' \
  --title "Asset Allocation"
```

**Dashboard (3 panels):**
```bash
python $SKILL/scripts/chart.py dashboard \
  --json '{
    "panels": [
      {"type":"gauge","data":[{"label":"CPU","value":73,"max":100}],"title":"CPU"},
      {"type":"sparkline","data":{"values":[1,3,5,2,8,4,6]},"title":"Load"},
      {"type":"table","data":{"columns":["Host","Status"],"rows":[["web-01","OK"],["db-01","WARN"]]},"title":"Services"}
    ]
  }' \
  --title "System Health"
```

**Large file:**
```bash
python $SKILL/scripts/chart.py scatter \
  --file ./data/million_points.json \
  --sample 5000 \
  --title "Correlation"
```

**From pipe:**
```bash
cat metrics.json | python $SKILL/scripts/chart.py bar --title "Benchmark Results"
```

**K-line from DuckDB:**
```bash
python $SKILL/scripts/chart.py kline \
  --title "600519 K-line" --width 80 --height 24 \
  --duckdb "SELECT trade_date,open,high,low,close FROM stock_daily WHERE ts_code='600519.SH' ORDER BY trade_date DESC LIMIT 30" \
  --db /path/to/data.duckdb
```

---

## Anti-patterns (don't do these)

```bash
# BAD: inline 10000-row JSON will crash the shell
python $SKILL/scripts/chart.py line --json '[...10000 items...]'
# GOOD:
python $SKILL/scripts/chart.py line --file data.json

# BAD: pie chart with 20 slices is unreadable
python $SKILL/scripts/chart.py pie --json '{"labels":["A","B",...20 items...],"values":[...]}'
# GOOD: switch to bar for many categories
python $SKILL/scripts/chart.py bar --json '{"labels":[...],"values":[...]}' --orientation horizontal

# BAD: no title in analysis context
python $SKILL/scripts/chart.py bar --json '{"labels":["Q1","Q2"],"values":[10,12]}'
# GOOD:
python $SKILL/scripts/chart.py bar --json '{"labels":["Q1","Q2"],"values":[10,12]}' --title "Q1 vs Q2 Revenue"
```

---

## Dependencies

```bash
pip install plotext rich drawille uniplot pyfiglet sparklines duckdb pandas networkx phart
# optional: LTTB shape-preserving downsampling (--sample for line/scatter/step/uniplot)
pip install lttb
# optional: Textual TUI dashboard (scripts/dashboard.py)
pip install textual
```

Auto-install check:
```bash
python $SKILL/scripts/chart.py --check-deps
# prints OK or lists missing packages
```

---

## DuckDB Integration

| Chart type | Column mapping |
|-----------|----------------|
| kline / candlestick | col0=date, open/high/low/close by name |
| line / scatter / step / uniplot | col0=x, col1..N=y series |
| bar / pie | col0=labels, col1=values |
| table | all columns as-is |
| hist | all columns as value series |
| heatmap | matrix from .values, col names as xlabels |
| curve | col0=x, col1=y |
| sparkline | col0 values |
| confusion | col0=actual, col1=predicted |
| graph | col0=src, col1=dst (edge list) |

---

## Textual TUI Dashboard

`scripts/dashboard.py` — standalone multi-panel dashboard (separate from `chart.py`).

```bash
python $SKILL/scripts/dashboard.py --demo                        # interactive Textual TUI
python $SKILL/scripts/dashboard.py --demo --no-interactive       # Rich static fallback (pipe-safe)
python $SKILL/scripts/dashboard.py --file config.json           # load panel config from file
python $SKILL/scripts/dashboard.py --json '{"panels":[...]}'    # inline JSON

# Panel types: gauge | sparkline | table | metric | bar
# Layout: auto-grid (<=4 panels -> 2col, >4 -> 3col) or manual via panel["row"]
# Live refresh: add "refresh_interval": 5 (seconds) to config
# Bindings: q=quit, r=refresh
```

Falls back to Rich static output if `textual` is not installed or stdout is not a tty.

---

## Integration Notes

- **Pipe-friendly**: all output is pure stdout, errors go to stderr only. Safe to pipe.
- **Session logging**: set `CLI_CHARTS_LOG=1` to append render history to `.chart_history.jsonl`.
- **NO_COLOR**: respects `NO_COLOR` env var (https://no-color.org) and `--no-color` flag.
- **LTTB sampling**: `--sample N` uses Largest-Triangle-Three-Buckets for line/scatter/step/uniplot (shape-preserving), OHLC group aggregation for kline, uniform stride fallback when `lttb` not installed.
