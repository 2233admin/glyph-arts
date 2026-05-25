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

Then run the backend doctor. It checks the system pieces that Python wheels
cannot reliably provide: `chafa`, `Graphviz`, `Diagon`, `ffmpeg`, Nerd Font
coverage, Symbols Nerd Font coverage, and the current terminal host profile.

```bash
glyph-arts doctor

# print the chat-quality backend pack:
glyph-arts install-backends --target chat

# execute the plan explicitly:
glyph-arts install-backends --target chat --run --yes
```

## See it in action

```bash
echo '[3,7,4,9,6,12]' | glyph-arts auto
glyph-arts chat image --file photo.jpg --width 80 --height 30
glyph-arts chat incplot --json 'name,value\nA,3\nB,7'
glyph-arts chat sdr spectrum --json '{"freq":[99.0,99.3,99.6],"power":[-93,-42,-93],"center":99.3,"bandwidth":0.2}'
glyph-arts chat sequence --json 'Client->Server: GET /health'
glyph-arts chat mermaid --json 'graph LR\nA[开始] --> B[完成]'
glyph-arts chat diagram note --json 'NOTE\nCache refresh required before reading results.'
glyph-arts chat graph --json 'Client -> API\nAPI -> DB'
glyph-arts chat plotext --json '{"series":[{"type":"error","x":[1,2,3],"y":[2,5,3],"yerr":[0.3,0.8,0.4],"label":"err"}],"texts":[{"text":"peak","x":2,"y":5}],"vlines":[2]}'
glyph-arts chat textplot --json '{"expr":"sin(x) / x","xmin":-20,"xmax":20}'
glyph-arts chat turtle --json '{"commands":[["forward",30],["right",90],["forward",20]]}'
glyph-arts chat effects
glyph-arts live random
glyph-arts dashboard --demo --no-interactive
glyph-arts bar --json '{"labels":["A","B"],"values":[3,7]}'
glyph-arts spectrum --json '{"freq":[99.0,99.3,99.6],"power":[-93,-42,-93],"center":99.3,"bandwidth":0.2}'
```

![demo](docs/demo.gif)
<!-- TODO: record actual demo.gif via asciinema/agg, see
     docs/recording-demo.md (P13). -->

## Image / Video Dependencies

The `image` chart type has a built-in Pillow text renderer for AI chat panes
and Markdown code blocks:

```bash
glyph-arts chat image --file photo.jpg --width 80 --height 30
glyph-arts chat photo.jpg --image-style retro-art --width 80 --height 30
glyph-arts image --file photo.jpg --chat --width 80 --height 30
glyph-arts image --file photo.jpg --chat --image-style braille --width 80 --height 30
glyph-arts image --file photo.jpg --chat --image-style retro-art --dither atkinson --width 80 --height 30
glyph-arts image --file photo.jpg --media-engine pillow --symbols half --width 80 --height 30
glyph-arts image --file photo.jpg --chat --image-mode silhouette --width 80 --height 30
glyph-arts image --file photo.jpg --image-style terminal --color-mode matrix --output art.html
```

Install `chafa` for higher-fidelity terminal image rendering. `video` still
requires both `ffmpeg` and `chafa`, but the chat-quality install target keeps
video/recording tools out of the first path. `glyph-arts doctor` detects the
current state, and `glyph-arts install-backends` prints an install plan:

| OS | Command |
|---|---|
| Windows | `scoop install chafa graphviz JetBrainsMono-NF NerdFontsSymbolsOnly` |
| macOS | `brew install chafa graphviz` plus Nerd Font casks |
| Linux (Debian/Ubuntu) | `apt install chafa graphviz` |
| Linux (Arch) | `pacman -S chafa graphviz ttf-jetbrains-mono-nerd ttf-nerd-fonts-symbols` |

For glyph-heavy terminal output, install a Nerd Font such as JetBrainsMono Nerd
Font and select it in the terminal. This covers Powerline/PUA icons, Braille,
block elements, and dense terminal glyphs. Also install Symbols Nerd Font as a
fallback for private-use icons. `install-backends --target fonts` uses Scoop on
Windows or Homebrew on macOS when available.

`glyph-arts doctor` also reports a first-class terminal profile. The profile
decides how `chafa` is invoked and what symbol tier is safe:

| Profile | Detection / override | Image path |
|---|---|---|
| Windows Terminal | `WT_SESSION` or `GLYPH_ARTS_TERMINAL_PROFILE=windows-terminal` | truecolor symbols/blocks |
| Windows Terminal Preview/Canary | `GLYPH_ARTS_TERMINAL_PROFILE=windows-terminal-preview` or `windows-terminal-canary` | Sixel via `chafa --format sixels` |
| Warp | `TERM_PROGRAM=WarpTerminal` or `GLYPH_ARTS_TERMINAL_PROFILE=warp` | truecolor symbols/blocks |

Use the explicit profile override when the terminal does not expose enough
environment detail, especially for Windows Terminal Preview.

If you run `bash` inside WSL from Warp, treat it as two layers: host profile
`warp`, runtime `wsl`, shell `bash`. Install `chafa`, Graphviz, and Diagon in
WSL, but configure Nerd Fonts in Warp. In that case `install-backends` uses the
Linux-side package context instead of Windows Scoop/Chocolatey. If a Windows
process inherits WSL environment variables through interop, force the intended
runtime with `GLYPH_ARTS_RUNTIME=wsl` or `GLYPH_ARTS_RUNTIME=windows`.

All non-video chart types are pure-Python and work after `pip install glyph-arts` alone.

## Developer Workflow

The project uses `uv` for Python dependency locking and `Nx` as a thin CI task
runner:

```bash
uv sync --extra all --extra test --extra dev
npm ci
npx nx run glyph-arts:test
npx nx run glyph-arts:lint
npx nx run glyph-arts:docs-check
```

Nx targets call `uv run ...`; Python dependencies still live in
`pyproject.toml` and `uv.lock`.

## Diagrams / Diagon

`diagram` brings Diagon-style structure drawings into the same chat drawing
surface:

```bash
glyph-arts chat sequence --json 'Client->Server: GET /health'
glyph-arts chat diagram flowchart --json 'Capture -> Render -> Reply'
glyph-arts chat diagram note --json 'NOTE\nCache refresh required before reading results.'
glyph-arts diagram math --diagram-engine diagon --json '1/2 + sqrt(x)'
glyph-arts chat diagram graphplanar --json 'A -- B\nB -- C\nC -- D\nD -- A'
```

## Mermaid / Beautiful Mermaid

`mermaid` restores the beautiful-mermaid-style contract inside the same chat
surface: Mermaid source in, chat-visible ASCII/Unicode diagram out.

```bash
glyph-arts chat mermaid --json 'graph LR\nA[开始] -->|是| B{判断}\nB --> C[完成]'
glyph-arts mermaid --mermaid-ascii --json 'sequenceDiagram\nAlice->>Bob: Hello'
glyph-arts mermaid --mermaid-theme tokyo-night --mermaid-padding-x 8 --json 'stateDiagram-v2\nIdle --> Running: start'
glyph-arts chat mermaid --json 'xychart-beta horizontal\nx-axis [Python, Rust, Go]\nbar [30, 22, 18]\nline [28, 24, 16]'
```

The builtin fallback handles `graph`/`flowchart`, `sequenceDiagram`,
`stateDiagram-v2`, `classDiagram`, `erDiagram`, and `xychart-beta`, with
Unicode/ASCII output, display-width-safe Chinese labels, theme names compatible
with the beautiful-mermaid convention, and spacing controls. `xychart-beta`
supports rounded columns, horizontal bars, line overlays, legends, named series,
and CJK-safe labels.

When the `diagon` binary is installed, `--diagram-engine auto` delegates to
Diagon for `math`, `sequence`, `tree`, `table`, `frame`, `flowchart`,
`graphdag`, and `graphplanar`. Without Diagon, glyph-arts keeps a small
chat-safe builtin fallback for `sequence`, `tree`, `table`, `frame`,
`math`, `note`, `flowchart`, `graphdag`, and `graphplanar`.
`glyph-arts doctor` reports both `graphviz` (`dot`) and `diagon`, while
`install-backends --target diagrams` installs Graphviz where a package-manager
path is known and prints the Diagon upstream install note when it is optional.

For network graphs, `graph` uses PHART and accepts JSON edges, simple edge-list
text, DOT, and GraphML:

```bash
glyph-arts chat graph --json 'Client -> API\nAPI -> DB'
glyph-arts chat graph --graph-format dot --json 'digraph { Client -> API; API -> DB; }'
glyph-arts graph --json '{"edges":[["Client","API"],["API","DB"]]}'
```

For plotext-specific power features, `plotext` exposes the upstream overlay API
inside the chat-safe CLI surface: error bars, date-time series, candlesticks,
histograms, text annotations, vertical/horizontal guide lines, rectangles,
polygons, and colorized strings. Video/audio/YouTube streaming remains outside
the chat contract.

```bash
glyph-arts chat plotext --json '{"series":[{"type":"line","x":[1,2,3],"y":[2,5,3],"label":"signal"},{"type":"error","x":[1,2,3],"y":[2,5,3],"yerr":[0.3,0.8,0.4],"label":"err"}],"texts":[{"text":"peak","x":2,"y":5}],"vlines":[2],"hlines":[4],"shapes":[{"type":"rectangle","x":[1.5,2.5],"y":[2.5,5.5],"lines":true}]}'
glyph-arts chat plotext --json '{"colorize":"OK","color":"green","style":"bold"}'
```

For incplot-style input, `incplot` is the automatic plotting door for raw
JSON, JSONL, CSV, and TSV. It infers category bars, grouped bars, temporal
lines, numeric scatter, histograms, tables, and OHLC candlesticks:

```bash
cat data.csv | glyph-arts chat incplot
glyph-arts chat incplot --json '{"x":1,"y":2}\n{"x":2,"y":5}\n{"x":3,"y":3}'
glyph-arts chat incplot --prefer line --json 'x,y\n1,2\n2,5\n3,3'
```

For textplots-rs and drawille-style Braille drawing, use `textplot` for
continuous function plots and `turtle` for path/canvas commands:

```bash
glyph-arts chat textplot --json '{"expr":"sin(x) / x","xmin":-20,"xmax":20}'
glyph-arts chat turtle --json '{"commands":[["forward",30],["right",90],["forward",20],["right",90],["forward",30]]}'
```

For other agents, the installable skill package is
[`skills/chat-drawing`](skills/chat-drawing). The short transferable instruction
packet is [`docs/agent_chat_drawing_skill.md`](docs/agent_chat_drawing_skill.md),
with a machine-readable capability map at
[`docs/chat_drawing_capabilities.json`](docs/chat_drawing_capabilities.json).

## Chat Effects

`effect` is the preset layer for richer chat drawings. It composes the lower
level chart, diagram, graph, SDR, and density-map renderers into reusable visual
recipes:

```bash
glyph-arts chat effects
glyph-arts effect pipeline --json '{"steps":["Input","Route","Render","Verify","Reply"]}'
glyph-arts effect metrics
glyph-arts effect system-map
glyph-arts effect signal-panel
glyph-arts effect timeline
glyph-arts effect matrix
glyph-arts effect comparison
glyph-arts effect swimlane
glyph-arts effect kanban
glyph-arts effect quadrant
glyph-arts effect mindmap
```

Use `chat effects` when the user asks "what can you draw?" or when a plain chart
is technically correct but visually too thin.

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
| `.md` | `table` | GitHub-Flavored Markdown table |

```bash
glyph-arts bar --json '{"labels":["A","B"],"values":[1,2]}' --output chart.txt
glyph-arts bar --json '{"labels":["A","B"],"values":[1,2]}' --output chart.ansi
glyph-arts bar --json '{"labels":["A","B"],"values":[1,2]}' --output chart.html
glyph-arts bar --engine pixel --json '{"labels":["A","B"],"values":[1,2]}' --output chart.png
glyph-arts table --json '{"columns":["A","B"],"rows":[["x","1"]]}' --output table.md
```

## Claude Code CLI compatible

glyph-arts includes Claude Code terminal compatibility flags for statuslines,
themes, hyperlinks, and markdown rendering:

```bash
glyph-arts sparkline --json '[1,2,3,4,5,6,7,8,9,10]' --statusline
glyph-arts line --theme claude-dark-ansi --json '[{"label":"X","x":[1,2,3],"y":[10,20,15]}]'
glyph-arts line --title Docs --link-title https://docs.anthropic.com --json '[{"label":"X","y":[1,2,3]}]'
glyph-arts scatter --link-data https://example.com/point --json '[{"label":"A","x":[1,2],"y":[3,4]}]'
glyph-arts line --theme subagent-rainbow --json '[{"label":"A","y":[1,2]},{"label":"B","y":[2,1]}]'
```

- `--theme claude-dark-ansi` and `--theme claude-light-ansi` read
  `~/.claude/themes/{dark,light}-ansi.json` when present, with a 16-color ANSI
  fallback.
- `--theme subagent-rainbow` uses the Claude Code subagent named colors:
  red, blue, green, yellow, purple, orange, pink, cyan.
- `--statusline` on `sparkline`, `indicator`, and `gauge` emits one line,
  capped at 80 chars, suitable for `~/.claude/settings.json` `statusLine.command`.
- `--link-title` and `--link-data` opt into OSC 8 hyperlinks. If the terminal
  capability is not detected, output falls back to `label (url)`.
- `table --output *.md` writes a GFM table for Claude Code markdown rendering.

## Animation

`animate` redraws an ASCII chart in-place using a cursor-home loop. MVP support:
`line`, `bar`, `scatter`, and `sparkline`.

```bash
glyph-arts animate line --duration 5 --frames 30 \
  --json '[{"label":"DAU","x":[1,2,3,4,5,6,7,8,9,10],"y":[100,120,115,130,125,140,135,150,145,160]}]'
```

Ctrl-C exits cleanly and leaves the complete final chart on screen.

## Live Demo

`live` renders a sliding-window line chart with no system-monitoring dependency:

```bash
glyph-arts live random --duration 10 --interval 0.2
seq 1 100 | glyph-arts live stdin --interval 0.1
```

Real `cpu`, `mem`, and `ping` sources are future work.

## WaveTerm Adapter

`wave` keeps ordinary chat output as plain text, but adds a WaveTerm-native
preview path when `wsh` is available:

```bash
glyph-arts wave doctor
glyph-arts wave view --file chart.html
glyph-arts wave render bar --json '{"labels":["A","B"],"values":[3,7]}'
glyph-arts wave render diagram sequence --json 'A->B: hello' --wave-format html
```

`wave render` exports the selected chart to `.html`, `.txt`, or `.ansi`, then
opens it with `wsh view` so WaveTerm can show it as a rich block. Add
`--dry-run` to print the planned chart and `wsh` commands without running them.

## Recording

`record` and `record-replay` wrap optional system tools for terminal session
capture and replay export. Install only the tools for the formats you need:

| Tool | Used for | Windows install |
|---|---|---|
| `asciinema` | `.cast` recording | `scoop install asciinema` or `choco install asciinema` or `pip install asciinema` |
| `agg` | `.cast` to `.gif` | `scoop install agg` or `cargo install --git https://github.com/asciinema/agg` |
| `svg-term` | `.cast` to `.svg` | `npm install -g svg-term-cli` |

```bash
glyph-arts record demo.cast --cmd 'glyph-arts art "DEMO" --gradient sunset' --duration 10
glyph-arts record-replay demo.cast --output demo.gif
glyph-arts record-replay demo.cast --output demo.svg
glyph-arts record-replay demo.cast --output demo.html
glyph-arts record-replay demo.cast --output demo.cast
```

Missing tools fail with `ERROR:dep:` and an OS-specific install hint.

## HyperFrames Integration

`to-hyperframes` generates a progressive line-chart PNG sequence plus
`manifest.json` and `composition.html` for HyperFrames. HyperFrames is not a
Python dependency; install and render it separately:

```bash
npx hyperframes init

glyph-arts to-hyperframes \
  --json '[{"label":"x","x":[1,2,3,4,5],"y":[10,20,15,30,25]}]' \
  --frames 30 \
  --duration 5 \
  --output-dir ./hf-demo

# Then render with HyperFrames, for example:
npx hyperframes render ./hf-demo/composition.html
```

The output directory contains `frame_001.png` through `frame_NNN.png`,
`manifest.json`, and `composition.html`. Each frame reveals a larger slice of
the input series.

## Phase 8: ASCII Motion integration

glyph-arts can use ascii-motion-mcp as a stdio MCP backend to polish rendered ASCII charts with palette remapping and levels, then export animated output formats such as HTML, MP4, GIF, React, and SVG while also saving an editable `.asciimtn` project. Install both sides first:

```bash
pip install "glyph-arts[ai-motion]"
npm i -g ascii-motion-mcp

glyph-arts bar --json '{"labels":["A","B"],"values":[1,2]}' --polish ascii-motion --polish-style retro --output chart.html
glyph-arts to-ascii-motion bar --json '{"labels":["A","B"],"values":[1,2]}' --formats html,mp4,svg --output-dir ./out
```

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
| incplot | `incplot` |
| plotext | `kline` `candlestick` `line` `scatter` `step` `bar` `multibar` `stackedbar` `hist` `heatmap` `box` `indicator` `event` `confusion` `plotext` |
| sdr | `spectrum` `waterfall` |
| rich | `table` `tree` `panel` `gauge` `pie` `dashboard` `rich_live` |
| diagram | `diagram` `mermaid` |
| drawille / braille | `curve` `hires` `radar` `textplot` `turtle` |
| plotille | `plotille` |
| uniplot | `uniplot` |
| misc | `graph` `effect` `sparkline` `banner` `art` `animate` `record` `record-replay` `to-hyperframes` `to-ascii-motion` `code` `status` `splash` `demo` `gallery` `auto` `live` `doctor` `install-backends` `wave` |
| media *(image uses Pillow/chafa; video requires chafa + ffmpeg)* | `image` `video` |

Total: **56 types**. See `CHART_TYPE_COUNT` in `cli_charts/chart.py` for the authoritative count.

For the chat-vs-ANSI-vs-artifact boundary, see
[`docs/capability_matrix.md`](docs/capability_matrix.md).

## All flags

```
glyph-arts <type> [--json JSON | --file PATH | --duckdb SQL --db PATH]
                  [--title TEXT] [--width N] [--height N] [--theme THEME]
                  [--sample N] [--xlabel X] [--ylabel Y]
                  [--xlim MIN MAX] [--ylim MIN MAX]
                  [--xscale linear|log] [--yscale linear|log]
                  [--orientation vertical|horizontal]
                  [--output FILE] [--no-color] [--chat]
```

**Width** defaults to `$COLUMNS` (terminal width). Override with `--width 120`.

**`--chat`** forces plain text output for AI chat panes. For `image`, it uses
the Pillow ASCII renderer so the result survives Markdown code blocks. The
default image path auto-crops the foreground, suppresses flat backgrounds, and
boosts contrast/edges. Use `--image-mode raw` to get the old whole-image
luminance path, `--image-mode edge` for outlines, `--image-mode silhouette` for
a readable subject mask, or `--no-trim` to keep the full frame.

`image` also includes the ascii-art skill style set:
`classic`, `braille`, `block`, `edge`, `dot-cross`, `halftone`, `particles`,
`retro-art`, and `terminal`. Pair them with
`--color-mode grayscale|original|matrix|amber|custom`, `--custom-color coral`,
`--background dark|light|transparent`, `--ratio original|16:9|4:3|1:1|3:4|9:16`,
`--dither none|floyd-steinberg|bayer|atkinson`, and static exports via
`.txt`, `.md`, `.html`, `.svg`, `.png`, `.gif`, or `.tsx`.

**`chat` mode** is the short front door for chat drawing. It rewrites to the
plain-text-safe command:

```bash
glyph-arts chat image --file photo.jpg
glyph-arts chat photo.jpg
glyph-arts chat sequence --json 'Alice->Bob: Hello'
glyph-arts chat mermaid --json 'graph LR\nA[开始] --> B[完成]'
glyph-arts chat graph --json 'A -> B\nB -> C'
glyph-arts chat incplot --json 'x,y\n1,2\n2,5\n3,3'
glyph-arts chat textplot --json '{"expr":"sin(x)"}'
glyph-arts chat turtle --json '{"commands":[["forward",30],["right",90],["forward",20]]}'
glyph-arts chat effects
glyph-arts chat sdr spectrum --json '{"freq":[99.0,99.3],"power":[-93,-42]}'
glyph-arts chat waterfall --json '{"matrix":[[-94,-42],[-90,-50]]}'
```

`chat image` implies `--chat`; chart commands imply `--no-color`.

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
| spectrum | frequency/power series via `freq`/`power` or `x`/`y` |
| waterfall | matrix rows plus optional `xlabels`, `ylabels`, `min`, `max` |
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

For Codex/Claude/OpenCode-style agents that support local skills, copy or link
[`skills/chat-drawing`](skills/chat-drawing) into that agent's skills directory.
It contains the closed loop: choose a `glyph-arts chat ...` route, render to
stdout, verify with `scripts/verify_chat_art.py`, then reply with the visible
drawing. The portable cross-agent prompt is
[`references/agent-contract.md`](skills/chat-drawing/references/agent-contract.md);
route selection is in
[`references/decision-tree.md`](skills/chat-drawing/references/decision-tree.md),
with adapters under [`skills/chat-drawing/agents`](skills/chat-drawing/agents).

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
