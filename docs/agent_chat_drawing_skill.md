# Agent Chat Drawing Skill

This is the compact instruction packet for skills-aware agents that need to
draw directly in a chat transcript. The installable skill package lives at
`skills/chat-drawing`.

Machine-readable companion: `docs/chat_drawing_capabilities.json`.
Portable agent contract: `skills/chat-drawing/references/agent-contract.md`.
Route decision tree: `skills/chat-drawing/references/decision-tree.md`.
Anti-lazy gate: `skills/chat-drawing/scripts/verify_agent_contract.py`.

## Rule

Prefer `glyph-arts chat ...` whenever the user asks to show, draw, visualize,
sketch, diagram, or preview inside the conversation.

Use stdout text first. Use files only when the user explicitly asks for an
artifact or the target format cannot be represented as text.

## Chat Rendering Protocol v1

Treat the chat pane as its own target, not as a terminal:

- `chat` means pure text that survives Markdown code blocks and copy/paste.
- `terminal` means ANSI, truecolor, cursor movement, Kitty/Sixel, chafa, or
  other TTY graphics.
- `artifact` means `.txt`, `.ansi`, `.html`, `.png`, `.svg`, `.gif`, or similar
  files.
- `host` means WaveTerm, browser, IDE, or another UI shell that needs an
  adapter.

Every machine-readable capability in `docs/chat_drawing_capabilities.json`
declares `protocol.targets`, `chat_safe`, `uses_ansi`, `unicode_tier`,
`fallback`, and `requires_host`. If `chat` is listed, `chat_safe` must be true
and `uses_ansi` must be false.

## Terminal Host Profiles

When the target is a real terminal, run or inspect `glyph-arts doctor` before
choosing image output. It reports `profile=...`, `format=...`, `sixel=...`,
`kitty=...`, and `font-tier=...`.

- `windows-terminal`: use truecolor symbols/blocks.
- `windows-terminal-preview` or `windows-terminal-canary`: prefer
  `chafa --format sixels`.
- `warp`: use truecolor symbols/blocks; do not emit Sixel.
- `waveterm`: prefer `glyph-arts wave render ...` for host blocks.

Use `GLYPH_ARTS_TERMINAL_PROFILE=...` when the host cannot be detected from
environment variables.

Do not confuse host, runtime, and shell. `profile=warp runtime=wsl shell=bash`
means Warp decides image protocol support, WSL owns installed binaries and file
paths, and bash owns command quoting.
If interop makes this ambiguous, set `GLYPH_ARTS_RUNTIME=wsl` or
`GLYPH_ARTS_RUNTIME=windows`.

## Formatting Rules

- Boxes must use equal-length lines, Unicode corners `┌ ┐ └ ┘`, and padding.
- For Chinese/full-width text, verify display width rather than Python string
  length. `中文` occupies four terminal columns, not two.
- Trees use `│` for continuation, `├──` and `└──` for branches, and 4-space
  child indentation.
- Vertical arrows use `▼` on their own line. Avoid inline arrows when a flow
  is meant to be read top-to-bottom.
- Titles use simple `─` separators or a box title, not heavy `═` decoration.
- Shade blocks `░ ▒ ▓ █` are reserved for density maps, coverage, heatmaps,
  and image-like output.
- Note boxes should use the labeled split layout from `chat diagram note`.

## Routing

| User intent | Command shape |
|---|---|
| Photo or portrait ASCII | `glyph-arts chat image --file image.jpg --width 80 --height 30` |
| Unknown CSV/TSV/JSONL data | `glyph-arts chat incplot < data.csv` |
| SDR spectrum | `glyph-arts chat sdr spectrum --json DATA` |
| SDR waterfall | `glyph-arts chat waterfall --json DATA` |
| Sequence diagram | `glyph-arts chat sequence --json 'A->B: message'` |
| Flowchart | `glyph-arts chat diagram flowchart --json 'A -> B -> C'` |
| Tree | `glyph-arts chat diagram tree --json 'root/a\nroot/b'` |
| Table | `glyph-arts chat diagram table --json 'a|b\n1|2'` |
| Note box | `glyph-arts chat diagram note --json 'NOTE\nmessage'` |
| Math notation | `glyph-arts chat diagram math --json 'alpha_i^2 + sqrt(x) + 1/2'` |
| Mermaid / beautiful-mermaid | `glyph-arts chat mermaid --json 'graph LR\nA[开始] --> B[完成]'` |
| Mermaid XY chart | `glyph-arts chat mermaid --json 'xychart-beta\nx-axis [A, B]\nbar [3, 7]\nline [2, 8]'` |
| Plotext overlays | `glyph-arts chat plotext --json '{"series":[...],"texts":[...],"vlines":[...],"shapes":[...]}'` |
| Continuous function plot | `glyph-arts chat textplot --json '{"expr":"sin(x) / x","xmin":-20,"xmax":20}'` |
| Braille turtle drawing | `glyph-arts chat turtle --json '{"commands":[["forward",30],["right",90],["forward",20]]}'` |
| Chinese callout/table | `glyph-arts chat diagram note|table --json DATA` |
| Network graph | `glyph-arts chat graph --json 'A -> B\nB -> C'` |
| DOT graph | `glyph-arts chat graph --graph-format dot --json 'digraph { A -> B; }'` |
| JSON graph | `glyph-arts chat graph --json '{"edges":[["A","B"]]}'` |
| Rich preset/effect gallery | `glyph-arts chat effects` |
| Rich preset/effect | `glyph-arts effect pipeline|metrics|system-map|signal-panel|timeline|matrix|comparison|swimlane|kanban|quadrant|mindmap` |
| Bar/line/scatter/heatmap | `glyph-arts chat bar|line|scatter|heatmap --json DATA` |

## Cross-Agent Install

For Codex, Claude, OpenCode, or similar agents:

1. Install or expose `skills/chat-drawing`.
2. Give the agent `references/agent-contract.md`.
3. Use `references/decision-tree.md` before choosing a renderer.
4. Use `agents/contract.json` for machine-readable route names.
5. Require the route -> render_stdout -> verify -> rerender_on_failure ->
   reply_with_stdout loop.
6. Run `python skills/chat-drawing/scripts/verify_agent_contract.py` in CI or
   before shipping the adapter. A failing gate means the adapter is too lazy to
   advertise chat drawing support.

## Backends

- Image ASCII: Pillow fallback, chafa optional for rich terminal rendering.
- incplot-style auto plot: use `chat incplot` for raw JSON, JSONL, CSV, or TSV
  when the user has not specified a chart type.
- SDR: native `spectrum` and `waterfall` renderers.
- Structure diagrams: Diagon when installed; builtin fallback for math,
  sequence, tree, frame, table, graphplanar, graphdag, flowchart, note, and box.
- Mermaid diagrams: builtin beautiful-mermaid-style fallback for flowchart,
  sequence, state, class, ER, and xychart-beta, with Unicode/ASCII output and
  spacing controls. XY charts support rounded bars, horizontal layout, line
  overlay, legends, series names, and CJK labels.
- Network graphs: PHART via `graph`, with JSON, edge-list, DOT, and GraphML
  support.
- Chat effects: native `effect` presets for pipeline, metrics, system maps,
  signal panels, timelines, matrices, before/after comparisons, swimlanes,
  kanban boards, quadrants, and mindmaps.
- Plotext overlays: use `chat plotext` when the user needs error bars,
  date-time/candlestick plots, text annotations, vertical/horizontal guide
  lines, rectangles, polygons, or colorized terminal strings. Do not route
  video/audio/YouTube requests through the chat contract.
- textplots/drawille: use `chat textplot` for continuous functions and `chat
  turtle` for Braille Canvas/Turtle path drawings.

## Verification

After rendering, check:

- stdout is non-empty.
- chat output does not contain ANSI escape codes unless ANSI was explicitly
  requested.
- output width is reasonable for the chat pane.
- the important labels from the input are visible.
- boxed diagrams have equal line widths. For generated markdown, verify with
  `wc -m` or an equivalent per-line character count before committing.

If a renderer fails, fall back in this order:

1. `glyph-arts chat diagram ...`
2. `glyph-arts chat graph ...`
3. `glyph-arts chat table ...`
4. plain fenced text with a short explanation of the missing dependency.
