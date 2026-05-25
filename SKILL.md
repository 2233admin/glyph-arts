---
name: glyph-arts
description: glyph-arts -- terminal-visible chart toolkit. All chart types directly in the CLI -- no files, no GUI. incplot-style auto plotting (JSON/JSONL/CSV/TSV inference), plotext (kline/candlestick/line/scatter/step/bar/multibar/stackedbar/hist/heatmap/box/indicator/event/confusion/plotext overlays), SDR spectrum/waterfall, Diagon-style diagram (math/sequence/tree/table/frame/flowchart/GraphDAG/GraphPlanar), Mermaid/beautiful-mermaid-style diagrams, rich (table/tree/panel/gauge/pie/dashboard/rich_live), drawille/textplots Braille (curve/hires/radar/textplot/turtle), plotille (composable braille Figure), uniplot scientific line, media image via Pillow chat-safe ASCII or chafa truecolor, terminal host profiles for Windows Terminal/Preview/Canary and Warp, WaveTerm adapter via `wave doctor/view/render`, video via ffmpeg+chafa, backend doctor/install helpers for chafa/ffmpeg/Graphviz/Diagon/Nerd Fonts/Symbols Nerd Font/terminal probes, ASCII network graph, chat effect presets, sparkline, pyfiglet banner, composable art text, cursor-home animate for line/bar/scatter/sparkline, asciinema record/replay export via record and record-replay. LTTB-aware downsampling via --sample. Textual TUI dashboard via scripts/dashboard.py.
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

Chat drawing front door:

```bash
python $SKILL/scripts/chart.py chat image --file photo.jpg --width 80 --height 30
python $SKILL/scripts/chart.py chat photo.jpg --image-style retro-art
python $SKILL/scripts/chart.py chat incplot --json 'name,value\nA,3\nB,7'
python $SKILL/scripts/chart.py chat sdr spectrum --json '{"freq":[99.0,99.3],"power":[-93,-42]}'
python $SKILL/scripts/chart.py chat sequence --json 'Client->Server: GET /health'
python $SKILL/scripts/chart.py chat mermaid --json 'graph LR\nA[开始] --> B[完成]'
python $SKILL/scripts/chart.py chat diagram note --json 'NOTE\nCache refresh required'
python $SKILL/scripts/chart.py chat textplot --json '{"expr":"sin(x) / x","xmin":-20,"xmax":20}'
python $SKILL/scripts/chart.py chat turtle --json '{"commands":[["forward",30],["right",90],["forward",20]]}'
python $SKILL/scripts/chart.py chat graph --json 'Client -> API\nAPI -> DB'
python $SKILL/scripts/chart.py chat effects
```

`chat image` implies `--chat`; chart commands imply `--no-color`.

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
|   +-- Unknown JSON/CSV/TSV shape     -> incplot
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
|   +-- RF spectrum trace             -> spectrum
|   +-- RF waterfall history          -> waterfall
|
+-- Structure / diagram text
|   +-- Formula / sequence / tree     -> diagram (Diagon backend when installed)
|   +-- Flowchart / DAG / planar graph -> diagram
|
+-- Continuous curve / function       -> drawille curve / textplot / turtle
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
+-- Draw in the chat transcript        -> chat image|bar|line|spectrum|waterfall ...
+-- Status line shell command         -> sparkline/indicator/gauge --statusline
+-- Clickable terminal reference      -> --link-title URL or --link-data URL
+-- Match current Claude ANSI theme   -> --theme claude-dark-ansi or claude-light-ansi
+-- Match subagent color names        -> --theme subagent-rainbow
+-- Render table as markdown          -> table --output result.md
+-- Fullscreen TUI requested          -> dashboard/rich_live only when the user accepts TUI behavior
```

---

## Chart Types Reference

### Engine: incplot (1 type)
| Type | Input | Notes |
|------|-------|-------|
| `incplot` | raw JSON, JSONL, CSV, TSV | Auto-detects sparkline, bar, multibar, line, scatter, hist, table, and OHLC candlestick payloads. Use `--prefer` to override. |

### Engine: plotext (15 types)
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
| `plotext` | `{"series":[{"type":"error","x":[],"y":[],"yerr":[]}],"texts":[],"vlines":[],"hlines":[],"shapes":[]}` | plotext overlay API: error bars, date plots, labels, lines, rectangles, polygons |

### Engine: SDR (2 types)
| Type | JSON keys | Notes |
|------|-----------|-------|
| `spectrum` | `{"freq":[], "power":[], "center":99.3, "bandwidth":0.2}` | chat-safe RF spectrum with center line, band edges, peak marker |
| `waterfall` | `{"matrix":[[]], "xlabels":[], "ylabels":[], "min":-94, "max":-42}` | dense ASCII intensity map for terminal/chat panes |

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

### Engine: diagram (1 type)
| Type | Input | Notes |
|------|-------|-------|
| `diagram` | `diagram sequence --json 'A->B: msg'` or `{"kind":"flowchart","text":"A -> B"}` | Uses Diagon binary when installed for math/sequence/tree/table/frame/flowchart/GraphDAG/GraphPlanar. Builtin chat-safe fallback covers sequence/tree/table/frame/note/flowchart/graphdag. `chat sequence ...` aliases to `chat diagram sequence ...` |

### Engine: drawille / textplots Braille (3 types)
| Type | JSON keys |
|------|-----------|
| `curve` | `{"points":[[x,y],...]}` -- Braille Unicode, highest resolution |
| `textplot` | `{"expr":"sin(x) / x","xmin":-20,"xmax":20}` -- textplots-rs-style continuous function plot |
| `turtle` | `{"commands":[["forward",30],["right",90],["forward",20]]}` -- drawille-style Turtle/Canvas path drawing |

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

### Engine: media (Pillow/chafa + ffmpeg) -- 2 types
Charts use a native Python engine. Image can render through Pillow as
plain chat-safe text, or through `chafa` for 24-bit truecolor terminal
rendering. Video needs `ffmpeg` plus `chafa`. These types take a
filesystem path via `--file`, not JSON data.

| Type | Input | Notes |
|------|-------|-------|
| `image` | `--file path/to.png` | PNG/JPEG/GIF/BMP/WebP via Pillow or chafa. Size via `--width`/`--height`. `--chat` emits plain ASCII for Claude/Codex chat panes and auto-crops/suppresses flat backgrounds. `--image-style classic/braille/block/edge/dot-cross/halftone/particles/retro-art/terminal` mirrors the ascii-art skill styles. `--color-mode grayscale/original/matrix/amber/custom`, `--custom-color`, `--background`, `--ratio`, `--dither`, and `.txt/.md/.html/.svg/.png/.gif/.tsx` exports are supported. `--image-mode raw/detail/edge/silhouette` controls the Pillow preprocessing; `--no-trim` keeps the full frame. `--media-engine pillow --symbols half` emits ANSI half-block color; `--media-engine chafa --symbols braille` uses chafa |
| `video` | `--file path/to.mp4` | ffmpeg extracts frames to tempdir then chafa renders each. `--fps N` (default 12) paces playback. `--duration SEC` clips (else plays to EOF). Ctrl-C exits cleanly, cursor restored |

Rationale for chart/media split: the native `curve` renderer connects
every consecutive point-pair via Bresenham, which fills silhouettes into
blobs when fed pixel data. chafa is purpose-built and superset of
timg/viu on Windows. HANDOFF 2026-04-14 records the full architectural
decision.

### Misc (4 types)
| Type | JSON keys |
|------|-----------|
| `graph` | `{"edges":[["A","B"]],"directed":true,"node_style":"ROUND"}` or edge-list/DOT/GraphML text | PHART backend. Use `chat graph --json 'A -> B\nB -> C'`, `--graph-format dot`, `--graph-style round`, `--graph-charset ascii` |
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
| sdr spectrum/waterfall | 5,000 points / 500 rows | resampled to terminal width/height |
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
- Use `chat graph` for network topology, DAGs, dependency maps, and DOT/GraphML
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
| spectrum | col0=frequency, col1=power |
| waterfall | matrix-shaped values only; prefer JSON/file input |
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
