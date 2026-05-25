# Agent Contract

This file is the portable instruction for Codex, Claude, OpenCode, and other
agents. It is intentionally small enough to paste into another agent.

## Contract

When a user asks to draw, show, visualize, sketch, plot, diagram, preview, or
render inside the conversation:

1. Use `glyph-arts chat ...` first.
2. Render to stdout.
3. Verify stdout before replying.
4. Reply with the drawing itself in a fenced `text` block.
5. Mention files only as secondary artifacts.

## Required Loop

```bash
glyph-arts chat incplot < data.csv > output.txt
python skills/chat-drawing/scripts/verify_chat_art.py output.txt --max-width 100
```

If stdout is empty, too wide, contains ANSI when chat-safe text was expected, or
loses the requested labels, rerender before replying.

## Core Routing

| User asks for | Use |
|---|---|
| Unknown JSON/JSONL/CSV/TSV data | `glyph-arts chat incplot` |
| Simple chart | `glyph-arts chat bar|line|scatter|heatmap` |
| Error bars, labels, guide lines, shapes | `glyph-arts chat plotext` |
| Function curve | `glyph-arts chat textplot` |
| Drawille/Turtle/Canvas path | `glyph-arts chat turtle` |
| Mermaid source | `glyph-arts chat mermaid` |
| Sequence/tree/math/table/frame/DAG | `glyph-arts chat diagram <kind>` |
| Network/DOT/GraphML | `glyph-arts chat graph` |
| Image/portrait | `glyph-arts chat image --file <path>` |
| Terminal-native image | `glyph-arts image --media-engine chafa --chafa-format auto --chafa-symbols sextant --file <path>` |
| SDR spectrum/waterfall | `glyph-arts chat sdr spectrum` / `glyph-arts chat waterfall` |

## Do Not

- Do not tell the user a file was created instead of showing the drawing.
- Do not hand-write charts when a `glyph-arts chat ...` route exists.
- Do not send ANSI escape codes into a markdown chat unless color was requested.
- Do not claim video/audio/YouTube streaming is chat-safe; use snapshots or text
  summaries instead.
- Do not use `kitty`, `iterm`, or `sixels` output in a chat transcript; force
  `--chafa-format symbols` there.
