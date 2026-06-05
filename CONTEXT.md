# Glyph Arts

Glyph Arts is the current project and CLI for Chat Arts: visual answers that belong in the chat-first workflow and can spill into terminals, files, or host applications only when the user's drawing intent requires it.

## Language

**Chat Arts**:
The product-level idea of making useful visuals directly inside chat-first workflows.
_Avoid_: Glyph Arts, terminal charting

**Conversation-First**:
The design philosophy that chat-readable output is the default surface unless the drawing needs another target.
_Avoid_: terminal-first, file-first, GUI-first

**Glyph Arts**:
The current project, package, and CLI name for Chat Arts capabilities.
_Avoid_: product positioning, user-facing category name

**Chat Drawing**:
A visual answer intended to be produced from a chat request and shown through the safest available target.
_Avoid_: terminal art, chart output

**Chat Output**:
The text printed directly into the conversation window.
_Avoid_: artifact, host preview, terminal-only output

**Diagram Renderer**:
A renderer for structured relationships such as sequences, flowcharts, notes, trees, graphs, math, Mermaid, and diagrams.net/draw.io material.
_Avoid_: graph renderer, flowchart mode

**Draw.io Export**:
A small Diagram Renderer output path that turns chat-originated diagram material into a diagrams.net/draw.io artifact or preview.
_Avoid_: Draw.io Artifact Bridge, primary renderer, chat drawing replacement

**Human Review Output**:
A visual output made so a person can inspect, share, or continue editing outside the chat window.
_Avoid_: core chat surface, renderer category

**Draw.io XML Output**:
The side-effect-free Draw.io Export path that produces or validates diagrams.net/draw.io XML.
_Avoid_: preview, host session

**Draw.io Host Handoff**:
The Draw.io Export path that sends diagram material to a diagrams.net/draw.io host for preview or export.
_Avoid_: chat output, pure XML output

**Artifact**:
A file output that preserves a visual beyond the chat turn.
_Avoid_: screenshot, preview

**Host Preview**:
A view opened in another UI shell, such as a browser, WaveTerm, or diagrams.net/draw.io.
_Avoid_: artifact, chat output

## Relationships

- **Chat Arts** is the product idea; **Glyph Arts** is the current implementation name.
- **Conversation-First** is the default design philosophy for **Chat Arts**.
- A **Chat Drawing** may produce **Chat Output**.
- A **Chat Drawing** may use a **Diagram Renderer**.
- A **Diagram Renderer** may produce chat-safe text, terminal output, an **Artifact**, or a **Host Preview**.
- Output targets are described in **Conversation-First** order: **Chat Output**, terminal output, **Artifact**, then **Host Preview**.
- **Draw.io Export** is one optional **Diagram Renderer** output path, not a primary product surface.
- **Draw.io Export** is a **Human Review Output** path under **Diagram Renderer**.
- **Draw.io XML Output** has no host side effects.
- **Draw.io Host Handoff** may open or depend on a host.
- A **Host Preview** may also produce an **Artifact**, but it is not itself the artifact.

## Example Dialogue

> **Dev:** "Should `glyph-arts chat diagram flowchart` open draw.io?"
> **Domain expert:** "No. It should stay chat-first. Use **Draw.io Export** only when the user needs a diagrams.net/draw.io artifact or preview."

## Flagged Ambiguities

- "draw.io integration" can sound like a primary surface; resolved: it is **Draw.io Export**, a small optional path inside **Diagram Renderer**.
- "direct draw.io support in chat" can sound like `chat` should open draw.io; resolved: `chat` means **Chat Output** in the conversation window.
- `diagram drawio` and `to-drawio` may look redundant; resolved: `diagram drawio` is **Draw.io XML Output**, while `to-drawio` is **Draw.io Host Handoff**.
- draw.io can look like a headline feature; resolved: it is **Human Review Output** for people who need diagrams.net/draw.io, while the core remains chat-first art.
- "terminal-first" conflicts with the product philosophy; resolved: the product is **Conversation-First**, while terminal rendering is one target.
