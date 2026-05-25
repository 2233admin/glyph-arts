# Quality Gates

Use these checks before sending the drawing back to the user.

## Boxes

- Use equal-length lines.
- Prefer Unicode corners: `┌ ┐ └ ┘`.
- Add one or two spaces of horizontal padding inside boxes.
- Avoid decorative double borders unless the user asks for ornate output.
- Measure display width, not character count. Chinese/full-width characters
  take two terminal columns.

Good:

```text
┌────────────┐
│  Capture   │
└────────────┘
```

Bad:

```text
┌────────────┐
│ Capture │
└──────────────┘
```

## Trees

- Use `│` for continuation.
- Use `├──` for non-final branches and `└──` for final branches.
- Indent children by 4 spaces.

## Flows

- For vertical flows, put arrows on their own line.
- Use `▼` when readability matters more than compactness.
- Keep labels short and aligned.

## Density Maps

- Use `░ ▒ ▓ █` only for heatmaps, coverage maps, waterfall plots, and image-like ASCII.
- Include a small legend when the meaning of density is not obvious.

## Images

- Preserve the subject before maximizing detail.
- For portraits, prefer a tight crop around the face and shoulders.
- If the subject disappears, reduce width/height, change the style, or rerun with stronger contrast.

## Math And CJK

- Route formulas through `glyph-arts chat diagram math` before hand-writing math.
- Prefer Unicode math when it fits: `α`, `β`, `π`, `√`, `≤`, `≥`, `≠`, `→`,
  superscripts, subscripts, and simple stacked fractions.
- For Chinese labels, keep table cells and boxes display-width aligned.

## Reply Contract

- Show the drawing directly in the response.
- Mention files only as secondary artifacts.
- If a dependency is missing, provide the best builtin fallback and say exactly what was unavailable.

## Agent Portability

- Another agent must be able to repeat the render from the command you used.
- Prefer commands that work from stdin or `--json`; avoid shell-specific tricks.
- Keep the final route and verifier result visible in handoffs when possible.
- For Claude/Codex/OpenCode installs, include `references/agent-contract.md`,
  `references/decision-tree.md`, and `agents/contract.json`.
