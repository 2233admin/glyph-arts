# Claude Adapter

Use `skills/chat-drawing/SKILL.md` as the skill entrypoint.

Claude-specific reminders:

- Prefer `glyph-arts chat ...` and `--no-color` for transcript output.
- If using a local skill install, run commands through the packaged script path
  when available: `python $SKILL/scripts/chart.py chat ...`.
- Render to stdout or capture stdout into a text file.
- Verify with `scripts/verify_chat_art.py` before every drawing reply.
- If verification fails, rerender smaller or fallback; do not paste broken
  output.
- Paste the verified visible stdout drawing back into the chat.

Shortcut prompt:

```text
Use glyph-arts chat drawing. Route with references/decision-tree.md, render to
stdout, verify with scripts/verify_chat_art.py, then reply with the drawing.
```
