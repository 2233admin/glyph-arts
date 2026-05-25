# Decision Tree

Use this tree before choosing a renderer. The goal is visible chat output, not
backend purity.

## Data First

1. Unknown raw data shape: use `glyph-arts chat incplot`.
   - Accepts JSON, JSONL, CSV, and TSV.
   - Detects sparkline, bar, multibar, line, scatter, hist, table, and OHLC.
   - Use `--prefer line|scatter|bar|multibar|hist|table|kline` only when the
     user asks for a specific view.
2. Known simple chart: use the direct chart command.
   - `bar`, `line`, `scatter`, `heatmap`, `table`, `dashboard`.
3. Statistical or annotated plot: use `glyph-arts chat plotext`.
   - Error bars, date-time plots, candlesticks, labels, guide lines, rectangles,
     polygons, and colorized strings.
4. Continuous function: use `glyph-arts chat textplot`.
   - Examples: `sin(x)`, `sin(x) / x`, `10*x + x^2`.
5. Pixel/path drawing: use `glyph-arts chat turtle`.
   - Drawille-style dot, line, pen, and turtle commands.

## Diagram First

1. Mermaid source provided: use `glyph-arts chat mermaid`.
2. Diagon-style request: use `glyph-arts chat diagram <kind>`.
3. Network or dependency graph: use `glyph-arts chat graph`.
4. Dense workflow or multi-panel visual: use `glyph-arts effect <preset>`.

## Media First

1. Image path: use `glyph-arts chat image --file`.
2. Portrait subject disappears: rerender with tighter crop, lower size, or a
   different `--image-style`.
3. SDR data: use `glyph-arts chat sdr spectrum` or `glyph-arts chat waterfall`.

## Fallback Order

If the chosen renderer fails:

1. Reduce width and labels.
2. Switch to the simpler route in the same family.
3. Use `glyph-arts chat incplot` for raw tabular data.
4. Use `glyph-arts chat table` if visual inference is unclear.
5. Reply with a compact text table and explain the missing dependency.
