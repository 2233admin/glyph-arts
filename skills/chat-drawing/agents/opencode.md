# OpenCode Adapter

Use this for OpenCode or OpenCLI-style agents.

- Treat `glyph-arts chat ...` as the default renderer for visible answers.
- Use `references/agent-contract.md` as the portable prompt.
- Use `references/decision-tree.md` for route selection.
- Always return the stdout drawing to the user.
- If a dependency is missing, use the builtin fallback route and say which
  dependency was unavailable.

Minimal portable prompt:

```text
For any visualization request, call glyph-arts chat, verify stdout, and include
the rendered text in the reply. Use incplot for unknown data, plotext for
overlays, textplot for functions, turtle for drawille paths, mermaid/diagram for
structures, and image for pictures.
```
