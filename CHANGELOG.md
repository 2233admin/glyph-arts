# Changelog

All notable changes to glyph-arts are documented here.
Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).
Versioning: [Semantic Versioning](https://semver.org/).

## [3.0.1] - 2026-04-15

### Fixed
- `confusion` chart: guard against plotext `ZeroDivisionError` on uniform confusion matrices
  (all cells equal -> `M-m=0` in internal color normalization). Falls back to Rich table render.
  Regression tests: `tests/test_confusion.py` (5 tests, issue #6).

## [3.0.0] - 2026-04-14

### Added
- **`image` chart type**: render any image file (PNG/JPEG/GIF/BMP/WebP) to
  the terminal via `chafa`. Supports 24-bit truecolor braille by default.
  Invocation: `glyph-arts image --file path/to.png --width 80 --height 24`.
  New flag `--symbols SET` exposes chafa's symbol selector (`braille`, `block`,
  `ascii`, `half`, `all`, etc.).
- **`video` chart type**: play a video file in the terminal by piping through
  `ffmpeg` -> `chafa`. Frames extracted to a tempdir at a configurable fps,
  then streamed with cursor-home + hide-cursor ANSI escapes for minimal
  flicker. New flag `--fps N` (default 12). Reuses `--duration SEC` to clip.
  Invocation: `glyph-arts video --file clip.mp4 --width 100 --height 30 --fps 15`.
- `chart.py --check-deps` now reports `chafa` and `ffmpeg` availability.

### Changed
- **Architectural split**: charts -> native engine (plotext/rich/drawille/
  plotille/uniprint); images and video -> shell out to chafa+ffmpeg. Rationale
  in HANDOFF 2026-04-14: the `curve` Bresenham polyline renderer is unsuitable
  for image data (every consecutive point-pair gets connected -> silhouettes
  become filled blobs), so pixel-accurate media work belongs with a purpose-
  built tool. chafa is a superset of timg/viu on Windows and pre-installed
  via `scoop install chafa`.
- Top-level docstring and `--help` now list 29 types (was 27).

### Removed
- `draw_cat.py`, `draw_crane.py`, `draw_cyberpunk.py`, `_draw_helpers.py`,
  `_smoke.png` -- failed-experiment scratch files from the image-via-curve
  dead-end. `img_to_curve.py` is kept; it still works for edge-only single-
  stroke ASCII art if a polyline renderer ever materializes.

## [2.4.1] - 2026-04-14

### Fixed
- **step chart LTTB formula**: render point count corrected to `2N-1` (was `2N-2`).
  50 LTTB-sampled points now produce 99 render points, not 98.
- **dashboard subprocess delegation**: `chart.py dashboard` type now delegates to
  `dashboard.py` via subprocess and propagates exit code faithfully. Adds
  `--no-interactive` automatically when stdout is not a tty.

### Added
- `dashboard.py --check-deps`: checks `rich` and `textual`, exits `0` if all
  present or `2` if any missing. Consistent with `chart.py --check-deps`.
- `tests/test_step_sampling.py`: two tests verifying LTTB -> step transform
  pipeline order and correct render point count (lttb path + uniform stride fallback).

## [2.4.0] - 2026-04-13

### Added
- `pie` chart type via plotext (`plt.pie()`). JSON: `{"labels":[], "values":[]}`.
  DuckDB: `col0=labels, col1=values`.
- `confusion` chart type: ML confusion matrix from `{"actual":[], "predicted":[], "labels":[]}`.
- `event` chart type: timeline plot from `{"data":[x1, x2, ...]}`.
- `indicator` chart type: big KPI number from `{"value":23.4, "label":"Return %"}`.
- `box` chart type: box-and-whisker from `{"data":[[s1],[s2]], "labels":["A","B"]}`.
- `heatmap` chart type: 2D matrix via `{"matrix":[[]], "xlabels":[], "ylabels":[]}`.
- `--sample N` flag: LTTB-aware downsampling for line/scatter/step/uniplot/kline.
- `--duckdb SQL` + `--db PATH`: query a DuckDB file and pipe results directly to any chart type.
- Session logging: set `CLI_CHARTS_LOG=1` to append render history to `.chart_history.jsonl`.

## [2.3.0] - 2026-04-12

### Added
- `dashboard` type: multi-panel Textual TUI or Rich static fallback.
  Delegates to `scripts/dashboard.py`. Supports gauge, sparkline, table, metric, bar panels.
- `--no-interactive` flag on `dashboard.py`: forces Rich static output (pipe-safe).
- `--xlim`, `--ylim`: axis range clamping for plotext charts.
- `--xscale`, `--yscale`: linear/log axis scaling.
- `--output FILE`: save plotext chart to file instead of stdout.

## [2.2.0] - 2026-04-11

### Added
- `graph` type: ASCII network graph via `networkx` + `phart`.
  JSON: `{"edges":[["A","B"]], "directed":true, "node_style":"ROUND"}`.
- `banner` type: large ASCII text via `pyfiglet`.
  JSON: `{"text":"HELLO", "font":"big", "color":"green"}`.
- `--no-color` flag and `NO_COLOR` env var support.

## [2.1.0] - 2026-04-10

### Added
- `curve` type: high-resolution Braille Unicode curves via `drawille`.
- `uniplot` type: scientific axis formatting via `uniplot`.
- `sparkline` type: single-row inline sparkline via `sparklines`.
- `tree` and `panel` rich types.
- `--orientation horizontal` for bar/multibar/stackedbar.

## [2.0.0] - 2026-04-09

### Added
- Initial public release.
- 13 plotext types: kline/candlestick, line, scatter, step, bar, multibar, stackedbar, hist.
- 3 rich types: table, gauge, pie.
- `--check-deps` flag.
- `--sample N` placeholder (LTTB added in 2.4.0).
- Structured stderr error tags: `ERROR:json:`, `ERROR:schema:`, `ERROR:dep:`, `ERROR:render:`.
- Exit codes: 0 success, 1 bad input, 2 missing dep, 4 render error.
