---
name: cli-charts
description: Terminal-visible chart toolkit for Claude Code. Renders 21 chart types directly in the CLI — no files, no GUI. Covers plotext (kline/line/scatter/bar/multibar/stackedbar/hist/heatmap/box/indicator/event/confusion), rich (table/tree/panel/gauge), drawille braille curve, uniplot scientific line, ASCII network graph, sparkline, and pyfiglet banner.
version: 2.1.0
---

# CLI Charts Skill

All charts render directly in the terminal via `python scripts/chart.py <type>`.

## Quick Reference

```bash
SKILL=~/.claude/skills/cli-charts
python $SKILL/scripts/chart.py <type> [--json '...'] [--duckdb 'SQL'] [--db PATH] \
  [--title 'T'] [--width 70] [--height 20] [--theme pro] \
  [--xlabel X] [--ylabel Y] [--xlim MIN MAX] [--ylim MIN MAX] \
  [--xscale linear|log] [--yscale linear|log] \
  [--orientation vertical|horizontal] [--output FILE] [--no-color]
```

Themes: `pro` (colored) | `dark` | `clear` | `matrix`

**21 chart types:**
- **plotext**: `kline` `line` `scatter` `bar` `multibar` `stackedbar` `hist` `heatmap` `box` `indicator` `event` `confusion`
- **rich**: `table` `tree` `panel` `gauge`
- **drawille**: `curve`
- **uniplot**: `uniplot`
- **misc**: `graph` `sparkline` `banner`

Note: `--width`, `--height`, `--theme` are ignored for `table`, `tree`, `panel`, `graph`, `sparkline`, `gauge`, `banner` (a warning is printed if you pass them with non-default values).

---

## K-Line (Candlestick)

OHLC bars with green (up) / red (down) color coding.

**CRITICAL**: dates must be `DD/MM/YYYY` — any other format raises ValueError.

```bash
python $SKILL/scripts/chart.py kline --title "茅台 30日K线" --width 80 --height 24 --json '{
  "dates":["07/04/2026","08/04/2026","09/04/2026"],
  "open": [100.0, 101.2,  99.8],
  "high": [102.5, 103.0, 101.5],
  "low":  [ 99.5, 100.8,  98.2],
  "close":[101.2,  99.8, 102.1]
}'

# DuckDB (auto-maps trade_date + open/high/low/close columns)
python $SKILL/scripts/chart.py kline --title "600519 K线" --width 80 --height 24 \
  --duckdb "SELECT trade_date,open,high,low,close FROM stock_daily WHERE ts_code='600519.SH' ORDER BY trade_date DESC LIMIT 30" \
  --db /path/to/data.duckdb
```

---

## Line Chart

Multi-series line chart. Each series needs `y`; `x` and `label` are optional.

```bash
# Single series
python $SKILL/scripts/chart.py line --title "收益率" \
  --json '{"label":"strategy","y":[1.0,1.05,1.03,1.08,1.12]}'

# Multi-series (pass array)
python $SKILL/scripts/chart.py line --json '[
  {"label":"策略","y":[1.0,1.05,1.03,1.08,1.12]},
  {"label":"基准","y":[1.0,1.02,1.01,1.03,1.04]}
]'

# Custom axes
python $SKILL/scripts/chart.py line --json '{"label":"loss","y":[1.2,0.9,0.7,0.5]}' \
  --xlabel "Epoch" --ylabel "Loss" --yscale log

# DuckDB — first col = x-axis, remaining cols = series
python $SKILL/scripts/chart.py line \
  --duckdb "SELECT trade_date, close FROM stock_daily WHERE ts_code='000001.SH' LIMIT 60" \
  --db /path/to/data.duckdb
```

---

## Scatter Plot

Same schema as line chart, uses dots instead of connected lines.

```bash
python $SKILL/scripts/chart.py scatter --title "因子散点" \
  --json '[{"label":"A","x":[1,2,3,4,5],"y":[2.1,1.8,3.2,2.7,4.0]},
           {"label":"B","x":[1,2,3,4,5],"y":[1.0,2.2,1.5,3.1,2.8]}]'
```

---

## Bar Chart

Vertical or horizontal bars for categorical comparisons.

```bash
python $SKILL/scripts/chart.py bar --title "因子得分" \
  --json '{"labels":["动量","价值","质量","低波"],"values":[0.8,0.6,0.9,0.4]}'

# Horizontal orientation
python $SKILL/scripts/chart.py bar --orientation horizontal \
  --json '{"labels":["A","B","C"],"values":[10,20,15]}'

# DuckDB — first col = labels, second col = values
python $SKILL/scripts/chart.py bar \
  --duckdb "SELECT industry, avg(close) FROM stock_daily GROUP BY industry LIMIT 10" \
  --db /path/to/data.duckdb
```

---

## Multi-Series Bar (Grouped)

Side-by-side grouped bars for comparing multiple series across categories.

```bash
python $SKILL/scripts/chart.py multibar --title "季度对比" \
  --json '{
    "labels": ["Q1","Q2","Q3","Q4"],
    "series": [
      {"label":"收入","values":[10,12,11,14]},
      {"label":"成本","values":[8,9,10,11]}
    ]
  }'

# Horizontal
python $SKILL/scripts/chart.py multibar --orientation horizontal \
  --json '{"labels":["A","B"],"series":[{"label":"X","values":[1,2]},{"label":"Y","values":[3,4]}]}'
```

---

## Stacked Bar

Stacked bars, same schema as multibar.

```bash
python $SKILL/scripts/chart.py stackedbar --title "成本构成" \
  --json '{
    "labels": ["1月","2月","3月"],
    "series": [
      {"label":"人力","values":[5,6,5]},
      {"label":"硬件","values":[3,3,4]},
      {"label":"其他","values":[2,1,2]}
    ]
  }'
```

---

## Histogram

Distribution of continuous values. Single or multi-series.

```bash
# Single
python $SKILL/scripts/chart.py hist --title "回报分布" \
  --json '{"values":[1,2,2,3,3,3,4,4,5,5,5,5],"bins":6}'

# Multi-series
python $SKILL/scripts/chart.py hist --json '[
  {"label":"策略A","values":[1,2,2,3,3,4],"bins":5},
  {"label":"策略B","values":[2,3,3,4,4,5],"bins":5}
]'

# DuckDB — each column becomes a series
python $SKILL/scripts/chart.py hist \
  --duckdb "SELECT returns_a, returns_b FROM backtest" \
  --db /path/to/data.duckdb
```

---

## Heatmap / Correlation Matrix

Requires `pandas` (already a standard quant dep). Color-mapped matrix.

```bash
python $SKILL/scripts/chart.py heatmap --title "相关矩阵" \
  --json '{
    "matrix": [[1.0,0.8,0.3],[0.8,1.0,0.5],[0.3,0.5,1.0]],
    "xlabels": ["动量","价值","质量"],
    "ylabels": ["动量","价值","质量"]
  }'

# DuckDB — full matrix as-is
python $SKILL/scripts/chart.py heatmap \
  --duckdb "SELECT * FROM correlation_matrix" \
  --db /path/to/data.duckdb
```

---

## Box Plot

Median/quartile/whisker display. Pass raw values per group; plotext computes stats.

```bash
python $SKILL/scripts/chart.py box --title "因子分布" \
  --json '{
    "data":   [[1,2,3,4,5,6],[3,4,5,6,7,8],[2,3,4,5,6]],
    "labels": ["动量","价值","质量"]
  }'

# Pre-computed quantiles [min, Q1, median, Q3, max]
python $SKILL/scripts/chart.py box --json '{
  "quintuples": [[1,2,3,4,5],[3,4,5,6,7]],
  "labels": ["A","B"]
}'
```

---

## Indicator (KPI Big Number)

Single large number display — great for dashboards.

```bash
python $SKILL/scripts/chart.py indicator \
  --json '{"value":23.4,"label":"Total Return %"}'

python $SKILL/scripts/chart.py indicator \
  --json '{"value":1.82,"label":"Sharpe Ratio"}'
```

---

## Event Plot (Timeline)

Vertical/horizontal markers for discrete events on a numeric axis.

```bash
# Vertical (default) — e.g., signal dates as numeric indices
python $SKILL/scripts/chart.py event --title "买入信号" \
  --json '{"data":[1,5,13,21,34]}'

# Horizontal
python $SKILL/scripts/chart.py event \
  --json '{"data":[1,5,13,21,34],"orientation":"horizontal"}'
```

---

## Sparkline

Compact unicode block line. One line output — ideal for inline metrics.

```bash
python $SKILL/scripts/chart.py sparkline --title "净值曲线" \
  --json '{"values":[1.0,1.02,1.05,0.98,1.10,1.08,1.15]}'

# DuckDB — single numeric column
python $SKILL/scripts/chart.py sparkline \
  --duckdb "SELECT close FROM stock_daily WHERE ts_code='000001.SH' ORDER BY trade_date LIMIT 40" \
  --db /path/to/data.duckdb
```

---

## Table

Rich double-edge formatted table. Good for dashboards and comparisons.

```bash
python $SKILL/scripts/chart.py table --title "持仓快照" --json '{
  "columns": [
    {"name":"股票","style":"yellow"},
    {"name":"持仓量","style":"cyan"},
    {"name":"涨跌%","style":"green"}
  ],
  "rows": [
    ["600519 茅台", "200", "+2.3%"],
    ["000858 五粮液","300", "-0.8%"]
  ],
  "caption": "截至 2026-04-14",
  "box": "DOUBLE_EDGE"
}'

# DuckDB — auto-maps all columns
python $SKILL/scripts/chart.py table \
  --duckdb "SELECT ts_code, close, pct_chg FROM stock_daily WHERE trade_date='2026-04-11' LIMIT 20" \
  --db /path/to/data.duckdb
```

Box styles: `DOUBLE_EDGE` (default) | `ROUNDED` | `SIMPLE` | `MINIMAL` | `SQUARE` | `MARKDOWN`

---

## Tree

Rich hierarchical tree. Great for model architecture, file trees, org charts.

```bash
python $SKILL/scripts/chart.py tree --json '{
  "label": "模型架构",
  "children": [
    {"label": "编码器", "children": [
      {"label": "Embedding"},
      {"label": "Attention", "style": "bold green"}
    ]},
    {"label": "解码器", "children": [
      {"label": "FFN"},
      {"label": "Output"}
    ]}
  ]
}'
```

---

## Panel

Rich bordered callout box. For status messages, alerts, summaries.

```bash
python $SKILL/scripts/chart.py panel --json '{
  "content": "部署已完成\n所有节点健康",
  "title":   "状态",
  "subtitle":"2026-04-14",
  "box":     "ROUNDED"
}'

# Box options: ROUNDED (default) | DOUBLE | SQUARE | HEAVY | MINIMAL
```

---

## Network Graph (ASCII)

PHART + NetworkX → ASCII directed/undirected graph.

```bash
python $SKILL/scripts/chart.py graph --json '{
  "edges": [["数据层","特征工程"],["特征工程","模型"],["模型","信号"],["信号","执行"]],
  "directed": true,
  "node_style": "ROUND"
}'
# node_style options: ROUND | SQUARE | MINIMAL | DIAMOND
# extra options: "node_spacing": 4, "layer_spacing": 2

# DuckDB — 2-col edge list
python $SKILL/scripts/chart.py graph \
  --duckdb "SELECT source, target FROM dependency_graph" \
  --db /path/to/data.duckdb
```

---

## Braille Curve

drawille canvas — 4×2 braille pixels per character cell, highest resolution.
Points are auto-scaled to fit `--width` × `--height`. Any coordinate range works.

```bash
# Sine wave
python $SKILL/scripts/chart.py curve --title "Sin Wave" --width 70 --height 15 \
  --json '{"points":[[0,0],[10,6],[20,10],[30,6],[40,0],[50,-6],[60,-10],[70,-6],[80,0]]}'

# Generate denser points inline for smooth curves
python -c "
import math, json, subprocess, sys
pts = [[x, math.sin(x * math.pi / 30) * 10] for x in range(120)]
subprocess.run([sys.executable, '$SKILL/scripts/chart.py', 'curve',
                '--title', 'Sin Wave', '--width', '70', '--height', '15',
                '--json', json.dumps({'points': pts})])
"

# DuckDB — 2-col table (x, y)
python $SKILL/scripts/chart.py curve \
  --duckdb "SELECT trade_date_idx, close FROM stock_daily WHERE ts_code='000001.SH' LIMIT 60" \
  --db /path/to/data.duckdb
```

---

## Confusion Matrix

ML confusion matrix via plotext — actual vs predicted, color-coded cells with percentages.

```bash
python $SKILL/scripts/chart.py confusion --title "分类结果" --width 80 --height 20 \
  --json '{"actual":[0,1,2,0,1,2],"predicted":[0,2,2,0,0,1],"labels":["Cat","Dog","Bird"]}'

# DuckDB — 2-col (actual, predicted)
python $SKILL/scripts/chart.py confusion \
  --duckdb "SELECT actual_label, predicted_label FROM model_results" \
  --db /path/to/data.duckdb
```

---

## Gauge (Progress Bars)

Rich multi-metric progress bars. Auto-colors green (<70%), yellow (<90%), red (>=90%).

```bash
python $SKILL/scripts/chart.py gauge --title "系统状态" \
  --json '[
    {"label":"CPU","value":72,"max":100},
    {"label":"RAM","value":14,"max":32},
    {"label":"GPU","value":95,"max":100,"color":"magenta"}
  ]'

# Single metric as object
python $SKILL/scripts/chart.py gauge \
  --json '{"metrics":[{"label":"胜率","value":63,"max":100}]}'
```

---

## Banner (ASCII Art Text)

pyfiglet large ASCII art text. Good for dashboard headers and alerts.

```bash
python $SKILL/scripts/chart.py banner --json '{"text":"PROFIT","font":"big"}'

# With color (rich markup)
python $SKILL/scripts/chart.py banner \
  --json '{"text":"ERROR","font":"banner3","color":"red"}'

# Available fonts (partial): big, banner, banner3, block, digital, doom, isometric1, larry3d, speed, standard, starwars, stop
python -c "import pyfiglet; print(pyfiglet.FigletFont.getFonts())"  # list all ~150 fonts
```

---

## Uniplot (Scientific Line/Scatter)

uniplot braille-pixel scientific charts with real axis labels. Same schema as `line`.
Prefer over `line` when axis precision matters; prefer `curve` for smooth math functions.

```bash
# Multi-series line
python $SKILL/scripts/chart.py uniplot --title "收益曲线" \
  --json '[{"label":"策略","y":[1.0,1.05,1.03,1.08,1.12]},
           {"label":"基准","y":[1.0,1.02,1.01,1.03,1.04]}]'

# Scatter mode (set "lines":false)
python $SKILL/scripts/chart.py uniplot \
  --json '[{"label":"因子","x":[1,2,3,4,5],"y":[2.1,1.8,3.2,2.7,4.0],"lines":false}]'

# With axis limits
python $SKILL/scripts/chart.py uniplot --ylim 0 2 --width 80 --height 20 \
  --json '{"label":"净值","y":[1.0,1.1,0.95,1.2,1.35]}'

# DuckDB — same mapping as line (col0=x, remaining=series)
python $SKILL/scripts/chart.py uniplot \
  --duckdb "SELECT trade_date_idx, close FROM stock_daily WHERE ts_code='000001.SH' LIMIT 60" \
  --db /path/to/data.duckdb
```

---

## DuckDB Integration

Always pass `--db /path/to/data.duckdb` with `--duckdb`. No default path.

Auto column mapping by chart type:

| Type | Expected SQL columns |
|------|---------------------|
| kline | col0=date, open, high, low, close |
| line / scatter | col0=x-axis, remaining cols=series |
| bar | col0=labels, col1=values |
| table | all columns as-is |
| hist | each column = one series |
| heatmap | full matrix (rows×cols) |
| curve | col0=x, col1=y |
| sparkline | col0=values |
| graph | col0=source, col1=target (edge list) |
| confusion | col0=actual, col1=predicted |
| uniplot | col0=x-axis, remaining cols=series |

---

## Flags Reference

| Flag | Applies to | Default |
|------|-----------|---------|
| `--title` | all | '' |
| `--width` | plotext + curve + uniplot | 70 |
| `--height` | plotext + curve + uniplot | 20 |
| `--theme` | plotext | pro |
| `--xlabel` | plotext | '' |
| `--ylabel` | plotext | '' |
| `--xlim MIN MAX` | plotext | auto |
| `--ylim MIN MAX` | plotext | auto |
| `--xscale linear\|log` | plotext | linear |
| `--yscale linear\|log` | plotext | linear |
| `--orientation vertical\|horizontal` | bar/multibar/stackedbar/event | vertical |
| `--output PATH` | plotext | (display) |
| `--no-color` | rich (table/tree/panel) | false |

---

## When to use

- User asks "画图"、"显示K线"、"出个图" → use cli-charts
- Quant data from warehouse → `--duckdb` with appropriate SQL
- Architecture/flow diagrams → use beautiful-mermaid instead
- Need SVG/PNG output → use beautiful-mermaid with `--format svg`
- Need highest resolution curve → use `curve` (braille, 4× more pixels than plotext)
- ML model evaluation → `confusion` for confusion matrix
- System/resource dashboards → `gauge` for multi-metric progress bars
- Dashboard section headers / alerts → `banner` (ASCII art, 150+ fonts)
- Scientific plots with precise axis labels → `uniplot` over `line`
