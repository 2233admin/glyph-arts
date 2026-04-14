# glyph-arts

> When AI lives in the terminal, visualization must live there too.

29 chart types rendered directly in your terminal — no browser, no generated files, no context switch.
`pip install glyph-arts` and your AI agent has a native sense of sight inside the CLI.

```
demo.gif  <-- record with: python -m cli_charts.dashboard --demo --no-interactive
```

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

## Chart types (29)

| Engine | Types |
|--------|-------|
| plotext | `kline` `candlestick` `line` `scatter` `step` `bar` `multibar` `stackedbar` `hist` `heatmap` `box` `indicator` `event` `confusion` |
| rich | `table` `tree` `panel` `gauge` `pie` `dashboard` |
| drawille *(optional `[braille]`)* | `curve` |
| uniplot | `uniplot` |
| misc | `graph` `sparkline` `banner` |

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
