# Routing

Choose the command by what the user wants to see, not by which backend sounds fancy.

| Intent | Prefer |
|---|---|
| Photo, portrait, logo, screenshot | `glyph-arts chat image --file <path> --width 80 --height 32` |
| Cropped portrait ASCII | `glyph-arts chat image --file <path> --crop subject --width 72 --height 32` |
| Monochrome chat-safe image | `glyph-arts chat image --file <path> --mode ascii --no-color` |
| Colored terminal image | `glyph-arts chat image --file <path> --color ansi` |
| High-fidelity terminal image | `glyph-arts image --file <path> --media-engine chafa --chafa-format auto --chafa-symbols sextant` |
| Unknown JSON/JSONL/CSV/TSV data | `glyph-arts chat incplot < data.csv` |
| Bar, line, scatter, heatmap | `glyph-arts chat bar|line|scatter|heatmap --json <json-or-path>` |
| Error bars / guide lines / chart annotations | `glyph-arts chat plotext --json <plotext-overlay-json>` |
| Date-time / candlestick with plotext overlays | `glyph-arts chat plotext --json '{"series":[{"type":"candlestick",...}],"vlines":[...]}'` |
| Compact table | `glyph-arts chat table --json <json-or-path>` |
| Dashboard summary | `glyph-arts chat dashboard --json <json-or-path>` |
| Sequence diagram | `glyph-arts chat sequence --json "A->B: message"` |
| Flowchart | `glyph-arts chat diagram flowchart --json "A -> B -> C"` |
| Math notation | `glyph-arts chat diagram math --json "alpha_i^2 + sqrt(x) + 1/2"` |
| Mermaid source | `glyph-arts chat mermaid --json <mermaid-source>` |
| Mermaid XY chart | `glyph-arts chat mermaid --json "xychart-beta\nx-axis [A, B]\nbar [3, 7]\nline [2, 8]"` |
| Continuous function plot | `glyph-arts chat textplot --json "{\"expr\":\"sin(x) / x\",\"xmin\":-20,\"xmax\":20}"` |
| Drawille-style turtle | `glyph-arts chat turtle --json "{\"commands\":[[\"forward\",30],[\"right\",90],[\"forward\",20]]}"` |
| Tree | `glyph-arts chat diagram tree --json "root/a\nroot/b"` |
| Frame | `glyph-arts chat diagram frame --json <text>` |
| Unicode table | `glyph-arts chat diagram table --json "a|b\n1|2"` |
| GraphDAG / GraphPlanar | `glyph-arts chat diagram graphdag|graphplanar --json "A -> B\nB -> C"` |
| Note/callout box | `glyph-arts chat diagram note --json "NOTE\nmessage"` |
| Chinese note/table | `glyph-arts chat diagram note|table --json <text>` |
| Edge-list graph | `glyph-arts chat graph --json "A -> B\nB -> C"` |
| DOT graph | `glyph-arts chat graph --graph-format dot --json "digraph { A -> B; }"` |
| JSON graph | `glyph-arts chat graph --json "{\"edges\":[[\"A\",\"B\"]]}"` |
| Effect gallery | `glyph-arts chat effects` |
| Preset visual recipe | `glyph-arts effect pipeline|metrics|system-map|signal-panel|timeline|matrix|comparison|swimlane|kanban|quadrant|mindmap` |
| SDR spectrum | `glyph-arts chat sdr spectrum --json <json-or-path>` |
| SDR waterfall | `glyph-arts chat waterfall --json <json-or-path>` |

## Split Rules

- For chat panes near 80 columns, keep diagrams under 76 columns.
- For wide terminal panes, keep drawings under 120 columns unless the user asks for full width.
- For dense graphs, render a path, cluster, or legend first; do not squeeze the whole system into unreadable noise.
- For mixed requests, render the strongest primary view first, then a compact table or legend below it.
- Use `chat image` for Markdown/chat panes; use `image --media-engine chafa`
  only for a real terminal or for explicit text captures with
  `--chafa-format symbols`.

## Backend Boundaries

- `incplot` is the first stop for unknown raw data. Do not use it when the user
  already asked for a specific annotated plot.
- `plotext` is for overlays and statistical plot features, not for guessing raw
  input shape.
- `textplot` is for continuous math expressions over `x`.
- `turtle` is for drawille-style paths and pixel commands.
- `chafa` is the raster terminal backend. In chat mode it must stay on
  `--chafa-format symbols`; terminal-native `kitty`, `iterm`, or `sixels`
  output is for real terminals only.
- `mermaid`, `diagram`, and `graph` are structure renderers; keep data plots out
  of them unless the user provided diagram syntax.
