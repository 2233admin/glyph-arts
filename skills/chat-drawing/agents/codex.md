# Codex Adapter

Use this when Codex is operating in a repo or terminal.

- Prefer the installed command: `glyph-arts chat ...`.
- For raw data, start with `glyph-arts chat incplot`.
- For diagrams, use `glyph-arts chat mermaid`, `diagram`, or `graph` instead of
  hand-drawing.
- For function/path drawing, use `textplot` or `turtle`.
- Run the verifier before final response when output will be pasted to chat.

Codex command loop:

```bash
glyph-arts chat textplot --json '{"expr":"sin(x) / x","xmin":-20,"xmax":20}' > output.txt
python skills/chat-drawing/scripts/verify_chat_art.py output.txt --max-width 100
```
