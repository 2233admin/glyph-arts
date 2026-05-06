# glyph-arts

> When AI lives in the terminal, visualization must live there too.

All chart types rendered natively in the terminal -- no browser, no generated files, no context switch.
`pip install glyph-arts` and your AI agent has a native sense of sight inside the CLI.

![demo](demo/chartex-demo.gif)

---

## Install

```bash
pip install glyph-arts

# with LTTB downsampling (recommended for time-series):
pip install "glyph-arts[lttb]"

# with Textual TUI dashboard:
pip install "glyph-arts[tui]"

# everything:
pip install "glyph-arts[all]"
```

## System dependencies (image / video charts only)

The `image` and `video` chart types shell out to `chafa` and `ffmpeg`.
Install them once before using those types:

| OS | Command |
|---|---|
| Windows | `scoop install chafa ffmpeg` or `choco install chafa ffmpeg` |
| macOS | `brew install chafa ffmpeg` |
| Linux (Debian/Ubuntu) | `apt install chafa ffmpeg` |
| Linux (Homebrew) | `brew install chafa ffmpeg` |

All other chart types are pure-Python and work after `pip install glyph-arts` alone.

## Art tiers (--engine pixel)

The pixel engine renders charts via matplotlib + chafa. The chafa
output character set controls visual fidelity:

| Tier | Flag | Symbol set | Resolution | Font requirement |
|---|---|---|---|---|
| Low | `--art low` | block | 1x1 px/char | Universal (any terminal) |
| Default | `--art default` | vhalf | 1x2 px/char | Universal (Block element) |
| High | `--art high` | sextant | 2x3 px/char | Needs Symbols-for-Legacy-Computing font (Cascadia Code OK) |

Default is `--art default` -- btop-like aesthetic, broad terminal compat.

![art tiers](docs/art-tiers.png)

## Output formats

`--output PATH` chooses the export format from the file suffix:

| Suffix | Engine | Result |
|---|---|---|
| `.png` | `--engine pixel` | Existing matplotlib PNG file output |
| `.txt` | default ASCII | Rendered chart text with ANSI escapes stripped |
| `.ansi` | default ASCII | Rendered chart text with ANSI escapes preserved |
| `.html` | default ASCII | `<pre>` snippet with ANSI foreground colors converted to inline spans |

```bash
glyph-arts bar --json '{"labels":["A","B"],"values":[1,2]}' --output chart.txt
glyph-arts bar --json '{"labels":["A","B"],"values":[1,2]}' --output chart.ansi
glyph-arts bar --json '{"labels":["A","B"],"values":[1,2]}' --output chart.html
glyph-arts bar --engine pixel --json '{"labels":["A","B"],"values":[1,2]}' --output chart.png
```

## Animation

`animate` redraws an ASCII chart in-place using a cursor-home loop. MVP support:
`line`, `bar`, `scatter`, and `sparkline`.

```bash
glyph-arts animate line --duration 5 --frames 30 \
  --json '[{"label":"DAU","x":[1,2,3,4,5,6,7,8,9,10],"y":[100,120,115,130,125,140,135,150,145,160]}]'
```

Ctrl-C exits cleanly and leaves the complete final chart on screen.

## Art command (Phase 2)

The `art` command renders composable terminal text art: figlet font,
optional art-lib decoration, optional Rich frame, and optional ANSI gradient.
Install the opt-in extra first:

```bash
pip install "glyph-arts[art]"

glyph-arts art SHIP IT --font slant --decor barcode --frame double --gradient sunset
glyph-arts art GLYPH-ARTS --font big --frame rounded --gradient viridis --no-color
```

Use `--output PATH` to write the rendered text to a file. `--no-color` strips
ANSI color and ignores gradients.

## Quick start

```bash
# bar chart
glyph-arts bar --json '{"labels":["Q1","Q2","Q3"],"values":[10,14,12]}' --title "Revenue"

# time series
glyph-arts line \
  --json '[{"label":"DAU","x":[1,2,3,4,5],"y":[100,120,115,130,125]}]' \
  --title "Daily Active Users"

# pie chart
glyph-arts pie \
  --json '{"labels":["Equity","Bond","Cash"],"values":[60,30,10]}' \
  --title "Asset Allocation"

# python -m also works:
python -m cli_charts bar --json '{"labels":["A","B"],"values":[3,7]}'

# check core dependencies:
glyph-arts --check-deps
# include optional extras (braille/lttb/tui):
glyph-arts --check-deps --all
```

## Chart types

| Engine | Types |
|--------|-------|
| plotext | `kline` `candlestick` `line` `scatter` `step` `bar` `multibar` `stackedbar` `hist` `heatmap` `box` `indicator` `event` `confusion` |
| rich | `table` `tree` `panel` `gauge` `pie` `dashboard` `rich_live` |
| drawille *(optional `[braille]`)* | `curve` `hires` `radar` |
| plotille | `plotille` |
| uniplot | `uniplot` |
| misc | `graph` `sparkline` `banner` `art` `animate` |
| media *(requires chafa + ffmpeg)* | `image` `video` |

Total: **33 types**. See `CHART_TYPE_COUNT` in `cli_charts/chart.py` for the authoritative count.

## All flags

```
glyph-arts <type> [--json JSON | --file PATH | --duckdb SQL --db PATH]
                  [--title TEXT] [--width N] [--height N] [--theme THEME]
                  [--sample N] [--xlabel X] [--ylabel Y]
                  [--xlim MIN MAX] [--ylim MIN MAX]
                  [--xscale linear|log] [--yscale linear|log]
                  [--orientation vertical|horizontal]
                  [--output FILE] [--no-color]
```

**Width** defaults to `$COLUMNS` (terminal width). Override with `--width 120`.

**`--sample N`** uses LTTB (Largest-Triangle-Three-Buckets) downsampling — shape-preserving, not random stride. Falls back to uniform stride if `lttb` not installed.

## Pipe / file input

```bash
# stdin pipe (for large data)
cat metrics.json | glyph-arts bar --title "Benchmark"

# file (use with --sample for large datasets)
glyph-arts scatter --file ./data/million_points.json --sample 5000 --title "Correlation"
```

## DuckDB integration

```bash
glyph-arts kline \
  --duckdb "SELECT trade_date,open,high,low,close FROM stock_daily WHERE ts_code='600519.SH' ORDER BY trade_date DESC LIMIT 60" \
  --db /path/to/data.duckdb \
  --title "Kweichow Moutai K-line"
```

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

## Dashboard

```bash
# interactive Textual TUI:
python -m cli_charts.dashboard --demo

# Rich static (pipe-safe, no textual required):
python -m cli_charts.dashboard --demo --no-interactive

# custom panels:
glyph-arts dashboard --json '{
  "panels": [
    {"type":"gauge","data":[{"label":"CPU","value":73,"max":100}],"title":"CPU"},
    {"type":"sparkline","data":{"values":[1,3,5,2,8,4,6]},"title":"Load"},
    {"type":"table","data":{"columns":["Host","Status"],"rows":[["web-01","OK"]]},"title":"Services"}
  ]
}' --title "System Health"
```

## Exit codes

| Code | Meaning |
|------|---------|
| 0 | Success |
| 1 | Bad input (JSON parse error or missing key) — `ERROR:json:` / `ERROR:schema:` on stderr |
| 2 | Missing dependency — `ERROR:dep: pip install <pkg>` on stderr |
| 4 | Render failed — `ERROR:render: <traceback last line>` on stderr |

## For Claude Code / AI agents

See [SKILL.md](SKILL.md) for the full AI usage contract: decision tree, schema reference, DO/DO NOT rules, and anti-patterns.

```bash
# Claude Code skill (no pip required — uses scripts/ shims):
SKILL=~/.claude/skills/glyph-arts
python $SKILL/scripts/chart.py bar \
  --json '{"labels":["A","B","C"],"values":[3,7,5]}' \
  --title "Example"
```

## Environment variables

| Variable | Effect |
|----------|--------|
| `CLI_CHARTS_LOG=1` | Append render history to `.chart_history.jsonl` |
| `NO_COLOR` | Disable ANSI colors (https://no-color.org) |

## License

MIT
