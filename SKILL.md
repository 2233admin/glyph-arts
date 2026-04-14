---
name: cli-charts
description: cli-ARTS — terminal-visible chart toolkit. 27 chart types directly in the CLI — no files, no GUI. plotext (kline/line/scatter/step/bar/multibar/stackedbar/hist/heatmap/box/indicator/event/confusion), rich (table/tree/panel/gauge/pie/dashboard), hires (24-bit braille Catmull-Rom+glow), radar (polar spider chart), plotille (composable braille Figure), drawille braille curve, uniplot scientific line, ASCII network graph, sparkline, pyfiglet banner. LTTB-aware downsampling via --sample. Textual TUI dashboard via scripts/dashboard.py.
version: 3.0.0
---

# CLI Charts Skill

## Vision

When AI lives in the terminal, visualization must live there too.
No browser. No generated files. No context switch.
cli-ARTS gives the AI a native sense of sight inside the terminal.

## Invocation

```bash
SKILL=~/.claude/skills/cli-charts
python $SKILL/scripts/chart.py <type> [--json '<data>'] [--file path.json] \
  [--duckdb 'SQL'] [--db PATH] \
  [--title 'T'] [--width N] [--height 20] [--theme pro] \
  [--sample N] [--xlabel X] [--ylabel Y] \
  [--xlim MIN MAX] [--ylim MIN MAX] \
  [--xscale linear|log] [--yscale linear|log] \
  [--orientation vertical|horizontal] [--output FILE] [--no-color]
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
|
+-- Network / graph topology          -> graph
|
+-- Large ASCII label / banner        -> banner
```

---

## Chart Types Reference

### Engine: plotext (13 types)
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

### Engine: rich (6 types)
| Type | JSON keys |
|------|-----------|
| `table` | `{"columns":[], "rows":[[]]}` |
| `tree` | `{"label":"root","children":[{"label":"A","children":[]}]}` |
| `panel` | `{"content":"text","title":"optional","box":"ROUNDED"}` |
| `gauge` | `[{"label":"CPU","value":72,"max":100,"color":"green"}]` |
| `pie` | `{"labels":["A","B","C"],"values":[30,50,20]}` |
| `dashboard` | `{"panels":[{"type":"gauge","data":{...},"title":"CPU"},...]}` — delegates to scripts/dashboard.py |

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

### Misc (3 types)
| Type | JSON keys |
|------|-----------|
| `graph` | `{"edges":[["A","B"]],"directed":true,"node_style":"ROUND"}` |
| `sparkline` | `{"values":[1,3,5,2,8]}` -- single-row inline |
| `banner` | `{"text":"PROFIT","font":"big","color":"green"}` |

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
