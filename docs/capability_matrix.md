# glyph-arts Capability Matrix

This matrix separates what renders directly in an AI chat pane from what needs
ANSI support, an exported artifact, or a host preview.

`glyph-arts chat ...` is the front door for chat drawing. It rewrites to
`image --chat` for image inputs and to `--no-color` for chart inputs.

## Chat Rendering Protocol v1

| Target | Meaning | Allowed mechanisms |
|---|---|---|
| `chat` | Codex/Claude/OpenCode chat pane | Pure text, Markdown-safe Unicode, no ANSI |
| `terminal` | Real TTY | ANSI, truecolor, cursor movement, chafa, Kitty/Sixel |
| `artifact` | File output | `.txt`, `.ansi`, `.html`, `.png`, `.svg`, `.gif`, `.tsx` |
| `host` | UI shell adapter | WaveTerm `wsh`, browser/IDE block previews |

## Terminal Host Profiles

`glyph-arts doctor` reports the current host profile so agents can pick a
rendering path without guessing:

| Profile | Truecolor | Sixel | Kitty | Default chafa format | Notes |
|---|---:|---:|---:|---|---|
| `windows-terminal` | yes | no | no | `symbols` | Conservative Windows Terminal baseline |
| `windows-terminal-preview` | yes | yes | no | `sixels` | Windows Terminal Preview 1.22+ image path |
| `windows-terminal-canary` | yes | yes | no | `sixels` | Canary image path |
| `warp` | yes | no | no | `symbols` | Truecolor blocks/symbols, no Sixel path |
| `waveterm` | yes | no | no | `symbols` | Prefer the `wave` host adapter |

Override with `GLYPH_ARTS_TERMINAL_PROFILE=warp`,
`windows-terminal-preview`, or `windows-terminal-canary` when environment
detection is too coarse.

Runtime is reported separately from the host. `profile=warp runtime=wsl
shell=bash` means render for Warp's graphics limits, install command-line
backends inside WSL, and use bash quoting examples.
Use `GLYPH_ARTS_RUNTIME=wsl|windows|linux|macos` to resolve interop ambiguity.

Machine-readable capabilities live in `docs/chat_drawing_capabilities.json`.
Every capability declares `protocol.targets`, `chat_safe`, `uses_ansi`,
`unicode_tier`, `fallback`, and `requires_host`.

| Capability | Chat text | ANSI terminal | Artifact export | Host preview | Entry point |
|---|---:|---:|---:|---:|---|
| Image ASCII | yes | yes | yes | no | `glyph-arts chat image --file photo.jpg` |
| Portrait foreground crop | yes | yes | yes | no | `glyph-arts image --chat --image-mode auto` |
| 9 ascii-art styles | yes | yes | yes | no | `--image-style classic|braille|block|edge|dot-cross|halftone|particles|retro-art|terminal` |
| Image color modes | plain text only | yes | yes | no | `--color-mode grayscale|original|full|matrix|amber|custom` |
| Dithering | yes | yes | yes | no | `--dither none|floyd-steinberg|bayer|atkinson` |
| Ratio crop | yes | yes | yes | no | `--ratio original|16:9|4:3|1:1|3:4|9:16` |
| Bar chart | yes | yes | `.txt` `.ansi` `.html` `.png` via pixel engine | no | `glyph-arts bar --json ...` |
| Line chart | yes | yes | `.txt` `.ansi` `.html` `.png` via pixel engine | yes, line TUI | `glyph-arts line --json ...` |
| Scatter chart | yes | yes | `.txt` `.ansi` `.html` `.png` via pixel engine | no | `glyph-arts scatter --json ...` |
| Heatmap | yes | yes | `.txt` `.ansi` `.html` | no | `glyph-arts heatmap --json ...` |
| Table | yes | yes | `.md` `.txt` `.ansi` `.html` | no | `glyph-arts table --json ...` |
| Dashboard | static yes | yes | `.txt` `.ansi` `.html` | yes, Textual TUI | `glyph-arts dashboard --json ... --no-interactive` |
| incplot-style auto plot | yes, JSON/JSONL/CSV/TSV inference | yes | `.txt` `.ansi` `.html` | no | `glyph-arts chat incplot < data.csv` |
| Plotext overlay | yes, error bars, date plots, text, lines, shapes | yes | `.txt` `.ansi` `.html` | no | `glyph-arts chat plotext --json ...` |
| SDR spectrum | yes | yes | `.txt` `.ansi` `.html` | no | `glyph-arts chat sdr spectrum --json ...` |
| SDR waterfall | yes | yes | `.txt` `.ansi` `.html` | no | `glyph-arts chat waterfall --json ...` |
| Math notation | yes, builtin Unicode fallback; Diagon optional | yes | `.txt` `.ansi` `.html` | no | `glyph-arts chat diagram math --json ...` |
| Mermaid diagrams | yes, beautiful-mermaid-style fallback | yes | `.txt` `.ansi` `.html` | no | `glyph-arts chat mermaid --json ...` |
| Mermaid XY chart | yes, rounded bars, line overlay, legend, horizontal layout | yes | `.txt` `.ansi` `.html` | no | `glyph-arts chat mermaid --json 'xychart-beta ...'` |
| Sequence diagram | yes | yes | `.txt` `.ansi` `.html` | no | `glyph-arts chat sequence --json 'A->B: msg'` |
| Tree/table/frame diagram | yes | yes | `.txt` `.ansi` `.html` | no | `glyph-arts chat diagram tree --json ...` |
| Note box | yes | yes | `.txt` `.ansi` `.html` | no | `glyph-arts chat diagram note --json 'NOTE\nmessage'` |
| Flowchart/DAG/planar graph | builtin flowchart, GraphDAG, GraphPlanar fallback | yes | `.txt` `.ansi` `.html` | no | `glyph-arts chat diagram flowchart --json 'A -> B'` |
| Network graph | yes | yes | `.txt` `.ansi` `.html` | no | `glyph-arts chat graph --json 'A -> B'` |
| DOT/GraphML graph | simple DOT fallback; full DOT/GraphML through PHART deps | yes | `.txt` `.ansi` `.html` | no | `glyph-arts chat graph --graph-format dot --json 'digraph { A -> B; }'` |
| textplots-rs function plot | yes, Braille continuous line | no ANSI needed | `.txt` `.html` | no | `glyph-arts chat textplot --json '{"expr":"sin(x)"}'` |
| drawille turtle/canvas | yes, Braille path drawing | no ANSI needed | `.txt` `.html` | no | `glyph-arts chat turtle --json ...` |
| Chat effect presets | yes | yes | `.txt` `.ansi` `.html` | no | `glyph-arts chat effects` |
| WaveTerm rich block preview | stdout still text | yes | `.html` `.txt` `.ansi` via `wsh view` | Wave block | `glyph-arts wave render bar --json ...` |
| Video | no, snapshot/artifact only | yes | terminal recording paths | playback stream | `glyph-arts video --file clip.mp4` |
| Static GIF / TSX image exports | no | no | yes | TSX consumer-side | `glyph-arts image --output art.gif|art.tsx` |

## Current Limits

- `--chat` intentionally disables ANSI color so Markdown and AI chat panes do
  not receive escape-code noise.
- PNG, SVG, GIF, HTML, and TSX are file artifacts. The chat can reference them,
  but they are not pure text.
- Live dashboards and video playback are terminal experiences. A chat transcript
  can show stable snapshots, not real interactivity.
- `plotext` is used as both the regular plot engine and the overlay engine for
  error bars, date-time plots, candlesticks, labels, guide lines, rectangles,
  polygons, and colorized strings. Video/audio/YouTube streaming remains outside
  the chat contract.
- `incplot` is the automatic plotting front door for raw JSON, JSONL, CSV, and
  TSV. It infers category bars, grouped bars, temporal lines, numeric scatter,
  sparkline, table, histogram, and OHLC candlestick payloads.
- `textplot` mirrors the textplots-rs continuous-function idea on a dependency
  free Braille canvas. `turtle` mirrors drawille Canvas/Turtle commands for
  paths, dots, pen movement, and simple line drawings.
- Clipboard and interactive canvas behavior from `neethanwu/ascii-art` are not
  implemented as first-class glyph-arts features yet.
- External `diagon` is still preferred for exact upstream fidelity, but the
  builtin chat fallback now covers the Diagon generator set used by agents:
  `math`, `sequence`, `tree`, `frame`, `table`, `graphplanar`, `graphdag`, and
  `flowchart`. Math covers common Unicode notation: Greek letters,
  superscript/subscript, square roots, comparisons, arrows, and simple stacked
  fractions.
- Builtin boxed diagrams, tables, notes, and verification use display width
  rather than Python character count, so Chinese/full-width text stays aligned.
- `mermaid` restores the beautiful-mermaid convention: Mermaid source, ASCII or
  Unicode output, theme names, spacing controls, and builtin chat fallback for
  flowchart, sequence, state, class, ER, and xychart-beta. XY charts include
  rounded columns, horizontal bars, line overlay, legends, and CJK-safe labels.
- PHART graph rendering is available through `graph`; DOT support falls back to
  a simple edge parser when optional DOT parsing dependencies are unavailable.
- `wave` is an adapter, not a renderer. It exports an existing glyph-arts chart
  and asks WaveTerm's `wsh view` to open the artifact as a rich block. Plain
  `chat` output remains the portable baseline for Codex/Claude transcripts.
- Windows Terminal and Warp are terminal profiles, not chat-pane protocols.
  Windows Terminal Preview/Canary can opt into Sixel image output; Warp uses
  truecolor symbols/blocks as the safe high-fidelity path.
