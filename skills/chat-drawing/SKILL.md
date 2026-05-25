---
name: chat-drawing
description: Use when a user asks Codex, Claude, OpenCode, or another agent to draw directly in a chat or CLI transcript with glyph-arts: ASCII/Unicode art, image-to-ASCII portraits, diagrams, flowcharts, sequence diagrams, PHART graphs, tables, dashboards, bar/line/scatter/heatmap charts, SDR spectrum/waterfall plots, or any request where the result must be visible in stdout instead of only saved to a file.
---

# Chat Drawing

Render first, verify second, reply with the visible artifact third. The point of this skill is not to create hidden files; it is to make the chat transcript itself carry the drawing.

This is a hard contract, not a suggestion. Agent adapters must pass
`scripts/verify_agent_contract.py`; if an adapter does not force routing,
stdout rendering, verification, fallback, and reply-with-visible-output, it is
not a valid chat-drawing adapter.

## Loop

1. Classify the request: image, chart, diagram, graph, SDR, table, dashboard, or mixed.
2. Choose the smallest `glyph-arts chat ...` command that can render the result. Use `references/decision-tree.md` first and `references/routing.md` for command shapes.
3. Render to stdout. Disable ANSI unless the user explicitly asks for colored terminal output.
   For a real terminal target, inspect `glyph-arts doctor` first: Windows Terminal Preview/Canary can use Sixel, Warp should use truecolor symbols/blocks, and WaveTerm should use `glyph-arts wave ...`.
4. Verify the rendered text before replying:
   - non-empty output
   - no ANSI escape codes unless allowed
   - width fits the target chat pane
   - requested labels are visible
   - box/frame lines are equal width when boxes are used
   - Chinese/full-width text is checked by display width, not character count
5. If verification fails, rerender with a simpler layout, smaller dimensions, fewer nodes, or a fallback backend. Do not hand the user a broken drawing and call it done.
6. Reply with the final visible drawing in a fenced text block or inline transcript block. Mention file paths only when the user explicitly asked for an artifact.

## Commands

Prefer these shapes:

```bash
glyph-arts chat image --file input.jpg --width 80 --height 32
glyph-arts chat incplot --json "name,value\nA,3\nB,7"
glyph-arts chat graph --json "A -> B\nB -> C"
glyph-arts chat graph --graph-format dot --json "digraph { A -> B; }"
glyph-arts chat diagram flowchart --json "Capture -> Render -> Verify -> Reply"
glyph-arts chat diagram note --json "NOTE\nCache refresh before reading results."
glyph-arts chat diagram math --json "alpha_i^2 + sqrt(x) + 1/2"
glyph-arts chat mermaid --json "graph LR\nA[开始] --> B[完成]"
glyph-arts chat mermaid --json "xychart-beta\nx-axis [Alpha, Beta]\nbar [3, 7]\nline [2, 8]"
glyph-arts chat plotext --json '{"series":[{"type":"error","x":[1,2,3],"y":[2,5,3],"yerr":[0.3,0.8,0.4]}],"texts":[{"text":"peak","x":2,"y":5}],"vlines":[2]}'
glyph-arts chat textplot --json '{"expr":"sin(x) / x","xmin":-20,"xmax":20}'
glyph-arts chat turtle --json '{"commands":[["forward",30],["right",90],["forward",20]]}'
glyph-arts chat effects
glyph-arts chat sdr spectrum --json data.json
glyph-arts chat waterfall --json data.json
glyph-arts chat bar --json data.json
```

Use `references/quality.md` when the output involves boxes, trees, vertical flows, density maps, or image-like ASCII.
Use `references/agent-contract.md` when installing or copying this capability into another agent.

## Verification Script

Use the bundled checker for deterministic gates:

```bash
python skills/chat-drawing/scripts/verify_chat_art.py output.txt --max-width 100 --require-label Agent
```

It also accepts stdin:

```bash
glyph-arts chat graph --json "Agent -> Tool" | python skills/chat-drawing/scripts/verify_chat_art.py --max-width 100 --require-label Agent
```

If the checker fails, rerender and rerun it. Treat this as the closed loop.

## Agent Adapter Gate

When copying this skill into another agent, run the adapter gate too:

```bash
python skills/chat-drawing/scripts/verify_agent_contract.py
```

This rejects lazy adapters that skip `glyph-arts chat`, skip verification,
save only hidden artifacts, or fail to paste the verified stdout drawing back to
the user.

## Fallbacks

- Image lost the subject: rerender with portrait crop, higher contrast, lower width, or a different ASCII style.
- Unknown data format: use `glyph-arts chat incplot`; it auto-detects JSON, JSONL, CSV, TSV, category bars, grouped bars, temporal lines, numeric scatter, histograms, tables, and OHLC candlesticks.
- Diagram too wide: split into sections, use a vertical flow, or convert to a table.
- Graph too dense: reduce nodes, show the critical path, or render multiple subgraphs.
- Output feels too thin: rerender through `glyph-arts chat effects` or a concrete `effect` preset such as `pipeline`, `metrics`, `system-map`, `signal-panel`, `timeline`, `matrix`, `comparison`, `swimlane`, `kanban`, `quadrant`, or `mindmap`.
- Math looks raw: use `glyph-arts chat diagram math`; builtin mode supports common Greek letters, superscript/subscript, square roots, arrows, comparisons, and simple stacked fractions.
- Mermaid source is provided: use `glyph-arts chat mermaid`; it follows the beautiful-mermaid-style contract for flowchart, sequence, state, class, ER, and xychart-beta. For `xychart-beta`, use the builtin rounded bars, horizontal mode, line overlay, and legend instead of hand-drawing charts.
- Error bars, date-time plots, guide lines, labels, or chart shapes are needed: use `glyph-arts chat plotext`; it exposes plotext overlays for error bars, text, vertical/horizontal lines, rectangles, polygons, histograms, and candlesticks. Video/audio streaming is intentionally not part of chat drawing.
- Function curve requested: use `glyph-arts chat textplot` for textplots-rs-style continuous Braille plots.
- Drawille/Turtle/Canvas requested: use `glyph-arts chat turtle` for Braille dot/path commands.
- Chinese boxes or tables drift: rerender with builtin `diagram note`, `diagram table`, or `effect` presets so display-width padding is applied.
- Diagon is unavailable: use builtin `diagram` kinds that still produce stdout: `math`, `sequence`, `tree`, `frame`, `table`, `graphplanar`, `graphdag`, `flowchart`, `note`, and `box`.
- ANSI is unreadable in chat: rerender with `--no-color`.
