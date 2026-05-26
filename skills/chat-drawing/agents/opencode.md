# OpenCode Adapter

Use this for OpenCode or OpenCLI-style agents.

- Treat `glyph-arts chat ...` as the default renderer for visible answers.
- Use `references/agent-contract.md` as the portable prompt.
- Use `references/decision-tree.md` for route selection.
- Render to stdout or capture stdout into a text file.
- Verify with `scripts/verify_chat_art.py` before every drawing reply.
- If verification fails, rerender smaller or fallback.
- Always return the verified stdout drawing to the user.
- If a dependency is missing, use the builtin fallback route and say which
  dependency was unavailable.

Minimal portable prompt:

```text
For any visualization request, call glyph-arts chat, capture stdout, verify with
scripts/verify_chat_art.py, rerender or fallback on failure, and include the
verified rendered text in the reply. Use incplot for unknown data, plotext for
overlays, textplot for functions, turtle for drawille paths, mermaid/diagram for
structures, and image for pictures.
```
